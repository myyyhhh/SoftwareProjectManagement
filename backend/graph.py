import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_moonshot import ChatMoonshot
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from schemas import ReviewFeedback, FinalContent
from tools import load_skill

load_dotenv()

# 定义全局状态 (State)
class AgentState(TypedDict):
    product_doc: str  # 产品文档
    content_type: str # 内容类型
    messages: Annotated[list, add_messages] # 自动累加对话历史
    is_approved: bool # 是否彻底完工
    final_data: dict  # 是否彻底完工

# 初始化大模型
llm = ChatMoonshot(
    model="moonshot-v1-128k",  # 根据你的产品说明书长度选择 8k, 32k 或 128k
    temperature=0.7,
)

# 绑定工具的生成器 LLM
generator_llm = llm.bind_tools([load_skill])
# 绑定结构化输出的 LLM
critic_llm = llm.with_structured_output(ReviewFeedback)
formatter_llm = llm.with_structured_output(FinalContent)

# 构建工具节点
tool_node = ToolNode([load_skill])

# --- 节点函数 ---

def generator_node(state: AgentState):
    """Maker 节点：负责起草和修改"""
    messages = state["messages"]
    # 如果是第一次运行，注入系统提示词和用户文档
    if not messages:
        sys_msg = SystemMessage(
            content=f"你是一个专业的品牌内容创作者。当前任务是撰写 {state['content_type']}。"
                    f"务必先调用 load_skill 工具，获取 'brand' 规范以及 '{state['content_type']}' 格式规范再开始写作。"
        )
        user_msg = HumanMessage(content=f"产品说明参考：\n{state['product_doc']}")
        messages = [sys_msg, user_msg]

    response = generator_llm.invoke(messages)
    
    # 如果是第一次运行，我们需要把 sys_msg 和 user_msg 一并返回，让它们被存入 State
    if not state["messages"]:
        return {"messages": messages + [response]}
    else:
        return {"messages": [response]}

def reviewer_node(state: AgentState):
    """Checker 节点：负责审核品牌一致性"""
    messages = state["messages"]
    last_ai_message = messages[-1].content
    
    review_prompt = f"""
    你是一个严苛的品牌合规审核员。请检查以下生成的 {state['content_type']} 草稿：
    1. 是否使用了恰当的品牌基调？
    2. 格式是否符合该媒介的要求？
    
    草稿内容：
    {last_ai_message}
    """
    # 强制输出 ReviewFeedback 的结构化反馈
    feedback = critic_llm.invoke([HumanMessage(content=review_prompt)])
    
    if feedback.is_approved:
        # 优化提示词，强制大模型以结构化的形式（函数调用）返回标题和正文
        prompt = f"你必须使用提供的工具/JSON格式返回结果！请从以下草稿中提取最终结果并剥离其他无关对话。\n草稿：\n{last_ai_message}"
        final = formatter_llm.invoke([HumanMessage(content=prompt)])
        
        # 增加容错：如果大模型死活不返回函数调用，导致 final 是 None
        if final is None:
            final_data = {
                "title": "默认标题（需调整）", 
                "content": last_ai_message
            }
        else:
            final_data = final.model_dump()
            
        return {
            "is_approved": True, 
            "final_data": final_data,
            "messages": [AIMessage(content="审核通过，流程结束。")]
        }
    else:
        # 如果不通过，将意见以 HumanMessage 打回给生成器
        return {
            "is_approved": False,
            "messages": [HumanMessage(content=f"品牌审核未通过。请根据以下意见修改并重新输出：{feedback.feedback}")]
        }

# --- 路由函数 ---

def should_continue(state: AgentState):
    """决定是去执行工具，还是去送审"""
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "reviewer"

def route_review(state: AgentState):
    """决定是结束，还是打回重写"""
    if state["is_approved"]:
        return END
    return "generator"

# --- 编译图结构 ---
workflow = StateGraph(AgentState)

workflow.add_node("generator", generator_node)
workflow.add_node("tools", tool_node)
workflow.add_node("reviewer", reviewer_node)

workflow.set_entry_point("generator")

# 生成器完成后，根据路由决定去执行工具还是送审
workflow.add_conditional_edges("generator", should_continue, {"tools": "tools", "reviewer": "reviewer"})
# 工具执行完后，永远回到生成器
workflow.add_edge("tools", "generator")
# 审查节点完成后，根据是否通过决定去向
workflow.add_conditional_edges("reviewer", route_review, {"generator": "generator", END: END})

# 编译为可执行应用
app = workflow.compile()