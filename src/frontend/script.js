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
        metaDuration: document.getElementById('metaDuration'),
        metaSubtitle: document.getElementById('metaSubtitle'),
        metaFrames: document.getElementById('metaFrames'),
        metaComments: document.getElementById('metaComments'),
        metaDanmaku: document.getElementById('metaDanmaku'),
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

        // Settings Drawer
        settingsBtn: document.getElementById('settingsBtn'),
        settingsDrawer: document.getElementById('settingsDrawer'),
        closeDrawerBtn: document.querySelector('.close-drawer'),
        drawerOverlay: document.querySelector('.drawer-overlay'),
        apiBaseInput: document.getElementById('apiBaseInput'),
        apiKeyInput: document.getElementById('apiKeyInput'),
        modelInput: document.getElementById('modelInput'),
        qaModelInput: document.getElementById('qaModelInput'),
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
        upPortraitContent: document.getElementById('upPortraitContent')
    };

    // State
    let currentData = {
        summary: '',
        danmaku: '',
        comments: '',
        rawContent: '',
        fullMarkdown: '',
        videoInfo: null,
        danmakuPreview: []
    };
    let isAnalyzing = false;
    let isChatting = false;
    let chatHistory = [];
    let loginPollInterval = null;

    // --- Event Listeners ---

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
            logoClicks++;
            if (logoClicks === 5) {
                showToast('🎉 你发现了隐藏彩蛋！感谢支持 BiliBili Summarize！');
                logoArea.style.animation = 'tada 1s';
                setTimeout(() => logoArea.style.animation = '', 1000);
                logoClicks = 0;
            }
        });
    }

    // Initial load
    initApp();

    async function initApp() {
        await checkLoginState();
        await fetchSettings();
        fetchPopularVideos();
        // Check local storage for dark mode
        const isDark = localStorage.getItem('darkMode') === 'true';
        if (isDark) {
            elements.darkModeToggle.checked = true;
            toggleDarkMode(true);
        }
    }

    async function fetchPopularVideos() {
        try {
            const response = await fetch('/api/video/popular');
            const result = await response.json();
            if (result.success) {
                renderInitRecommendations(result.data);
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
        if (!videos || !elements.initRelatedList) return;
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
                        <span class="related-views">${formatNumber(video.view)} 播放</span>
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

    async function fetchSettings() {
        try {
            const response = await fetch('/api/settings');
            const result = await response.json();
            if (result.success) {
                const data = result.data;
                elements.apiBaseInput.value = data.openai_api_base || '';
                elements.apiKeyInput.value = data.openai_api_key || '';
                // Change input type to text so it's not hidden
                elements.apiKeyInput.type = 'text';
                elements.modelInput.value = data.model || '';
                elements.qaModelInput.value = data.qa_model || '';
                
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

    async function saveSettings() {
        const data = {
            openai_api_base: elements.apiBaseInput.value.trim(),
            openai_api_key: elements.apiKeyInput.value.trim(),
            model: elements.modelInput.value.trim(),
            qa_model: elements.qaModelInput.value.trim(),
            dark_mode: elements.darkModeToggle.checked
        };

        try {
            elements.saveSettingsBtn.disabled = true;
            elements.saveSettingsBtn.textContent = '保存中...';
            
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (result.success) {
                showToast('设置已保存！');
                closeSettings();
            } else {
                showToast('保存失败: ' + result.error);
            }
        } catch (error) {
            showToast('保存时发生错误');
        } finally {
            elements.saveSettingsBtn.disabled = false;
            elements.saveSettingsBtn.textContent = '保存设置';
        }
    }

    function toggleDarkMode(isDark) {
        if (isDark) {
            document.body.classList.add('dark-theme');
            localStorage.setItem('darkMode', 'true');
        } else {
            document.body.classList.remove('dark-theme');
            localStorage.setItem('darkMode', 'false');
        }
    }

    function resetMeta() {
        elements.tokenCount.textContent = '0';
        elements.metaDuration.textContent = '--:--';
        elements.metaSubtitle.textContent = '检测中...';
        elements.metaFrames.textContent = '0 帧';
        elements.metaComments.textContent = '0 评';
        elements.metaDanmaku.textContent = '0 弹';
    }

    async function startAnalysis() {
        if (isAnalyzing) return;
        
        const url = elements.videoUrl.value.trim();
        if (!url) {
            showToast('请输入B站视频链接');
            return;
        }

        // Reset UI
        isAnalyzing = true;
        elements.analyzeBtn.disabled = true;
        elements.welcomeSection.classList.add('hidden');
        elements.loadingState.classList.remove('hidden');
        elements.resultArea.classList.add('hidden');
        resetProgress();
        resetMeta();
        resetStepper();
        
        // Reset Data
        currentData = { summary: '', danmaku: '', comments: '', rawContent: '', fullMarkdown: '', videoInfo: null, danmakuPreview: [] };
        chatHistory = [];
        elements.chatMessages.innerHTML = `
            <div class="message assistant">
                <div class="message-content">
                    你好！我是你的视频助手。我已经阅读了视频分析报告，你可以问我关于视频内容的任何问题。
                </div>
            </div>
        `;
        elements.summaryContent.innerHTML = '<div class="empty-state"><p>正在生成分析...</p></div>';
        elements.danmakuWordCloudContainer.classList.add('hidden');
        elements.danmakuAnalysisResult.innerHTML = '<div class="empty-state"><p>正在分析弹幕...</p></div>';
        elements.topCommentsList.innerHTML = '';
        elements.commentsAnalysisResult.innerHTML = '<div class="empty-state"><p>正在分析评论...</p></div>';
        elements.rawSubtitleText.textContent = '获取中...';
        elements.upPortraitCard.classList.add('hidden');
        elements.upPortraitContent.innerHTML = '';

        try {
            await processStreamAnalysis(url);
        } catch (error) {
            console.error('Analysis failed:', error);
            showToast('分析失败: ' + error.message);
            isAnalyzing = false;
            elements.analyzeBtn.disabled = false;
            elements.loadingState.classList.add('hidden');
        }
    }

    async function processStreamAnalysis(url) {
        const response = await fetch('/api/analyze/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
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
                elements.loadingText.textContent = 'AI 正在深度分析内容...';
                if (data.tokens_used) {
                    elements.chunkCounter.textContent = Math.floor(data.tokens_used / 10);
                }
                updateProgress(data.progress); // Only update bar
            } else {
                elements.streamingStatus.classList.add('hidden');
                updateProgress(data.progress, data.message);
            }
        }

        // Update metadata and stepper as it arrives
        if (data.type === 'stage') {
            if (data.stage === 'fetching_info') {
                updateStepper('info', 'active');
            } else if (data.stage === 'info_complete') {
                updateStepper('info', 'completed');
                updateStepper('content', 'active');
                fetchVideoInfo(elements.videoUrl.value).then(res => {
                    if (res && res.owner && res.owner.mid) {
                        loadUpPortrait(res.owner.mid);
                    }
                });
            } else if (data.stage === 'content_ready') {
                updateStepper('content', 'completed');
                updateStepper('frames', 'active');
                elements.metaSubtitle.textContent = data.text_source === "字幕" ? '有字幕' : '视频文案';
            } else if (data.stage === 'frames_ready') {
                updateStepper('frames', 'completed');
                updateStepper('ai', 'active');
                elements.metaFrames.textContent = `${data.frame_count || (data.has_frames ? '已提取' : '0')} 帧`;
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
                    renderMarkdown(elements.summaryContent, currentData.summary || '暂无内容总结');
                    renderMarkdown(elements.danmakuAnalysisResult, currentData.danmaku || '暂无弹幕分析');
                    renderMarkdown(elements.commentsAnalysisResult, currentData.comments || '暂无评论解析');
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
                    if (currentData.videoInfo) {
                        elements.metaDuration.textContent = currentData.videoInfo.duration_str || currentData.videoInfo.duration;
                    }
                    // Extract counts from data if available
                    if (data.frame_count !== undefined) elements.metaFrames.textContent = `${data.frame_count} 帧`;
                    if (data.comments_count !== undefined) elements.metaComments.textContent = `${data.comments_count} 评`;
                    if (data.danmaku_count !== undefined) elements.metaDanmaku.textContent = `${data.danmaku_count} 弹`;
                }

                if (data.content) {
                    currentData.rawContent = data.content;
                    elements.rawSubtitleText.textContent = data.content;
                }
                if (data.type === 'complete' || data.type === 'final') {
                    showToast('分析完成！✨');
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
                        <span class="related-views">${formatNumber(video.view)} 播放</span>
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
        if (isChatting) return;
        const text = elements.chatInput.value.trim();
        if (!text) return;

        if (!currentData.fullMarkdown) {
            showToast('请先完成视频分析');
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

    async function startLogin() {
        if (loginPollInterval) clearInterval(loginPollInterval);
        elements.loginStatus.textContent = '正在生成二维码...';
        elements.qrcode.innerHTML = '';

        try {
            const response = await fetch('/api/bilibili/login/start', { method: 'POST' });
            const result = await response.json();

            if (result.success) {
                const qrCodeData = result.data.qr_code;
                const sessionId = result.data.session_id;
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

    async function pollLoginStatus(sessionId) {
        try {
            const response = await fetch('/api/bilibili/login/status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            const result = await response.json();

            if (result.success) {
                const status = result.data.status;
                if (status === 'success') {
                    clearInterval(loginPollInterval);
                    loginPollInterval = null;
                    showToast('登录成功！🎉');
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

    async function checkLoginState() {
        try {
            const response = await fetch('/api/bilibili/login/check');
            const result = await response.json();

            if (result.success && result.data.is_logged_in) {
                const userId = result.data.user_id || '';
                elements.loginBtn.innerHTML = `
                    <div class="user-avatar-placeholder">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                    </div>
                    <span>UID: ${userId}</span>
                `;
                elements.loginBtn.classList.add('logged-in');
                elements.loginBtn.onclick = () => {
                    if(confirm('确定要退出登录吗？')) {
                        logout();
                    }
                };
                // Hide hint if logged in
                elements.loginHint.classList.add('hidden');
            } else {
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

    async function logout() {
        try {
            await fetch('/api/bilibili/login/logout', { method: 'POST' });
            showToast('已退出登录');
            window.location.assign('/');
        } catch (error) {
            showToast('退出失败');
        }
    }

    function updateVideoCard(info) {
        elements.videoTitle.textContent = info.title;
        elements.upName.textContent = info.author;
        elements.viewCount.textContent = formatNumber(info.view);
        elements.danmakuCount.textContent = formatNumber(info.danmaku);
        elements.likeCount.textContent = formatNumber(info.like);
        elements.commentCount.textContent = formatNumber(info.reply);
        elements.videoDuration.textContent = info.duration_str || info.duration;
        elements.videoCover.src = `/api/image-proxy?url=${encodeURIComponent(info.cover)}`;
        elements.watchBiliBtn.href = `https://www.bilibili.com/video/${info.bvid}`;
    }

    function switchTab(tabName) {
        elements.navBtns.forEach(btn => {
            if (btn.dataset.tab === tabName) btn.classList.add('active');
            else btn.classList.remove('active');
        });
        elements.tabContents.forEach(pane => {
            pane.classList.remove('active');
        });
        if (tabName === 'summary') elements.summaryContent.classList.add('active');
        else if (tabName === 'danmaku') {
            elements.danmakuContent.classList.add('active');
            // Re-render word cloud after a short delay to ensure DOM is visible
            if (currentData.danmakuPreview && currentData.danmakuPreview.length > 0) {
                setTimeout(() => generateWordCloud(currentData.danmakuPreview), 50);
            }
        }
        else if (tabName === 'comments') elements.commentsContent.classList.add('active');
        else if (tabName === 'subtitle') elements.subtitleContent.classList.add('active');
        else if (tabName === 'chat') {
            elements.chatContent.classList.add('active');
            elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        }
    }

    function resetProgress() {
        elements.progressBar.style.width = '0%';
        elements.loadingText.textContent = '准备就绪...';
        elements.streamingStatus.classList.add('hidden');
        elements.chunkCounter.textContent = '0';
        elements.danmakuWordCloudContainer.classList.add('hidden');
    }

    function updateProgress(percent, text) {
        elements.progressBar.style.width = percent + '%';
        if (text) elements.loadingText.textContent = text;
    }

    function updateStepper(stepId, status) {
        const step = document.getElementById(`step-${stepId}`);
        if (!step) return;

        if (status === 'active') {
            // Remove active from others
            document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
            step.classList.add('active');
            step.classList.remove('completed');
        } else if (status === 'completed') {
            step.classList.add('completed');
            step.classList.remove('active');
        }
    }

    function resetStepper() {
        document.querySelectorAll('.step').forEach(s => {
            s.className = 'step';
        });
    }
    
    function renderMarkdown(element, text) {
        element.innerHTML = marked.parse(text);
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
                            ${formatNumber(comment.like)}
                        </span>
                        <span class="comment-stat" title="回复数">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                            </svg>
                            ${formatNumber(comment.reply_count)}
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
            ? ['#FB7299', '#23ADE5', '#FF85AD', '#3EBAD5', '#FFFFFF', '#9499A0']
            : ['#FB7299', '#23ADE5', '#E06489', '#1E96C8', '#18191C', '#9499A0'];

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

    function formatNumber(num) {
        if (!num) return '0';
        if (num > 10000) return (num / 10000).toFixed(1) + '万';
        return num;
    }

    function showToast(msg) {
        elements.toast.textContent = msg;
        elements.toast.classList.remove('hidden');
        setTimeout(() => elements.toast.classList.add('hidden'), 3000);
    }

    function openSettings() {
        elements.settingsDrawer.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    }

    function closeSettings() {
        elements.settingsDrawer.classList.add('hidden');
        document.body.style.overflow = ''; // Restore scrolling
    }

    function copyContent() {
        const activeTab = document.querySelector('.nav-btn.active').dataset.tab;
        let content = '';
        if (activeTab === 'summary') content = currentData.summary;
        else if (activeTab === 'danmaku') content = currentData.danmaku;
        else if (activeTab === 'comments') content = currentData.comments;
        else if (activeTab === 'subtitle') content = currentData.rawContent;
        if (!content) {
            showToast('当前没有可复制的内容');
            return;
        }
        navigator.clipboard.writeText(content).then(() => {
            showToast('复制成功！');
        });
    }

    function downloadMarkdown() {
        const content = currentData.fullMarkdown;
        if (!content) {
            showToast('没有可下载的内容');
            return;
        }
        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'bilibili_analysis_' + new Date().getTime() + '.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
});