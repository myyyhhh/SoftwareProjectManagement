from pydantic import BaseModel, Field

# API 接收的请求体
class GenerationRequest(BaseModel):
    product_doc: str = Field(..., description="产品说明书或参考文件的纯文本内容")
    content_type: str = Field(..., description="要生成的内容类型，例如：'blog', 'video', 'case_study'")

# 审查节点的内部反馈结构
class ReviewFeedback(BaseModel):
    is_approved: bool = Field(..., description="内容是否完全符合品牌一致性且没有格式错误")
    feedback: str = Field(..., description="如果不通过，给出具体的修改指令；如果通过，填 'OK'")

# 最终输出给前端的结构化数据
class FinalContent(BaseModel):
    title: str = Field(..., description="生成内容的标题")
    content: str = Field(..., description="生成的最终正文、脚本或案例分析")