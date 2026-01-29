document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const elements = {
        videoUrl: document.getElementById('videoUrl'),
        analyzeBtn: document.getElementById('analyzeBtn'),
        loginBtn: document.getElementById('loginBtn'),
        loadingState: document.getElementById('loadingState'),
        resultArea: document.getElementById('resultArea'),
        progressBar: document.getElementById('progressBar'),
        loadingText: document.getElementById('loadingText'),
        loadingSteps: document.getElementById('loadingSteps'),
        
        // Video Info
        videoCover: document.getElementById('videoCover'),
        videoTitle: document.getElementById('videoTitle'),
        upName: document.getElementById('upName'),
        viewCount: document.getElementById('viewCount'),
        danmakuCount: document.getElementById('danmakuCount'),
        likeCount: document.getElementById('likeCount'),
        commentCount: document.getElementById('commentCount'),
        videoDuration: document.getElementById('videoDuration'),
        
        // Tabs & Content
        navBtns: document.querySelectorAll('.nav-btn'),
        tabContents: document.querySelectorAll('.tab-pane'),
        summaryContent: document.getElementById('summaryContent'),
        danmakuContent: document.getElementById('danmakuContent'),
        danmakuWordCloudContainer: document.getElementById('danmakuWordCloudContainer'),
        danmakuCanvas: document.getElementById('danmakuCanvas'),
        danmakuAnalysisResult: document.getElementById('danmakuAnalysisResult'),
        commentsContent: document.getElementById('commentsContent'),
        topCommentsList: document.getElementById('topCommentsList'),
        commentsAnalysisResult: document.getElementById('commentsAnalysisResult'),
        subtitleContent: document.getElementById('subtitleContent'),
        chatContent: document.getElementById('chatContent'),
        rawSubtitleText: document.getElementById('rawSubtitleText'),
        relatedSection: document.getElementById('relatedSection'),
        relatedList: document.getElementById('relatedList'),
        welcomeSection: document.getElementById('welcomeSection'),
        initRelatedList: document.getElementById('initRelatedList'),
        reAnalyzeBtn: document.getElementById('reAnalyzeBtn'),
        watchBiliBtn: document.getElementById('watchBiliBtn'),

        // Tools & Meta
        tokenCount: document.getElementById('tokenCount'),
        analysisMeta: document.getElementById('analysisMeta'),
        copyBtn: document.getElementById('copyBtn'),
        downloadBtn: document.getElementById('downloadBtn'),
        
        // Modal & Toast
        loginModal: document.getElementById('loginModal'),
        closeModal: document.querySelector('.close-modal'),
        qrcodeContainer: document.getElementById('qrcodeContainer'),
        qrcode: document.getElementById('qrcode'),
        loginStatus: document.getElementById('loginStatus'),
        toast: document.getElementById('toast'),

        // Streaming UI
        streamingStatus: document.getElementById('streamingStatus'),
        streamingText: document.getElementById('streamingText'),
        chunkCounter: document.getElementById('chunkCounter'),
        loadingStepper: document.getElementById('loadingStepper'),

        // Settings Drawer
        settingsBtn: document.getElementById('settingsBtn'),
        settingsDrawer: document.getElementById('settingsDrawer'),
        closeDrawerBtn: document.querySelector('.close-drawer'),
        drawerOverlay: document.querySelector('.drawer-overlay'),
        apiBaseInput: document.getElementById('apiBaseInput'),
        apiKeyInput: document.getElementById('apiKeyInput'),
        modelInput: document.getElementById('modelInput'),
        qaModelInput: document.getElementById('qaModelInput'),
        deepResearchModelInput: document.getElementById('deepResearchModelInput'),
        exaApiKeyInput: document.getElementById('exaApiKeyInput'),
        darkModeToggle: document.getElementById('darkModeToggle'),
        saveSettingsBtn: document.getElementById('saveSettingsBtn'),

        // Chat
        chatInput: document.getElementById('chatInput'),
        sendMsgBtn: document.getElementById('sendMsgBtn'),
        chatMessages: document.getElementById('chatMessages'),

        // Hints
        loginHint: document.getElementById('loginHint'),
        hintLoginBtn: document.getElementById('hintLoginBtn'),

        // UP Portrait
        upPortraitCard: document.getElementById('upPortraitCard'),
        upFace: document.getElementById('upFace'),
        upNameDetail: document.getElementById('upNameDetail'),
        upSign: document.getElementById('upSign'),
        upPortraitContent: document.getElementById('upPortraitContent'),

        // New Mode Elements
        modeBtns: document.querySelectorAll('.mode-btn'),
        sidebarNav: document.getElementById('sidebarNav'),
        articleAnalysisContent: document.getElementById('articleAnalysisContent'),
        articleOriginalContent: document.getElementById('articleOriginalContent'),
        userPortraitContentPane: document.getElementById('userPortraitContentPane'),
        userWorksContent: document.getElementById('userWorksContent'),
        userWorksList: document.getElementById('userWorksList'),

        // Search Results Panel
        searchResultsPanel: document.getElementById('searchResultsPanel'),
        resultsList: document.getElementById('resultsList'),
        resultsCount: document.getElementById('resultsCount'),
        closeResultsBtn: document.getElementById('closeResultsBtn'),

        // Research Elements
        researchReportContent: document.getElementById('researchReportContent'),
        researchProcessContent: document.getElementById('researchProcessContent'),
        researchTimeline: document.getElementById('researchTimeline'),
        historyModal: document.getElementById('historyModal'),
        historyList: document.getElementById('historyList'),
        downloadPdfBtn: document.getElementById('downloadPdfBtn'),
        researchHistoryShortcut: document.getElementById('researchHistoryShortcut'),

        // Guide & Donate
        guideBtn: document.getElementById('guideBtn'),
        guideModal: document.getElementById('guideModal'),
        guideContent: document.getElementById('guideContent'),
        closeGuideBtn: document.querySelector('.guide-close'),
        guideDonateBtn: document.getElementById('guideDonateBtn'),
        donateModal: document.getElementById('donateModal'),
        closeDonateBtn: document.getElementById('closeDonateBtn'),
        homeBtn: document.getElementById('homeBtn')
    };

    // State
    let currentMode = 'research'; // video, article, user, research
    let manualModeLock = false; // Prevent auto-switch if user manually clicked
    let currentData = {
        summary: '',
        danmaku: '',
        comments: '',
        rawContent: '',
        fullMarkdown: '',
        videoInfo: null,
        danmakuPreview: [],
        articleData: null,
        userData: null
    };
    let isAnalyzing = false;
    let isChatting = false;
    let chatHistory = [];
    let popularVideosCache = null; // 缓存热门视频数据
    let loginPollInterval = null;

    // --- Event Listeners ---

    // Mode Switcher
    elements.modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetMode = btn.dataset.mode;
            
            // 如果点击的是当前模式，不触发切换提示
            if (targetMode === currentMode && !elements.resultArea.classList.contains('hidden')) {
                return;
            }

            // 如果当前已经在展示结果，提示用户回到主页
            if (!elements.resultArea.classList.contains('hidden')) {
                if (confirm('切换模式将回到主页并清空当前分析结果，确定吗？')) {
                    goHome(targetMode);
                }
                return;
            }

            manualModeLock = true;
            switchMode(targetMode);
            // Reset lock after 15s or when input is cleared
            setTimeout(() => { manualModeLock = false; }, 15000);
        });
    });

    // Auto detect link type
    elements.videoUrl.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        if (!val) {
            manualModeLock = false;
            return;
        }
        
        // If locked by manual click, skip auto-detect
        if (manualModeLock) return;

        if (val.includes('cv') || val.includes('read/') || val.includes('opus/')) {
            switchMode('article');
        } else if (val.includes('space.bilibili.com') || (val.match(/^\d+$/) && val.length > 5)) {
            switchMode('user');
        } else if (val.includes('BV') || val.includes('video/') || val.includes('b23.tv')) {
            switchMode('video');
        }
    });

    // Chat
    elements.sendMsgBtn.addEventListener('click', sendMessage);
    elements.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Settings Drawer
    elements.settingsBtn.addEventListener('click', openSettings);
    elements.closeDrawerBtn.addEventListener('click', closeSettings);
    elements.drawerOverlay.addEventListener('click', closeSettings);
    elements.saveSettingsBtn.addEventListener('click', saveSettings);
    elements.darkModeToggle.addEventListener('change', (e) => toggleDarkMode(e.target.checked));

    // Analyze Button
    elements.analyzeBtn.addEventListener('click', startAnalysis);
    
    // Guide Modal
    const guideMarkdown = `
### 🚀 快速开始
欢迎使用 BiliBili Summarize！这是一个强大的 AI 驱动内容分析工具。本次更新带来了全新的 **智能小UP** 与 **深度研究** 模式。

#### 1. 🤖 智能小UP (全新)
- **定位**：自适应全能助手。
- **功能**：能够根据您问题的复杂度，自动决定是进行简单搜索还是深度检索。它会综合 B 站视频内容与全网资讯，为您提供精准、带有引用的深度回答。
- **操作**：在首页切换至“智能小UP”模式，直接输入您想了解的问题即可。

#### 2. 🔬 深度研究 (全新)
- **定位**：针对复杂课题的自动化研究员。
- **功能**：它会拆解您的课题，自动执行多轮视频搜索、内容解析与网页检索，最终汇总生成一份结构清晰、论据充分的深度研究报告。
- **特性**：全新的“思考过程”面板，实时展示 Agent 的推理链路与预分析文本。

#### 3. 📺 视频/专栏/用户分析
- **视频分析**：支持 BV 号/链接，自动提炼总结、弹幕舆情、评论热点及视觉关键帧。
- **专题解析**：深度解析 B 站专栏文章及 Opus 动态图文的脉络。
- **用户画像**：输入 UID 或空间链接，基于作品风格分析 UP 主的内容价值。

#### 4. ⌨️ 快捷操作
- **全屏模式**：在智能小UP界面，双击消息区域或点击右上角按钮可进入沉浸式全屏对话。
- **模糊匹配**：直接输入关键词，系统会自动搜索并列出匹配的视频供您选择。

---

### 🛡️ 隐私与信息收集
- **凭据处理**：若您选择登录 B 站，您的 Cookie 仅保存在本地 \`.env\` 文件中，仅用于访问高清视频、提取弹幕等必要操作。
- **数据流向**：分析过程中的文本/画面信息将通过您的 **自定义 AI 渠道** 处理，我们不存储任何分析内容。

---

### ⚖️ 免责声明
- **内容准确性**：分析结果由 AI 生成，可能存在“幻觉”或不准确之处，**请仅供参考**。
- **责任边界**：本工具仅供学习交流使用，严禁用于商业用途。请尊重 Bilibili 平台及原作者的版权。

---

### ❤️ 支持项目
如果您觉得本工具对您有帮助：
1. 请前往 [GitCode 仓库](https://gitcode.com/mumu_xsy/Bilibili_Analysis_Helper) 点个 **Star**。
2. 欢迎点击下方按钮进行赞助，您的支持是项目持续更新的最大动力！
`;

    elements.guideBtn.onclick = () => {
        elements.guideContent.innerHTML = marked.parse(guideMarkdown);
        elements.guideModal.classList.remove('hidden');
    };

    elements.closeGuideBtn.onclick = () => elements.guideModal.classList.add('hidden');
    
    elements.guideDonateBtn.onclick = () => {
        elements.guideModal.classList.add('hidden');
        elements.donateModal.classList.remove('hidden');
    };

    elements.closeDonateBtn.onclick = () => elements.donateModal.classList.add('hidden');

    window.addEventListener('click', (e) => {
        if (e.target === elements.guideModal) elements.guideModal.classList.add('hidden');
        if (e.target === elements.donateModal) elements.donateModal.classList.add('hidden');
    });

    // Enter Key
    elements.videoUrl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') startAnalysis();
    });

    // Tab Switching
    elements.navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            switchTab(targetTab);
        });
    });

    // Copy & Download
    elements.copyBtn.addEventListener('click', copyContent);
    elements.downloadBtn.addEventListener('click', downloadMarkdown);
    elements.reAnalyzeBtn.addEventListener('click', () => {
        if (currentData.videoInfo && currentData.videoInfo.bvid) {
            elements.videoUrl.value = currentData.videoInfo.bvid;
            startAnalysis();
        }
    });

    // Login Modal
    elements.closeModal.addEventListener('click', closeLoginModal);
    window.addEventListener('click', (e) => {
        if (e.target === elements.loginModal) closeLoginModal();
    });

    // Logo Easter Egg
    let logoClicks = 0;
    const logoArea = document.querySelector('.logo-area');
    if (logoArea) {
        logoArea.addEventListener('click', () => {
            // 如果已经在主页且点击次数不够，触发彩蛋逻辑
            if (elements.resultArea.classList.contains('hidden') && elements.loadingState.classList.contains('hidden')) {
                logoClicks++;
                if (logoClicks === 5) {
                    BiliHelpers.showToast('🎉 你发现了隐藏彩蛋！感谢支持 BiliBili Summarize！', elements.toast);
                    logoArea.style.animation = 'tada 1s';
                    setTimeout(() => logoArea.style.animation = '', 1000);
                    logoClicks = 0;
                }
            } else {
                // 如果在结果页或加载页，点击 Logo 直接回首页
                goHome();
            }
        });
    }

    // Initial load
    initApp();

    async function initApp() {
        // --- 1. 优先加载本地主题设置 (消除白屏/闪烁) ---
        const isDark = localStorage.getItem('darkMode') === 'true';
        if (isDark) {
            elements.darkModeToggle.checked = true;
            toggleDarkMode(true);
        }

        // --- 2. 并行执行所有初始化请求 (提升 2-3 倍启动速度) ---
        try {
            await Promise.all([
                checkLoginState(),
                fetchSettings(),
                fetchPopularVideos()
            ]);
        } catch (err) {
            console.error('Initialization error:', err);
        }
    }

    // 已迁移到 BiliAPI.getPopularVideos，保留包装函数以兼容调用
    async function fetchPopularVideos() {
        try {
            // 如果已有缓存，直接渲染
            if (popularVideosCache) {
                renderInitRecommendations(popularVideosCache);
                setupHorizontalScroll();
                return;
            }

            const videos = await BiliAPI.getPopularVideos();
            if (videos && videos.length > 0) {
                popularVideosCache = videos; // 存入缓存
                renderInitRecommendations(videos);
                setupHorizontalScroll();
            }
        } catch (error) {
            console.error('Fetch popular failed:', error);
        }
    }

    function setupHorizontalScroll() {
        const scrollContainer = elements.initRelatedList;
        if (!scrollContainer) return;

        scrollContainer.addEventListener('wheel', (evt) => {
            evt.preventDefault();
            scrollContainer.scrollLeft += evt.deltaY;
        });
    }

    function renderInitRecommendations(videos) {
        if (!videos || videos.length === 0 || !elements.initRelatedList) return;
        elements.initRelatedList.innerHTML = '';
        videos.forEach((video, index) => {
            const card = document.createElement('div');
            card.className = 'related-card animate-up';
            // Staggered animation delay
            card.style.animationDelay = `${0.5 + (index * 0.1)}s`;
            card.innerHTML = `
                <div class="related-cover-wrapper">
                    <img class="related-cover" src="/api/image-proxy?url=${encodeURIComponent(video.cover)}" loading="lazy">
                    <span class="related-duration">${video.duration_str}</span>
                </div>
                <div class="related-content">
                    <div class="related-title" title="${video.title}">${video.title}</div>
                    <div class="related-info">
                        <span class="related-author">${video.author}</span>
                        <span class="related-views">${BiliHelpers.formatNumber(video.view)} 播放</span>
                    </div>
                    <div class="related-actions" style="display: flex; gap: 8px; margin-top: 12px;">
                        <button class="btn-mini btn-primary-mini" style="padding: 6px 12px;" onclick="event.stopPropagation(); window.analyzeBvid('${video.bvid}')">开始分析</button>
                        <a href="https://www.bilibili.com/video/${video.bvid}" target="_blank" class="btn-mini btn-outline-mini" style="padding: 6px 12px;" onclick="event.stopPropagation()">观看视频</a>
                    </div>
                </div>
            `;
            card.onclick = () => {
                elements.videoUrl.value = video.bvid;
                startAnalysis();
            };
            elements.initRelatedList.appendChild(card);
        });
    }

    // --- Main Functions ---

    // 已迁移到 BiliAPI.getSettings，保留包装函数以兼容调用
    async function fetchSettings() {
        try {
            const data = await BiliAPI.getSettings();
            if (data) {
                elements.apiBaseInput.value = data.openai_api_base || '';
                elements.apiKeyInput.value = data.openai_api_key || '';
                // Change input type to text so it's not hidden
                elements.apiKeyInput.type = 'text';
                elements.modelInput.value = data.model || '';
                elements.qaModelInput.value = data.qa_model || '';
                elements.deepResearchModelInput.value = data.deep_research_model || '';
                elements.exaApiKeyInput.value = data.exa_api_key || '';

                // Change input type to text so it's not hidden
                elements.apiKeyInput.type = 'text';
                elements.exaApiKeyInput.type = 'text';

                // If backend says dark mode and local storage is empty, use backend
                if (data.dark_mode && localStorage.getItem('darkMode') === null) {
                    elements.darkModeToggle.checked = true;
                    toggleDarkMode(true);
                }
            }
        } catch (error) {
            console.error('Fetch settings failed:', error);
        }
    }

    // 已迁移到 BiliAPI.saveSettings，保留包装函数以兼容调用
    async function saveSettings() {
        const data = {
            openai_api_base: elements.apiBaseInput.value.trim(),
            openai_api_key: elements.apiKeyInput.value.trim(),
            model: elements.modelInput.value.trim(),
            qa_model: elements.qaModelInput.value.trim(),
            deep_research_model: elements.deepResearchModelInput.value.trim(),
            exa_api_key: elements.exaApiKeyInput.value.trim(),
            dark_mode: elements.darkModeToggle.checked
        };

        try {
            elements.saveSettingsBtn.disabled = true;
            elements.saveSettingsBtn.textContent = '保存中...';

            const result = await BiliAPI.saveSettings(data);

            if (result.success) {
                BiliHelpers.showToast('设置已保存！', elements.toast);
                closeSettings();
            } else {
                BiliHelpers.showToast('保存失败: ' + (result.error || '未知错误'), elements.toast);
            }
        } catch (error) {
            BiliHelpers.showToast('保存时发生错误: ' + error.message, elements.toast);
        } finally {
            elements.saveSettingsBtn.disabled = false;
            elements.saveSettingsBtn.textContent = '保存设置';
        }
    }

    // 已迁移到 ModeUI，保留包装函数以兼容调用
    function initAnalysisMeta(mode) {
        ModeUI.initAnalysisMeta(elements, mode);
    }

    function updateMetaValue(id, value, prefix = '') {
        ModeUI.updateMetaValue(id, value, prefix);
    }

    function toggleDarkMode(isDark) {
        ModeUI.toggleDarkMode(isDark);
    }

    function resetMeta(mode) {
        ModeUI.resetMeta(elements, mode);
    }

    // Search Results Panel
    elements.closeResultsBtn.onclick = () => elements.searchResultsPanel.classList.add('hidden');

    async function startAnalysis() {
        if (isAnalyzing) return;
        
        const input = elements.videoUrl.value.trim();
        if (!input) {
            BiliHelpers.showToast('请输入B站链接或关键词', elements.toast);
            return;
        }

        // Hide previous search results
        elements.searchResultsPanel.classList.add('hidden');

        // Check if input is a direct ID/Link or a keyword
        const isBvid = input.includes('BV') || input.includes('video/');
        const isCvid = input.includes('cv') || input.includes('read/') || input.includes('opus/');
        const isUid = input.includes('space.bilibili.com') || (input.match(/^\d+$/) && input.length > 5);
        
        // --- 核心修复：如果是深度研究模式，不要触发模糊搜索下拉框，直接开始任务 ---
        if (currentMode !== 'research') {
            // If it's a keyword (not a link/ID), perform search first
            if (!isBvid && !isCvid && !isUid && !input.startsWith('http')) {
                await performSearch(input);
                return;
            }
        }

        // --- Standard Analysis Flow ---
        isAnalyzing = true;
        elements.analyzeBtn.disabled = true;
        elements.homeBtn.classList.remove('hidden');

        // --- 核心修复：深度研究采用平滑动画过渡，不显示 TV 加载动画 ---
        const isFastMode = currentMode === 'research';

        if (isFastMode) {
            elements.welcomeSection.classList.add('fade-out-down');
            // 延迟一小会儿显示结果区，等欢迎区退场
            setTimeout(() => {
                elements.welcomeSection.classList.add('hidden');
                elements.resultArea.classList.remove('hidden');
                elements.resultArea.classList.add('fade-in-up');
            }, 300);
        } else {
            elements.welcomeSection.classList.add('hidden');
            elements.loadingState.classList.remove('hidden');
            elements.resultArea.classList.add('hidden');
        }

        resetProgress();
        resetMeta(currentMode); // 传入当前模式进行重置
        initStepper(currentMode);
        updateSidebarUI(); // 在此处真正切换功能入口

        // Reset Data
        currentData = { summary: '', danmaku: '', comments: '', rawContent: '', fullMarkdown: '', videoInfo: null, danmakuPreview: [], articleData: null, userData: null };
        chatHistory = [];

        // --- 核心修复：不同模式显示不同的对话初始消息 ---
        const assistantGreeting = '你好！我是你的智能分析助手。我已经阅读了分析报告，你可以随时问我细节问题。';

        elements.chatMessages.innerHTML = `
            <div class="message assistant">
                <div class="message-content">${assistantGreeting}</div>
            </div>
        `;

        // Reset contents
        elements.summaryContent.innerHTML = '<div class="empty-state"><p>正在生成视频分析...</p></div>';
        elements.danmakuAnalysisResult.innerHTML = '<div class="empty-state"><p>正在分析弹幕...</p></div>';
        elements.commentsAnalysisResult.innerHTML = '<div class="empty-state"><p>正在分析评论...</p></div>';
        elements.articleAnalysisContent.innerHTML = '<div class="empty-state"><p>正在生成专栏分析...</p></div>';
        elements.userPortraitContentPane.innerHTML = '<div class="empty-state"><p>正在分析UP主风格画像...</p></div>';

        try {
            if (currentMode === 'user') {
                // User mode: not streaming, direct API
                await startUserAnalysis(input);
            } else if (currentMode === 'research') {
                // Research mode: special streaming
                await processResearchStream(input);
            } else {
                // Video/Article mode: streaming API
                await processStreamAnalysis(input);
            }
        } catch (error) {
            console.error('Analysis failed:', error);
            BiliHelpers.showToast('分析失败: ' + error.message, elements.toast);
            isAnalyzing = false;
            elements.analyzeBtn.disabled = false;
            elements.loadingState.classList.add('hidden');
        }
    }

    async function startUserAnalysis(input) {
        // Extract UID
        let uid = input;
        if (input.includes('space.bilibili.com/')) {
            uid = input.match(/space\.bilibili\.com\/(\d+)/)[1];
        }
        
        updateStepper('info', 'active');
        updateProgress(20, '正在获取UP主资料...');
        const res = await fetch('/api/user/portrait', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uid: uid })
        });
        const json = await res.json();
        
        if (json.success) {
            updateStepper('info', 'completed');
            updateStepper('content', 'active');
            updateProgress(60, '分析作品趋势...');
            
            // Artificial delay for better UX feel
            await new Promise(r => setTimeout(r, 800));
            
            updateStepper('content', 'completed');
            updateStepper('ai', 'active');
            updateProgress(90, '生成AI深度画像...');
            
            renderUserPortrait(json.data);
            updateStepper('ai', 'completed');
            updateProgress(100, '分析完成');
            
            isAnalyzing = false;
            elements.analyzeBtn.disabled = false;
            elements.loadingState.classList.add('hidden');
            elements.resultArea.classList.remove('hidden');
            BiliHelpers.showToast('分析完成！✨', elements.toast);
        } else {
            throw new Error(json.error);
        }
    }

    function renderUserPortrait(data) {
        currentData.userData = data;
        currentData.fullMarkdown = data.portrait; // For chat
        currentData.videoInfo = { title: data.info.name, author: data.info.name }; // Mock for chat
        
        // Update Token Count
        if (data.tokens_used) {
            elements.tokenCount.textContent = data.tokens_used;
        }

        // Update Meta/Card (Reusing video card area for basic user info)
        elements.videoTitle.textContent = data.info.name;
        elements.upName.textContent = data.info.official || '个人UP主';
        elements.viewCount.textContent = '粉丝: ' + BiliHelpers.formatNumber(data.info.follower || 0);
        elements.danmakuCount.textContent = '-';
        elements.likeCount.textContent = '-';
        elements.commentCount.textContent = '-';
        elements.videoDuration.textContent = 'UID: ' + data.info.mid;
        elements.videoCover.src = `/api/image-proxy?url=${encodeURIComponent(data.info.face)}`;
        
        // Update both the Portrait Card and the Tab Pane
        const portraitHTML = marked.parse(data.portrait);
        if (elements.upPortraitContent) elements.upPortraitContent.innerHTML = portraitHTML;
        if (elements.userPortraitContentPane) elements.userPortraitContentPane.innerHTML = portraitHTML;
        
        // Update Meta for User
        updateMetaValue('metaUserLevel', 'L' + data.info.level);
        updateMetaValue('metaFollowers', BiliHelpers.formatNumber(data.info.follower || 0));
        updateMetaValue('metaWorksCount', data.recent_videos ? data.recent_videos.length : 0);
        
        // Update Works Tab
        elements.userWorksList.innerHTML = '';
        if (data.recent_videos && data.recent_videos.length > 0) {
            data.recent_videos.forEach(v => {
                const card = document.createElement('div');
                card.className = 'user-work-card';
                // Ensure pic URL is absolute
                const picUrl = v.pic.startsWith('//') ? 'https:' + v.pic : v.pic;
                card.innerHTML = `
                    <div class="user-work-cover-wrapper">
                        <img class="user-work-cover" src="/api/image-proxy?url=${encodeURIComponent(picUrl)}" loading="lazy">
                        <span class="user-work-duration">${v.length}</span>
                    </div>
                    <div class="user-work-info">
                        <div class="user-work-title" title="${v.title}">${v.title}</div>
                        <div class="user-work-meta">播放: ${BiliHelpers.formatNumber(v.play)}</div>
                        <div class="user-work-actions">
                            <button class="btn-mini btn-primary-mini" onclick="event.stopPropagation(); window.analyzeBvid('${v.bvid}')">智能分析</button>
                            <a href="https://www.bilibili.com/video/${v.bvid}" target="_blank" class="btn-mini btn-outline-mini" onclick="event.stopPropagation()">跳转观看</a>
                        </div>
                    </div>
                `;
                card.onclick = () => {
                    elements.videoUrl.value = v.bvid;
                    switchMode('video');
                    startAnalysis();
                };
                elements.userWorksList.appendChild(card);
            });
        } else {
            elements.userWorksList.innerHTML = '<div class="empty-state"><p>暂无近期公开作品</p></div>';
        }
    }

    async function processResearchStream(topic) {
        const response = await fetch('/api/research', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '深度研究请求失败');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        // Reset Research UI
        elements.researchTimeline.innerHTML = '';
        elements.researchReportContent.innerHTML = '<div class="empty-state"><p>AI 正在分析并搜集资料...</p></div>';
        let fullReport = '';
        let totalResearchTokens = 0;
        let thinkingTokens = 0;

        // 初始化工具栏元数据
        initAnalysisMeta('research');
        elements.tokenCount.textContent = '0';

        // 更新大卡片显示课题
        elements.videoTitle.textContent = `课题研究：${topic}`;
        elements.upName.textContent = 'Deep Research Agent';
        // 使用一个更合适的图标
        elements.videoCover.src = 'https://www.bilibili.com/favicon.ico'; 
        elements.videoDuration.textContent = '深度研究模式';
        
        // 更新大卡片统计
        elements.viewCount.textContent = '🔄 轮0';
        elements.danmakuCount.textContent = '🔍 次0';
        elements.likeCount.textContent = '📽️ 次0';
        elements.commentCount.textContent = '🪙 0';

        let roundCount = 0;
        let searchCount = 0;
        let analysisCount = 0;

        // 初始节点
        addTimelineItem('tool_start', '初始化研究计划', '深度研究 Agent 已启动，正在拆解研究课题...');

        updateStepper('ai', 'active');
        updateProgress(50, '深度研究 Agent 启动中...');

        updateSidebarUI();
        switchTab('research_process');

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonStr = line.slice(6);
                    let data;
                    try {
                        data = JSON.parse(jsonStr);
                    } catch (e) { continue; }
                    
                            if (data.type === 'round_start') {
                                roundCount = data.round;
                                elements.viewCount.textContent = `🔄 轮${roundCount}`;
                                updateMetaValue('metaRounds', roundCount, '轮');
                            } else if (data.type === 'report_start') {
                                // 收到正式报告开始信号，清空之前的研究过程/计划文本，确保报告纯净
                                fullReport = '';
                                // 核心修复：Token 消耗应全程叠加，不再此处清零
                                elements.researchReportContent.innerHTML = '';
                            } else if (data.type === 'thinking') {
                        thinkingTokens += data.content.length;
                        const totalTokens = totalResearchTokens + thinkingTokens;
                        updateStreamingBadge(totalTokens);
                        elements.commentCount.textContent = `🪙 ${totalTokens}`;
                        elements.tokenCount.textContent = totalTokens;
                        updateMetaValue('metaTokens', totalTokens);
                        
                        const lastItem = elements.researchTimeline.lastElementChild;
                        if (lastItem && lastItem.classList.contains('type-thinking') && lastItem.classList.contains('active')) {
                            const detail = lastItem.querySelector('.timeline-detail');
                            detail.textContent += data.content;
                        } else {
                            addTimelineItem('thinking', 'Agent 思考中...', data.content);
                        }
                    } else if (data.type === 'content') {
                        fullReport += data.content;
                        totalResearchTokens += data.content.length;
                        const totalTokens = totalResearchTokens + thinkingTokens;
                        elements.commentCount.textContent = `🪙 ${totalTokens}`;
                        elements.tokenCount.textContent = totalTokens;
                        updateMetaValue('metaTokens', totalTokens);
                        
                        renderMarkdown(elements.researchReportContent, fullReport);
                        currentData.fullMarkdown = fullReport;
                        
                        const thinkingItems = elements.researchTimeline.querySelectorAll('.type-thinking.active');
                        thinkingItems.forEach(item => {
                            item.classList.remove('active');
                            item.classList.add('completed');
                        });

                        updateStreamingBadge(totalTokens);
                            } else if (data.type === 'tool_progress') {
                                if (data.tool === 'analyze_video') {
                                    const msgEl = document.getElementById(`msg-${data.bvid}`);
                                    const tokenEl = document.getElementById(`tokens-${data.bvid}`);
                                    const ghostEl = document.getElementById(`ghost-${data.bvid}`);
                                    const titleEl = document.getElementById(`title-${data.bvid}`);
                                    
                                    if (msgEl && data.message) {
                                        msgEl.textContent = data.message;
                                    }

                                    if (titleEl && data.title) {
                                        titleEl.textContent = `正在分析视频: ${data.title}`;
                                        titleEl.title = data.title; // 悬浮显示完整标题
                                    }
                                    
                                    if (tokenEl && data.tokens !== undefined) {
                                        const currentTokens = data.tokens || 0;
                                        tokenEl.textContent = `正在建模: ${currentTokens} Tokens`;
                                        
                                        // 同时更新顶部的总 Token 消耗预览（估算）
                                        const totalSoFar = totalResearchTokens + thinkingTokens + currentTokens;
                                        elements.commentCount.textContent = `🪙 ${totalSoFar}`;
                                        elements.tokenCount.textContent = totalSoFar;
                                        updateMetaValue('metaTokens', totalSoFar);
                                    }

                                    // 幻影流式预览更新
                                    if (ghostEl && data.content) {
                                        ghostEl.textContent += data.content;
                                        ghostEl.scrollTop = ghostEl.scrollHeight;
                                    }
                                }
                            } else if (data.type === 'tool_start') {
                                let title = `执行工具: ${data.tool}`;
                                let toolBvid = data.args ? data.args.bvid : null;
                                let toolKeyword = data.args ? data.args.keyword : null;
                                
                                if (data.tool === 'search_videos') {
                                    title = '🔍 搜索相关视频';
                                    searchCount++;
                                    elements.danmakuCount.textContent = `🔍 次${searchCount}`;
                                    updateMetaValue('metaSearch', searchCount, '次');
                                    
                                    // 丰富搜索参数显示，并增加等待状态
                                    data.args._status = 'loading';
                                } else if (data.tool === 'web_search') {
                                    title = '🌐 全网深度搜索';
                                    data.args._status = 'searching';
                                } else if (data.tool === 'analyze_video') {
                                    title = `📽️ 分析视频: ${data.args.bvid}`;
                                    analysisCount++;
                                    elements.likeCount.textContent = `📽️ 次${analysisCount}`;
                                    updateMetaValue('metaAnalysis', analysisCount, '次');
                                    
                                    const oldTitle = document.getElementById(`title-${toolBvid}`);
                                    if (oldTitle) {
                                        const oldItem = oldTitle.closest('.timeline-item');
                                        if (oldItem) oldItem.remove();
                                    }
                                } else if (data.tool === 'search_users') {
                                    title = '👤 搜索 B 站 UP 主';
                                    data.args._status = 'searching_user';
                                } else if (data.tool === 'get_user_recent_videos') {
                                    title = `📽️ 获取 UP 主最近作品 (UID: ${data.args.mid})`;
                                    data.args._status = 'fetching_works';
                                } else if (data.tool === 'finish_research_and_write_report') {
                                    title = '✍️ 正在撰写深度研究报告';
                                    elements.downloadPdfBtn.classList.add('hidden');
                                    data.args._status = 'writing';
                                }
                                
                                addTimelineItem('tool_start', title, data.args);
                            } else if (data.type === 'tool_result') {
                                let title = `工具已完成: ${data.tool}`;
                                if (data.tool === 'search_videos') {
                                    title = '✅ 搜索完成';
                                    // 寻找并更新搜索状态
                                    const items = elements.researchTimeline.querySelectorAll('.timeline-item.type-tool_start.active');
                                    items.forEach(item => {
                                        const statusEl = item.querySelector('.search-status');
                                        if (statusEl) {
                                            statusEl.textContent = '搜索已就绪';
                                            statusEl.style.color = '#4CAF50';
                                            item.classList.remove('active');
                                            item.classList.add('completed');
                                        }
                                    });
                                } else if (data.tool === 'web_search') {
                                    title = '✅ 全网搜索完成';
                                    const items = elements.researchTimeline.querySelectorAll('.timeline-item.type-tool_start.active');
                                    items.forEach(item => {
                                        const statusEl = item.querySelector('.search-status');
                                        if (statusEl && statusEl.textContent.includes('全网')) {
                                            statusEl.textContent = '联网检索已完成';
                                            statusEl.style.color = 'var(--bili-blue)';
                                            item.classList.remove('active');
                                            item.classList.add('completed');
                                        }
                                    });
                                } else if (data.tool === 'search_users') {
                                    title = '✅ 用户搜索完成';
                                } else if (data.tool === 'get_user_recent_videos') {
                                    title = '✅ UP 主作品集获取成功';
                                }
                                else if (data.tool === 'analyze_video') {
                                    // 智能更新 UI：如果已经有这个视频的进度框，直接更新它，不要新建节点
                                    const msgEl = document.getElementById(`msg-${data.result.bvid}`);
                                    const tokenEl = document.getElementById(`tokens-${data.result.bvid}`);
                                    const containerEl = document.getElementById(`tokens-container-${data.result.bvid}`);
                                    const titleEl = document.getElementById(`title-${data.result.bvid}`);

                                    if (msgEl) {
                                        msgEl.textContent = '分析建模已完成';
                                        msgEl.style.color = '#4CAF50';
                                        
                                        if (tokenEl && data.tokens) {
                                            tokenEl.textContent = `✨ 消耗: ${data.tokens} Tokens`;
                                            tokenEl.style.color = '#2E7D32'; // 更深一点的绿色
                                            tokenEl.style.fontWeight = 'bold';
                                            
                                            if (containerEl) {
                                                containerEl.style.background = 'rgba(76, 175, 80, 0.1)';
                                                containerEl.style.border = '1px solid rgba(76, 175, 80, 0.2)';
                                            }
                                            
                                            totalResearchTokens += data.tokens;
                                            const totalTokens = totalResearchTokens + thinkingTokens;
                                            elements.commentCount.textContent = `🪙 ${totalTokens}`;
                                            elements.tokenCount.textContent = totalTokens;
                                            updateMetaValue('metaTokens', totalTokens);
                                        }
                                        
                                        if (containerEl) {
                                            const dot = containerEl.querySelector('.pulse-dot');
                                            if (dot) dot.style.display = 'none';
                                        }

                                        // 清理幻影内容（完成后保持清爽，或保留一点余韵）
                                        const ghostEl = document.getElementById(`ghost-${data.result.bvid}`);
                                        if (ghostEl) {
                                            ghostEl.style.opacity = '0.05'; // 进一步变淡
                                        }
                                        
                                        if (titleEl) {
                                            titleEl.textContent = `✅ 视频分析完成: ${data.result.title || data.result.bvid}`;
                                            titleEl.title = data.result.title || '';
                                        }
                                        
                                        // 标记该时间轴节点为完成状态
                                        const item = msgEl.closest('.timeline-item');
                                        if (item) {
                                            item.classList.remove('active');
                                            item.classList.add('completed');
                                        }
                                        continue; // 关键：不再向下执行 addTimelineItem，而是继续处理下一条流数据
                                    }
                                    title = `✅ 视频分析完成`;
                                } else if (data.tool === 'finish_research_and_write_report') {
                                    title = '✅ 报告大纲已就绪';
                                }
                                
                                addTimelineItem('tool_result', title, data.result);
                            } else if (data.type === 'error') {
                        addTimelineItem('error', `出现错误: ${data.error}`);
                    } else if (data.type === 'done') {
                        BiliHelpers.showToast('深度研究已完成并持久化！', elements.toast);
                        updateProgress(100, '研究完成');
                        addTimelineItem('tool_result', '✨ 研究报告生成完毕', '所有资料已整合并持久化，点击左侧“研究报告”查看。');
                        
                        // 尝试获取刚生成的文件ID以便立即下载 PDF
                        fetch('/api/research/history')
                            .then(res => res.json())
                            .then(hist => {
                                if (hist.success && hist.data.length > 0) {
                                    currentData.researchFileId = hist.data[0].id;
                                    elements.downloadPdfBtn.classList.remove('hidden');
                                }
                            });
                    }
                }
            }
        }
        
        isAnalyzing = false;
        elements.analyzeBtn.disabled = false;
        if (fullReport) {
            switchTab('research_report');
        }
    }

    function updateStreamingBadge(tokenCount) {
        const lastItem = elements.researchTimeline.lastElementChild;
        if (!lastItem) return;
        
        const titleArea = lastItem.querySelector('.timeline-title');
        let badge = titleArea.querySelector('.streaming-data-badge');
        
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'streaming-data-badge';
            titleArea.appendChild(badge);
        }
        
        badge.innerHTML = `<span class="pulse-dot"></span> 🪙 累计 Tokens: ${tokenCount}`;
    }

    function addTimelineItem(type, title, data = null) {
        const item = document.createElement('div');
        item.className = `timeline-item type-${type} active`;
        
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        
        let contentHTML = `
            <div class="timeline-time">${timeStr}</div>
            <div class="timeline-content-box">
                <div class="timeline-title">
                    ${type === 'thinking' ? '<span class="thinking-badge">Think</span>' : ''}
                    ${title}
                </div>
                <div class="timeline-detail"></div>
            </div>
        `;
        
        item.innerHTML = contentHTML;
        const detailDiv = item.querySelector('.timeline-detail');
        
        if (data) {
            if (typeof data === 'string') {
                detailDiv.textContent = data;
            } else {
                if (Array.isArray(data)) {
                    if (data.length > 0 && data[0].url) {
                        // 网络搜索结果美化
                        detailDiv.innerHTML = `<div class="tool-call-card" style="border-left: 3px solid var(--bili-blue); background: rgba(35, 173, 229, 0.03);">
                            <div class="tool-name" style="color: var(--bili-blue);">全网搜索结果 (${data.length} 条):</div>
                            <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 8px;">
                                ${data.map(item => `
                                    <div style="font-size: 13px; display: flex; flex-direction: column; gap: 2px;">
                                        <a href="${item.url}" target="_blank" style="color: var(--bili-blue); font-weight: 600; text-decoration: none;">🌐 ${item.title}</a>
                                        <span style="font-size: 11px; color: var(--text-secondary); opacity: 0.8;">发布于: ${item.published_date}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>`;
                    } else if (data.length > 0 && data[0].mid) {
                        // 用户搜索结果美化
                        detailDiv.innerHTML = `<div class="tool-call-card" style="border-left-color: var(--bili-blue);">
                            <div class="tool-name" style="color: var(--bili-blue);">找到相关 UP 主 (${data.length} 位):</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                                ${data.map(u => `
                                    <div style="display: flex; align-items: center; gap: 6px; background: rgba(35, 173, 229, 0.05); padding: 4px 8px; border-radius: 12px; border: 1px solid rgba(35, 173, 229, 0.1);">
                                        <img src="/api/image-proxy?url=${encodeURIComponent(u.face)}" style="width: 20px; height: 20px; border-radius: 50%;">
                                        <span style="font-size: 12px; font-weight: 600;">${u.name}</span>
                                        <span style="font-size: 10px; color: var(--text-secondary);">UID:${u.mid}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>`;
                    } else if (data.length > 0 && data[0].bvid && !data[0].url) {
                        // 视频列表/作品集美化
                        detailDiv.innerHTML = `<div class="tool-call-card">
                            <div class="tool-name">获取到 ${data.length} 条视频素材:</div>
                            <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 6px;">
                                ${data.map(v => `<div style="font-size: 12px; color: var(--text-main); opacity: 0.9;">📽️ <span style="font-weight: 600; color: var(--bili-pink);">${v.bvid}</span> ${v.title}</div>`).join('')}
                            </div>
                        </div>`;
                    } else {
                        // 默认列表美化 (兜底)
                        detailDiv.innerHTML = `<div class="tool-call-card">
                            <div class="tool-name">发现 ${data.length} 条相关内容:</div>
                            ${data.map(v => `<div style="margin-bottom:4px; font-size: 12px;">📄 ${v.title || JSON.stringify(v)}</div>`).join('')}
                        </div>`;
                    }
                } else if (data.keyword) {
                    // 搜索参数美化 (视频 or 用户)
                    const isUserSearch = data._status === 'searching_user';
                    detailDiv.innerHTML = `<div class="tool-call-card" ${isUserSearch ? 'style="border-left-color: var(--bili-blue);"' : ''}>
                        <div class="tool-name">${isUserSearch ? '发起 UP 主搜索:' : '发起视频搜索:'}</div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-top: 8px;">
                            <span class="search-keyword" ${isUserSearch ? 'style="background: rgba(35, 173, 229, 0.1); color: var(--bili-blue); border-color: rgba(35, 173, 229, 0.2);"' : ''}>${data.keyword}</span>
                            ${data._status ? `
                                <span class="search-status" style="font-size: 12px; color: ${isUserSearch ? 'var(--bili-blue)' : 'var(--bili-pink)'}; display: flex; align-items: center; gap: 4px;">
                                    <span class="pulse-dot" ${isUserSearch ? 'style="background-color: var(--bili-blue);"' : ''}></span> ⏳ ${isUserSearch ? '正在检索 B 站用户...' : '正在检索 B 站视频...'}
                                </span>
                            ` : ''}
                        </div>
                    </div>`;
                } else if (data.mid) {
                    // 获取作品集参数美化
                    detailDiv.innerHTML = `<div class="tool-call-card" style="border-left-color: var(--bili-blue);">
                        <div class="tool-name">发起作品集检索:</div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-top: 8px;">
                            <span class="search-keyword" style="background: rgba(35, 173, 229, 0.1); color: var(--bili-blue); border-color: rgba(35, 173, 229, 0.2);">UID: ${data.mid}</span>
                            ${data._status === 'fetching_works' ? `
                                <span class="search-status" style="font-size: 12px; color: var(--bili-blue); display: flex; align-items: center; gap: 4px;">
                                    <span class="pulse-dot" style="background-color: var(--bili-blue);"></span> ⏳ 正在抓取该 UP 主的近期稿件...
                                </span>
                            ` : ''}
                        </div>
                    </div>`;
                } else if (data.bvid) {
                                // 分析视频参数美化
                                detailDiv.innerHTML = `<div class="tool-call-card">
                                    <div id="title-${data.bvid}" class="tool-name" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%;" title="正在深度分析视频内容">正在深度分析视频内容:</div>
                                    <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 8px; position: relative; z-index: 1;">
                                        <div style="display: flex; align-items: center; gap: 12px;">
                                            <span class="search-keyword" style="background: rgba(35, 173, 229, 0.1); color: var(--bili-blue); border-color: rgba(35, 173, 229, 0.2); margin: 0; flex-shrink: 0;">${data.bvid}</span>
                                            <span id="msg-${data.bvid}" style="font-size: 12px; color: var(--bili-pink); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">准备中...</span>
                                        </div>
                                    <div id="tokens-container-${data.bvid}" style="font-size: 12px; color: var(--text-main); font-weight: 600; display: flex; align-items: center; gap: 6px; padding: 4px 8px; background: rgba(0,0,0,0.03); border-radius: 6px; width: fit-content;">
                                        <span class="pulse-dot"></span> <span id="tokens-${data.bvid}">等待响应...</span>
                                    </div>
                                </div>
                                <div id="ghost-${data.bvid}" class="ghost-content"></div>
                            </div>`;
                } else if (data.query) {
                    // Exa 搜索参数美化
                    detailDiv.innerHTML = `<div class="tool-call-card" style="border-left: 3px solid var(--bili-blue); background: rgba(35, 173, 229, 0.03);">
                        <div class="tool-name" style="color: var(--bili-blue);">发起 Exa 全网搜索:</div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-top: 8px;">
                            <span class="search-keyword" style="background: rgba(35, 173, 229, 0.1); color: var(--bili-blue); border-color: rgba(35, 173, 229, 0.2);">${data.query}</span>
                            ${data._status === 'searching' ? `
                                <span class="search-status" style="font-size: 12px; color: var(--bili-blue); display: flex; align-items: center; gap: 4px;">
                                    <span class="pulse-dot" style="background-color: var(--bili-blue);"></span> ⏳ 正在检索全网数据...
                                </span>
                            ` : ''}
                        </div>
                    </div>`;
                } else if (data.summary_of_findings) {
                    // 撰写报告参数美化
                    detailDiv.innerHTML = `<div class="tool-call-card">
                        <div class="tool-name">研究成果概览:</div>
                        <div style="font-size: 13px; color: var(--text-main); line-height: 1.6; background: rgba(251, 114, 153, 0.05); padding: 12px; border-radius: 8px; border-left: 3px solid var(--bili-pink);">
                            ${data.summary_of_findings}
                        </div>
                        <div style="margin-top: 10px; font-size: 12px; color: var(--bili-pink); font-weight: 500; display: flex; align-items: center; gap: 6px;">
                            <span class="pulse-dot"></span> ✍️ 正在将研究成果整理为深度报告，由于内容较多，请耐心等待...
                        </div>
                    </div>`;
                } else if (data.summary) {
                    detailDiv.innerHTML = `<div class="tool-call-card">
                        <div class="tool-name">AI 提取摘要:</div>
                        <div style="font-style: italic; color: var(--text-secondary)">${data.summary.substring(0, 150)}...</div>
                    </div>`;
                } else {
                    detailDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                }
            }
        }
        
        const prevActive = elements.researchTimeline.querySelectorAll('.timeline-item.active');
        prevActive.forEach(node => {
            if (node !== item && (type !== 'thinking' || !node.classList.contains('type-thinking'))) {
                node.classList.remove('active');
                node.classList.add('completed');
            }
        });
        
        elements.researchTimeline.appendChild(item);
        elements.researchTimeline.scrollTop = elements.researchTimeline.scrollHeight;
    }

    async function processStreamAnalysis(url) {
        const response = await fetch('/api/analyze/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                url: url,
                mode: currentMode // 告知后端搜索意图
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '请求失败');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonStr = line.slice(6);
                    let data;
                    try {
                        data = JSON.parse(jsonStr);
                    } catch (e) {
                        console.warn('JSON Parse Error:', e, 'Raw string:', jsonStr);
                        continue;
                    }
                    
                    try {
                        handleStreamData(data);
                    } catch (e) {
                        // Re-throw to be caught by startAnalysis
                        throw e;
                    }
                }
            }
        }
        
        isAnalyzing = false;
        elements.analyzeBtn.disabled = false;
        elements.loadingState.classList.add('hidden');
        elements.resultArea.classList.remove('hidden');
    }

    function handleStreamData(data) {
        if (data.progress) {
            if (data.stage === 'streaming') {
                // For streaming, use the dedicated badge to avoid flickering
                elements.streamingStatus.classList.remove('hidden');
                elements.loadingText.textContent = currentMode === 'article' ? 'AI 正在深度解析专栏...' : 'AI 正在深度分析内容...';
                if (data.tokens_used) {
                    elements.chunkCounter.textContent = Math.floor(data.tokens_used / 10);
                }
                updateProgress(data.progress); // Only update bar
                updateStepper('ai', 'active'); // Ensure AI step is active during streaming
            } else {
                elements.streamingStatus.classList.add('hidden');
                updateProgress(data.progress, data.message);
            }
        }

        // Update metadata and stepper as it arrives
        if (data.type === 'stage') {
            if (data.stage === 'searching') {
                updateStepper('search', 'active');
            } else if (data.stage === 'search_complete') {
                updateStepper('search', 'completed');
                updateStepper('info', 'active');
            } else if (data.stage === 'fetching_info') {
                updateStepper('info', 'active');
            } else if (data.stage === 'info_complete') {
                updateStepper('info', 'completed');
                updateStepper('content', 'active');
                
                if (currentMode === 'article' && data.info) {
                    currentData.videoInfo = data.info;
                    updateVideoCard(data.info);

                    // 关键修复：专栏原文应优先从 info_complete 填充（无需等待 AI/最终 final）
                    // 这样即使 AI Key 无效导致后续流式解析失败，也能正常看到“专栏原文”。
                    if (typeof data.info.content === 'string') {
                        elements.articleOriginalContent.textContent = data.info.content || '无法获取专栏原文';
                        updateMetaValue('metaWordCount', (data.info.content || '').length, '');
                    }
                } else if (currentMode === 'video') {
                    fetchVideoInfo(elements.videoUrl.value).then(res => {
                        if (res && res.owner && res.owner.mid) {
                            loadUpPortrait(res.owner.mid);
                        }
                    });
                }
            } else if (data.stage === 'content_ready') {
                updateStepper('content', 'completed');
                updateStepper('frames', 'active');
                if (currentMode === 'video') {
                    updateMetaValue('metaSubtitle', data.text_source === "字幕" ? '有字幕' : '视频文案');
                } else if (currentMode === 'article') {
                    updateMetaValue('metaWordCount', (data.content || '').length, '');
                }
            } else if (data.stage === 'frames_ready') {
                updateStepper('frames', 'completed');
                updateStepper('ai', 'active');
                if (currentMode === 'video') {
                    updateMetaValue('metaFrames', data.frame_count || (data.has_frames ? '已提取' : '0'), '');
                }
            }
            
            if (data.content) {
                currentData.rawContent = data.content;
                elements.rawSubtitleText.textContent = data.content;
            }
        }

        switch (data.type) {
            case 'stage':
                break;
                
            case 'content_preview':
            case 'complete':
            case 'final':
                if (data.parsed) {
                    currentData.summary = data.parsed.summary || '';
                    currentData.danmaku = data.parsed.danmaku || '';
                    currentData.comments = data.parsed.comments || '';
                    
                    if (currentMode === 'video') {
                        renderMarkdown(elements.summaryContent, currentData.summary || '暂无内容总结');
                        renderMarkdown(elements.danmakuAnalysisResult, currentData.danmaku || '暂无弹幕分析');
                        renderMarkdown(elements.commentsAnalysisResult, currentData.comments || '暂无评论解析');
                    } else if (currentMode === 'article') {
                        renderMarkdown(elements.articleAnalysisContent, currentData.summary || '暂无文章分析');
                    }
                }
                
                if (data.type === 'final' && currentMode === 'article') {
                    elements.articleOriginalContent.textContent = data.content || '无法获取专栏原文';
                    // 再强制更新一次卡片，因为 final 可能带了更全的数据
                    if (data.info) updateVideoCard(data.info);
                }
                
                // If we have danmaku data, generate word cloud
                if (data.type === 'final' && data.danmaku_preview && data.danmaku_preview.length > 0) {
                    currentData.danmakuPreview = data.danmaku_preview;
                    generateWordCloud(data.danmaku_preview);
                }
                if (data.top_comments) {
                    renderTopComments(data.top_comments);
                }
                if (data.full_analysis) {
                    currentData.fullMarkdown = data.full_analysis;
                }
                if (data.tokens_used) {
                    elements.tokenCount.textContent = data.tokens_used;
                }
                
                // Final metadata update
                if (data.type === 'final') {
                    if (currentMode === 'video' && currentData.videoInfo) {
                        updateMetaValue('metaDuration', currentData.videoInfo.duration_str || currentData.videoInfo.duration);
                        if (data.frame_count !== undefined) updateMetaValue('metaFrames', data.frame_count, '');
                        if (data.danmaku_count !== undefined) updateMetaValue('metaDanmaku', data.danmaku_count, '');
                    } else if (currentMode === 'article' && data.info) {
                        updateMetaValue('metaViews', BiliHelpers.formatNumber(data.info.view));
                        updateMetaValue('metaLikes', BiliHelpers.formatNumber(data.info.like));
                        updateMetaValue('metaWordCount', (data.content || '').length, '');
                    }
                }

                if (data.content) {
                    currentData.rawContent = data.content;
                    elements.rawSubtitleText.textContent = data.content;
                }
                if (data.type === 'complete' || data.type === 'final') {
                    BiliHelpers.showToast('分析完成！✨', elements.toast);
                }
                break;
                
            case 'error':
                throw new Error(data.message || data.error || '未知错误');
        }
    }
    
    async function fetchVideoInfo(url) {
        try {
            const res = await fetch('/api/video/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const json = await res.json();
            if (json.success) {
                currentData.videoInfo = json.data;
                updateVideoCard(json.data);
                if (json.related) {
                    renderRelatedVideos(json.related);
                }
                return json.data;
            }
        } catch (e) {
            console.error('Info fetch error', e);
        }
        return null;
    }

    async function loadUpPortrait(mid) {
        elements.upPortraitCard.classList.remove('hidden');
        elements.upPortraitContent.innerHTML = '<div class="loading-dots">正在生成深度画像</div>';
        
        try {
            const res = await fetch('/api/user/portrait', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ uid: mid })
            });
            const json = await res.json();
            if (json.success) {
                elements.upNameDetail.textContent = json.data.info.name;
                elements.upSign.textContent = json.data.info.sign;
                elements.upFace.src = `/api/image-proxy?url=${encodeURIComponent(json.data.info.face)}`;
                elements.upPortraitContent.innerHTML = marked.parse(json.data.portrait);
            }
        } catch (e) {
            elements.upPortraitContent.textContent = '画像分析失败';
        }
    }

    function renderRelatedVideos(videos) {
        if (!videos || videos.length === 0) {
            elements.relatedSection.classList.add('hidden');
            return;
        }

        elements.relatedSection.classList.remove('hidden');
        elements.relatedList.innerHTML = '';

        videos.forEach(video => {
            const card = document.createElement('div');
            card.className = 'related-card';
            card.innerHTML = `
                <div class="related-cover-wrapper">
                    <img class="related-cover" src="/api/image-proxy?url=${encodeURIComponent(video.cover)}" loading="lazy">
                    <span class="related-duration">${video.duration_str}</span>
                </div>
                <div class="related-content">
                    <div class="related-title" title="${video.title}">${video.title}</div>
                    <div class="related-info">
                        <span class="related-author">${video.author}</span>
                        <span class="related-views">${BiliHelpers.formatNumber(video.view)} 播放</span>
                    </div>
                    <div class="related-actions" style="display: flex; gap: 8px; margin-top: 8px;">
                        <button class="btn-mini btn-primary-mini" onclick="event.stopPropagation(); window.analyzeBvid('${video.bvid}')">分析</button>
                        <a href="https://www.bilibili.com/video/${video.bvid}" target="_blank" class="btn-mini btn-outline-mini" onclick="event.stopPropagation()">观看</a>
                    </div>
                </div>
            `;
            card.onclick = () => {
                elements.videoUrl.value = video.bvid;
                startAnalysis();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            };
            elements.relatedList.appendChild(card);
        });
    }

    // Expose analyze function globally for inline onclick
    window.analyzeBvid = (bvid) => {
        elements.videoUrl.value = bvid;
        startAnalysis();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // --- Chat Functions ---

    async function sendMessage() {
        if (isAnalyzing) {
            BiliHelpers.showToast('AI 正在分析视频，请在分析完成后再发起提问', elements.toast);
            return;
        }
        if (isChatting) return;
        const text = elements.chatInput.value.trim();
        if (!text) return;

        if (!currentData.fullMarkdown) {
            BiliHelpers.showToast('请先完成视频分析', elements.toast);
            return;
        }

        // Add user message
        addMessage('user', text);
        elements.chatInput.value = '';
        elements.chatInput.style.height = 'auto';

        // Add assistant message placeholder
        const assistantMsgDiv = addMessage('assistant', '');
        const contentDiv = assistantMsgDiv.querySelector('.message-content');
        contentDiv.classList.add('loading-dots');

        isChatting = true;
        elements.sendMsgBtn.disabled = true;

        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: text,
                    context: currentData.fullMarkdown,
                    video_info: currentData.videoInfo,
                    history: chatHistory
                })
            });

            if (!response.ok) throw new Error('网络请求失败');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';
            contentDiv.classList.remove('loading-dots');

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        if (data.type === 'content') {
                            fullResponse += data.content;
                            contentDiv.innerHTML = marked.parse(fullResponse);
                            elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
                        } else if (data.type === 'error') {
                            throw new Error(data.error);
                        }
                    }
                }
            }

            chatHistory.push({ role: 'user', content: text });
            chatHistory.push({ role: 'assistant', content: fullResponse });
            // Keep history short to save tokens
            if (chatHistory.length > 10) chatHistory = chatHistory.slice(-10);

        } catch (error) {
            console.error('Chat error:', error);
            contentDiv.innerHTML = `<span style="color: var(--bili-pink)">错误: ${error.message}</span>`;
        } finally {
            isChatting = false;
            elements.sendMsgBtn.disabled = false;
        }
    }

    function addMessage(role, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        msgDiv.innerHTML = `
            <div class="message-content markdown-body">
                ${text ? marked.parse(text) : ''}
            </div>
        `;
        elements.chatMessages.appendChild(msgDiv);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        return msgDiv;
    }

    function openLoginModal() {
        elements.loginModal.classList.remove('hidden');
        startLogin();
    }

    function closeLoginModal() {
        elements.loginModal.classList.add('hidden');
        if (loginPollInterval) {
            clearInterval(loginPollInterval);
            loginPollInterval = null;
        }
    }

    // 已迁移到 BiliAPI.loginStart，保留包装函数以兼容调用
    async function startLogin() {
        if (loginPollInterval) clearInterval(loginPollInterval);
        elements.loginStatus.textContent = '正在生成二维码...';
        elements.qrcode.innerHTML = '';

        try {
            const data = await BiliAPI.loginStart();

            if (data) {
                const qrCodeData = data.qr_code;
                const sessionId = data.session_id;
                const img = document.createElement('img');
                img.src = qrCodeData;
                elements.qrcode.appendChild(img);
                elements.loginStatus.textContent = '请使用B站App扫码登录';
                loginPollInterval = setInterval(() => pollLoginStatus(sessionId), 3000);
            } else {
                elements.loginStatus.textContent = '生成二维码失败，请重试';
            }
        } catch (error) {
            elements.loginStatus.textContent = '网络错误，请重试';
        }
    }

    // 已迁移到 BiliAPI.loginStatus，保留包装函数以兼容调用
    async function pollLoginStatus(sessionId) {
        try {
            const data = await BiliAPI.loginStatus(sessionId);

            if (data) {
                const status = data.status;
                if (status === 'success') {
                    clearInterval(loginPollInterval);
                    loginPollInterval = null;
                    BiliHelpers.showToast('登录成功！🎉', elements.toast);
                    closeLoginModal();
                    checkLoginState();
                } else if (status === 'expired') {
                    clearInterval(loginPollInterval);
                    loginPollInterval = null;
                    elements.loginStatus.textContent = '二维码已过期，请重新打开';
                }
            }
        } catch (error) {
            console.error('Poll status error:', error);
        }
    }

    // 已迁移到 BiliAPI.loginCheck，保留包装函数以兼容调用
    async function checkLoginState() {
        // --- 尝试从本地缓存加载用户信息 (实现瞬时加载) ---
        const cachedUser = localStorage.getItem('bili_user');
        if (cachedUser) {
            try {
                renderUserBadge(JSON.parse(cachedUser));
            } catch (e) {}
        }

        try {
            const user = await BiliAPI.loginCheck();

            if (user) {
                // 更新缓存
                localStorage.setItem('bili_user', JSON.stringify(user));
                renderUserBadge(user);
            } else {
                localStorage.removeItem('bili_user');
                elements.loginBtn.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                    登录B站
                `;
                elements.loginBtn.classList.remove('logged-in');
                elements.loginBtn.onclick = openLoginModal;

                // Show hint if NOT logged in
                elements.loginHint.classList.remove('hidden');
                elements.hintLoginBtn.onclick = (e) => {
                    e.preventDefault();
                    openLoginModal();
                };
            }
        } catch (error) {
            console.error('Check login error:', error);
        }
    }

    function renderUserBadge(user) {
        const faceUrl = user.face ? `/api/image-proxy?url=${encodeURIComponent(user.face)}` : '';
        
        elements.loginBtn.innerHTML = `
            <div class="user-badge-container">
                <div class="user-face-circle" id="analyzeMeBtn" title="点击分析我的UP主画像">
                    ${user.face ? `<img src="${faceUrl}">` : `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>`}
                </div>
                <span class="user-name-text" id="logoutUserBtn" title="点击退出登录">${user.name || '已登录'}</span>
            </div>
        `;

        elements.loginBtn.classList.add('logged-in');
        elements.loginBtn.onclick = null; 

        // 绑定“分析我”逻辑
        const analyzeMeBtn = document.getElementById('analyzeMeBtn');
        if (analyzeMeBtn) {
            analyzeMeBtn.onclick = (e) => {
                e.stopPropagation();
                elements.videoUrl.value = user.user_id;
                switchMode('user');
                startAnalysis();
            };
        }

        // 绑定“退出”逻辑
        const logoutUserBtn = document.getElementById('logoutUserBtn');
        if (logoutUserBtn) {
            logoutUserBtn.onclick = (e) => {
                e.stopPropagation();
                if(confirm('确定要退出登录吗？')) {
                    logout();
                }
            };
        }
        
        // Hide hint if logged in
        elements.loginHint.classList.add('hidden');
    }

    // 已迁移到 BiliAPI.logout，保留包装函数以兼容调用
    async function logout() {
        try {
            await BiliAPI.logout();
            BiliHelpers.showToast('已退出登录', elements.toast);
            window.location.assign('/');
        } catch (error) {
            BiliHelpers.showToast('退出失败', elements.toast);
        }
    }

    // 已迁移到 ModeUI，保留包装函数以兼容调用
    function switchMode(mode) {
        currentMode = ModeUI.switchMode(mode, {
            elements,
            updateSidebarUI: () => updateSidebarUI(),
            showToast: (msg) => BiliHelpers.showToast(msg, elements.toast)
        });

        // 切换模式时应刷新侧边栏入口（否则可能保留上一模式的隐藏/显示状态）
        updateSidebarUI();
    }

    // 已迁移到 TabUI，保留包装函数以兼容调用
    function updateSidebarUI() {
        TabUI.updateSidebarUI({
            elements,
            currentMode,
            switchTab: (tabName) => switchTab(tabName)
        });
    }

    function updateVideoCard(info) {
        elements.videoTitle.textContent = info.title;
        elements.upName.textContent = info.author;
        elements.viewCount.textContent = BiliHelpers.formatNumber(info.view);
        
        // 适配视频/专栏不同的点赞/弹幕字段
        elements.danmakuCount.textContent = (info.danmaku !== undefined) ? BiliHelpers.formatNumber(info.danmaku) : '-';
        elements.likeCount.textContent = (info.like !== undefined) ? BiliHelpers.formatNumber(info.like) : (info.stats ? BiliHelpers.formatNumber(info.stats.like) : '-');
        elements.commentCount.textContent = (info.reply !== undefined) ? BiliHelpers.formatNumber(info.reply) : (info.stats ? BiliHelpers.formatNumber(info.stats.reply) : '-');
        
        elements.videoDuration.textContent = info.duration_str || info.duration || (currentMode === 'article' ? '专栏文章' : '');
        
        // 封面图适配：pic, cover, banner_url, face
        const coverUrl = info.cover || info.banner_url || info.pic || info.face || '';
        if (coverUrl) {
            elements.videoCover.src = `/api/image-proxy?url=${encodeURIComponent(coverUrl)}`;
        }
        
        if (info.bvid) {
            elements.watchBiliBtn.href = `https://www.bilibili.com/video/${info.bvid}`;
        } else if (currentMode === 'article') {
            // 如果是 cvid
            const cvidMatch = elements.videoUrl.value.match(/cv(\d+)/);
            const opusMatch = elements.videoUrl.value.match(/opus\/(\d+)/);
            if (cvidMatch) elements.watchBiliBtn.href = `https://www.bilibili.com/read/cv${cvidMatch[1]}`;
            else if (opusMatch) elements.watchBiliBtn.href = `https://www.bilibili.com/opus/${opusMatch[1]}`;
        }
    }

    window.goHome = function(targetMode = 'research') {
        if (isAnalyzing) {
            if (!confirm('分析正在进行中，现在返回主页将无法看到实时进度，确定吗？')) {
                return false;
            }
        }
        elements.resultArea.classList.add('hidden');
        elements.loadingState.classList.add('hidden');
        elements.welcomeSection.classList.remove('hidden');
        elements.homeBtn.classList.add('hidden');

        // --- 核心修复：还原平滑过渡相关的 CSS 类与元素显示 ---
        elements.welcomeSection.classList.remove('fade-out-down');
        elements.resultArea.classList.remove('fade-in-up');
        const videoCard = document.querySelector('.video-info-card');
        if (videoCard) videoCard.classList.remove('hidden');

        // 确保所有聊天面板都被隐藏
        if (elements.chatContent) elements.chatContent.classList.remove('active');

        // 清空输入框以便下次使用
        elements.videoUrl.value = '';
        manualModeLock = false;

        // 确保热门视频始终存在
        if (elements.initRelatedList && elements.initRelatedList.children.length === 0) {
            fetchPopularVideos();
        }

        // 重置模式
        switchMode(targetMode);
        return true;
    };

    // 已迁移到 TabUI，保留包装函数以兼容调用
    function switchTab(tabName) {
        TabUI.switchTab(tabName, {
            elements,
            currentMode,
            isAnalyzing,
            currentData,
            showToast: (msg) => BiliHelpers.showToast(msg, elements.toast),
            generateWordCloud: (data) => generateWordCloud ? generateWordCloud(data) : null
        });
    }

    // --- 历史研究报告逻辑 ---
    window.showResearchHistory = async function() {
        elements.historyModal.classList.remove('hidden');
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '<div class="loading">正在加载历史报告...</div>';
        
        try {
            const response = await fetch('/api/research/history');
            const data = await response.json();
            
            if (data.success && data.data.length > 0) {
                historyList.innerHTML = data.data.map(item => `
                    <div class="history-item">
                        <div class="history-item-info" onclick="loadReport('${item.id}.md')">
                            <span class="topic">${item.topic}</span>
                            <span class="time">${item.created_at}</span>
                        </div>
                        <div class="history-actions">
                            ${item.has_pdf ? `<button class="btn-icon-small" title="下载 PDF" onclick="downloadFile('${item.id}', 'pdf')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg></button>` : ''}
                            <button class="btn-icon-small" title="下载 Markdown" onclick="downloadFile('${item.id}', 'md')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg></button>
                        </div>
                    </div>
                `).join('');
            } else {
                historyList.innerHTML = '<div class="empty-state">暂无历史研究报告</div>';
            }
        } catch (e) {
            historyList.innerHTML = '<div class="error">加载失败，请稍后重试</div>';
        }
    };

    window.downloadFile = function(fileId, format) {
        window.open(`/api/research/download/${fileId}/${format}`);
    };

    window.closeHistoryModal = function() {
        elements.historyModal.classList.add('hidden');
    };

    window.loadReport = async function(filename) {
        closeHistoryModal();
        try {
            // 获取文件 ID 用于后续可能的 PDF 下载
            const fileId = filename.replace('.md', '');
            
            const response = await fetch(`/api/research/report/${filename}`);
            const data = await response.json();
            
            if (data.success) {
                // 模拟一个切换到结果区域的状态
                elements.loadingState.classList.add('hidden');
                elements.resultArea.classList.remove('hidden');
                currentMode = 'research';
                updateSidebarUI();
                
                // 更新 UI
                elements.videoTitle.textContent = `课题研究：${data.data.filename.split('_').slice(2).join('_').replace('.md', '')}`;
                elements.upName.textContent = 'History Research Report';
                
                renderMarkdown(elements.researchReportContent, data.data.content);
                currentData.fullMarkdown = data.data.content;
                
                // 设置当前文件 ID 用于顶部的 PDF 下载
                currentData.researchFileId = fileId;
                elements.downloadPdfBtn.classList.remove('hidden');
                
                switchTab('research_report');
                BiliHelpers.showToast('已加载历史报告', elements.toast);
            } else {
                BiliHelpers.showToast('加载报告失败: ' + data.error, elements.toast);
            }
        } catch (e) {
            BiliHelpers.showToast('请求报告失败', elements.toast);
        }
    };

    // 绑定 PDF 下载按钮
    elements.downloadPdfBtn.onclick = () => {
        if (currentData.researchFileId) {
            downloadFile(currentData.researchFileId, 'pdf');
        } else {
            // 如果是刚生成的，尝试根据当前状态寻找最新文件
            BiliHelpers.showToast('正在为您从历史中寻找刚生成的 PDF...', elements.toast);
            showResearchHistory();
        }
    };

    // 已迁移到 ProgressUI，保留包装函数以兼容调用
    function initStepper(mode) {
        ProgressUI.initStepper(elements, mode);
    }

    function resetProgress() {
        ProgressUI.resetProgress(elements);
    }

    function updateProgress(percent, text) {
        ProgressUI.updateProgress(elements, percent, text);
    }

    function updateStepper(stepId, status) {
        ProgressUI.updateStepper(stepId, status);
    }

    function resetStepper() {
        ProgressUI.resetStepper();
    }
    
    // 已迁移到 BiliHelpers.renderMarkdown，保留包装函数以兼容调用
    function renderMarkdown(element, text) {
        BiliHelpers.renderMarkdown(element, text);
    }

    function renderTopComments(comments) {
        if (!comments || comments.length === 0) {
            elements.topCommentsList.style.display = 'none';
            return;
        }

        elements.topCommentsList.style.display = 'block';
        elements.topCommentsList.innerHTML = `
            <h3 class="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                </svg>
                高赞精彩评论
            </h3>
        `;

        comments.forEach(comment => {
            const card = document.createElement('div');
            card.className = 'comment-card';
            
            // 使用代理获取头像，如果失败使用默认图
            const avatarUrl = `/api/image-proxy?url=${encodeURIComponent(comment.avatar)}`;
            
            card.innerHTML = `
                <img class="comment-avatar" src="${avatarUrl}" onerror="this.src='https://static.hdslb.com/images/akari.jpg'">
                <div class="comment-main">
                    <div class="comment-header">
                        <span class="comment-user">${comment.username}</span>
                        <span class="comment-level">LV${comment.user_level}</span>
                    </div>
                    <div class="comment-text">${comment.message}</div>
                    <div class="comment-footer">
                        <span class="comment-stat" title="点赞数">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                            </svg>
                            ${BiliHelpers.formatNumber(comment.like)}
                        </span>
                        <span class="comment-stat" title="回复数">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                            </svg>
                            ${BiliHelpers.formatNumber(comment.reply_count)}
                        </span>
                    </div>
                </div>
            `;
            elements.topCommentsList.appendChild(card);
        });
    }

    function generateWordCloud(danmakus) {
        if (!danmakus || danmakus.length === 0) return;
        
        elements.danmakuWordCloudContainer.classList.remove('hidden');
        
        // Simple word frequency counter
        const wordMap = {};
        // Common stop words or useless tokens
        const stopWords = new Set(['的', '了', '是', '我', '你', '他', '她', '它', '们', '这', '那', '在', '也', '都', '不', '有', '人', '就', '要', '而', '及', '并', '等', '或', '和', '与', '为', '以', '于', '啊', '哈', '呀', '嘿', '哦', '吧']);
        
        danmakus.forEach(text => {
            // Remove punctuation
            const cleanText = text.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()？。，！；：]/g, '');
            
            // For Chinese without spaces, we can't just split by space.
            // A better simple approach: use words of length 2-4
            for (let i = 0; i < cleanText.length; i++) {
                // Try 2-char and 3-char "words"
                for (let len = 2; i + len <= cleanText.length && len <= 3; len++) {
                    const word = cleanText.substring(i, i + len);
                    if (!stopWords.has(word)) {
                        wordMap[word] = (wordMap[word] || 0) + 1;
                    }
                }
            }
            
            // Also split by space for English/spaced content
            text.split(/\s+/).forEach(w => {
                if (w.length > 1 && !stopWords.has(w)) {
                    wordMap[w] = (wordMap[w] || 0) + 5; // Give higher weight to actual spaced words
                }
            });
        });
        
        // Convert to wordcloud2 format: [ ['word', count], ... ]
        let list = Object.entries(wordMap)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 60); // Top 60 words
            
        if (list.length === 0) {
            elements.danmakuWordCloudContainer.classList.add('hidden');
            return;
        }

        // Adjust canvas size - ensure we have a fallback if element is hidden
        const container = elements.danmakuCanvas.parentElement;
        const width = container.offsetWidth || 800;
        elements.danmakuCanvas.width = width;
        elements.danmakuCanvas.height = 300;

        const isDark = document.body.classList.contains('dark-theme');
        
        // Bilibili themed colors
    const colors = isDark 
        ? ['#FB7299', '#23ADE5', '#7B68EE', '#3EBAD5', '#FFFFFF', '#9499A0']
        : ['#FB7299', '#23ADE5', '#7B68EE', '#1E96C8', '#18191C', '#9499A0'];

        try {
            WordCloud(elements.danmakuCanvas, {
                list: list,
                gridSize: Math.round(12 * width / 1024),
                weightFactor: function (size) {
                    return (size * 35) / (list[0][1] || 1) + 8;
                },
                fontFamily: 'Noto Sans SC, sans-serif',
                color: function() {
                    return colors[Math.floor(Math.random() * colors.length)];
                },
                rotateRatio: 0.3,
                rotationSteps: 2,
                backgroundColor: 'transparent',
                shuffle: true,
                drawOutOfBound: false // Prevent words from disappearing
            });
        } catch (e) {
            console.error('WordCloud render error:', e);
        }
    }

    async function performSearch(keyword) {
        elements.analyzeBtn.disabled = true;
        const btnText = elements.analyzeBtn.lastChild;
        const originalText = btnText.textContent;
        btnText.textContent = ' 搜索中...';

        try {
            const res = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword, mode: currentMode })
            });
            const json = await res.json();
            if (json.success && json.data && json.data.length > 0) {
                renderSearchResults(json.data);
            } else {
                BiliHelpers.showToast('未找到相关内容，请尝试更精确的关键词', elements.toast);
            }
        } catch (e) {
            BiliHelpers.showToast('搜索失败，请检查网络', elements.toast);
        } finally {
            elements.analyzeBtn.disabled = false;
            btnText.textContent = originalText;
        }
    }

    function renderSearchResults(results) {
        elements.resultsList.innerHTML = '';
        elements.resultsCount.textContent = `找到 ${results.length} 条相关结果`;
        elements.searchResultsPanel.classList.remove('hidden');

        results.forEach(item => {
            const div = document.createElement('div');
            div.className = 'result-item';
            
            let idValue = '';
            let metaText = '';
            let displayTitle = item.title || item.name; // 优先使用 title，用户模式下回退到 name
            let thumbClass = 'result-thumb';

            if (currentMode === 'video') {
                idValue = item.bvid;
                metaText = `UP主: ${item.author} | 播放: ${BiliHelpers.formatNumber(item.play)}`;
            } else if (currentMode === 'user') {
                idValue = item.mid;
                displayTitle = item.name; // 用户模式强制使用 name
                metaText = `等级: L${item.level} | 签名: ${item.sign || '无'}`;
                thumbClass += ' user-face';
            } else if (currentMode === 'article') {
                idValue = 'cv' + item.cvid;
                metaText = `作者: ${item.author}`;
            }

            div.innerHTML = `
                <img class="${thumbClass}" src="/api/image-proxy?url=${encodeURIComponent(item.pic || item.face)}">
                <div class="result-info">
                    <div class="result-title">${displayTitle}</div>
                    <div class="result-meta">${metaText}</div>
                </div>
            `;

            div.onclick = () => {
                elements.videoUrl.value = idValue;
                elements.searchResultsPanel.classList.add('hidden');
                startAnalysis();
            };
            elements.resultsList.appendChild(div);
        });
    }

    // formatNumber 和 showToast 已迁移到 helpers.js (BiliHelpers)

    function openSettings() {
        elements.settingsDrawer.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    }

    function closeSettings() {
        elements.settingsDrawer.classList.add('hidden');
        document.body.style.overflow = ''; // Restore scrolling
    }

    // 已迁移到 BiliHelpers.copyToClipboard，保留包装函数以兼容事件绑定
    function copyContent() {
        const activeTab = document.querySelector('.nav-btn.active').dataset.tab;
        let content = '';
        if (activeTab === 'summary') content = currentData.summary;
        else if (activeTab === 'danmaku') content = currentData.danmaku;
        else if (activeTab === 'comments') content = currentData.comments;
        else if (activeTab === 'subtitle') content = currentData.rawContent;

        // 使用 BiliHelpers.copyToClipboard
        BiliHelpers.copyToClipboard(content, (msg) => BiliHelpers.showToast(msg, elements.toast));
    }

    // 已迁移到 BiliHelpers.downloadMarkdown，保留包装函数以兼容事件绑定
    function downloadMarkdown() {
        const content = currentData.fullMarkdown;
        const filename = 'bilibili_analysis_' + new Date().getTime() + '.md';
        BiliHelpers.downloadMarkdown(content, filename);
    }

    // 初始化默认模式
    switchMode('research');
});