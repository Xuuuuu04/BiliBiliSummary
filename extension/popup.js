/**
 * BiliBili AI 助手 - Popup 核心脚本
 * 纯前端实现：直接调用 B 站接口和 AI 接口
 */

// 默认配置 (从你的 .env 中提取作为初始值)
const DEFAULT_CONFIG = {
    apiKey: 'sk-kjfvtxdspxngnsgsmeciaycwitfpuyvnybokuivrliquzbbt',
    apiBase: 'https://api.siliconflow.cn/v1',
    model: 'Qwen/Qwen2.5-72B-Instruct'
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
        // 1. 初始化设置
        const config = await chrome.storage.local.get(['apiKey', 'apiBase', 'model']);
        elements.apiKey.value = config.apiKey || DEFAULT_CONFIG.apiKey;
        elements.apiBase.value = config.apiBase || DEFAULT_CONFIG.apiBase;
        elements.apiModel.value = config.model || DEFAULT_CONFIG.model;

        // 2. 获取当前视频信息
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.url && tab.url.includes('bilibili.com/video/')) {
            currentBvid = extractBvid(tab.url);
            if (currentBvid) {
                elements.vBvid.textContent = currentBvid;
                elements.videoBox.style.display = 'block';
                await fetchVideoInfo(currentBvid);
            } else {
                showError('未能解析视频 ID');
            }
        } else {
            showError('请在 B 站视频播放页使用此插件');
            elements.btnAI.disabled = true;
            elements.btnTxt.disabled = true;
        }
    } catch (err) {
        console.error('Initialization error:', err);
        showError('插件初始化失败，请重试');
    }

    // --- 事件监听 ---

    // 切换设置面板
    elements.toggleSettings.addEventListener('click', () => {
        const isVisible = elements.settingsPanel.style.display === 'block';
        elements.settingsPanel.style.display = isVisible ? 'none' : 'block';
    });

    // 保存设置
    elements.saveBtn.addEventListener('click', async () => {
        try {
            await chrome.storage.local.set({
                apiKey: elements.apiKey.value,
                apiBase: elements.apiBase.value,
                model: elements.apiModel.value
            });
            alert('配置已保存');
            elements.settingsPanel.style.display = 'none';
        } catch (err) {
            alert('保存失败: ' + err.message);
        }
    });

    // 提取文本
    elements.btnTxt.addEventListener('click', async () => {
        if (!videoData) {
            showError('正在加载视频信息，请稍后再试');
            return;
        }
        resetUI();
        showLoading('正在提取视频文本及相关信息...');
        try {
            const transcript = await getTranscript(currentBvid);
            const danmaku = await getDanmaku(videoData.cid);
            
            elements.loading.style.display = 'none';
            elements.resultContainer.style.display = 'block';
            
            let html = `<h3>视频原文本</h3><pre>${transcript}</pre>`;
            if (danmaku) {
                html += `<h3>精选弹幕</h3><pre>${danmaku}</pre>`;
            }
            elements.resultContent.innerHTML = html;
        } catch (e) {
            console.error('Extraction error:', e);
            showError(`内容提取失败: ${e.message}`);
            elements.loading.style.display = 'none';
        }
    });

    // AI 智能总结
    elements.btnAI.addEventListener('click', async () => {
        if (!videoData) {
            showError('正在加载视频信息，请稍后再试');
            return;
        }
        resetUI();
        showLoading('正在采集视频多维数据...', '获取字幕、弹幕及高赞评论...');

        try {
            const [transcript, danmaku, comments] = await Promise.all([
                getTranscript(currentBvid),
                getDanmaku(videoData.cid),
                getComments(videoData.aid)
            ]);

            showLoading('AI 正在深度解析内容...', '正在生成总结报告...');

            const prompt = `你是一个专业的B站视频分析专家。请根据以下采集到的多维度视频数据，生成一份简洁、专业且富有洞察力的总结报告。

【视频基本信息】
标题：${videoData.title}
作者：${videoData.owner.name}
简介：${videoData.desc}

【视频文本内容】
${transcript.substring(0, 8000)}

【精选弹幕】
${danmaku.substring(0, 1000)}

【热门评论】
${comments.substring(0, 1500)}

要求：
1. **核心总结**：用一句话概括视频主旨。
2. **内容精华**：分点列出视频的关键知识点或核心论点。
3. **舆情分析**：分析观众对视频的反馈、共鸣点或争议点。
4. **精华结论**：提取视频中的金句或实际价值。
5. **格式要求**：使用 Markdown 格式。`;

            await callAIService(prompt, (chunk) => {
                elements.loading.style.display = 'none';
                elements.resultContainer.style.display = 'block';
                renderStreamingContent(chunk);
            });

        } catch (e) {
            console.error('AI error:', e);
            showError(`总结生成失败: ${e.message}`);
            elements.loading.style.display = 'none';
        }
    });

    // 复制按钮
    elements.btnCopy.addEventListener('click', () => {
        const text = elements.resultContent.innerText;
        navigator.clipboard.writeText(text).then(() => {
            const originalText = elements.btnCopy.textContent;
            elements.btnCopy.textContent = '已复制';
            setTimeout(() => elements.btnCopy.textContent = originalText, 2000);
        });
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
            } else {
                showError(`获取视频信息失败: ${json.message}`);
            }
        } catch (e) {
            console.error('fetchVideoInfo error:', e);
            showError(`请求视频接口失败: ${e.message}`);
        }
    }

    async function getTranscript(bvid) {
        if (!videoData || !videoData.cid) throw new Error('未获取到视频信息');
        
        try {
            const playerUrl = `https://api.bilibili.com/x/player/v2?bvid=${bvid}&cid=${videoData.cid}`;
            const playerResp = await fetch(playerUrl);
            const playerData = await playerResp.json();
            
            const subtitles = playerData.data?.subtitle?.subtitles;
            if (subtitles && subtitles.length > 0) {
                const targetSub = subtitles.find(s => s.lan.includes('zh')) || subtitles[0];
                const subUrl = targetSub.subtitle_url.replace(/^\/\//, 'https://');
                const subContentResp = await fetch(subUrl);
                const subJson = await subContentResp.json();
                return subJson.body.map(item => item.content).join(' ');
            }
        } catch (e) {
            console.warn('获取官方字幕失败', e);
        }
        return `[无官方字幕] 视频简介：${videoData.desc}`;
    }

    async function getDanmaku(cid) {
        try {
            const resp = await fetch(`https://api.bilibili.com/x/v1/dm/list.so?oid=${cid}`);
            const text = await resp.text();
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(text, "text/xml");
            const dNodes = xmlDoc.getElementsByTagName("d");
            const danmakus = [];
            for (let i = 0; i < Math.min(dNodes.length, 150); i++) {
                danmakus.push(dNodes[i].textContent);
            }
            return danmakus.join('\n');
        } catch (e) {
            return '';
        }
    }

    async function getComments(aid) {
        try {
            const resp = await fetch(`https://api.bilibili.com/x/v2/reply?type=1&oid=${aid}&sort=2&ps=20`);
            const json = await resp.json();
            if (json.code === 0 && json.data?.replies) {
                return json.data.replies
                    .map(r => `${r.member.uname}: ${r.content.message}`)
                    .join('\n');
            }
            return '';
        } catch (e) {
            return '';
        }
    }

    async function callAIService(prompt, onChunk) {
        const apiKey = elements.apiKey.value;
        const apiBase = elements.apiBase.value.replace(/\/$/, '');
        const model = elements.apiModel.value;

        const response = await fetch(`${apiBase}/chat/completions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                messages: [{ role: 'user', content: prompt }],
                stream: true
            })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error?.message || 'AI 接口请求失败');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.trim() === '' || line.trim() === 'data: [DONE]') continue;
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
        const html = text
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^\d\. (.*$)/gm, '<li>$1</li>')
            .replace(/^\* (.*$)/gm, '<li>$1</li>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        elements.resultContent.innerHTML = html;
        elements.resultContainer.scrollTop = elements.resultContainer.scrollHeight;
    }

    function resetUI() {
        elements.resultContainer.style.display = 'none';
        elements.resultContent.innerHTML = '';
        elements.error.style.display = 'none';
    }

    function showLoading(text, detail = '') {
        elements.loading.style.display = 'block';
        elements.loadingText.textContent = text;
        // 如果 HTML 中有 status-detail 元素可以显示更多细节
        const detailEl = document.getElementById('status-detail');
        if (detailEl) detailEl.textContent = detail;
    }

    function showError(msg) {
        elements.error.textContent = msg;
        elements.error.style.display = 'block';
    }
});
