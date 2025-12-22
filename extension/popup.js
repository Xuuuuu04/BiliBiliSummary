/**
 * BiliBili AI 助手 (全量版) - Popup 核心脚本
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

    // 1. 初始化设置
    const config = await chrome.storage.local.get(['apiKey', 'apiBase', 'model']);
    elements.apiKey.value = config.apiKey || DEFAULT_CONFIG.apiKey;
    elements.apiBase.value = config.apiBase || DEFAULT_CONFIG.apiBase;
    elements.apiModel.value = config.model || DEFAULT_CONFIG.model;

    // 2. 获取当前视频信息
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    console.log('Current tab:', tab);
    if (tab && tab.url.includes('bilibili.com/video/')) {
        currentBvid = extractBvid(tab.url);
        console.log('Extracted BVID:', currentBvid);
        elements.vBvid.textContent = currentBvid;
        elements.videoBox.style.display = 'block';
        await fetchVideoInfo(currentBvid);
    } else {
        showError('请在 B 站视频播放页使用');
        elements.btnAI.disabled = true;
        elements.btnTxt.disabled = true;
    }

    // 事件监听
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

        elements.btnTxt.addEventListener('click', async () => {

            if (!videoData) {

                showError('正在加载视频信息，请稍后再试');

                return;

            }

            resetUI();

            showLoading('正在提取视频字幕...');

            try {

                console.log('Starting transcript extraction for CID:', videoData.cid);

                const transcript = await getTranscript(currentBvid);

                elements.loading.style.display = 'none';

                elements.resultContainer.style.display = 'block';

                elements.resultContent.innerHTML = `<h3>视频文本内容</h3><pre>${transcript}</pre>`;

            } catch (e) {

                console.error('Transcript error:', e);

                showError(`获取字幕失败: ${e.message}`);

                elements.loading.style.display = 'none';

            }

        });

    

        elements.btnAI.addEventListener('click', async () => {

            if (!videoData) {

                showError('正在加载视频信息，请稍后再试');

                return;

            }

            resetUI();

            showLoading('获取内容并生成 AI 总结...');

    

            try {

                console.log('Fetching transcript for AI...');

                const transcript = await getTranscript(currentBvid);

                showLoading('AI 正在深度思考中...');

    

                const prompt = `你是一个专业的B站视频分析专家。请根据以下视频内容，生成一份简洁、专业且富有洞察力的总结。

    视频标题：${videoData.title}

    视频简介：${videoData.desc}

    内容文本：${transcript.substring(0, 10000)}

    

    要求：

    1. 分段总结核心观点。

    2. 提取视频中的精华结论或金句。

    3. 如果是技术或教程类，总结出具体步骤。

    4. 使用 Markdown 格式。`;

    

                console.log('Calling AI service...');

                await callAIService(prompt, (chunk) => {

                    elements.loading.style.display = 'none';

                    elements.resultContainer.style.display = 'block';

                    // 简单的流式渲染

                    renderStreamingContent(chunk);

                });

    

            } catch (e) {

                console.error('AI error:', e);

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
                console.log('Fetching video info for:', bvid);
                const resp = await fetch(`https://api.bilibili.com/x/web-interface/view?bvid=${bvid}`);
                const json = await resp.json();
                console.log('Video info response:', json);
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
            if (!videoData || !videoData.cid) {
                throw new Error('未获取到视频 CID，请尝试刷新页面');
            }
            
            console.log('Fetching player info for CID:', videoData.cid);
            // 获取视频分段和字幕列表
            const playerUrl = `https://api.bilibili.com/x/player/v2?bvid=${bvid}&cid=${videoData.cid}`;
            const playerResp = await fetch(playerUrl);
            const playerData = await playerResp.json();
            console.log('Player info response:', playerData);
    
            if (playerData.code !== 0) {
                throw new Error(`获取播放信息失败: ${playerData.message}`);
            }
    
            const subtitles = playerData.data.subtitle.subtitles;
            if (!subtitles || subtitles.length === 0) {
                console.log('No official subtitles found, using description');
                return `[提示] 该视频暂无官方字幕。视频简介：${videoData.desc}`;
            }
    
            // 2. 获取第一个字幕的内容 (通常是中文)
            const subUrl = subtitles[0].subtitle_url.replace(/^\/\//, 'https://');
            console.log('Fetching subtitle content from:', subUrl);
            const subContentResp = await fetch(subUrl);
            const subJson = await subContentResp.json();
            
            const text = subJson.body.map(item => item.content).join(' ');
            console.log('Transcript length:', text.length);
            return text;
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

            const chunks = decoder.decode(value).split('\n');
            for (const chunk of chunks) {
                if (chunk.trim() === '' || chunk.trim() === 'data: [DONE]') continue;
                if (chunk.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(chunk.slice(6));
                        const content = data.choices[0].delta.content || '';
                        fullContent += content;
                        onChunk(fullContent);
                    } catch (e) {}
                }
            }
        }
    }

    // 渲染 Markdown (极简版)
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

    function showLoading(text) {
        elements.loading.style.display = 'block';
        elements.loadingText.textContent = text;
    }

    function showError(msg) {
        elements.error.textContent = msg;
        elements.error.style.display = 'block';
    }
});
