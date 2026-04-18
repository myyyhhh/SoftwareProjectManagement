# SoftwareProjectManagement

> 2026春，软件项目管理，分组12

## 项目基本信息

内容智能体——轻量化品牌内容自动生成工具：自动将产品/品牌素材生成博客、案例研究、视频脚本

## 📖 项目简介

本项目目标是做一个**内容智能体**——能 轻量化品牌内容自动生成工具：自动将产品/品牌素材生成博客、案例研究、视频脚本

本项目是一个全栈应用，包含 React 前端界面和 Python 后端服务。

它允许用户上传产品文档（PDF/DOCX/图片）或提供网页链接，选择内容类型（博客、案例研究、视频脚本），系统将通过 **LangGraph** 构建的多阶段工作流自动生成高质量、符合品牌规范且经过事实核查的内容。

### 核心特性

- 🛡️ **品牌一致性审核**：自动提炼品牌规范，确保生成内容的语气、风格与品牌调性一致。
- 🕵️ **防幻觉事实核查**：独立的事实核查节点，将生成内容与源材料比对，杜绝虚构数据或功能。
- 📄 **多格式支持**：支持 PDF, DOCX, 图片 (OCR) 及网页 URL 作为输入源。
- 🎯 **多场景输出**：支持生成博客文章、案例研究 (Case Study) 和视频脚本。
- ⚡ **实时流式响应**：后端支持 SSE 流式输出，前端实时展示生成进度。

## 🏗️ 技术栈

### 前端 (react-frontend)
- **框架**: React 18
- **样式**: Tailwind CSS
- **构建工具**: Create React App (react-scripts)
- **状态管理**: React Hooks (`useState`, `useEffect`, `useRef`)

### 后端 (backend)
- **框架**: FastAPI
- **AI 编排**: LangGraph (StateGraph)
- **LLM 提供商**: Moonshot AI (月之暗面) / 兼容 OpenAI 接口
- **文档处理**: PyMuPDF (PDF), python-docx (Word), OpenAI/VLM (图片 OCR)
- **其他**: Uvicorn, Pydantic, LangChain

## 📂 项目结构

```text
SoftwareProjectManagement/
├── react-frontend/          # 前端项目目录
│   ├── public/
│   ├── src/
│   │   ├── App.js           # 主组件：文件上传、类型选择、结果展示
│   │   ├── index.js         # 入口文件
│   │   └── index.css        # Tailwind 样式入口
│   ├── package.json
│   └── tailwind.config.js
├── backend/                 # 后端项目目录
│   ├── main.py              # FastAPI 入口，定义 API 接口
│   ├── graph.py             # LangGraph 工作流定义 (Analyzer -> Generator -> Reviewer -> FactChecker -> Formatter)
│   ├── schemas.py           # Pydantic 数据模型
│   ├── tools.py             # LangChain 工具 (加载技能提示词)
│   ├── utils.py             # 文件解析工具 (PDF/DOCX/Image/Web)
│   └── skills/              # 不同内容类型的写作规范提示词
│       ├── blog.md           # 博客skill
│       ├── case_study.md     # 案例研究skill
│       └── video.md          # 视频脚本skill
└── README.md
