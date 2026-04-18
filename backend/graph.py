import operator
import os
from pathlib import Path
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_moonshot import ChatMoonshot

from schemas import FactCheckFeedback, FinalContent, ReviewFeedback
from tools import load_skill

PROJECT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT.parent
load_dotenv(REPO_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "skills" / ".env", override=False)


class AgentState(TypedDict):
    source_material: str               # 聚合后的原始资料（文件/网页/文本）
    product_spec: str                  # 从原始资料中提炼出的品牌与产品规范
    content_type: str                  # 输出类型：blog/video/case_study...
    user_prompt: str                   # 用户补充的品牌规范、禁用词、额外要求
    messages: Annotated[list, add_messages]
    is_review_approved: bool
    is_fact_checked: bool
    final_data: dict
    status_updates: Annotated[list[str], operator.add]


llm = ChatMoonshot(
    model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-128k"),
    temperature=0.3,
)

generator_llm = llm.bind_tools([load_skill])
critic_llm = llm.with_structured_output(ReviewFeedback)
fact_checker_llm = llm.with_structured_output(FactCheckFeedback)
formatter_llm = llm.with_structured_output(FinalContent)

tool_node = ToolNode([load_skill])


def analyzer_node(state: AgentState):
    """提炼产品信息 + 合并用户品牌要求"""
    if state.get("product_spec"):
        return {"status_updates": ["⏭️ 已存在品牌规范，跳过提炼"]}

    analyze_prompt = f"""
你是一个资深品牌策略师。请根据【原始资料】和【用户附加要求】提炼一份后续生成要严格遵守的品牌/产品规范。

输出要求：
1. 总字数控制在 220 字以内。
2. 必须包含以下内容：
   - 核心卖点（最多 3 条）
   - 目标受众
   - 推荐语气与风格
   - 明确禁区/不要写的内容（若资料中没有，就写“不要虚构未提供的功能/数据/案例”）
   - 用户特别追加的要求（若有）
3. 只输出规范本身，不要解释。

【用户附加要求】
{state.get('user_prompt', '') or '无'}

【原始资料】
{state['source_material']}
"""
    response = llm.invoke([HumanMessage(content=analyze_prompt)])
    return {
        "product_spec": response.content,
        "status_updates": ["🔎 已完成品牌特征提炼"]
    }


def generator_node(state: AgentState):
    """根据品牌规范生成内容；若收到打回意见，则继续修改"""
    messages = state["messages"]

    if not messages:
        sys_msg = SystemMessage(
            content=(
                f"你是一个专业的品牌内容创作者，当前任务是撰写 {state['content_type']}。\n"
                f"你必须严格遵守以下品牌/产品规范：\n{state.get('product_spec', '')}\n\n"
                f"附加要求：{state.get('user_prompt', '') or '无'}\n"
                "开始写作前，优先调用 load_skill 工具读取该内容类型的格式要求。"
                "写作时只允许使用源资料里能被支持的信息；如果资料里没有，就不要编造。"
            )
        )
        user_msg = HumanMessage(
            content=(
                f"请基于以下原始资料撰写最终 {state['content_type']} 内容。\n\n"
                f"【原始资料】\n{state['source_material']}"
            )
        )
        messages = [sys_msg, user_msg]

    response = generator_llm.invoke(messages)

    if not state["messages"]:
        return {
            "messages": messages + [response],
            "status_updates": [f"📝 已生成首版 {state['content_type']} 草稿"]
        }

    return {
        "messages": [response],
        "status_updates": [f"✏️ 已根据审核意见重写 {state['content_type']} 草稿"]
    }


def reviewer_node(state: AgentState):
    """品牌风格、格式、语气审核，不负责事实真实性"""
    last_message = state["messages"][-1]
    last_ai_message = getattr(last_message, "content", "")

    review_prompt = f"""
你是一个严苛的品牌与格式审核员。请只检查下面草稿的：
1. 是否符合用户追加要求
2. 是否符合品牌基调
3. 是否符合 {state['content_type']} 的格式习惯
4. 是否存在明显跑题、空话、过度营销或语气失衡

注意：此轮不检查事实真伪，事实真伪交给后续 fact-checker。

【品牌规范】
{state.get('product_spec', '')}

【用户附加要求】
{state.get('user_prompt', '') or '无'}

【待审核草稿】
{last_ai_message}
"""
    feedback = critic_llm.invoke([HumanMessage(content=review_prompt)])

    if feedback.is_approved:
        return {
            "is_review_approved": True,
            "status_updates": ["✅ 品牌/格式审核通过"]
        }

    return {
        "is_review_approved": False,
        "messages": [
            HumanMessage(content=f"品牌审核未通过，请严格按以下意见修改：{feedback.feedback}")
        ],
        "status_updates": ["🔁 品牌/格式审核未通过，已打回重写"]
    }


def fact_checker_node(state: AgentState):
    """新增防幻觉阶段：将草稿回查原始资料，禁止虚构功能/数据/案例"""
    last_message = state["messages"][-1]
    last_ai_message = getattr(last_message, "content", "")

    fact_prompt = f"""
你是一个强硬的事实核查员。请把【待核查草稿】逐条回查【原始资料】。

核查规则：
1. 不能把资料里没有的功能、参数、案例、客户、数据、奖项、承诺写进去。
2. 可以做语言润色，但不能新增未经证实的事实。
3. 对每一项可疑表述，指出具体问题并给出可执行修改建议。
4. 若草稿整体可被资料支撑，则判定通过。

输出时务必遵守结构化字段要求。

【原始资料】
{state['source_material']}

【待核查草稿】
{last_ai_message}
"""

    feedback = fact_checker_llm.invoke([HumanMessage(content=fact_prompt)])

    if feedback.is_grounded:
        return {
            "is_fact_checked": True,
            "status_updates": ["🛡️ 事实核查通过"]
        }

    unsupported = "；".join(feedback.unsupported_claims) if feedback.unsupported_claims else "未指明具体句子，请按反馈整体修订"
    advice = feedback.feedback or "请删除未经证实的内容，并改写为源资料可支持的表述。"
    return {
        "is_fact_checked": False,
        "messages": [
            HumanMessage(
                content=(
                    "事实核查未通过。请只保留源资料能支持的内容，删除或改写以下未经证实的表述："
                    f"{unsupported}。\n修改建议：{advice}"
                )
            )
        ],
        "status_updates": ["🚫 事实核查未通过，已打回重写"]
    }


def formatter_node(state: AgentState):
    """将通过审查的草稿格式化为结构化输出"""
    last_message = state["messages"][-1]
    last_ai_message = getattr(last_message, "content", "")

    prompt = f"""
请将以下最终草稿转为结构化结果：
1. title: 生成一个准确、克制、符合内容主题的标题
2. content: 保留正文完整内容

不要添加额外解释。

草稿：
{last_ai_message}
"""
    final = formatter_llm.invoke([HumanMessage(content=prompt)])
    final_data = final.model_dump() if final else {"title": "默认标题（需人工确认）", "content": last_ai_message}
    return {
        "final_data": final_data,
        "status_updates": ["🎉 已完成最终结构化输出"]
    }


def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "reviewer"


def route_review(state: AgentState):
    if state["is_review_approved"]:
        return "fact_checker"
    return "generator"


def route_fact_check(state: AgentState):
    if state["is_fact_checked"]:
        return "formatter"
    return "generator"


workflow = StateGraph(AgentState)
workflow.add_node("analyzer", analyzer_node)
workflow.add_node("generator", generator_node)
workflow.add_node("tools", tool_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("fact_checker", fact_checker_node)
workflow.add_node("formatter", formatter_node)

workflow.set_entry_point("analyzer")
workflow.add_edge("analyzer", "generator")
workflow.add_conditional_edges("generator", should_continue, {"tools": "tools", "reviewer": "reviewer"})
workflow.add_edge("tools", "generator")
workflow.add_conditional_edges("reviewer", route_review, {"fact_checker": "fact_checker", "generator": "generator"})
workflow.add_conditional_edges("fact_checker", route_fact_check, {"formatter": "formatter", "generator": "generator"})
workflow.add_edge("formatter", END)

app = workflow.compile()
