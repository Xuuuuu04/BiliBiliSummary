/**
 * BiliBili AI 助手 - Popup 脚本
 * 负责与本地 Flask 后端通信并显示结果
 */

const API_BASE = 'http://localhost:5000';

document.addEventListener('DOMContentLoaded', async () => {
    const btnSummarize = document.getElementById('btn-summarize');
    const btnTranscript = document.getElementById('btn-transcript');
    const loading = document.getElementById('loading');
    const resultContent = document.getElementById('result-content');
    const resultContainer = document.getElementById('result-container');
    const errorMsg = document.getElementById('error-msg');
    const videoInfo = document.getElementById('video-info');
    const displayTitle = document.getElementById('display-title');
    const displayBvid = document.getElementById('display-bvid');
    const statusDetail = document.getElementById('status-detail');

    let currentUrl = '';

    // 1. 获取当前标签页 URL
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        currentUrl = tab.url;

        if (currentUrl.includes('bilibili.com/video/')) {
            videoInfo.style.display = 'block';
            const bvid = extractBvid(currentUrl);
            displayBvid.textContent = bvid;
            // 尝试获取视频标题
            displayTitle.textContent = tab.title.replace('_哔哩哔哩_bilibili', '');
        } else {
            showError('请在 B 站视频播放页面使用此插件');
            btnSummarize.disabled = true;
            btnTranscript.disabled = true;
        }
    } catch (e) {
        showError('无法获取当前页面信息');
    }

    // 2. 智能总结功能 (流式)
    btnSummarize.addEventListener('click', async () => {
        resetUI();
        showLoading('正在生成智能总结...', '正在分析视频内容，请稍候...');
        
        try {
            const response = await fetch(`${API_BASE}/api/analyze/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: currentUrl })
            });

            if (!response.ok) throw new Error('后端服务未启动或连接失败');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let summaryHtml = '';
            
            resultContainer.style.display = 'block';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.type === 'stage') {
                                statusDetail.textContent = data.message;
                            } else if (data.type === 'chunk') {
                                // 隐藏加载动画，显示实时内容
                                loading.style.display = 'none';
                                summaryHtml += data.content;
                                resultContent.innerHTML = formatMarkdown(summaryHtml);
                                // 滚动到底部
                                resultContainer.scrollTop = resultContainer.scrollHeight;
                            } else if (data.type === 'error') {
                                throw new Error(data.error);
                            } else if (data.type === 'final') {
                                statusDetail.textContent = '总结完成！';
                            }
                        } catch (e) {
                            console.error('解析 JSON 失败', e);
                        }
                    }
                }
            }
        } catch (e) {
            showError(`总结失败: ${e.message}`);
        } finally {
            loading.style.display = 'none';
        }
    });

    // 3. 提取文本功能
    btnTranscript.addEventListener('click', async () => {
        resetUI();
        showLoading('正在提取视频文本...', '正在获取字幕信息...');

        try {
            const response = await fetch(`${API_BASE}/api/video/subtitle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: currentUrl })
            });

            const data = await response.json();
            loading.style.display = 'none';

            if (data.success) {
                resultContainer.style.display = 'block';
                const text = data.data.full_text || '未找到字幕内容';
                resultContent.innerHTML = `<h3>视频全文本</h3><pre>${text}</pre>`;
            } else {
                throw new Error(data.error || '提取失败');
            }
        } catch (e) {
            showError(`提取失败: ${e.message}`);
            loading.style.display = 'none';
        }
    });

    // 4. 复制功能
    document.getElementById('btn-copy').addEventListener('click', () => {
        const text = resultContent.innerText;
        navigator.clipboard.writeText(text).then(() => {
            const btn = document.getElementById('btn-copy');
            const originalText = btn.textContent;
            btn.textContent = '已复制！';
            setTimeout(() => btn.textContent = originalText, 2000);
        });
    });

    // 辅助函数
    function extractBvid(url) {
        const match = url.match(/BV[a-zA-Z0-9]+/);
        return match ? match[0] : '';
    }

    function resetUI() {
        resultContainer.style.display = 'none';
        resultContent.innerHTML = '';
        errorMsg.style.display = 'none';
    }

    function showLoading(text, detail) {
        loading.style.display = 'block';
        document.getElementById('loading-text').textContent = text;
        statusDetail.textContent = detail;
    }

    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.style.display = 'block';
    }

    // 极简 Markdown 格式化 (由于插件环境，我们不引入大库)
    function formatMarkdown(text) {
        return text
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^\d\. (.*$)/gim, '<li>$1</li>')
            .replace(/^\- (.*$)/gim, '<li>$1</li>')
            .replace(/\n/g, '<br>');
    }
});
