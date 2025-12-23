/**
 * Content Script - B站页面注入脚本
 * 改进版：流式分析 + 详细进度显示
 */

// 全局实例
let biliProcessor = null;
let aiService = null;
let ui = null;
let currentVideoData = null;

/**
 * 初始化
 */
async function init() {
    console.log('[BiliSummarize] Initializing...');

    // 初始化组件
    biliProcessor = new VideoProcessor();
    await biliProcessor.init();

    aiService = new AIService();
    ui = new UIComponents();

    // 检查当前页面类型
    const pageType = detectPageType();

    if (pageType === 'video') {
        // 视频页面 - 添加浮动按钮
        setTimeout(() => {
            const floatBtn = ui.createFloatingButton();
            document.body.appendChild(floatBtn);
        }, 1000);
    }

    // 监听事件
    setupEventListeners();

    console.log('[BiliSummarize] Initialized');
}

/**
 * 检测页面类型
 */
function detectPageType() {
    const url = window.location.href;

    if (url.includes('/video/')) return 'video';
    if (url.includes('/read/')) return 'article';
    if (url.includes('/opus/')) return 'opus';
    if (url.includes('space.bilibili.com')) return 'user';

    return 'other';
}

/**
 * 检查是否使用登录状态（Cookie）- 修复版
 */
async function checkLoginStatus() {
    try {
        // 尝试从 background script 获取 Cookie
        if (typeof chrome !== 'undefined' && chrome.runtime) {
            const response = await chrome.runtime.sendMessage({
                action: 'getBiliCookies'
            });

            if (response && response.cookies) {
                const hasSESSDATA = !!response.cookies['SESSDATA'];
                const hasBiliJct = !!response.cookies['bili_jct'];
                console.log('[BiliSummarize] Cookie check:', { hasSESSDATA, hasBiliJct });
                return hasSESSDATA && hasBiliJct;
            }
        }
    } catch (e) {
        console.warn('[BiliSummarize] Failed to check cookies via background:', e);
    }

    // 降级：检查 document.cookie
    const cookies = document.cookie;
    const hasSESSDATA = cookies.includes('SESSDATA');
    const hasBiliJct = cookies.includes('bili_jct');
    console.log('[BiliSummarize] Document cookie check:', { hasSESSDATA, hasBiliJct });
    return hasSESSDATA && hasBiliJct;
}

/**
 * 分析当前视频 - 流式版本
 */
async function analyzeCurrentVideo() {
    try {
        // 1. 检查登录状态
        const usingCookie = await checkLoginStatus();

        // 2. 显示数据收集进度
        ui.showDataProgress({
            step: '正在获取视频信息...',
            usingCookie: usingCookie,
            hasSubtitle: false,
            subtitleLength: 0,
            frameCount: 0,
            commentCount: 0,
            danmakuCount: 0
        });

        // 3. 获取视频BVID
        const bvid = biliProcessor.getCurrentPageBVID();
        if (!bvid) {
            throw new Error('无法获取视频BVID');
        }

        // 4. 收集视频数据
        ui.showDataProgress({
            step: '正在收集视频数据...',
            usingCookie: usingCookie,
            hasSubtitle: false,
            frameCount: 0,
            commentCount: 0,
            danmakuCount: 0
        });

        currentVideoData = await biliProcessor.collectVideoData(bvid, {
            needFrames: false,  // 暂时不提取帧，简化处理
            needDanmaku: true,
            needComments: true,
            needSubtitle: true,
            maxComments: 30
        });

        // 5. 更新收集到的数据统计
        const hasSubtitle = currentVideoData.subtitle?.hasSubtitle || false;
        const subtitleLength = currentVideoData.subtitle?.text?.length || 0;
        const frameCount = currentVideoData.frames?.frames?.length || 0;
        const commentCount = currentVideoData.comments?.comments?.length || 0;
        const danmakuCount = currentVideoData.danmaku?.count || 0;

        ui.showDataProgress({
            step: '数据收集完成',
            usingCookie: usingCookie,
            hasSubtitle: hasSubtitle,
            subtitleLength: subtitleLength,
            frameCount: frameCount,
            commentCount: commentCount,
            danmakuCount: danmakuCount
        });

        // 6. 开始AI流式分析
        await performStreamAnalysis(currentVideoData);

    } catch (e) {
        console.error('[BiliSummarize] Analyze failed:', e);
        ui.showToast('分析失败: ' + e.message);
        ui.updateStatus('active', '分析失败');
    }
}

/**
 * 执行流式AI分析
 */
async function performStreamAnalysis(videoData) {
    try {
        // 切换到AI分析状态
        ui.showAIAnalyzing();

        // 准备流式内容
        ui.streamContent = '';

        // 构建提示词
        const prompt = buildAnalysisPrompt(videoData);

        // 调用流式API
        await streamAnalysis(prompt);

        // 分析完成
        ui.showAnalyzeComplete();

    } catch (e) {
        console.error('[BiliSummarize] Stream analysis failed:', e);
        ui.showToast('AI分析失败: ' + e.message);
        ui.updateStatus('active', '分析失败');
    }
}

/**
 * 构建分析提示词
 */
function buildAnalysisPrompt(videoData) {
    const { info, subtitle, danmaku, comments } = videoData;

    let prompt = `你是B站视频内容分析专家，请对以下视频进行深度分析：

【视频基本信息】
标题：${info?.title || '未知'}
UP主：${info?.owner?.name || '未知'}
时长：${info ? Math.floor(info.duration / 60) + '分' + (info.duration % 60) + '秒' : '未知'}
播放量：${info?.stat?.view || 0}  点赞：${info?.stat?.like || 0}
`;

    // 添加字幕内容
    if (subtitle && subtitle.text) {
        prompt += `
【视频字幕】（${subtitle.text.length}字符）
${subtitle.text.substring(0, 3000)}${subtitle.text.length > 3000 ? '...' : ''}
`;
    } else {
        prompt += `
【视频字幕】无字幕
`;
    }

    // 添加弹幕样本
    if (danmaku && danmaku.danmaku && danmaku.danmaku.length > 0) {
        const danmakuText = danmaku.danmaku.slice(0, 30).map(d => d.text).join('\n');
        prompt += `
【弹幕样本】（共${danmaku.count || danmaku.danmaku.length}条）
${danmakuText}
`;
    }

    // 添加评论样本
    if (comments && comments.comments && comments.comments.length > 0) {
        const commentText = comments.comments.slice(0, 15).map(c =>
            `${c.username || c.member?.uname || '用户'}: ${c.message || c.content || ''}`
        ).join('\n');
        prompt += `
【热门评论】（共${comments.comments.length}条）
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
给出3-5个描述内容的标签。`;

    return prompt;
}

/**
 * 流式分析API调用
 */
async function streamAnalysis(prompt) {
    const config = aiService.config;

    if (!config.apiBase || !config.apiKey) {
        throw new Error('AI配置不完整');
    }

    const response = await fetch(`${config.apiBase}/chat/completions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${config.apiKey}`
        },
        body: JSON.stringify({
            model: config.model,
            messages: [{ role: 'user', content: prompt }],
            stream: true,
            temperature: config.temperature || 0.7,
            max_tokens: 4000
        })
    });

    if (!response.ok) {
        const error = await response.text();
        throw new Error(`API Error: ${response.status} - ${error}`);
    }

    // 读取流式响应
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
                        // 实时追加内容
                        ui.appendStreamContent(content);
                    }
                } catch (e) {
                    // 忽略解析错误
                }
            }
        }
    }
}

/**
 * 提取字幕
 */
async function extractCurrentSubtitle() {
    try {
        ui.showDataProgress({
            step: '正在提取字幕...',
            usingCookie: false,
            hasSubtitle: false,
            subtitleLength: 0,
            frameCount: 0,
            commentCount: 0,
            danmakuCount: 0
        });

        const bvid = biliProcessor.getCurrentPageBVID();
        if (!bvid) {
            throw new Error('无法获取视频BVID');
        }

        // 获取视频信息
        const info = await biliProcessor.getVideoInfo(bvid);
        const cid = info?.cid;

        if (!cid) {
            throw new Error('无法获取视频CID');
        }

        // 获取字幕
        const subtitleData = await biliProcessor.getVideoSubtitle(bvid, cid);

        ui.hideLoading();
        ui.showSubtitleResult(subtitleData);

    } catch (e) {
        console.error('[BiliSummarize] Extract subtitle failed:', e);
        ui.hideLoading();
        ui.showToast('提取失败: ' + e.message);
    }
}

/**
 * 设置事件监听
 */
function setupEventListeners() {
    // AI分析事件
    window.addEventListener('biliSummarizeAnalyze', () => {
        analyzeCurrentVideo();
    });

    // 字幕提取事件
    window.addEventListener('biliSummarizeSubtitle', () => {
        extractCurrentSubtitle();
    });

    // 配置更新事件
    window.addEventListener('biliSummarizeConfigUpdate', (event) => {
        const { config } = event.detail;
        if (aiService) {
            aiService.config = { ...aiService.config, ...config };
        }
        console.log('[BiliSummarize] Config updated:', config);
    });
}

/**
 * 启动
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
