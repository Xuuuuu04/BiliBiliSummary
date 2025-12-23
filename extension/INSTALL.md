# 🎉 BiliBili Summarize AI - 浏览器插件

> 完整的 B 站视频 AI 智能分析插件

## ✅ 已完成的文件

```
extension/
├── 📄 manifest.json          # 插件配置文件
├── 🔧 background.js          # 后台服务
├── 🖼️  popup.html/js/css      # 弹窗界面
├── 📄 options.html/js        # 设置页面
├── 🎬 content-script.js      # 页面注入脚本
├── 🎨 content-style.css      # B站风格样式
├── 🌐 bilibili-api.js        # B站API封装（JS版）
├── 📹 video-processor.js     # 视频处理器
├── 🤖 ai-service.js          # AI服务
├── 💻 ui-components.js       # UI组件
├── 🖼️  icon*.png             # 图标文件（16/48/128）
└── 📖 README.md              # 使用说明
```

## 🚀 快速开始

### 1️⃣ 安装插件

1. 打开 **Chrome** 或 **Edge** 浏览器
2. 访问 `chrome://extensions/` （Edge是 `edge://extensions/`）
3. 打开右上角的 **「开发者模式」**
4. 点击 **「加载已解压的扩展程序」**
5. 选择文件夹：`I:\BiliBiliSummarize\extension`
6. ✅ 插件安装成功！

### 2️⃣ 配置AI模型

#### 方式一：使用扩展弹窗（推荐）

1. 点击浏览器工具栏的插件图标
2. 填写API配置：
   - **API地址**：`https://api.siliconflow.cn/v1`
   - **API密钥**：你的密钥
   - **文本模型**：`Qwen/Qwen2.5-72B-Instruct`
   - **视觉模型**：`Qwen/Qwen2-VL-72B-Instruct`
3. 点击「保存配置」
4. 等待状态变为「已连接」

#### 方式二：使用设置页面

1. 在扩展管理页面点击「详细信息」
2. 点击「扩展程序选项」
3. 在设置页面填写配置信息

### 3️⃣ 获取免费API密钥（可选）

**SiliconFlow（推荐，有免费额度）：**
1. 访问：https://cloud.siliconflow.cn
2. 注册账号
3. 进入「API密钥」页面
4. 创建新密钥

**其他选择：**
- OpenAI：https://platform.openai.com
- 通义千问：https://dashscope.aliyuncs.com
- 智谱AI：https://open.bigmodel.cn

## 📖 使用方法

### 分析视频

1. 访问任意B站视频页面
2. 视频标题旁会出现 **「AI分析」** 按钮
3. 点击按钮开始分析

### 查看结果

分析完成后可以查看：
- 📝 **总结**：AI生成的视频内容总结
- 💬 **字幕**：完整字幕，可一键复制
- 💭 **弹幕**：热门弹幕采样
- 🗨️ **评论**：高赞评论列表
- 🤖 **问答**：基于视频内容的AI对话

## 🎨 界面预览

- **B站蓝色渐变**主题
- **5个功能标签页**
- **流畅动画效果**
- **浮动快捷按钮**
- **响应式设计**

## 🔧 技术特性

### ✨ 核心功能

- ✅ **零依赖部署**：完全基于浏览器原生API
- ✅ **Cookie复用**：自动利用B站登录状态
- ✅ **bilibili-api迁移**：完整的Python库JS移植
  - WBI签名算法
  - 视频信息API
  - 字幕/弹幕/评论API
- ✅ **多模态分析**：视频+文本综合分析
- ✅ **隐私保护**：数据本地处理

### 🛠️ 技术栈

- **Vanilla JavaScript**：无框架依赖
- **Chrome Extension API**：Manifest V3
- **Fetch API**：网络请求
- **Canvas API**：视频帧提取
- **Chrome Storage API**：配置存储

## 📊 数据流程

```
用户点击分析
    ↓
获取B站Cookie
    ↓
收集数据：
├── 视频信息（bilibili-api）
├── 字幕内容
├── 弹幕采样（最多1000条）
├── 评论精选（前100条）
└── 视频关键帧（Canvas截图）
    ↓
构建AI Prompt
    ↓
调用OpenAI兼容API
    ↓
流式返回结果
    ↓
显示在面板中
```

## 🐛 故障排除

### 插件无法加载

❌ **错误**：找不到图标文件
✅ **解决**：运行 `python generate_icons.py` 生成图标

❌ **错误**：无法加载选项页
✅ **解决**：确保 `options.html` 和 `options.js` 存在

### 分析失败

❌ **错误**：API连接失败
✅ **解决**：
1. 检查API地址是否正确
2. 确认API密钥有效
3. 查看网络连接

❌ **错误**：获取视频信息失败
✅ **解决**：
1. 确认已登录B站
2. 刷新页面重试
3. 检查视频是否可用

## 🎯 未来计划

- [ ] 支持番剧分析
- [ ] 支持专栏文章深度分析
- [ ] 添加分析历史记录
- [ ] 支持本地LLM（Ollama）
- [ ] 导出分析报告
- [ ] 批量分析功能
- [ ] 自定义Prompt模板

## 📝 更新日志

### v1.0.0 (2024-12-23)
- ✨ 首次发布
- ✅ 完整的bilibili-api JavaScript移植
- ✅ 视频分析功能
- ✅ AI问答功能
- ✅ 字幕提取复制
- ✅ B站风格UI
- ✅ 多模态分析支持

## 📄 许可证

MIT License

## 🙏 致谢

- [bilibili-api](https://github.com/Nemo2011/bilibili-api) - Python版B站API库
- [BiliBili](https://www.bilibili.com) - 哔哩哔哩

---

💡 **提示**：推荐使用 [SiliconFlow](https://cloud.siliconflow.cn) 的免费API进行体验！
