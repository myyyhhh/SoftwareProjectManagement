# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导入路由
from api.upload import router as upload_router

# 初始化 FastAPI 应用
app = FastAPI(
    title="内容智能体 API",
    description="软件项目管理 - 第12组 - 后端接口",
    version="1.0.0"
)

# 配置 CORS 跨域请求 (为了让前端 React 可以成功访问后端)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 实际部署时建议改成前端实际的 URL，如 ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(upload_router, prefix="/api/v1/files", tags=["文件处理"])

# 根目录健康检查接口
@app.get("/")
def read_root():
    return {"message": "Welcome to Group 12 Content Agent API!"}

# 本地启动代码
if __name__ == "__main__":
    print("🚀 正在启动项目，访问 http://127.0.0.1:8000/docs 查看接口文档...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)