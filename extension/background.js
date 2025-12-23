/**
 * Background Service Worker
 * 插件后台服务
 */

// 默认配置（与.env保持一致）
const DEFAULT_CONFIG = {
    apiBase: 'https://api.siliconflow.cn/v1',
    apiKey: 'sk-kjfvtxdspxngnsgsmeciaycwitfpuyvnybokuivrliquzbbt',
    model: 'Qwen/Qwen3-Omni-30B-A3B-Captioner',
    vlModel: 'Qwen/Qwen3-Omni-30B-A3B-Captioner',
    temperature: 0.7
};

// 初始化配置（确保始终有默认值）
chrome.storage.local.get(['aiConfig'], (result) => {
    if (!result.aiConfig || !result.aiConfig.apiKey) {
        console.log('[BiliSummarize] Setting default config...');
        chrome.storage.local.set({ aiConfig: DEFAULT_CONFIG });
    } else {
        console.log('[BiliSummarize] Config exists:', result.aiConfig);
    }
});

// 监听插件安装
chrome.runtime.onInstalled.addListener((details) => {
    console.log('[BiliSummarize] Extension event:', details.reason);

    if (details.reason === 'install') {
        console.log('[BiliSummarize] Extension installed');

        // 确保设置默认配置
        chrome.storage.local.set({ aiConfig: DEFAULT_CONFIG });

        // 打开欢迎页面
        chrome.tabs.create({
            url: 'https://github.com/your-repo/bilibili-summarize#readme'
        });
    } else if (details.reason === 'update') {
        console.log('[BiliSummarize] Extension updated');
        // 更新时也确保配置存在
        chrome.storage.local.set({ aiConfig: DEFAULT_CONFIG });
    }

    // 创建右键菜单
    chrome.contextMenus.create({
        id: 'analyzeVideo',
        title: 'AI分析此视频',
        contexts: ['link'],
        documentUrlPatterns: ['*://*.bilibili.com/*']
    }, () => {
        if (chrome.runtime.lastError) {
            console.error('[BiliSummarize] Context menu creation failed:', chrome.runtime.lastError);
        } else {
            console.log('[BiliSummarize] Context menu created successfully');
        }
    });
});

// 监听来自content script的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('[BiliSummarize] Message received:', request);

    if (request.action === 'openPanel') {
        // 打开分析面板
        chrome.tabs.sendMessage(sender.tab.id, {
            action: 'togglePanel'
        });
        sendResponse({ success: true });
    }

    if (request.action === 'getConfig') {
        // 获取配置
        chrome.storage.local.get(['aiConfig'], (result) => {
            sendResponse({ config: result.aiConfig });
        });
        return true; // 异步响应
    }

    if (request.action === 'saveConfig') {
        // 保存配置
        chrome.storage.local.set({
            aiConfig: request.config
        }, () => {
            sendResponse({ success: true });
        });
        return true;
    }

    if (request.action === 'checkAPI') {
        // 检查API连接
        checkAPIConnection(request.config).then(result => {
            sendResponse(result);
        });
        return true;
    }

    if (request.action === 'getBiliCookies') {
        // 获取B站Cookie
        getBiliCookies().then(cookies => {
            sendResponse({ cookies });
        });
        return true; // 异步响应
    }
});

/**
 * 检查API连接
 */
async function checkAPIConnection(config) {
    try {
        const response = await fetch(`${config.apiBase}/models`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${config.apiKey}`
            }
        });

        return {
            success: response.ok,
            status: response.status
        };
    } catch (e) {
        return {
            success: false,
            error: e.message
        };
    }
}

/**
 * 获取B站Cookie
 */
async function getBiliCookies() {
    try {
        const cookies = await chrome.cookies.getAll({ domain: '.bilibili.com' });
        const cookieMap = {};

        cookies.forEach(cookie => {
            cookieMap[cookie.name] = cookie.value;
        });

        console.log('[BiliSummarize] B站Cookie获取成功:', Object.keys(cookieMap));
        return cookieMap;
    } catch (e) {
        console.error('[BiliSummarize] 获取Cookie失败:', e);
        return {};
    }
}

// 监听标签页更新
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && tab.url.includes('bilibili.com')) {
        console.log('[BiliSummarize] Bilibili page loaded:', tab.url);

        // 更新图标badge
        if (tab.url.includes('/video/')) {
            chrome.action.setBadgeText({ tabId, text: 'AI' });
            chrome.action.setBadgeTextColor({ tabId, color: '#FFFFFF' });
            chrome.action.setBadgeBackgroundColor({ tabId, color: '#00A1D6' });
        } else {
            chrome.action.setBadgeText({ tabId, text: '' });
        }
    }
});

// 右键菜单点击事件
chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'analyzeVideo') {
        // 分析链接中的视频
        chrome.tabs.sendMessage(tab.id, {
            action: 'analyzeVideo',
            url: info.linkUrl
        });
    }
});

console.log('[BiliSummarize] Background service worker loaded');
