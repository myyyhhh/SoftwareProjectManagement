# from pydantic import BaseModel, Field
# from typing import List, Optional
# from enum import Enum


# class ContentType(str, Enum):
#     """生成内容类型"""
#     BLOG = "blog"               # 博客文章
#     CASE_STUDY = "case_study"   # 案例研究
#     VIDEO_SCRIPT = "script"     # 视频脚本

# class DocumentSchema(BaseModel):
#     """文档模型"""
#     filename: str
#     content: str = Field(..., description="清洗后的纯文本内容")
#     token_count: Optional[int] = None  # 预估的 token 数量


# class GenerateRequest(BaseModel):
#     """生成内容请求"""
#     # 核心输入
#     raw_text: str = Field(..., min_length=10, description="产品说明书的文本内容")
#     content_type: ContentType = Field(..., description="想要生成的类型")
    
#     # 可选配置
#     brand_style_id: Optional[str] = "default"  # 选用的品牌风格指南ID
#     target_audience: Optional[str] = "通用受众" 
#     additional_notes: Optional[str] = None    # 用户额外备注，如“幽默一点”


# class VideoScriptScene(BaseModel):
#     """视频脚本场景"""
#     scene_number: int
#     visual: str = Field(..., description="画面描述")
#     audio: str = Field(..., description="旁白/对话内容")

# class VideoScriptResponse(BaseModel):
#     """视频脚本响应"""
#     title: str
#     scenes: List[VideoScriptScene]
#     estimated_duration: str # 预计时长

# class ArticleResponse(BaseModel):
#     """文章响应"""
#     title: str
#     outline: List[str]  # 目录/大纲
#     content: str        # 正文内容
#     keywords: List[str] # 关键词/标签

# class ResponseModel(BaseModel):
#     """响应模型"""
#     code: int = 200
#     message: str = "success"
#     data: Optional[dict] = None


# backend/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

# ==========================================
# 1. 枚举类型定义
# ==========================================
class ContentType(str, Enum):
    BLOG = "blog"
    CASE_STUDY = "case_study"
    VIDEO_SCRIPT = "video_script"

# ==========================================
# 2. API 请求与响应模型 (与前端交互)
# ==========================================
class GenerateRequest(BaseModel):
    content_type: ContentType = Field(..., description="生成内容的类型")
    topic: str = Field(..., description="用户提供的主题或关键词")
    reference_text: str = Field(..., description="经过解析后的产品说明或参考资料文本")
    brand_guidelines: Optional[str] = Field(None, description="品牌风格指南文本")

class BaseResponse(BaseModel):
    status: str = Field(default="success")
    message: str
    data: Optional[dict] = None

class ParseResult(BaseModel):
    """解析结果的数据结构"""
    filename: str        # 文件名
    file_type: str       # 文件类型
    text_length: int     # 纯文本长度
    extracted_text: str  # 纯文本内容

# ==========================================
# 3. LLM 强制结构化输出模型 (传给大模型的 JSON Schema)
# ==========================================

# 3.1 博客文章结构
class BlogSection(BaseModel):
    heading: str = Field(..., description="段落小标题")
    content: str = Field(..., description="段落正文")

class BlogOutput(BaseModel):
    title: str = Field(..., description="吸引人的博客标题")
    introduction: str = Field(..., description="博客引言")
    sections: List[BlogSection] = Field(..., description="博客正文分段")
    conclusion: str = Field(..., description="总结与行动呼吁(CTA)")
    seo_tags: List[str] = Field(..., description="SEO 关键词标签，不超过5个")

# 3.2 案例研究结构
class CaseStudyOutput(BaseModel):
    title: str = Field(..., description="案例研究标题")
    background: str = Field(..., description="客户背景介绍")
    challenge: str = Field(..., description="客户面临的核心挑战或痛点")
    solution: str = Field(..., description="我们提供的解决方案（结合产品说明）")
    results: List[str] = Field(..., description="取得的成效（条目式，可量化指标优先）")
    conclusion: str = Field(..., description="案例总结")

# 3.3 视频脚本结构 (体现分镜规范)
class VideoScene(BaseModel):
    scene_number: int = Field(..., description="镜头编号")
    visual: str = Field(..., description="画面描述/视觉元素")
    audio: str = Field(..., description="旁白/对话内容")
    duration_seconds: int = Field(..., description="预估镜头时长(秒)")

class VideoScriptOutput(BaseModel):
    title: str = Field(..., description="视频主题名称")
    target_audience: str = Field(..., description="目标受众描述")
    scenes: List[VideoScene] = Field(..., description="分镜头脚本列表")
    total_duration_estimate: int = Field(..., description="总预估时长(秒)")

# ==========================================
# 4. LangGraph 状态机模型 (用于节点间传递数据)
# ==========================================
class AgentState(BaseModel):
    task_id: str
    content_type: str
    source_material: str
    current_draft: Optional[dict] = None
    feedback: Optional[str] = None # 审查节点给出的修改意见
    iteration_count: int = 0       # 循环修改次数