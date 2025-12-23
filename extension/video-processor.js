/**
 * 视频处理器 - 负责视频帧提取、字幕解析等
 */

class VideoProcessor {
    constructor() {
        this.biliApi = new BiliBiliAPI();
    }

    /**
     * 初始化
     */
    async init() {
        await this.biliApi.init();
    }

    /**
     * 提取BVID从URL
     */
    extractBVID(url) {
        const patterns = [
            /BV([a-zA-Z0-9]{10})/,
            /bilibili\.com\/video\/(BV[a-zA-Z0-9]{10})/,
            /b23\.tv\/([a-zA-Z0-9]+)/
        ];

        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match) {
                return match[1] || match[2];
            }
        }

        return null;
    }

    /**
     * 提取CV号（专栏）
     */
    extractCVID(url) {
        const match = url.match(/cv(\d+)|read\/cv(\d+)/);
        return match ? (match[1] || match[2]) : null;
    }

    /**
     * 提取Opus ID
     */
    extractOpusID(url) {
        const match = url.match(/opus\/(\d+)/);
        return match ? match[1] : null;
    }

    /**
     * 提取用户UID
     */
    extractUID(url) {
        const patterns = [
            /space\.bilibili\.com\/(\d+)/,
            /^(\d{7,})$/  // 7位以上纯数字
        ];

        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match) return match[1];
        }

        return null;
    }

    /**
     * 从页面获取当前视频BVID
     */
    getCurrentPageBVID() {
        // 从URL获取
        const urlMatch = window.location.href.match(/\/video\/(BV[a-zA-Z0-9]{10})/);
        if (urlMatch) return urlMatch[1];

        // 从__INITIAL_STATE__获取
        if (window.__INITIAL_STATE__?.videoData?.bvid) {
            return window.__INITIAL_STATE__.videoData.bvid;
        }

        return null;
    }

    /**
     * 获取视频CID
     */
    async getVideoCID(bvid) {
        try {
            const info = await this.biliApi.getVideoInfo(bvid);
            return info?.cid;
        } catch (e) {
            console.error('[VideoProcessor] Get CID failed:', e);
            return null;
        }
    }

    /**
     * 获取完整视频信息
     */
    async getVideoInfo(bvid) {
        try {
            const data = await this.biliApi.getVideoInfo(bvid);

            return {
                bvid: data.bvid,
                aid: data.aid,
                cid: data.cid,
                title: data.title,
                desc: data.desc,
                duration: data.duration,
                owner: {
                    mid: data.owner?.mid,
                    name: data.owner?.name,
                    face: data.owner?.face
                },
                stat: {
                    view: data.stat?.view,
                    like: data.stat?.like,
                    coin: data.stat?.coin,
                    favorite: data.stat?.favorite,
                    share: data.stat?.share,
                    reply: data.stat?.reply
                },
                pic: data.pic,
                pubdate: data.pubdate,
                cover: 'https:' + data.pic
            };
        } catch (e) {
            console.error('[VideoProcessor] Get video info failed:', e);
            return null;
        }
    }

    /**
     * 获取视频字幕 - 修复版
     */
    async getVideoSubtitle(bvid, cid) {
        try {
            console.log('[VideoProcessor] Getting subtitle for:', bvid, cid);

            const data = await this.biliApi.getVideoSubtitle(bvid, cid);

            if (!data || !data.body || data.body.length === 0) {
                console.log('[VideoProcessor] No subtitle found');
                return { hasSubtitle: false, text: '' };
            }

            // 提取字幕文本
            const text = data.body
                .map(item => item.content)
                .filter(c => c && c.trim())
                .join('\n');

            console.log('[VideoProcessor] Subtitle extracted, length:', text.length);

            return {
                hasSubtitle: true,
                text,
                raw: data.body,
                language: data.lan_doc || '中文'
            };
        } catch (e) {
            console.error('[VideoProcessor] Get subtitle failed:', e);
            return { hasSubtitle: false, text: '' };
        }
    }

    /**
     * 从页面video元素提取帧
     */
    async extractFramesFromVideo(videoElement, options = {}) {
        const {
            maxFrames = 16,
            interval = null,  // 自动计算
            quality = 0.7
        } = options;

        if (!videoElement) {
            throw new Error('Video element not found');
        }

        const duration = videoElement.duration;
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        // 计算采样间隔
        const step = interval || Math.max(1, duration / maxFrames);

        const frames = [];
        const frameData = [];

        // 保存当前播放位置
        const currentTime = videoElement.currentTime;
        const wasPaused = videoElement.paused;

        videoElement.pause();

        try {
            // 提取帧
            for (let time = 0; time < duration && frames.length < maxFrames; time += step) {
                videoElement.currentTime = time;

                await new Promise(resolve => {
                    videoElement.addEventListener('seeked', () => resolve(), { once: true });
                });

                const width = videoElement.videoWidth;
                const height = videoElement.videoHeight;

                canvas.width = width;
                canvas.height = height;

                ctx.drawImage(videoElement, 0, 0, width, height);

                // 转换为base64
                const dataUrl = canvas.toDataURL('image/jpeg', quality);
                frames.push(dataUrl);

                // 只保存前几个字节用于分析
                if (frames.length <= 8) {
                    frameData.push(dataUrl);
                }
            }

            return {
                frames: frameData,  // 返回前8帧用于AI分析
                allFrames: frames,  // 所有帧
                count: frames.length
            };
        } finally {
            // 恢复播放状态
            videoElement.currentTime = currentTime;
            if (!wasPaused) {
                videoElement.play();
            }
        }
    }

    /**
     * 获取弹幕（分段）
     */
    async getDanmaku(bvid, cid, maxSegments = 10) {
        try {
            const allDanmaku = [];

            for (let i = 0; i < maxSegments; i++) {
                const danmaku = await this.biliApi.getVideoDanmaku(bvid, cid, i);
                if (!danmaku || danmaku.length === 0) break;

                allDanmaku.push(...danmaku);

                if (allDanmaku.length >= 1000) break;
            }

            // 智能采样
            const sampled = this.sampleDanmaku(allDanmaku, 200);

            return {
                count: allDanmaku.length,
                danmaku: sampled,
                fullText: sampled.map(d => d.text).join('\n')
            };
        } catch (e) {
            console.error('[VideoProcessor] Get danmaku failed:', e);
            return { count: 0, danmaku: [], fullText: '' };
        }
    }

    /**
     * 智能采样弹幕
     */
    sampleDanmaku(danmakuList, maxCount) {
        if (danmakuList.length <= maxCount) {
            return danmakuList;
        }

        const step = danmakuList.length / maxCount;
        const sampled = [];

        for (let i = 0; i < maxCount; i++) {
            const index = Math.floor(i * step);
            sampled.push(danmakuList[index]);
        }

        return sampled;
    }

    /**
     * 获取评论 - 修复版
     */
    async getComments(bvid, cid, maxCount = 100) {
        try {
            console.log('[VideoProcessor] Getting comments for:', bvid);

            const info = await this.biliApi.getVideoInfo(bvid);
            const aid = info?.aid;

            if (!aid) {
                throw new Error('Cannot get aid');
            }

            let allComments = [];
            let page = 1;

            // 获取评论
            while (allComments.length < maxCount && page <= 5) {
                const result = await this.biliApi.getVideoComments(aid, page);

                // 尝试从多个来源获取评论
                let replies = result?.replies || [];

                // 如果主评论为空，尝试从 top 获取（置顶评论）
                if (replies.length === 0 && result?.top?.replies) {
                    console.log('[VideoProcessor] Using top replies, count:', result.top.replies.length);
                    replies = result.top.replies;
                }

                // 如果仍然为空，尝试从 upper 获取（UP主评论）
                if (replies.length === 0 && result?.upper?.replies) {
                    console.log('[VideoProcessor] Using upper replies, count:', result.upper.replies.length);
                    replies = result.upper.replies;
                }

                if (replies.length === 0) {
                    console.log('[VideoProcessor] No comments found on page', page);
                    break;
                }

                console.log('[VideoProcessor] Found', replies.length, 'comments on page', page);
                allComments.push(...replies);
                page++;
            }

            const processed = allComments.slice(0, maxCount).map(c => ({
                username: c.member?.uname || '未知用户',
                message: c.content?.message || '',
                like: c.like || 0,
                replyCount: c.rcount || 0,
                time: c.ctime,
                avatar: c.member?.avatar
            }));

            console.log('[VideoProcessor] Comments loaded:', processed.length);
            return {
                count: processed.length,
                comments: processed
            };
        } catch (e) {
            console.error('[VideoProcessor] Get comments failed:', e);
            return { count: 0, comments: [] };
        }
    }

    /**
     * 获取在线人数
     */
    async getOnlineCount(bvid, cid) {
        try {
            const data = await this.biliApi.getVideoOnline(bvid, cid);
            return data?.total || 0;
        } catch (e) {
            return 0;
        }
    }

    /**
     * 完整的视频数据采集
     */
    async collectVideoData(bvid, options = {}) {
        const {
            needFrames = true,
            needDanmaku = true,
            needComments = true,
            needSubtitle = true,
            maxFrames = 8,
            maxComments = 50
        } = options;

        // 获取基本信息
        const videoInfo = await this.getVideoInfo(bvid);
        if (!videoInfo) {
            throw new Error('Failed to get video info');
        }

        const { cid } = videoInfo;

        // 并行获取所有数据
        const tasks = {};

        if (needSubtitle) {
            tasks.subtitle = this.getVideoSubtitle(bvid, cid);
        }

        if (needDanmaku) {
            tasks.danmaku = this.getDanmaku(bvid, cid);
        }

        if (needComments) {
            tasks.comments = this.getComments(bvid, cid, maxComments);
        }

        tasks.online = this.getOnlineCount(bvid, cid);
        tasks.related = this.biliApi.getRelatedVideos(bvid);

        const results = await Promise.allSettled(Object.values(tasks));
        const taskKeys = Object.keys(tasks);

        const data = {
            info: videoInfo,
            subtitle: null,
            danmaku: null,
            comments: null,
            online: 0,
            related: [],
            frames: null
        };

        results.forEach((result, index) => {
            const key = taskKeys[index];
            if (result.status === 'fulfilled') {
                data[key] = result.value;
            } else {
                console.error(`[VideoProcessor] ${key} failed:`, result.reason);
            }
        });

        // 从页面提取帧
        if (needFrames) {
            try {
                const videoElement = document.querySelector('video');
                if (videoElement) {
                    data.frames = await this.extractFramesFromVideo(videoElement, {
                        maxFrames,
                        quality: 0.6
                    });
                }
            } catch (e) {
                console.error('[VideoProcessor] Extract frames failed:', e);
            }
        }

        return data;
    }

    /**
     * 获取专栏数据
     */
    async collectArticleData(cvid) {
        const info = await this.biliApi.getArticleInfo(cvid);

        return {
            title: info?.title,
            author: info?.authorName,
            content: info?.content || '',
            summary: info?.summary,
            stats: {
                view: info?.stats?.view,
                like: info?.stats?.like,
                favorite: info?.stats?.favorite
            },
            banner: info?.banner_url
        };
    }

    /**
     * 获取用户数据
     */
    async collectUserData(uid) {
        const [info, relation, videos] = await Promise.allSettled([
            this.biliApi.getUserInfo(uid),
            this.biliApi.getUserRelation(uid),
            this.biliApi.getUserVideos(uid, 1, 20)
        ]);

        return {
            info: info.status === 'fulfilled' ? info.value : null,
            relation: relation.status === 'fulfilled' ? relation.value : null,
            videos: videos.status === 'fulfilled' ? videos.value?.list?.vlist || [] : []
        };
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoProcessor;
}
