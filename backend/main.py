import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# 导入你定义的路由模块
from api import upload
# 导入配置和工具
# from config import UPLOAD_DIR
import os

def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 实例
    """
    app = FastAPI(
        title="内容智能体 (Content Agent) API",
        description="基于 LangGraph 的品牌内容自动化生成系统后端",
        version="1.0.0",
        # 这里定义的 docs_url 就是你访问 /docs 的路径
        docs_url="/docs", 
        redoc_url="/redoc"
    )

    # 1. 配置跨域资源共享 (CORS)
    origins = [
        "http://localhost:3000",    # React 默认开发地址
        "http://127.0.0.1:3000",
        # 如果有生产环境域名，也加在这里
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,       # 允许访问的源
        allow_credentials=True,      # 允许携带 Cookie
        allow_methods=["*"],         # 允许所有 HTTP 方法 (GET, POST, etc.)
        allow_headers=["*"],         # 允许所有 HTTP 请求头
    )

    # 2. 注册路由 (Router)
    # 将不同功能的接口模块化
    app.include_router(upload.router, prefix="/api/v1", tags=["文件上传与解析"])
    # app.include_router(generate.router, prefix="/api/v1", tags=["AI 内容生成"])

    # # 3. 事件钩子：启动时确保环境就绪
    # @app.on_event("startup")
    # async def startup_event():
    #     # 自动创建临时上传目录，防止报错
    #     if not os.path.exists(UPLOAD_DIR):
    #         os.makedirs(UPLOAD_DIR)
    #         print(f"已创建临时目录: {UPLOAD_DIR}")
    #     print("后端服务已启动...")

    # 4. 根路径检查（健康检查）
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "Welcome to Content Agent API",
            "status": "running",
            "docs": "/docs"
        }

    return app

app = create_app()


if __name__ == "__main__":
    # 本地开发运行：python main.py
    # reload=True 表示代码修改后自动重启
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)