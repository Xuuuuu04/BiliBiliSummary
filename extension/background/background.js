/**
 * Background Service Worker
 *
 * Chrome Extension 的后台服务，负责与 API 通信和消息处理
 */

import { APIClient } from './api-client.js';

// 初始化 API 客户端
const API_BASE_URL = 'http://localhost:5000';
const apiClient = new APIClient(API_BASE_URL);

// 监听扩展安装
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        console.log('BiliBili API 转换器已安装');

        // 设置默认配置
        chrome.storage.local.set({
            apiBaseUrl: API_BASE_URL,
            autoAnalyze: false,
            showEnhancedInfo: true
        });
    }
});

// 监听来自 content script 和 popup 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('收到消息:', request);

    // 处理不同的消息类型
    switch (request.action) {
        case 'fetchVideoInfo':
            handleFetchVideoInfo(request.data)
                .then(result => sendResponse({ success: true, data: result }))
                .catch(error => sendResponse({ success: false, error: error.message }));
            return true; // 保持消息通道开放

        case 'fetchVideoComments':
            handleFetchVideoComments(request.data)
                .then(result => sendResponse({ success: true, data: result }))
                .catch(error => sendResponse({ success: false, error: error.message }));
            return true;

        case 'fetchVideoDanmaku':
            handleFetchVideoDanmaku(request.data)
                .then(result => sendResponse({ success: true, data: result }))
                .catch(error => sendResponse({ success: false, error: error.message }));
            return true;

        case 'checkAPIStatus':
            handleCheckAPIStatus()
                .then(result => sendResponse({ success: true, data: result }))
                .catch(error => sendResponse({ success: false, error: error.message }));
            return true;

        default:
            sendResponse({ success: false, error: '未知的操作类型' });
    }
});

/**
 * 获取视频信息
 */
async function handleFetchVideoInfo({ bvid }) {
    try {
        const response = await apiClient.get(`/api/v1/video/${bvid}/info`);

        if (response.success) {
            return response.data;
        } else {
            throw new Error(response.error);
        }
    } catch (error) {
        console.error('获取视频信息失败:', error);
        throw error;
    }
}

/**
 * 获取视频评论
 */
async function handleFetchVideoComments({ bvid, limit = 50 }) {
    try {
        const response = await apiClient.get(`/api/v1/video/${bvid}/comments`, {
            params: { limit }
        });

        if (response.success) {
            return response.data;
        } else {
            throw new Error(response.error);
        }
    } catch (error) {
        console.error('获取视频评论失败:', error);
        throw error;
    }
}

/**
 * 获取视频弹幕
 */
async function handleFetchVideoDanmaku({ bvid, limit = 1000 }) {
    try {
        const response = await apiClient.get(`/api/v1/video/${bvid}/danmaku`, {
            params: { limit }
        });

        if (response.success) {
            return response.data;
        } else {
            throw new Error(response.error);
        }
    } catch (error) {
        console.error('获取视频弹幕失败:', error);
        throw error;
    }
}

/**
 * 检查 API 状态
 */
async function handleCheckAPIStatus() {
    try {
        const response = await apiClient.get('/api/v1/health');

        if (response.success) {
            return { status: 'healthy', ...response };
        } else {
            return { status: 'unhealthy' };
        }
    } catch (error) {
        console.error('API 健康检查失败:', error);
        return { status: 'disconnected', error: error.message };
    }
}

/**
 * 获取存储的配置
 */
async function getConfig() {
    return new Promise((resolve) => {
        chrome.storage.local.get(['apiBaseUrl', 'autoAnalyze', 'showEnhancedInfo'], (result) => {
            resolve({
                apiBaseUrl: result.apiBaseUrl || API_BASE_URL,
                autoAnalyze: result.autoAnalyze || false,
                showEnhancedInfo: result.showEnhancedInfo !== false
            });
        });
    });
}

/**
 * 更新配置
 */
async function updateConfig(config) {
    return new Promise((resolve) => {
        chrome.storage.local.set(config, () => {
            resolve({ success: true });
        });
    });
}

console.log('BiliBili API 转换器 Background Service Worker 已启动');
