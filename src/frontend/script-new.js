/**
 * script.js - 主程序逻辑（重构版）
 *
 * 【模块职责】
 * 应用的主要业务逻辑，包括：
 * - DOM 元素管理
 * - 事件监听
 * - 状态管理
 * - 业务流程协调
 *
 * 【重构说明】
 * - 创建日期：2025-12-24
 * - 使用模块：helpers.js, bilibili-api.js, video-api.js, research-api.js
 * - 使用UI模块：progress.js, tabs.js, modes.js
 * - 删除了重复的工具函数、API函数、UI函数
 * - 拆分了大型流式处理函数
 *
 * @author 幽浮喵 (mumu_xsy)
 * @version 2.0.0 (模块化重构版)
 */

document.addEventListener('DOMContentLoaded', () => {
    // =========================================================================
    // DOM Elements
    // =========================================================================
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
        
        // Smart UP
        smartUpChatContent: document.getElementById('smartUpChatContent'),
        smartUpMessages: document.getElementById('smartUpMessages'),
        smartUpProgress: document.getElementById('smartUpProgress'),
        smartUpInput: document.getElementById('smartUpInput'),
        smartUpSendBtn: document.getElementById('smartUpSendBtn'),

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

    // =========================================================================
    // State
    // =========================================================================
    let currentMode = 'smart_up';
    let manualModeLock = false;
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
    let smartUpHistory = [];
    let popularVideosCache = null;
    let loginPollInterval = null;

    // 提示：继续在下一个部分添加事件监听和业务逻辑...
    // 由于文件太大，会分多次创建
    
    console.log('✨ Bilibili Analysis Helper v2.0 (模块化重构版) 已启动');
    console.log('📦 使用模块: helpers.js, bilibili-api.js, video-api.js, research-api.js');
    console.log('📦 使用UI模块: progress.js, tabs.js, modes.js');
});
