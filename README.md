# BiliBili Summarize | AI 视频深度分析助手

**一键提取 B 站视频字幕、弹幕、评论及关键帧画面，通过 AI 多模态大模型生成深度总结、思维导图及舆情分析报告。**

<div align="center">

![BiliBili Logo](https://img.shields.io/badge/BiliBili-FF6699?style=for-the-badge&logo=bilibili&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-green?style=for-the-badge&logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey?style=for-the-badge)

[快速开始](#🚀-快速开始) • [功能特性](#✨-功能特性) • [技术栈](#🛠️-技术栈) • [致谢](#🙏-致谢)

</div>

## ✨ 功能特性

- **📋 深度内容总结**：秒级提炼视频章节与核心知识点。
- **🖼️ 多模态视觉分析**：结合视频关键帧，画面细节不遗漏。
- **💬 舆情价值深挖**：看透弹幕热梗与评论区高赞观点。
- **🤖 智能对话问答**：针对视频内容进行深度互动追问。
- **🔐 B 站登录支持**：支持扫码登录以获取更高质量的评论与互动数据。
- **🎨 现代艺术化 UI**：极致流畅的响应式设计，支持深色模式。

## 🚀 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境**
   复制 `.env.example` 为 `.env` 并填写您的硅基流动的key即可。
   或者直接进入面板后，通过右上角设置按钮，点击配置硅基流动的key，即可立即开始使用。

3. **启动应用**
   ```bash
   python app.py
   ```
   访问 `http://localhost:5000` 即可开始使用。

## 🏗️ 项目结构

```text
Bilibili_Analysis_Helper/
├── app.py              # 程序启动唯一入口
├── requirements.txt    # 核心依赖
├── .env.example        # 环境变量模板
├── README.md           # 项目文档
└── src/                # 核心源代码包
    ├── backend/        # 后端逻辑（B站服务、AI服务）
    ├── frontend/       # 前端网页资源（HTML、CSS、JS）
    └── config.py       # 系统统一配置文件
```

## 🛠️ 技术栈

- **后端**：Python (Flask), `bilibili-api-python`, `aiohttp`
- **前端**：原生 HTML/JS/CSS3, `Marked.js` (Markdown 渲染)
- **AI 引擎**：支持 OpenAI 兼容格式的所有视觉多模态大模型 (推荐：SiliconCloud, Qwen)

## 🙏 致谢



- [bilibili-api-python](https://github.com/Nemo2011/bilibili-api) - 强大的 B 站 API 封装库。

- [SiliconCloud](https://cloud.siliconflow.cn/) - 提供极速算力支持。

- [LobeHub Icons](https://github.com/lobehub/lobe-icons) - 精美的厂商图标支持。



---



## 💖 赞助与支持

如果您觉得这个项目对您有所帮助，欢迎请作者喝杯咖啡 ☕。您的支持是我持续维护和开发新功能的动力！

<div align="center">

![Sponsor QR Code](assets/donate.jpg)

*扫码赞赏，备注“B站总结”*

</div>



---

Created by [mumu_xsy](https://gitcode.com/mumu_xsy) | [项目仓库](https://gitcode.com/mumu_xsy/Bilibili_Analysis_Helper)
