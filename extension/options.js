/**
 * Options页面脚本
 */

let currentConfig = {};

/**
 * 初始化
 */
async function init() {
    console.log('[Options] Initializing...');

    // 加载配置
    await loadConfig();

    // 检查API状态
    checkAPIStatus();

    // 绑定事件
    bindEvents();

    console.log('[Options] Initialized');
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
            document.getElementById('bspApiBase')?.value = currentConfig.apiBase || '';
            document.getElementById('bspApiKey')?.value = currentConfig.apiKey || '';
            document.getElementById('bspModel')?.value = currentConfig.model || '';
            document.getElementById('vlModel').value = currentConfig.vlModel || '';
            document.getElementById('temperature').value = currentConfig.temperature || 0.7;

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
        temperature: parseFloat(document.getElementById('temperature').value) || 0.7
    };

    if (!config.apiBase) {
        showStatus('error', '请输入API地址');
        return;
    }

    if (!config.apiKey) {
        showStatus('error', '请输入API密钥');
        return;
    }

    currentConfig = config;

    return new Promise((resolve) => {
        chrome.storage.local.set({ aiConfig: config }, () => {
            console.log('[Options] Config saved:', config);
            showStatus('active', '配置已保存');
            checkAPIStatus();
            resolve();
        });
    });
}

/**
 * 检查API状态
 */
async function checkAPIStatus() {
    if (!currentConfig.apiBase || !currentConfig.apiKey) {
        showStatus('inactive', '未配置');
        return;
    }

    showStatus('checking', '检查中...');

    try {
        const response = await fetch(`${currentConfig.apiBase}/models`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${currentConfig.apiKey}`
            }
        });

        if (response.ok) {
            showStatus('active', '连接成功');
        } else {
            showStatus('error', '认证失败');
        }
    } catch (e) {
        showStatus('error', '连接失败');
    }
}

/**
 * 显示状态
 */
function showStatus(status, text) {
    const statusDiv = document.getElementById('apiStatus');
    const statusDot = statusDiv.querySelector('.status-dot');
    const statusText = statusDiv.querySelector('.status-text');

    statusDot.className = 'status-dot';

    switch (status) {
        case 'active':
            statusDot.classList.add('active');
            break;
        case 'inactive':
            statusDot.classList.add('inactive');
            break;
        case 'error':
            statusDot.classList.add('error');
            break;
    }

    statusText.textContent = text;
}

/**
 * 绑定事件
 */
function bindEvents() {
    // 保存配置
    document.getElementById('saveSettings').addEventListener('click', async () => {
        await saveConfig();
    });

    // 测试连接
    document.getElementById('testConnection').addEventListener('click', async () => {
        await saveConfig();
        await checkAPIStatus();
    });

    // 监听配置变化（从popup或其他地方）
    chrome.storage.onChanged.addListener((changes, area) => {
        if (area === 'local' && changes.aiConfig) {
            loadConfig();
        }
    });
}

/**
 * 启动
 */
document.addEventListener('DOMContentLoaded', init);
