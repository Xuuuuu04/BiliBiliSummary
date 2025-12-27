/**
 * Popup 界面逻辑
 */

document.addEventListener('DOMContentLoaded', async () => {
    // 检查连接状态
    await checkStatus();

    // 获取当前标签页信息
    await getCurrentPageInfo();

    // 绑定按钮事件
    document.getElementById('btn-info').addEventListener('click', getVideoInfo);
    document.getElementById('btn-comments').addEventListener('click', getVideoComments);
    document.getElementById('btn-danmaku').addEventListener('click', getVideoDanmaku);
    document.getElementById('btn-test').addEventListener('click', testAPI);
});

async function checkStatus() {
    try {
        const response = await chrome.runtime.sendMessage({
            action: 'checkAPIStatus'
        });

        const statusElement = document.getElementById('status');

        if (response.success && response.data.status === 'healthy') {
            statusElement.innerHTML = '🟢 已连接';
            statusElement.className = 'status connected';
        } else {
            statusElement.innerHTML = '🔴 未连接';
            statusElement.className = 'status disconnected';
        }
    } catch (error) {
        document.getElementById('status').innerHTML = '🔴 未连接';
        document.getElementById('status').className = 'status disconnected';
    }
}

async function getCurrentPageInfo() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab.url.includes('bilibili.com/video/')) {
            document.getElementById('page-info').innerHTML = '<p>请在 B站视频页面使用本扩展</p>';
            return;
        }

        const bvid = extractBVID(tab.url);
        document.getElementById('page-info').innerHTML = `
            <p><strong>BVID:</strong> ${bvid}</p>
            <p style="font-size: 12px; color: #999;">${tab.url}</p>
        `;
    } catch (error) {
        console.error('获取页面信息失败:', error);
    }
}

async function getVideoInfo() {
    const bvid = await getCurrentBVID();
    if (!bvid) {
        showResult('请先在 B站视频页面打开扩展', 'error');
        return;
    }

    showResult('正在获取视频信息...', 'info');

    try {
        const response = await chrome.runtime.sendMessage({
            action: 'fetchVideoInfo',
            data: { bvid }
        });

        if (response.success) {
            showResult(JSON.stringify(response.data, null, 2), 'success');
        } else {
            showResult('获取失败: ' + response.error, 'error');
        }
    } catch (error) {
        showResult('请求失败: ' + error.message, 'error');
    }
}

async function getVideoComments() {
    const bvid = await getCurrentBVID();
    if (!bvid) {
        showResult('请先在 B站视频页面打开扩展', 'error');
        return;
    }

    showResult('正在获取评论...', 'info');

    try {
        const response = await chrome.runtime.sendMessage({
            action: 'fetchVideoComments',
            data: { bvid, limit: 20 }
        });

        if (response.success) {
            const data = response.data;
            showResult(`成功获取 ${data.comments?.length || 0} 条评论\n\n` + JSON.stringify(data, null, 2), 'success');
        } else {
            showResult('获取失败: ' + response.error, 'error');
        }
    } catch (error) {
        showResult('请求失败: ' + error.message, 'error');
    }
}

async function getVideoDanmaku() {
    const bvid = await getCurrentBVID();
    if (!bvid) {
        showResult('请先在 B站视频页面打开扩展', 'error');
        return;
    }

    showResult('正在获取弹幕...', 'info');

    try {
        const response = await chrome.runtime.sendMessage({
            action: 'fetchVideoDanmaku',
            data: { bvid, limit: 500 }
        });

        if (response.success) {
            const data = response.data;
            showResult(`成功获取 ${data.danmaku_count || 0} 条弹幕\n\n` + JSON.stringify(data, null, 2), 'success');
        } else {
            showResult('获取失败: ' + response.error, 'error');
        }
    } catch (error) {
        showResult('请求失败: ' + error.message, 'error');
    }
}

async function testAPI() {
    const input = document.getElementById('api-input').value.trim();
    if (!input) {
        showResult('请输入 BVID 或视频链接', 'error');
        return;
    }

    const bvid = extractBVID(input);
    if (!bvid) {
        showResult('无效的 BVID 或视频链接', 'error');
        return;
    }

    showResult('正在测试 API...', 'info');

    try {
        const response = await chrome.runtime.sendMessage({
            action: 'fetchVideoInfo',
            data: { bvid }
        });

        if (response.success) {
            showResult('API 测试成功！\n\n' + JSON.stringify(response.data, null, 2), 'success');
        } else {
            showResult('API 测试失败: ' + response.error, 'error');
        }
    } catch (error) {
        showResult('API 测试失败: ' + error.message, 'error');
    }
}

function showResult(text, type = 'info') {
    const resultBox = document.getElementById('api-result');
    resultBox.textContent = text;

    // 根据类型设置样式
    resultBox.style.color = type === 'error' ? '#ff4d4f' : (type === 'success' ? '#52c41a' : '#666');
}

function extractBVID(url) {
    const match = url.match(/video\/(BV\w+)/);
    return match ? match[1] : null;
}

async function getCurrentBVID() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab.url && tab.url.includes('bilibili.com/video/')) {
            return extractBVID(tab.url);
        }
    } catch (error) {
        console.error('获取当前 BVID 失败:', error);
    }
    return null;
}
