from typing import List
from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    product_doc: str = Field(..., description="产品说明书或参考文件的纯文本内容")
    content_type: str = Field(..., description="要生成的内容类型，例如：blog、video、case_study")
    user_prompt: str = Field(default="", description="用户补充的品牌要求、禁用词、语气要求等")


class ReviewFeedback(BaseModel):
    is_approved: bool = Field(..., description="内容是否符合品牌一致性、语气和格式要求")
    feedback: str = Field(..., description="若不通过，给出具体修改意见；若通过，返回 OK")


class FactCheckFeedback(BaseModel):
    is_grounded: bool = Field(..., description="内容是否被源材料支撑，是否不存在明显幻觉")
    feedback: str = Field(..., description="若不通过，给出可执行的修改建议；若通过，返回 OK")
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="没有证据支撑、需要删除或改写的说法",
    )
    evidence_snippets: List[str] = Field(
        default_factory=list,
        description="用于支持判断的源文档片段",
    )


class FinalContent(BaseModel):
    title: str = Field(..., description="生成内容的标题")
    content: str = Field(..., description="生成的最终正文、脚本或案例分析")
