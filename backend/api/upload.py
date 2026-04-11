# backend/upload.py
"""


"""

# api/upload.py
from fastapi import APIRouter, UploadFile, File
from models.schemas import DocumentSchema # 导入模型

router = APIRouter()



@router.post("/upload", response_model=DocumentSchema) # 这里是关键！
async def upload_file(file: UploadFile):
    return DocumentSchema(filename="test.pdf", content="清洗后的内容")