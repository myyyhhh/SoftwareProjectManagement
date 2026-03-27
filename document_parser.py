# document_parser.py

def extract_text_from_file(uploaded_file) -> str:
    """
    【接口说明】解析用户上传的文档，提取纯文本。
    
    Args:
        uploaded_file: Streamlit 的 UploadedFile 对象 (包含文件名和字节流)
        
    Returns:
        str: 提取出的纯文本字符串。如果解析失败，返回错误提示文本。
    """
    # 1. 获取文件名和后缀名
    file_name = uploaded_file.name
    
    # 2. 根据后缀名进入不同的解析逻辑 (这里需要2号同学去写具体实现)
    if file_name.endswith('.pdf'):
        # 伪代码：return parse_pdf(uploaded_file)
        pass
    elif file_name.endswith('.docx'):
        # 伪代码：return parse_docx(uploaded_file)
        pass
    elif file_name.endswith('.txt'):
        # 伪代码：return uploaded_file.getvalue().decode("utf-8")
        pass
    else:
        raise ValueError("不支持的文件格式！")
        
    return "这里是解析出来的长长长长的产品说明书纯文本..."