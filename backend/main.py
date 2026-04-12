from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from schemas import GenerationRequest
from graph import app as agent_workflow
from utils import extract_text_from_file
import uvicorn

app = FastAPI(title="Brand-Consistent Content Agent API")

def run_content_generation_agent(product_doc_text: str, content_type: str) -> dict:
    """
    具体的模型调用逻辑：只接收处理好的字符串，不关心 HTTP 请求和文件对象。
    """
    # 构造初始状态
    initial_state = {
        "product_doc": product_doc_text,
        "product_spec": "",
        "content_type": content_type,
        "messages": [],
        "is_approved": False,
        "final_data": {}
    }

    # 触发 LangGraph 分析
    try:
        result = agent_workflow.invoke(initial_state, {"recursion_limit": 10})
        return result["final_data"]
    except Exception as e:
        # 这里可以记录大模型调用失败的日志
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"大模型内容生成失败: {str(e)}")

@app.post("/generate_from_file")
async def generate_content_from_file(
    content_type: str = Form(..., description="要生成的内容类型 (例如: blog, video)"),
    file: UploadFile = File(..., description="上传的PDF或Word文档")
    # 如果未来需要额外的前端输入/提示词，可以直接在这里加一个参数：
    # user_prompt: str = Form("", description="用户额外的补充提示词")
):
    try:
        # 第一关：前置校验文件合法性，不合法直接打回（不走大模型）
        if not (file.filename.endswith(".pdf") or file.filename.endswith(".docx")):
            raise HTTPException(status_code=400, detail="只允许上传 .pdf 或 .docx 文件")

        # 第二关：读取与解析文件，不合法直接打回
        file_bytes = await file.read()
        try:
            product_doc_text = extract_text_from_file(file_bytes, file.filename)
        except ValueError as ve:
             raise HTTPException(status_code=400, detail=str(ve))
             
        if not product_doc_text or not product_doc_text.strip():
            raise HTTPException(status_code=400, detail="无法从文件中提取到有效文本，文件可能为空。")

        # 第三关：文件处理完毕且合法，调用封装好的业务函数
        # (如果传入了额外的 user_prompt，你可以把 product_doc_text 和 user_prompt 拼接后传给模型)
        final_data = run_content_generation_agent(
            product_doc_text=product_doc_text, 
            content_type=content_type
        )

        # 正常返回
        return {
            "status": "success",
            "content_type": content_type,
            "filename": file.filename,
            "data": final_data
        }

    except HTTPException:
        # 将我们主动抛出的 400 错误原样抛出给前端
        raise
    except RuntimeError as re:
        # 捕获大模型崩溃的异常
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        # 捕获其他未知错误
        raise HTTPException(status_code=500, detail="服务器内部发生了意外错误。")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)