# # parser_service.py
# """文档解析服务"""

# async def parse_file(file_path: str, file_extension: str) -> str:
#     """
#     文档解析
#     Args:
#         file_path(str): 文档路径
#         file_extension(str): 文档后缀名
#     Returns:
#         str: 解析后的文本
#     """

    
#     return 


# backend/service/parser_service.py
import os
from PyPDF2 import PdfReader
import docx
from utils.text_cleaner import TextCleaner

class DocumentParserService:
    @staticmethod
    def parse_txt(file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as file:
                return file.read()

    @staticmethod
    def parse_pdf(file_path: str) -> str:
        text_content = []
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content.append(extracted)
            return "\n".join(text_content)
        except Exception as e:
            raise ValueError(f"PDF解析失败: {str(e)}")

    @staticmethod
    def parse_docx(file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            text_content = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(text_content)
        except Exception as e:
            raise ValueError(f"DOCX解析失败: {str(e)}")

    @classmethod
    def extract_and_clean_text(cls, file_path: str, filename: str) -> str:
        """根据后缀解析文件，并调用 Cleaner 清洗文本"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"找不到文件: {file_path}")

        ext = filename.split('.')[-1].lower()
        raw_text = ""

        if ext == 'txt':
            raw_text = cls.parse_txt(file_path)
        elif ext == 'pdf':
            raw_text = cls.parse_pdf(file_path)
        elif ext in ['doc', 'docx']:
            raw_text = cls.parse_docx(file_path)
        else:
            raise ValueError(f"不支持的文件格式: .{ext}。目前仅支持 TXT, PDF, DOCX。")

        # 调用 utils 中的清洗工具
        cleaned_text = TextCleaner.clean_parsed_text(raw_text)
        return cleaned_text