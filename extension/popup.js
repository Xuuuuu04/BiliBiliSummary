/**
 * BiliBili AI 助手 - Popup 核心脚本
 * 纯前端实现：直接调用 B 站接口和 AI 接口
 */

// 默认配置
const DEFAULT_CONFIG = {
    apiKey: 'sk-kjfvtxdspxngnsgsmeciaycwitfpuyvnybokuivrliquzbbt',
    apiBase: 'https://api.siliconflow.cn/v1',
    model: 'Qwen/Qwen3-Omni-30B-A3B-Captioner'
};

document.addEventListener('DOMContentLoaded', async () => {
    // DOM 元素
    const elements = {
        apiKey: document.getElementById('api-key'),
        apiBase: document.getElementById('api-base'),
        apiModel: document.getElementById('api-model'),
        saveBtn: document.getElementById('save-settings'),
        toggleSettings: document.getElementById('toggle-settings'),
        settingsPanel: document.getElementById('settings-panel'),
        videoBox: document.getElementById('video-box'),
        vTitle: document.getElementById('v-title'),
        vAuthor: document.getElementById('v-author'),
        vBvid: document.getElementById('v-bvid'),
        btnAI: document.getElementById('btn-ai'),
        btnTxt: document.getElementById('btn-txt'),
        btnCopy: document.getElementById('btn-copy'),
        loading: document.getElementById('loading'),
        loadingText: document.getElementById('loading-text'),
        resultContainer: document.getElementById('result-container'),
        resultContent: document.getElementById('result-content'),
        error: document.getElementById('err')
    };

    let currentBvid = '';
    let videoData = null;

    // --- 基础初始化 ---
    try {
        const config = await chrome.storage.local.get(['apiKey', 'apiBase', 'model']);
        elements.apiKey.value = config.apiKey || DEFAULT_CONFIG.apiKey;
        elements.apiBase.value = config.apiBase || DEFAULT_CONFIG.apiBase;
        elements.apiModel.value = config.model || DEFAULT_CONFIG.model;

        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.url && tab.url.includes('bilibili.com/video/')) {
            currentBvid = extractBvid(tab.url);
            if (currentBvid) {
                elements.vBvid.textContent = currentBvid;
                elements.videoBox.style.display = 'block';
                await fetchVideoInfo(currentBvid);
            }
        } else {
            showError('请在 B 站视频播放页使用此插件');
            elements.btnAI.disabled = true;
            elements.btnTxt.disabled = true;
        }
    } catch (err) {
        console.error('Init error:', err);
    }

    // --- 事件监听 ---

    elements.toggleSettings.addEventListener('click', () => {
        const isVisible = elements.settingsPanel.style.display === 'block';
        elements.settingsPanel.style.display = isVisible ? 'none' : 'block';
    });

    elements.saveBtn.addEventListener('click', async () => {
        await chrome.storage.local.set({
            apiKey: elements.apiKey.value,
            apiBase: elements.apiBase.value,
            model: elements.apiModel.value
        });
        alert('配置已保存');
        elements.settingsPanel.style.display = 'none';
    });

    // 提取文本
    elements.btnTxt.addEventListener('click', async () => {
        if (!videoData) return;
        resetUI();
        showLoading('正在提取视频文本及相关信息...');
        try {
            const transcript = await getTranscript(currentBvid);
            const danmaku = await getDanmaku(videoData.cid);
            
            elements.loading.style.display = 'none';
            elements.resultContainer.style.display = 'block';
            
            let html = `<h3>视频原文本</h3><pre>${transcript}</pre>`;
            if (danmaku) html += `<h3>精选弹幕</h3><pre>${danmaku}</pre>`;
            elements.resultContent.innerHTML = html;
        } catch (e) {
            showError(`内容提取失败: ${e.message}`);
            elements.loading.style.display = 'none';
        }
    });

    // AI 智能总结
    elements.btnAI.addEventListener('click', async () => {
        if (!videoData) return;
        resetUI();
        showLoading('正在全维度采集视频数据...', '正在提取画面、字幕、弹幕及评论...');

        try {
            // 并行获取所有数据（含画面帧）
            const [transcript, danmaku, comments, frames] = await Promise.all([
                getTranscript(currentBvid),
                getDanmaku(videoData.cid),
                getComments(videoData.aid),
                extractVideoFrames(currentBvid, videoData.cid)
            ]);

            showLoading('AI 正在进行多模态分析...', `已采集 ${frames.length} 帧画面，生成报告中...`);

            const prompt = `你是一位严谨的B站视频分析专家。你的任务是基于我提供的全维度素材生成一份准确无误、深度且专业的分析报告。

【分析准则 - 严禁幻觉】
1. **视觉与文本交叉验证**：我提供了视频的关键帧截图。请结合画面中的文字、代码或实物，与字幕内容进行交叉校验。
2. **仅限素材**：所有结论必须直接来源于提供的素材。禁止编造。

【视频基本信息】
标题：${videoData.title}
UP主：${videoData.owner.name}
简介：${videoData.desc}

【视频文本内容 (字幕/文案)】
${transcript.substring(0, 10000)}

【互动舆情 (弹幕与评论)】
弹幕：${danmaku.substring(0, 1000)}
评论：${comments.substring(0, 1500)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
请严格按照以下**三大板块**提供深度分析报告：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 第一板块：内容深度总结与分析
### 1. 视频核心概览
- **核心主旨**：用一句话精准概括视频。
- **目标价值**：视频解决了什么核心问题？提供了什么独特价值？
### 2. 结构化内容详述
- 按逻辑顺序，**精细化**提取核心论据、关键步骤、数据支撑和典型案例。深度解析内容背后的逻辑。
### 3. 关键知识点与深度见解
- **事实罗列**：列出视频中提到的核心知识点。
- **深度延伸**：分析其在更广阔背景下的意义。

## 💬 第二板块：弹幕互动与舆情分析
- **氛围洞察**：分析观众在哪一时刻反响最热烈，情绪倾向如何。
- **互动槽点**：捕捉视频中的“梗”、争议点或共鸣点。

## 📝 第三板块：评论区深度解析与建议
- **评论画像**：分析高赞评论的构成（干货补充/质疑讨论/情感共鸣）。
- **优化建议**：基于目前的观众反馈，为UP主提供具体可执行的改进方向。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**格式要求**：使用 Markdown，大量使用**加粗**，适当使用 Emoji。`;

            await callAIService(prompt, frames, (chunk) => {
                elements.loading.style.display = 'none';
                elements.resultContainer.style.display = 'block';
                renderStreamingContent(chunk);
            });

        } catch (e) {
            showError(`总结生成失败: ${e.message}`);
            elements.loading.style.display = 'none';
        }
    });

    elements.btnCopy.addEventListener('click', () => {
        navigator.clipboard.writeText(elements.resultContent.innerText);
        elements.btnCopy.textContent = '已复制';
        setTimeout(() => elements.btnCopy.textContent = '复制', 2000);
    });

    // --- 核心业务函数 ---

    function extractBvid(url) {
        const match = url.match(/BV[a-zA-Z0-9]+/);
        return match ? match[0] : '';
    }

    async function fetchVideoInfo(bvid) {
        try {
            const resp = await fetch(`https://api.bilibili.com/x/web-interface/view?bvid=${bvid}`);
            const json = await resp.json();
            if (json.code === 0) {
                videoData = json.data;
                elements.vTitle.textContent = videoData.title;
                elements.vAuthor.textContent = `UP: ${videoData.owner.name}`;
            }
        } catch (e) {
            showError('请求视频接口失败');
        }
    }

    async function getTranscript(bvid) {
        if (!videoData) throw new Error('未获取到视频信息');
        try {
            const playerUrl = `https://api.bilibili.com/x/player/v2?bvid=${bvid}&cid=${videoData.cid}`;
            const playerResp = await fetch(playerUrl);
            const playerData = await playerResp.json();
            const subtitles = playerData.data?.subtitle?.subtitles;
            if (subtitles && subtitles.length > 0) {
                const targetSub = subtitles.find(s => s.lan.includes('zh')) || subtitles[0];
                const subUrl = targetSub.subtitle_url.replace(/^\/\/, 'https://');
                const subContentResp = await fetch(subUrl);
                const subJson = await subContentResp.json();
                return subJson.body.map(item => item.content).join(' ');
            }
        } catch (e) {}
        return `[无官方字幕] 视频简介：${videoData.desc}`;
    }

    /**
     * 关键升级：提取视频关键帧 (多模态支持)
     */
    async function extractVideoFrames(bvid, cid) {
        try {
            const shotUrl = `https://api.bilibili.com/x/player/videoshot?bvid=${bvid}&cid=${cid}`;
            const resp = await fetch(shotUrl);
            const json = await resp.json();
            if (json.code !== 0 || !json.data?.image || json.data.image.length === 0) return [];

            const spriteUrl = json.data.image[0].replace(/^\/\/, 'https://');
            const img = new Image();
            img.crossOrigin = "Anonymous";
            await new Promise((r, j) => { img.onload = r; img.onerror = j; img.src = spriteUrl; });

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const cellW = img.width / 10;
            const cellH = img.height / 10;
            canvas.width = cellW;
            canvas.height = cellH;

            const frames = [];
            const positions = [0, 20, 40, 60, 80]; // 采样 5 帧
            for (const pos of positions) {
                const row = Math.floor(pos / 10), col = pos % 10;
                ctx.clearRect(0, 0, cellW, cellH);
                ctx.drawImage(img, col * cellW, row * cellH, cellW, cellH, 0, 0, cellW, cellH);
                frames.push(canvas.toDataURL('image/jpeg', 0.5).split(',')[1]);
            }
            return frames;
        } catch (e) { return []; }
    }

    async function getDanmaku(cid) {
        try {
            const resp = await fetch(`https://api.bilibili.com/x/v1/dm/list.so?oid=${cid}`);
            const text = await resp.text();
            const dNodes = new DOMParser().parseFromString(text, "text/xml").getElementsByTagName("d");
            const danmakus = [];
            for (let i = 0; i < Math.min(dNodes.length, 150); i++) danmakus.push(dNodes[i].textContent);
            return danmakus.join(' | ');
        } catch (e) { return ''; }
    }

    async function getComments(aid) {
        try {
            const resp = await fetch(`https://api.bilibili.com/x/v2/reply?type=1&oid=${aid}&sort=2&ps=30`);
            const json = await resp.json();
            if (json.code === 0 && json.data?.replies) {
                return json.data.replies.map(r => `${r.member.uname}: ${r.content.message}`).join('\n');
            }
            return '';
        } catch (e) { return ''; }
    }

    async function callAIService(prompt, frames, onChunk) {
        const apiKey = elements.apiKey.value;
        const apiBase = elements.apiBase.value.replace(/\/$/, '');
        const userContent = [{ type: 'text', text: prompt }];
        for (const base64 of frames) {
            userContent.push({ type: 'image_url', image_url: { url: `data:image/jpeg;base64,${base64}`, detail: 'low' } });
        }

        const response = await fetch(`${apiBase}/chat/completions`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: elements.apiModel.value,
                messages: [
                    { role: 'system', content: '你是一位精通视频内容、画面视觉与用户心理的B站深度分析专家。' },
                    { role: 'user', content: userContent }
                ],
                stream: true
            })
        });

        if (!response.ok) throw new Error('AI 接口请求失败');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            const lines = decoder.decode(value).split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        const content = data.choices[0].delta.content || '';
                        fullContent += content;
                        onChunk(fullContent);
                    } catch (e) {}
                }
            }
        }
    }

    function renderStreamingContent(text) {
        let html = text
            .replace(/^# (.*$)/gm, '<h1>$1</h1>').replace(/^## (.*$)/gm, '<h2>$1</h2>').replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━/gm, '<hr style="border:0; border-top:1px solid #eee; margin:20px 0;">').replace(/^\d\. (.*$)/gm, '<li>$1</li>').replace(/^\* (.*$)/gm, '<li>$1</li>').replace(/^\- (.*$)/gm, '<li>$1</li>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        elements.resultContent.innerHTML = html;
        elements.resultContainer.scrollTop = elements.resultContainer.scrollHeight;
    }

    function resetUI() { elements.resultContainer.style.display = 'none'; elements.resultContent.innerHTML = ''; elements.error.style.display = 'none'; }
    function showLoading(text, detail = '') {
        elements.loading.style.display = 'block'; elements.loadingText.textContent = text;
        const d = document.getElementById('status-detail'); if (d) d.textContent = detail;
    }
    function showError(msg) { elements.error.textContent = msg; elements.error.style.display = 'block'; }
});