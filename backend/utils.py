import fitz  # PyMuPDF
import docx
import io

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    text = ""
    # 判断是否为 PDF
    if filename.endswith('.pdf'):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text()
    
    # 判断是否为 Word
    elif filename.endswith('.docx'):
        doc = docx.Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            text += para.text + "\n"
    
    else:
        raise ValueError("不支持的文件格式，仅支持 .pdf 和 .docx")
        
    return text.strip()