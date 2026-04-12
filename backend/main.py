from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from schemas import GenerationRequest
from graph import app as agent_workflow
from utils import extract_text_from_file
import uvicorn

app = FastAPI(title="Brand-Consistent Content Agent API")

@app.post("/generate_from_file")
async def generate_content_from_file(
    content_type: str = Form(..., description="要生成的内容类型 (例如: blog, video)"),
    file: UploadFile = File(..., description="上传的PDF或Word文档")
):
    try:
        # 1. 验证文件后缀
        if not (file.filename.endswith(".pdf") or file.filename.endswith(".docx")):
            raise HTTPException(status_code=400, detail="只允许上传 .pdf 或 .docx 文件")

        # 2. 读取文件并提取文本
        file_bytes = await file.read()
        product_doc_text = extract_text_from_file(file_bytes, file.filename)
        
        if not product_doc_text:
            raise HTTPException(status_code=400, detail="无法从文件中提取到有效文本")

        # 3. 构造初始状态 (使用提取出的文档文本)
        initial_state = {
            "product_doc": product_doc_text,
            "content_type": content_type,
            "messages": [],
            "is_approved": False,
            "final_data": {}
        }

        # 4. 触发 LangGraph 分析
        result = agent_workflow.invoke(initial_state, {"recursion_limit": 10})

        return {
            "status": "success",
            "content_type": content_type,
            "filename": file.filename,
            "data": result["final_data"]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()  # 打印完整报错堆栈到控制台
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)