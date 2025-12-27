/**
 * 视频页面增强器
 *
 * 在 B站视频页面注入增强功能
 */

class VideoEnhancer {
    constructor() {
        this.bvid = this.extractBVID();
        this.init();
    }

    extractBVID() {
        const match = window.location.pathname.match(/video\/(BV\w+)/);
        return match ? match[1] : null;
    }

    async init() {
        if (!this.bvid) {
            console.log('当前页面不是视频页面');
            return;
        }

        console.log('BiliBili 视频增强器已启动:', this.bvid);

        // 等待页面加载完成
        if (document.readyState === 'loading') {
            await new Promise(resolve => {
                document.addEventListener('DOMContentLoaded', resolve);
            });
        }

        // 等待一下，确保页面元素加载完成
        await this.sleep(1000);

        // 注入增强按钮
        this.injectEnhancedButton();

        // 显示视频统计信息
        this.showVideoStats();
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    injectEnhancedButton() {
        const toolbar = document.querySelector('.video-toolbar');
        if (!toolbar) {
            console.log('未找到工具栏');
            return;
        }

        // 检查是否已经注入
        if (toolbar.querySelector('.bili-api-enhance-btn')) {
            return;
        }

        const button = document.createElement('button');
        button.className = 'bili-api-enhance-btn';
        button.textContent = '📊 数据分析';
        button.style.cssText = `
            margin-left: 10px;
            padding: 8px 16px;
            background: #FB7299;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
        `;

        button.addEventListener('click', () => this.showAnalysis());
        toolbar.appendChild(button);
    }

    async showVideoStats() {
        try {
            // 向 background 发送消息
            const response = await chrome.runtime.sendMessage({
                action: 'fetchVideoInfo',
                data: { bvid: this.bvid }
            });

            if (response && response.success) {
                this.displayStats(response.data);
            } else {
                console.error('获取视频信息失败:', response?.error);
            }
        } catch (error) {
            console.error('获取视频信息失败:', error);
        }
    }

    displayStats(videoInfo) {
        // 在视频标题下方显示统计信息
        const titleElement = document.querySelector('.video-info h1');
        if (!titleElement) {
            console.log('未找到标题元素');
            return;
        }

        // 检查是否已经显示
        if (titleElement.parentElement.querySelector('.bili-api-stats')) {
            return;
        }

        const statsDiv = document.createElement('div');
        statsDiv.className = 'bili-api-stats';
        statsDiv.innerHTML = `
            <div style="margin-top: 10px; padding: 15px; background: #f6f7f8; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #666;">📊 视频数据</h3>
                <div style="display: flex; gap: 20px; font-size: 12px; color: #999;">
                    <span>👁️ ${this.formatNumber(videoInfo.view || 0)}</span>
                    <span>👍 ${this.formatNumber(videoInfo.like || 0)}</span>
                    <span>🪙 ${this.formatNumber(videoInfo.coin || 0)}</span>
                    <span>⭐ ${this.formatNumber(videoInfo.favorite || 0)}</span>
                    <span>💬 ${this.formatNumber(videoInfo.comment || 0)}</span>
                </div>
            </div>
        `;

        titleElement.insertAdjacentElement('afterend', statsDiv);
    }

    formatNumber(num) {
        if (num >= 10000) {
            return (num / 10000).toFixed(1) + '万';
        }
        return num.toString();
    }

    async showAnalysis() {
        const loadingToast = this.showToast('正在分析视频...', 'info');

        try {
            // 获取视频基本信息
            const infoResponse = await chrome.runtime.sendMessage({
                action: 'fetchVideoInfo',
                data: { bvid: this.bvid }
            });

            // 获取评论
            const commentsResponse = await chrome.runtime.sendMessage({
                action: 'fetchVideoComments',
                data: { bvid: this.bvid, limit: 20 }
            });

            loadingToast.remove();

            if (infoResponse.success && commentsResponse.success) {
                this.showAnalysisModal({
                    info: infoResponse.data,
                    comments: commentsResponse.data
                });
            } else {
                this.showToast('分析失败: ' + (infoResponse.error || commentsResponse.error), 'error');
            }
        } catch (error) {
            loadingToast.remove();
            this.showToast('分析失败: ' + error.message, 'error');
        }
    }

    showAnalysisModal(data) {
        // 创建模态框
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 600px;
            max-height: 80vh;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            z-index: 10000;
            padding: 24px;
            overflow-y: auto;
        `;

        modal.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h2 style="margin: 0;">📊 视频数据分析</h2>
                <button class="close-btn" style="background: none; border: none; font-size: 24px; cursor: pointer;">✕</button>
            </div>
            <div class="analysis-content">
                <h3>视频信息</h3>
                <p><strong>标题:</strong> ${data.info.title || 'N/A'}</p>
                <p><strong>简介:</strong> ${data.info.desc || '无'}</p>
                <p><strong>时长:</strong> ${data.info.duration_str || 'N/A'}</p>
                <hr style="margin: 16px 0;">
                <h3>评论统计</h3>
                <p>已获取 ${data.comments?.comments?.length || 0} 条评论</p>
            </div>
        `;

        modal.querySelector('.close-btn').addEventListener('click', () => modal.remove());
        document.body.appendChild(modal);
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        const bgColor = type === 'error' ? '#ff4d4f' : (type === 'success' ? '#52c41a' : '#1890ff');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 24px;
            background: ${bgColor};
            color: white;
            border-radius: 8px;
            z-index: 10001;
            animation: slideDown 0.3s ease;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 3000);
        return toast;
    }
}

// 启动增强器
new VideoEnhancer();

console.log('BiliBili 视频页面增强器已加载');
