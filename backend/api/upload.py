# backend/api/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
import uuid

from config import TEMP_UPLOAD_DIR
from service.parser_service import DocumentParserService
from models.schemas import BaseResponse, ParseResult

router = APIRouter()

@router.post("/parse", response_model=BaseResponse)
async def upload_and_parse_file(file: UploadFile = File(...)):
    """
    接收前端上传的文件 -> 存入临时目录 -> 解析提取文本 -> 删除临时文件 -> 返回给前端
    """
    # 1. 校验文件后缀
    allowed_extensions = {"txt", "pdf", "docx", "doc"}
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    # 2. 生成唯一文件名，防止高并发时文件被覆盖
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(TEMP_UPLOAD_DIR, unique_filename)

    try:
        # 3. 保存文件到本地临时目录
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 4. 调用 Service 解析出纯文本
        extracted_text = DocumentParserService.extract_and_clean_text(file_path, file.filename)
        
        # 5. 构造返回数据
        parse_result = ParseResult(
            filename=file.filename,
            file_type=file_ext,
            text_length=len(extracted_text),
            extracted_text=extracted_text
        )

        return BaseResponse(
            status="success",
            message="文件解析成功",
            data=parse_result.model_dump()
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")
    
    finally:
        # 6. 【重要】清理临时文件！无论成功还是抛出异常，最后一定删除临时文件防止磁盘爆满
        if os.path.exists(file_path):
            os.remove(file_path)