/**
 * Popup脚本 - 插件弹窗逻辑
 */

// 全局状态
let currentConfig = {};

/**
 * 初始化
 */
async function init() {
    console.log('[Popup] Initializing...');

    // 加载配置
    await loadConfig();

    // 检查API状态
    await checkAPIStatus();

    // 检查当前标签页
    await checkCurrentPage();

    // 绑定事件
    bindEvents();

    console.log('[Popup] Initialized');
}

/**
 * 加载配置
 */
async function loadConfig() {
    return new Promise((resolve) => {
        chrome.storage.local.get(['aiConfig'], (result) => {
            currentConfig = result.aiConfig || {
                apiBase: 'https://api.siliconflow.cn/v1',
                apiKey: 'sk-kjfvtxdspxngnsgsmeciaycwitfpuyvnybokuivrliquzbbt',
                model: 'Qwen/Qwen3-Omni-30B-A3B-Captioner',
                vlModel: 'Qwen/Qwen3-Omni-30B-A3B-Captioner',
                temperature: 0.7
            };

            // 填充表单
            document.getElementById('apiBase')?.value = currentConfig.apiBase || '';
            document.getElementById('apiKey')?.value = currentConfig.apiKey || '';
            document.getElementById('model')?.value = currentConfig.model || '';
            document.getElementById('vlModel')?.value = currentConfig.vlModel || '';

            resolve();
        });
    });
}

/**
 * 保存配置
 */
async function saveConfig() {
    const config = {
        apiBase: document.getElementById('apiBase').value.trim(),
        apiKey: document.getElementById('apiKey').value.trim(),
        model: document.getElementById('model').value.trim(),
        vlModel: document.getElementById('vlModel').value.trim(),
        temperature: 0.7
    };

    currentConfig = config;

    return new Promise((resolve) => {
        chrome.storage.local.set({ aiConfig: config }, () => {
            console.log('[Popup] Config saved:', config);

            // 检查API状态
            checkAPIStatus();

            // 显示成功提示
            showToast('配置已保存');

            resolve();
        });
    });
}

/**
 * 检查API状态
 */
async function checkAPIStatus() {
    const statusDiv = document.getElementById('apiStatus');
    const statusDot = statusDiv.querySelector('.status-dot');
    const statusText = statusDiv.querySelector('.status-text');

    // 重置状态
    statusDot.className = 'status-dot status-checking';
    statusText.textContent = '检查中...';

    if (!currentConfig.apiBase || !currentConfig.apiKey) {
        statusDot.className = 'status-dot status-error';
        statusText.textContent = '未配置';
        return;
    }

    try {
        const response = await fetch(`${currentConfig.apiBase}/models`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${currentConfig.apiKey}`
            }
        });

        if (response.ok) {
            statusDot.className = 'status-dot status-success';
            statusText.textContent = '已连接';
        } else {
            statusDot.className = 'status-dot status-error';
            statusText.textContent = '认证失败';
        }
    } catch (e) {
        statusDot.className = 'status-dot status-error';
        statusText.textContent = '连接失败';
    }
}

/**
 * 检查当前标签页
 */
async function checkCurrentPage() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const pageCard = document.getElementById('currentPageCard');
    const pageInfo = document.getElementById('pageInfo');

    if (!tab.url) return;

    const url = tab.url;

    // 检查是否是B站页面
    if (url.includes('bilibili.com/video/')) {
        // 视频页面
        const bvidMatch = url.match(/\/video\/(BV[a-zA-Z0-9]{10})/);
        if (bvidMatch) {
            pageCard.style.display = 'block';
            pageInfo.innerHTML = `
                <div class="page-item">
                    <svg viewBox="0 0 24 24"><path d="M10 16.5l6-4.5-6-4.5v9zM12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>
                    <span>视频: ${bvidMatch[1]}</span>
                </div>
            `;
        }
    } else if (url.includes('bilibili.com/read/')) {
        // 专栏页面
        const cvMatch = url.match(/\/read\/cv(\d+)/);
        if (cvMatch) {
            pageCard.style.display = 'block';
            pageInfo.innerHTML = `
                <div class="page-item">
                    <svg viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                    <span>专栏: CV${cvMatch[1]}</span>
                </div>
            `;
        }
    } else if (url.includes('space.bilibili.com')) {
        // 用户页面
        const uidMatch = url.match(/space\.bilibili\.com\/(\d+)/);
        if (uidMatch) {
            pageCard.style.display = 'block';
            pageInfo.innerHTML = `
                <div class="page-item">
                    <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
                    <span>用户: UID${uidMatch[1]}</span>
                </div>
            `;
        }
    }
}

/**
 * 绑定事件
 */
function bindEvents() {
    // 保存配置
    document.getElementById('saveSettings').addEventListener('click', async () => {
        await saveConfig();
    });

    // 分析当前页面
    document.getElementById('analyzePage').addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        // 发送消息到content script
        chrome.tabs.sendMessage(tab.id, { action: 'openPanel' }, (response) => {
            if (chrome.runtime.lastError) {
                // 需要刷新页面或注入脚本
                chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    files: ['content-script.js']
                }, () => {
                    chrome.tabs.sendMessage(tab.id, { action: 'openPanel' });
                });
            }
        });
    });

    // 打开面板
    document.getElementById('openPanel').addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        chrome.tabs.sendMessage(tab.id, { action: 'openPanel' }, (response) => {
            if (chrome.runtime.lastError) {
                chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    files: ['content-script.js']
                });
            }
        });
    });

    // 打开设置
    document.getElementById('openSettings').addEventListener('click', () => {
        chrome.runtime.openOptionsPage();
    });

    // 查看历史
    document.getElementById('viewHistory').addEventListener('click', () => {
        // TODO: 实现历史记录功能
        showToast('历史记录功能即将上线');
    });
}

/**
 * 显示Toast提示
 */
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

/**
 * 启动
 */
document.addEventListener('DOMContentLoaded', init);
