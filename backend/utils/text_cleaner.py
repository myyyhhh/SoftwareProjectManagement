# backend/utils/text_cleaner.py
import re

class TextCleaner:
    @staticmethod
    def clean_parsed_text(text: str) -> str:
        """
        清洗解析出来的文本，去除多余的空格、换行和特殊不可见字符，
        以节省传给大模型时的 Token 消耗。
        """
        if not text:
            return ""
        
        # 1. 替换多个连续空格为一个空格
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 2. 替换多个连续换行符为一个或两个换行符
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 3. 去除首尾空白
        text = text.strip()
        
        return text