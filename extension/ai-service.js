/**
 * AI服务 - 处理所有AI相关功能
 * 支持OpenAI兼容的VL模型
 */

class AIService {
    constructor() {
        // 默认配置（与.env保持一致）
        this.config = {
            apiBase: 'https://api.siliconflow.cn/v1',
            apiKey: 'sk-kjfvtxdspxngnsgsmeciaycwitfpuyvnybokuivrliquzbbt',
            model: 'Qwen/Qwen3-Omni-30B-A3B-Captioner',
            vlModel: 'Qwen/Qwen3-Omni-30B-A3B-Captioner',  // 视觉模型
            temperature: 0.7
        };

        this.loadConfig();
    }

    /**
     * 加载配置
     */
    async loadConfig() {
        return new Promise((resolve) => {
            if (typeof chrome !== 'undefined' && chrome.storage) {
                chrome.storage.local.get(['aiConfig'], (result) => {
                    if (result.aiConfig) {
                        this.config = { ...this.config, ...result.aiConfig };
                    }
                    resolve();
                });
            } else {
                resolve();
            }
        });
    }

    /**
     * 保存配置
     */
    async saveConfig(config) {
        this.config = { ...this.config, ...config };

        if (typeof chrome !== 'undefined' && chrome.storage) {
            return new Promise((resolve) => {
                chrome.storage.local.set({ aiConfig: this.config }, resolve);
            });
        }
    }

    /**
     * 检查配置是否完整
     */
    isConfigured() {
        return !!(this.config.apiBase && this.config.apiKey);
    }

    /**
     * 调用OpenAI兼容API
     */
    async callAPI(messages, options = {}) {
        if (!this.isConfigured()) {
            throw new Error('AI配置不完整，请先设置API地址和密钥');
        }

        const {
            model = this.config.model,
            temperature = this.config.temperature,
            stream = false,
            maxTokens = 4000
        } = options;

        try {
            const response = await fetch(`${this.config.apiBase}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.config.apiKey}`
                },
                body: JSON.stringify({
                    model,
                    messages,
                    temperature,
                    stream,
                    max_tokens: maxTokens
                })
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`API Error: ${response.status} - ${error}`);
            }

            const data = await response.json();
            return data.choices[0].message.content;
        } catch (e) {
            console.error('[AIService] API call failed:', e);
            throw e;
        }
    }

    /**
     * 调用VL模型（多模态）
     */
    async callVLModel(text, images, options = {}) {
        if (!images || images.length === 0) {
            // 如果没有图片，使用普通模型
            return await this.callAPI([{ role: 'user', content: text }], options);
        }

        const model = options.model || this.config.vlModel || this.config.model;

        // 构建多模态消息
        const content = [
            { type: 'text', text }
        ];

        // 添加图片（最多8张）
        images.slice(0, 8).forEach(imgUrl => {
            if (imgUrl.startsWith('data:')) {
                // Base64图片
                content.push({
                    type: 'image_url',
                    image_url: { url: imgUrl }
                });
            } else {
                content.push({
                    type: 'image_url',
                    image_url: { url: imgUrl }
                });
            }
        });

        return await this.callAPI([{ role: 'user', content }], { ...options, model });
    }

    /**
     * 分析视频总结
     */
    async analyzeVideo(videoData) {
        const { info, subtitle, danmaku, comments, frames } = videoData;

        // 构建分析提示
        let prompt = `你是B站视频内容分析专家，请对以下视频进行深度分析：

【视频基本信息】
标题：${info.title}
UP主：${info.owner.name}
时长：${Math.floor(info.duration / 60)}分${info.duration % 60}秒
播放量：${info.stat.view}  点赞：${info.stat.like}
`;

        // 添加字幕内容
        if (subtitle && subtitle.text) {
            prompt += `
【视频字幕】
${subtitle.text}
`;
        }

        // 添加弹幕样本
        if (danmaku && danmaku.danmaku.length > 0) {
            const danmakuText = danmaku.danmaku.slice(0, 50).map(d => d.text).join('\n');
            prompt += `
【弹幕样本】（${danmaku.count}条）
${danmakuText}
`;
        }

        // 添加评论样本
        if (comments && comments.comments.length > 0) {
            const commentText = comments.comments.slice(0, 20).map(c =>
                `${c.username}: ${c.message}`
            ).join('\n');
            prompt += `
【热门评论】
${commentText}
`;
        }

        prompt += `
请输出结构化的分析报告，包括以下部分：

# 📹 视频总结
用简洁的语言总结视频的核心内容、主要观点和价值。

# 🎯 内容亮点
列出3-5个视频的亮点或特色。

# 💬 观众反馈
根据弹幕和评论，总结观众的反应和评价。

# 📊 数据洞察
分析视频数据（播放、点赞等），评估视频受欢迎程度。

# 🏷️ 内容标签
给出3-5个描述内容的标签标签。`;

        // 如果有视频帧，使用VL模型
        if (frames && frames.frames && frames.frames.length > 0) {
            prompt = `请结合视频画面和字幕弹幕，对以下B站视频进行多模态分析：\n\n` + prompt;
            return await this.callVLModel(prompt, frames.frames, {
                maxTokens: 3000
            });
        } else {
            return await this.callAPI([{ role: 'user', content: prompt }], {
                maxTokens: 3000
            });
        }
    }

    /**
     * 生成简短摘要（用于快速预览）
     */
    async generateQuickSummary(videoData) {
        const { info, subtitle } = videoData;

        let prompt = `请用2-3句话总结这个B站视频的核心内容：

标题：${info.title}
`;

        if (subtitle && subtitle.text) {
            prompt += `\n字幕内容：\n${subtitle.text.substring(0, 2000)}...`;
        }

        prompt += `\n\n请直接输出总结，不要有其他内容。`;

        return await this.callAPI([{ role: 'user', content: prompt }], {
            maxTokens: 500
        });
    }

    /**
     * 智能问答
     */
    async chat(videoData, question, history = []) {
        const { info, subtitle } = videoData;

        let context = `基于以下视频内容回答问题：

标题：${info.title}
UP主：${info.owner.name}

`;

        if (subtitle && subtitle.text) {
            context += `字幕内容：\n${subtitle.text}\n\n`;
        }

        const messages = [
            {
                role: 'system',
                content: '你是B站视频助手，基于视频内容回答用户问题。回答要准确、友好、有帮助。'
            },
            {
                role: 'user',
                content: context + `\n用户问题：${question}`
            }
        ];

        // 添加历史对话
        if (history && history.length > 0) {
            messages.push(...history);
        }

        return await this.callAPI(messages, {
            maxTokens: 2000
        });
    }

    /**
     * 分析用户画像
     */
    async analyzeUserPortrait(userData) {
        const { info, relation, videos } = userData;

        let prompt = `请分析以下B站UP主的创作风格和特点：

【基本信息】
昵称：${info.name}
等级：${info.level}
简介：${info.sign}

【数据统计】
粉丝数：${relation?.follower || 0}
关注数：${relation?.following || 0}

【代表作品】
${videos.slice(0, 10).map(v => `- ${v.title} (${v.play}播放)`).join('\n')}

请输出包含以下内容的分析：
1. 创作风格和内容类型
2. 视频特点（制作水平、风格等）
3. 粉丝画像推测
4. 内容价值评估`;

        return await this.callAPI([{ role: 'user', content: prompt }], {
            maxTokens: 2000
        });
    }

    /**
     * 分析专栏文章
     */
    async analyzeArticle(articleData) {
        const { title, content, author, stats } = articleData;

        let prompt = `请分析以下B站专栏文章：

【文章信息】
标题：${title}
作者：${author}
阅读量：${stats?.view || 0}

【文章内容】
${content.substring(0, 5000)}

请输出：
1. 文章主旨和核心观点
2. 论证逻辑分析
3. 价值评估
4. 关键信息提取`;

        return await this.callAPI([{ role: 'user', content: prompt }], {
            maxTokens: 2000
        });
    }

    /**
     * 流式分析
     */
    async *analyzeStream(videoData, onProgress) {
        if (!this.isConfigured()) {
            throw new Error('AI配置不完整');
        }

        const { info, subtitle, frames } = videoData;

        let prompt = this.buildAnalysisPrompt(info, subtitle);

        onProgress?.('准备分析...');

        try {
            const model = (frames && frames.frames?.length > 0)
                ? (this.config.vlModel || this.config.model)
                : this.config.model;

            const response = await fetch(`${this.config.apiBase}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.config.apiKey}`
                },
                body: JSON.stringify({
                    model,
                    messages: [{ role: 'user', content: prompt }],
                    stream: true,
                    temperature: this.config.temperature,
                    max_tokens: 4000
                })
            });

            onProgress?.('正在分析...');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);
                        if (jsonStr === '[DONE]') continue;

                        try {
                            const data = JSON.parse(jsonStr);
                            const content = data.choices[0]?.delta?.content;

                            if (content) {
                                yield content;
                            }
                        } catch (e) {
                            // 忽略解析错误
                        }
                    }
                }
            }
        } catch (e) {
            console.error('[AIService] Stream failed:', e);
            throw e;
        }
    }

    /**
     * 构建分析提示词
     */
    buildAnalysisPrompt(info, subtitle) {
        let prompt = `请深度分析这个B站视频：

【视频信息】
标题：${info.title}
UP主：${info.owner.name}
时长：${Math.floor(info.duration / 60)}分钟
`;

        if (subtitle && subtitle.text) {
            prompt += `\n【字幕内容】\n${subtitle.text.substring(0, 3000)}...\n`;
        }

        prompt += `
请输出包含以下部分的分析报告：

# 📹 视频总结
简洁总结视频核心内容

# 🎯 内容亮点
3-5个亮点

# 💬 观众反馈
基于弹幕和评论的分析

# 📊 数据洞察
数据分析

# 🏷️ 标签
3-5个标签`;

        return prompt;
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIService;
}
