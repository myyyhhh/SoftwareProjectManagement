from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ContentType(str, Enum):
    BLOG = "blog"               # 博客文章
    CASE_STUDY = "case_study"   # 案例研究
    VIDEO_SCRIPT = "script"     # 视频脚本

class DocumentSchema(BaseModel):
    filename: str
    content: str = Field(..., description="清洗后的纯文本内容")
    token_count: Optional[int] = None  # 预估的 token 数量


class GenerateRequest(BaseModel):
    # 核心输入
    raw_text: str = Field(..., min_length=10, description="产品说明书的文本内容")
    content_type: ContentType = Field(..., description="想要生成的类型")
    
    # 可选配置
    brand_style_id: Optional[str] = "default"  # 选用的品牌风格指南ID
    target_audience: Optional[str] = "通用受众" 
    additional_notes: Optional[str] = None    # 用户额外备注，如“幽默一点”


class VideoScriptScene(BaseModel):
    scene_number: int
    visual: str = Field(..., description="画面描述")
    audio: str = Field(..., description="旁白/对话内容")

class VideoScriptResponse(BaseModel):
    title: str
    scenes: List[VideoScriptScene]
    estimated_duration: str # 预计时长

class ArticleResponse(BaseModel):
    title: str
    outline: List[str]  # 目录/大纲
    content: str        # 正文内容
    keywords: List[str] # 关键词/标签

class ResponseModel(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None