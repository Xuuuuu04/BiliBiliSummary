/**
 * 改进版UI组件 - B站粉蓝风格
 * 顶部标签栏 + 流式分析 + 详细过程显示
 */

class UIComponents {
    constructor() {
        this.currentPanel = null;
        this.currentTab = 'home';
        this.isMinimized = false;
        this.streamContent = '';
    }

    /**
     * 创建主面板 - 改进版布局
     */
    createMainPanel() {
        const panel = document.createElement('div');
        panel.id = 'bili-summarize-panel';
        panel.className = 'bili-summarize-panel';
        panel.innerHTML = `
            <div class="bsp-header">
                <div class="bsp-title">
                    <svg viewBox="0 0 24 24">
                        <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <span>B站AI助手</span>
                </div>
                <div class="bsp-header-actions">
                    <button class="bsp-minimize" id="bspMinimize" title="最小化">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 13H5v-2h14v2z"/></svg>
                    </button>
                    <button class="bsp-close" title="关闭">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    </button>
                </div>
            </div>

            <!-- 顶部标签栏 -->
            <div class="bsp-tabs-bar">
                <button class="bsp-tab bsp-tab-active" data-tab="home">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
                    首页
                </button>
                <button class="bsp-tab" data-tab="analyze">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                    AI分析
                </button>
                <button class="bsp-tab" data-tab="subtitle">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
                    字幕提取
                </button>
            </div>

            <div class="bsp-content" id="bspContent">
                <!-- 内容区域动态显示 -->
            </div>

            <div class="bsp-status-bar">
                <div class="bsp-status" id="bspStatus">
                    <span class="bsp-status-dot"></span>
                    <span class="bsp-status-text">就绪</span>
                </div>
            </div>
        `;

        this.bindPanelEvents(panel);
        return panel;
    }

    /**
     * 绑定面板事件
     */
    bindPanelEvents(panel) {
        // 关闭按钮
        panel.querySelector('.bsp-close').addEventListener('click', () => {
            this.hidePanel();
        });

        // 最小化按钮
        panel.querySelector('#bspMinimize').addEventListener('click', () => {
            this.toggleMinimize();
        });

        // 标签切换
        panel.querySelectorAll('.bsp-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    /**
     * 切换标签
     */
    switchTab(tabName) {
        this.currentTab = tabName;

        // 更新标签状态
        this.currentPanel.querySelectorAll('.bsp-tab').forEach(tab => {
            tab.classList.toggle('bsp-tab-active', tab.dataset.tab === tabName);
        });

        // 显示对应内容
        const content = this.currentPanel.querySelector('#bspContent');

        switch(tabName) {
            case 'home':
                this.showHomePage(content);
                break;
            case 'analyze':
                this.showAnalyzePage(content);
                break;
            case 'subtitle':
                this.showSubtitlePage(content);
                break;
        }
    }

    /**
     * 显示首页
     */
    showHomePage(content) {
        content.innerHTML = `
            <div class="bsp-home-content">
                <div class="bsp-welcome-card">
                    <div class="bsp-welcome-icon">🎬</div>
                    <h2>欢迎使用B站AI助手</h2>
                    <p>智能分析视频内容，快速提取字幕信息</p>
                </div>

                <div class="bsp-quick-actions">
                    <button class="bsp-action-btn bsp-btn-analyze" id="bspQuickAnalyze">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        <div>
                            <div class="bsp-action-title">AI分析视频概要</div>
                            <div class="bsp-action-desc">深度分析视频内容、弹幕和评论</div>
                        </div>
                    </button>
                    <button class="bsp-action-btn bsp-btn-subtitle" id="bspQuickSubtitle">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
                        <div>
                            <div class="bsp-action-title">提取视频字幕</div>
                            <div class="bsp-action-desc">一键获取完整字幕内容</div>
                        </div>
                    </button>
                    <button class="bsp-action-btn bsp-btn-settings" id="bspQuickSettings">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
                        <div>
                            <div class="bsp-action-title">模型设置</div>
                            <div class="bsp-action-desc">配置API和模型参数</div>
                        </div>
                    </button>
                </div>
            </div>
        `;

        // 绑定快速操作按钮
        content.querySelector('#bspQuickAnalyze').addEventListener('click', () => {
            this.switchTab('analyze');
            this.startAnalyze();
        });
        content.querySelector('#bspQuickSubtitle').addEventListener('click', () => {
            this.switchTab('subtitle');
            this.startSubtitle();
        });
        content.querySelector('#bspQuickSettings').addEventListener('click', () => {
            this.openSettings();
        });
    }

    /**
     * 显示分析页面
     */
    showAnalyzePage(content) {
        content.innerHTML = `
            <div class="bsp-analyze-page">
                <div id="bspAnalyzeStatus" class="bsp-analyze-status" style="display:none;">
                    <!-- 数据收集进度 -->
                </div>
                <div id="bspAnalyzeResult" class="bsp-analyze-result" style="display:none;">
                    <!-- 分析结果 -->
                </div>
                <div id="bspAnalyzeEmpty" class="bsp-analyze-empty">
                    <div class="bsp-empty-icon">🤖</div>
                    <h3>AI视频分析</h3>
                    <p>点击下方按钮开始智能分析</p>
                    <button class="bsp-start-btn bsp-btn-analyze" id="bspStartAnalyze">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>
                        开始分析
                    </button>
                </div>
            </div>
        `;

        content.querySelector('#bspStartAnalyze').addEventListener('click', () => {
            this.startAnalyze();
        });
    }

    /**
     * 显示字幕页面
     */
    showSubtitlePage(content) {
        content.innerHTML = `
            <div class="bsp-subtitle-page">
                <div id="bspSubtitleResult" class="bsp-subtitle-result" style="display:none;">
                    <!-- 字幕结果 -->
                </div>
                <div id="bspSubtitleEmpty" class="bsp-subtitle-empty">
                    <div class="bsp-empty-icon">📝</div>
                    <h3>视频字幕提取</h3>
                    <p>一键获取完整视频字幕</p>
                    <button class="bsp-start-btn bsp-btn-subtitle" id="bspStartSubtitle">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
                        提取字幕
                    </button>
                </div>
            </div>
        `;

        content.querySelector('#bspStartSubtitle').addEventListener('click', () => {
            this.startSubtitle();
        });
    }

    /**
     * 显示面板
     */
    showPanel() {
        if (!this.currentPanel) {
            this.currentPanel = this.createMainPanel();
            document.body.appendChild(this.currentPanel);
        }

        this.currentPanel.style.display = 'flex';
        this.isMinimized = false;
        this.currentPanel.classList.remove('bsp-minimized');
        this.switchTab('home');
    }

    /**
     * 隐藏面板
     */
    hidePanel() {
        if (this.currentPanel) {
            this.currentPanel.style.display = 'none';
        }
    }

    /**
     * 切换面板显示
     */
    togglePanel() {
        if (this.currentPanel && this.currentPanel.style.display !== 'none') {
            this.hidePanel();
        } else {
            this.showPanel();
        }
    }

    /**
     * 切换最小化
     */
    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        this.currentPanel.classList.toggle('bsp-minimized', this.isMinimized);
    }

    /**
     * 开始分析
     */
    startAnalyze() {
        window.dispatchEvent(new CustomEvent('biliSummarizeAnalyze'));
    }

    /**
     * 开始字幕提取
     */
    startSubtitle() {
        window.dispatchEvent(new CustomEvent('biliSummarizeSubtitle'));
    }

    /**
     * 显示数据收集进度
     */
    showDataProgress(progressData) {
        const statusDiv = this.currentPanel?.querySelector('#bspAnalyzeStatus');
        const emptyDiv = this.currentPanel?.querySelector('#bspAnalyzeEmpty');
        const resultDiv = this.currentPanel?.querySelector('#bspAnalyzeResult');

        if (!statusDiv) return;

        emptyDiv.style.display = 'none';
        resultDiv.style.display = 'none';
        statusDiv.style.display = 'block';

        const {
            step = '初始化',
            usingCookie = false,
            hasSubtitle = false,
            subtitleLength = 0,
            frameCount = 0,
            commentCount = 0,
            danmakuCount = 0
        } = progressData;

        statusDiv.innerHTML = `
            <div class="bsp-progress-item bsp-progress-current">
                <div class="bsp-progress-icon">📊</div>
                <div class="bsp-progress-content">
                    <div class="bsp-progress-title">${step}</div>
                    <div class="bsp-progress-desc">正在收集视频数据...</div>
                </div>
                <div class="bsp-progress-spinner"></div>
            </div>

            <div class="bsp-data-summary">
                <div class="bsp-data-item ${usingCookie ? 'bsp-data-success' : 'bsp-data-neutral'}">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
                    <span>${usingCookie ? '使用登录状态' : '未使用登录状态'}</span>
                </div>
                <div class="bsp-data-item ${hasSubtitle ? 'bsp-data-success' : 'bsp-data-warning'}">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
                    <span>字幕: ${hasSubtitle ? subtitleLength + '字符' : '无字幕'}</span>
                </div>
                <div class="bsp-data-item ${frameCount > 0 ? 'bsp-data-success' : 'bsp-data-neutral'}">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M21 3H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h5v2h8v-2h5c1.1 0 1.99-.9 1.99-2L23 5c0-1.1-.9-2-2-2zm0 14H3V5h18v12z"/></svg>
                    <span>视频帧: ${frameCount}张</span>
                </div>
                <div class="bsp-data-item ${commentCount > 0 ? 'bsp-data-success' : 'bsp-data-neutral'}">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18z"/></svg>
                    <span>评论: ${commentCount}条</span>
                </div>
                <div class="bsp-data-item ${danmakuCount > 0 ? 'bsp-data-success' : 'bsp-data-neutral'}">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
                    <span>弹幕: ${danmakuCount}条</span>
                </div>
            </div>
        `;

        this.updateStatus('processing', step);
    }

    /**
     * 显示AI分析中状态
     */
    showAIAnalyzing() {
        const statusDiv = this.currentPanel?.querySelector('#bspAnalyzeStatus');

        if (!statusDiv) return;

        statusDiv.innerHTML = `
            <div class="bsp-progress-item bsp-progress-current">
                <div class="bsp-progress-icon">🤖</div>
                <div class="bsp-progress-content">
                    <div class="bsp-progress-title">AI正在分析...</div>
                    <div class="bsp-progress-desc">正在生成分析报告，内容将实时显示</div>
                </div>
                <div class="bsp-progress-spinner"></div>
            </div>
            <div class="bsp-stream-container" id="bspStreamContainer">
                <div class="bsp-stream-content" id="bspStreamContent"></div>
            </div>
        `;

        this.updateStatus('processing', 'AI分析中');
    }

    /**
     * 追加流式内容
     */
    appendStreamContent(content) {
        const streamContent = this.currentPanel?.querySelector('#bspStreamContent');
        if (!streamContent) return;

        this.streamContent += content;
        streamContent.innerHTML = this.formatMarkdown(this.streamContent);

        // 自动滚动到底部
        const container = this.currentPanel?.querySelector('#bspStreamContainer');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }

    /**
     * 显示分析完成
     */
    showAnalyzeComplete() {
        this.updateStatus('active', '分析完成');

        // 移除加载动画
        const spinner = this.currentPanel?.querySelector('.bsp-progress-spinner');
        if (spinner) {
            spinner.remove();
        }

        const progressItem = this.currentPanel?.querySelector('.bsp-progress-current');
        if (progressItem) {
            progressItem.classList.remove('bsp-progress-current');
            progressItem.classList.add('bsp-progress-done');
        }
    }

    /**
     * 显示字幕结果
     */
    showSubtitleResult(subtitleData) {
        const emptyDiv = this.currentPanel?.querySelector('#bspSubtitleEmpty');
        const resultDiv = this.currentPanel?.querySelector('#bspSubtitleResult');

        if (!emptyDiv || !resultDiv) return;

        const hasSubtitle = subtitleData.hasSubtitle;
        const text = subtitleData.text || '';

        emptyDiv.style.display = 'none';
        resultDiv.style.display = 'block';

        resultDiv.innerHTML = `
            <div class="bsp-result-header">
                <h3>
                    <svg viewBox="0 0 24 24" style="fill: #00A1D6;"><path fill="currentColor" d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
                    视频字幕
                </h3>
                ${hasSubtitle ? `
                    <button class="bsp-copy-btn" id="bspCopySubtitle">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
                        复制全部
                    </button>
                ` : ''}
            </div>
            ${hasSubtitle ? `
                <div class="bsp-result-content">${this.escapeHtml(text)}</div>
                <div class="bsp-result-footer">
                    <span>共 ${text.length} 字符</span>
                </div>
            ` : `
                <div class="bsp-empty-state">
                    <p>该视频没有字幕</p>
                </div>
            `}
        `;

        // 绑定复制按钮
        const copyBtn = resultDiv.querySelector('#bspCopySubtitle');
        if (copyBtn) {
            copyBtn.addEventListener('click', async () => {
                const success = await this.copyToClipboard(text);
                if (success) {
                    this.showToast('字幕已复制到剪贴板');
                }
            });
        }

        this.updateStatus('active', hasSubtitle ? '字幕提取完成' : '无字幕');
    }

    /**
     * 隐藏加载状态（兼容方法）
     */
    hideLoading() {
        // 不需要做任何事，新的 UI 模式会自动切换显示
        console.log('[UIComponents] hideLoading called');
    }

    /**
     * 更新状态
     */
    updateStatus(state, message) {
        const statusDot = this.currentPanel?.querySelector('.bsp-status-dot');
        const statusText = this.currentPanel?.querySelector('.bsp-status-text');

        if (!statusDot || !statusText) return;

        statusDot.className = 'bsp-status-dot';

        switch (state) {
            case 'active':
                statusDot.classList.add('active');
                break;
            case 'processing':
                statusDot.classList.add('processing');
                break;
        }

        statusText.textContent = message;
    }

    /**
     * 显示Toast
     */
    showToast(message, duration = 2000) {
        const toast = document.createElement('div');
        toast.className = 'bsp-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('bsp-show'), 10);

        setTimeout(() => {
            toast.classList.remove('bsp-show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    /**
     * 打开设置对话框
     */
    openSettings() {
        const dialog = document.createElement('div');
        dialog.className = 'bsp-settings-dialog';
        dialog.innerHTML = `
            <div class="bsp-settings-overlay"></div>
            <div class="bsp-settings-content">
                <div class="bsp-settings-header">
                    <h2>⚙️ 模型配置</h2>
                    <button class="bsp-close" id="bspCloseSettings">
                        <svg viewBox="0 0 24 24" style="width:18px;height:18px;"><path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    </button>
                </div>
                <div class="bsp-settings-body">
                    <div class="bsp-form-group">
                        <label>API地址</label>
                        <input type="text" id="bspApiBase" placeholder="https://api.siliconflow.cn/v1">
                    </div>
                    <div class="bsp-form-group">
                        <label>API密钥</label>
                        <input type="password" id="bspApiKey" placeholder="sk-...">
                    </div>
                    <div class="bsp-form-group">
                        <label>模型</label>
                        <input type="text" id="bspModel" placeholder="Qwen/Qwen3-Omni-30B-A3B-Captioner">
                    </div>
                </div>
                <div class="bsp-settings-footer">
                    <button class="bsp-btn bsp-btn-secondary" id="bspCancelSettings">取消</button>
                    <button class="bsp-btn bsp-btn-primary" id="bspSaveSettings">保存</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        this.loadSettingsToDialog(dialog);

        const closeHandler = () => dialog.remove();
        dialog.querySelector('.bsp-close').addEventListener('click', closeHandler);
        dialog.querySelector('.bsp-settings-overlay').addEventListener('click', closeHandler);
        dialog.querySelector('#bspCancelSettings').addEventListener('click', closeHandler);

        dialog.querySelector('#bspSaveSettings').addEventListener('click', () => {
            this.saveSettingsFromDialog(dialog);
            dialog.remove();
            this.showToast('配置已保存');
        });
    }

    /**
     * 加载设置到对话框
     */
    async loadSettingsToDialog(dialog) {
        if (typeof chrome !== 'undefined' && chrome.storage) {
            chrome.storage.local.get(['aiConfig'], (result) => {
                const config = result.aiConfig || {};
                dialog.querySelector('#bspApiBase').value = config.apiBase || '';
                dialog.querySelector('#bspApiKey').value = config.apiKey || '';
                dialog.querySelector('#bspModel').value = config.model || '';
            });
        }
    }

    /**
     * 保存设置
     */
    saveSettingsFromDialog(dialog) {
        const config = {
            apiBase: dialog.querySelector('#bspApiBase').value.trim(),
            apiKey: dialog.querySelector('#bspApiKey').value.trim(),
            model: dialog.querySelector('#bspModel').value.trim(),
            vlModel: dialog.querySelector('#bspModel').value.trim(),
            temperature: 0.7
        };

        if (typeof chrome !== 'undefined' && chrome.storage) {
            chrome.storage.local.set({ aiConfig: config });
        }

        window.dispatchEvent(new CustomEvent('biliSummarizeConfigUpdate', {
            detail: { config }
        }));
    }

    /**
     * 复制到剪贴板
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (e) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            const success = document.execCommand('copy');
            textarea.remove();
            return success;
        }
    }

    /**
     * 格式化Markdown（简化版）
     */
    formatMarkdown(text) {
        if (!text) return '';

        return text
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 创建浮动按钮
     */
    createFloatingButton() {
        const btn = document.createElement('button');
        btn.id = 'bili-summarize-float-btn';
        btn.className = 'bili-summarize-float-btn';
        btn.title = 'B站AI助手';
        btn.innerHTML = `
            <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
        `;

        btn.addEventListener('click', () => {
            this.togglePanel();
        });

        return btn;
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIComponents;
}
