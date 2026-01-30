<div align="center">
  <h1>BiliBili Summarize | AI-Powered In-depth Video Analysis Assistant</h1>
  <img src="assets/logo.svg" width="200" alt="BiliBili Summarize Logo">
  <h3>Master the Content, Deep Dive into Value</h3>
</div>

**One-click extraction of Bilibili video subtitles, danmaku, comments, and keyframes. Generates deep summaries, mind maps, and sentiment analysis reports using AI multimodal large language models.**

<div align="center">

[简体中文](README.md) | [English](README_EN.md) | [日本語](README_JP.md)

</div>

<div align="center">

![BiliBili Logo](https://img.shields.io/badge/BiliBili-FF6699?style=for-the-badge&logo=bilibili&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey?style=for-the-badge)

[Quick Start](#🚀-quick-start) • [Features](#✨-features) • [Screenshots](#🖼️-screenshots) • [Tech Stack](#🛠️-tech-stack) • [Acknowledgements](#🙏-acknowledgements)

</div>

## ✨ Features

- **📋 Deep Content Summary**: Extract video chapters and core knowledge in seconds.
- **🖼️ Multimodal Visual Analysis**: Combines video keyframes so no visual detail is missed.
- **💬 Public Sentiment Mining**: Insight into danmaku memes and top-voted comments.
- **🤖 Intelligent Q&A**: Deeply interact with the video content through AI-powered chat.
- **📝 Article & Opus Analysis**: Support for logical deconstruction of Bilibili articles and "Opus" dynamic posts.
- **🎭 UP Creator Portrait**: Analyze creator style and value based on recent works.
- **🔐 Bilibili Login Support**: Scan QR code to login for higher-quality comments and interaction data.
- **🎨 Modern Artistic UI**: Ultra-smooth responsive design with Dark Mode support.

## 🖼️ Screenshots

### 🏠 Homepage Preview
![Homepage](assets/主页截图.png)

### ⚙️ Analysis Process
![Analysis Processing](assets/分析中.png)

### 📊 Deep Analysis Results
| Video Summary | Sentiment Analysis |
| :---: | :---: |
| ![Video Summary](assets/视频总结.png) | ![Danmaku Analysis](assets/弹幕分析.png) |

| Comment Analysis | Video Text Extraction |
| :---: | :---: |
| ![Comment Analysis](assets/评论分析.png) | ![Video Text Extraction](assets/视频文本提取.png) |

### 📝 Articles & Dialogue
| Opus Analysis | AI Dialogue |
| :---: | :---: |
| ![Opus Analysis](assets/专题文档解析.png) | ![AI Dialogue](assets/分析后AI对话.png) |

### 🎭 Creator Portrait
![Creator Portrait](assets/UP主画像.png)

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Copy `.env.example` to `.env` and fill in your API Key.
   Alternatively, configure it via the settings button in the UI after launching.

3. **Launch Application**
   ```bash
   uvicorn asgi:app --reload --host 0.0.0.0 --port 5001
   ```
   Visit `http://localhost:5001` to start analyzing.

## 🏗️ Project Structure

```text
Bilibili_Analysis_Helper/
├── asgi.py             # FastAPI entrypoint (recommended)
├── requirements.txt    # Core dependencies
├── .env.example        # Environment variable template
├── README.md           # Project documentation
└── src/                # Source code
    ├── backend/        # Domain capabilities (Bilibili/AI/tools; no HTTP)
    ├── backend_fastapi/# HTTP layer (FastAPI routes + orchestration)
    ├── frontend/       # Frontend assets (HTML, CSS, JS)
    └── config.py       # Global configuration
```

## 🛠️ Tech Stack

- **Backend**: Python (FastAPI), `bilibili-api-python`, `aiohttp`
- **Frontend**: Vanilla HTML/JS/CSS3, `Marked.js` (Markdown rendering)
- **AI Engine**: Supports all OpenAI-compatible vision multimodal models (Recommended: SiliconCloud, Qwen)

## 🙏 Acknowledgements

- [bilibili-api-python](https://github.com/Nemo2011/bilibili-api) - Powerful Bilibili API wrapper.
- [SiliconCloud](https://cloud.siliconflow.cn/) - High-speed computing power support.
- [LobeHub Icons](https://github.com/lobehub/lobe-icons) - Beautiful vendor icons.

---

## 💖 Sponsorship & Support

If you find this project helpful, feel free to buy the author a coffee ☕. Your support is the driving force for continuous maintenance and new features!

<div align="center">

![Sponsor QR Code](assets/donate.jpg)

*Scan to donate*

</div>

---

Created by [mumu_xsy](https://gitcode.com/mumu_xsy) | [Repository](https://gitcode.com/mumu_xsy/Bilibili_Analysis_Helper)
