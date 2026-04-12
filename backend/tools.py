import os
from langchain_core.tools import tool
import fitz  # PyMuPDF
import docx
import io

@tool
def load_skill(skill_name: str) -> str:
    """
    加载专业的技能提示词和品牌规范。
    可用的 skill_name 必须是以下之一:
    - brand: 品牌调性规范与禁用词检查清单
    - blog: 博客文章的排版和写作要求
    - video: 视频脚本的分镜格式要求
    """
    # 假设你的根目录下有一个 skills 文件夹
    file_path = os.path.join("skills", f"{skill_name}.md")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"系统提示：找不到名为 {skill_name} 的技能文件，请检查拼写。"