# SoftwareProjectManagement
软件项目管理，分组12，

```
backend/
├── main.py # 项目入口，启动文件
├── api/ # API 路由层
│ ├── __init__.py
│ ├── upload.py # 上传接口（文件/文本）
│ └── generate.py # AI 内容生成接口
│
├── service/ # 业务逻辑层（核心）
│ ├── __init__.py
│ ├── parser_service.py # PDF/DOCX/TXT 解析服务
│ └── ai_service.py # AI 调用、LangGraph 服务
│
├── utils/ # 工具类
│ ├── __init__.py
│ └── text_cleaner.py # 文本清洗工具
│
├── models/ # 数据模型
│ ├── __init__.py
│ └── schemas.py # Pydantic 结构体
│
├── config.py # 配置（模型key、路径等）
├── requirements.txt
└── .gitignore 

```

