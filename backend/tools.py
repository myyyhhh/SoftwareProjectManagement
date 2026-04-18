import os
from langchain_core.tools import tool


@tool
def load_skill(skill_name: str) -> str:
    """
    加载指定内容类型的写作技能提示词。
    可用 skill_name 示例：
    - blog
    - case_study
    - video
    """
    file_path = os.path.join("skills", f"{skill_name}.md")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"系统提示：找不到名为 {skill_name} 的技能文件，请检查拼写。"
