# prompt_template.py

def build_llm_messages(parsed_text: str, content_type: str, tone: str, audience: str, forbidden_words: str) -> list:
    """将所有参数组装成大模型 API 需要的格式。
    
    Args:
        parsed_text (str): 刚才解析出来的产品说明书文本
        content_type (str): "博客文章" | "案例研究" | "视频脚本"
        tone (str): 品牌语调，如"幽默风趣"
        audience (str): 目标受众，如"大学生"
        forbidden_words (str): 违禁词，如"遥遥领先"
        
    Returns:
        list: 包含系统指令和用户输入的字典列表（OpenAI/DeepSeek标准格式）
    """
    
    # 1. 组装系统提示词
    system_prompt = f"""你是一个顶级的资深文案专家。
请严格遵守以下品牌护栏：
- 品牌语调：{tone}
- 目标人群：{audience}
- 绝对禁止使用的词汇：{forbidden_words}
如果违反以上任何一条，请重写！"""

    # 2. 组装任务提示词 (根据不同模板)
    if content_type == "博客文章":
        task_prompt = f"请根据以下产品资料，写一篇吸引人的博客，包含3个小标题。\n\n产品资料：\n{parsed_text}"
    elif content_type == "视频脚本":
        task_prompt = f"请根据以下产品资料，写一段60秒短视频脚本。必须以Markdown表格输出，表头为【镜头、画面描述、旁白】。\n\n产品资料：\n{parsed_text}"
    else:
        task_prompt = f"请根据以下产品资料写一篇案例研究。\n\n产品资料：\n{parsed_text}"

    # 3. 返回标准 Messages 列表
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task_prompt}
    ]
    
    return messages