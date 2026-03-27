# app.py
import streamlit as st

# 导入接口
from document_parser import extract_text_from_file
from prompt_template import build_llm_messages
from llm_api import call_ai_generator

st.title("🤖 产品文案生成器")

# --- UI 侧边栏：收集品牌参数 ---
with st.sidebar:
    st.header("文案要求")
    tone = st.text_input("品牌语调", value="专业且平易近人")
    audience = st.text_input("目标受众", value="在校学生")
    forbidden_words = st.text_input("禁忌词", value="同行竞品名称")

# --- 主界面：上传与选择 ---
st.header("上传产品说明书")
uploaded_file = st.file_uploader("支持 PDF, Word, TXT", type=['pdf', 'docx', 'txt'])

content_type = st.selectbox("3. 选择生成类型", ["博客文章", "案例研究", "视频脚本"])

st.divider() 

# --- 核心调度逻辑 ---
if st.button("🚀 开始生成内容") and uploaded_file is not None:
    
    with st.spinner("1️⃣ 正在解析文档..."):
        # 调用 document_parser 的接口
        parsed_text = extract_text_from_file(uploaded_file)
        
    with st.spinner("2️⃣ 正在注入品牌资产并组装提示词..."):
        # 调用 prompt_template 的接口
        messages = build_llm_messages(parsed_text, content_type, tone, audience, forbidden_words)
        
    with st.spinner("3️⃣ AI 正在奋笔疾书，请稍候..."):
        # 调用 llm_api 的接口
        final_result = call_ai_generator(messages)
        
    # --- 显示结果 ---
    st.success("✨ 生成成功！")
    st.markdown("### 最终结果")
    st.write(final_result)