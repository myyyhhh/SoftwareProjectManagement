前端项目 README

# 前端项目

本项目为前端部分，基于 React 开发，使用 Tailwind CSS 进行样式设计，实现项目核心前端页面与交互功能。

📋 项目介绍

该前端项目用于配合后端接口，提供简洁、高效的用户操作界面，包含核心业务页面的展示与交互，适配团队项目整体需求，代码结构规范，可直接运行与二次开发。

🔧 技术栈

- 核心框架：React

- 样式框架：Tailwind CSS

- 构建工具：npm

- 代码规范：遵循团队统一代码格式要求

📦 环境准备

确保本地已安装 Node.js（版本 ≥ 14.x）和 npm（版本 ≥ 6.x）。

检查环境：

node -v
npm -v

🚀 启动步骤

1. 克隆仓库到本地：
        git clone https://github.com/myyyhhh/SoftwareProjectManagement.git

2. 进入前端项目目录：
        cd SoftwareProjectManagement/react-frontend

3. 安装项目依赖：
        npm install

4. 启动本地开发服务器：
        npm start

5. 启动成功后，浏览器访问 http://localhost:3000即可查看项目。

📂 项目结构

react-frontend/
├── public/          # 静态资源目录
│   └── index.html   # 项目入口HTML
├── src/             # 核心代码目录
│   ├── App.js       # 根组件
│   ├── index.js     # 入口文件
│   └── index.css    # 全局样式（结合Tailwind）
├── package.json     # 项目依赖配置
├── tailwind.config.js # Tailwind样式配置
├── postcss.config.js  # PostCSS配置
├── .gitignore       # Git忽略文件配置
└── README.md        # 项目说明文档
