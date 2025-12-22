# BiliBili AI 助手 - 浏览器扩展

这是 **BiliBiliSummarize** 的纯前端版本。它**不需要运行任何 Python 后端**，直接在浏览器中与 B 站 API 和 AI 服务通信。

## 核心特性
- **零依赖**：不需要安装 Python 或运行 `app.py`。
- **全量功能**：支持视频信息获取、字幕提取、AI 流式总结。
- **隐私安全**：所有的 API Key 存储在浏览器的本地存储 (`chrome.storage.local`) 中，不经过任何中转服务器。
- **即插即用**：配置好 SiliconFlow 或 OpenAI 的 Key 后即可在任何 B 站视频页使用。

## 安装步骤
1. 打开 Chrome/Edge/浏览器，进入 `扩展程序` 管理页面 (`chrome://extensions/`)。
2. 开启右上角的 **开发者模式**。
3. 点击 **加载解压的扩展程序**。
4. 选择当前项目中的 `extension_standalone` 文件夹。

## 配置指南
1. 点击插件图标，点击右上角的 **⚙️ (设置)** 图标。
2. 输入你的 **API Key**（已默认填充你系统 `.env` 中的 SiliconFlow Key）。
3. 检查 **API Base** 和 **Model** 是否正确。
4. 点击 **保存配置**。

## 开发者说明
- 本版本使用了 B 站的原生 Web API 提取字幕，无需 Cookie 即可获取大部分视频的官方 CC 字幕。
- 使用 `fetch` 直接调用 AI 接口，支持 SSE 流式渲染，体验流畅。
- 由于是纯前端实现，部分受 WBI 签名限制的 API（如高级搜索）可能无法直接使用，但总结和文本提取功能不受影响。
