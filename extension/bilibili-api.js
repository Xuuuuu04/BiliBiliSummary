/**
 * bilibili-api JavaScript移植版 - 修复版
 * 支持通过background script获取Cookie
 */

/**
 * BytesReader - 字节流读取器 (参考 bilibili-api Python 实现)
 * 用于解析B站弹幕protobuf数据
 */
class BytesReader {
    constructor(buffer) {
        this.buffer = buffer;
        this.offset = 0;
    }

    /**
     * 是否已读到末尾
     */
    hasEnd() {
        return this.offset >= this.buffer.length;
    }

    /**
     * 读取 varint (变长整数)
     */
    varint() {
        let value = 0;
        let shift = 0;

        while (this.offset < this.buffer.length) {
            const byte = this.buffer[this.offset];
            this.offset++;
            value += (byte & 0x7F) << shift;
            if ((byte & 0x80) === 0) {
                break;
            }
            shift += 7;
        }

        return value;
    }

    /**
     * 读取字符串 (UTF-8)
     */
    string(encoding = 'utf-8') {
        const length = this.varint();
        const bytes = this.buffer.subarray(this.offset, this.offset + length);
        this.offset += length;

        // 解码 UTF-8
        return new TextDecoder(encoding).decode(bytes);
    }

    /**
     * 读取原始字节
     */
    bytesString() {
        const length = this.varint();
        const bytes = this.buffer.subarray(this.offset, this.offset + length);
        this.offset += length;
        return bytes;
    }

    /**
     * 获取当前位置
     */
    getPos() {
        return this.offset;
    }

    /**
     * 设置读取位置
     */
    setPos(pos) {
        if (pos < 0 || pos > this.buffer.length) {
            throw new Error('Invalid position');
        }
        this.offset = pos;
    }
}

class BiliBiliAPI {
    constructor() {
        this.cookie = {};
        this.wbiKeys = null;
        this.wbiKeyExpire = 0;
        this.cookieInitialized = false;
    }

    /**
     * 初始化 - 从background获取Cookie
     */
    async init() {
        if (this.cookieInitialized) {
            return;
        }

        // 尝试从background获取cookie
        if (typeof chrome !== 'undefined' && chrome.runtime) {
            try {
                const response = await chrome.runtime.sendMessage({
                    action: 'getBiliCookies'
                });

                if (response && response.cookies) {
                    this.cookie = response.cookies;
                    console.log('[BiliBiliAPI] Cookies loaded from background:', Object.keys(this.cookie));
                }
            } catch (e) {
                console.warn('[BiliBiliAPI] Failed to get cookies from background:', e);
                // 降级：从document获取
                this.initFromDocument();
            }
        } else {
            // 从document获取cookie
            this.initFromDocument();
        }

        this.cookieInitialized = true;
    }

    /**
     * 从document获取cookie（降级方案）
     */
    initFromDocument() {
        if (typeof document !== 'undefined' && document.cookie) {
            document.cookie.split(';').forEach(c => {
                const [key, value] = c.trim().split('=');
                if (key && value) {
                    this.cookie[key] = value;
                }
            });
            console.log('[BiliBiliAPI] Cookies loaded from document:', Object.keys(this.cookie));
        }
    }

    /**
     * WBI签名算法
     */
    async getWBIKeys() {
        if (this.wbiKeys && Date.now() < this.wbiKeyExpire) {
            return this.wbiKeys;
        }

        try {
            const resp = await fetch('https://api.bilibili.com/x/web-interface/nav');
            const data = await resp.json();
            const wbiImg = data.data?.wbi_img;

            if (!wbiImg) {
                console.warn('[BiliBiliAPI] WBI img not found');
                return null;
            }

            const imgKey = this.extractKey(wbiImg.img_url);
            const subKey = this.extractKey(wbiImg.sub_url);

            this.wbiKeys = { imgKey, subKey };
            this.wbiKeyExpire = Date.now() + 12 * 60 * 60 * 1000;

            return this.wbiKeys;
        } catch (e) {
            console.error('[BiliBiliAPI] Get WBI keys failed:', e);
            return null;
        }
    }

    extractKey(url) {
        const match = url.match(/([a-z0-9]{32})/);
        return match ? match[1] : '';
    }

    /**
     * 混合密钥
     */
    getMixinKey(imgKey, subKey) {
        const ORDER = [
            46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 30, 33, 10, 20, 13,
            28, 12, 5, 52, 15, 31, 57, 40, 37, 43, 20, 13, 23, 51, 25, 41,
            44, 20, 8, 22, 39, 29, 20, 15
        ];

        const key = imgKey + subKey;
        let result = '';
        for (let i = 0; i < 32; i++) {
            result += key[ORDER[i]];
        }
        return result;
    }

    /**
     * 计算WBI签名
     */
    async calcWBI(params) {
        const keys = await this.getWBIKeys();
        if (!keys) return params;

        const mixinKey = this.getMixinKey(keys.imgKey, keys.subKey);
        const wts = Math.floor(Date.now() / 1000);

        const sortedParams = Object.entries({ ...params, wts })
            .sort((a, b) => a[0].localeCompare(b[0]));

        const queryStr = sortedParams.map(([k, v]) => `${k}=${v}`).join('&');

        // 使用MD5计算签名
        const w_rid = await this.md5(queryStr + mixinKey);

        return { ...params, wts, w_rid };
    }

    /**
     * MD5哈希函数
     */
    async md5(string) {
        function md5cycle(x, k) {
            var a = x[0], b = x[1], c = x[2], d = x[3];

            a = ff(a, b, c, d, k[0], 7, -680876936);
            d = ff(d, a, b, c, k[1], 12, -389564586);
            c = ff(c, d, a, b, k[2], 17, 606105819);
            b = ff(b, c, d, a, k[3], 22, -1044525330);
            a = ff(a, b, c, d, k[4], 7, -176418897);
            d = ff(d, a, b, c, k[5], 12, 1200080426);
            c = ff(c, d, a, b, k[6], 17, -1473231341);
            b = ff(b, c, d, a, k[7], 22, -45705983);
            a = ff(a, b, c, d, k[8], 7, 1770035416);
            d = ff(d, a, b, c, k[9], 12, -1958414417);
            c = ff(c, d, a, b, k[10], 17, -42063);
            b = ff(b, c, d, a, k[11], 22, -1990404162);
            a = ff(a, b, c, d, k[12], 7, 1804603682);
            d = ff(d, a, b, c, k[13], 12, -40341101);
            c = ff(c, d, a, b, k[14], 17, -1502002290);
            b = ff(b, c, d, a, k[15], 22, 1236535329);

            a = gg(a, b, c, d, k[1], 5, -165796510);
            d = gg(d, a, b, c, k[6], 9, -1069501632);
            c = gg(c, d, a, b, k[11], 14, 643717713);
            b = gg(b, c, d, a, k[0], 20, -373897302);
            a = gg(a, b, c, d, k[5], 5, -701558691);
            d = gg(d, a, b, c, k[10], 9, 38016083);
            c = gg(c, d, a, b, k[15], 14, -660478335);
            b = gg(b, c, d, a, k[4], 20, -405537848);
            a = gg(a, b, c, d, k[9], 5, 568446438);
            d = gg(d, a, b, c, k[14], 9, -1019803690);
            c = gg(c, d, a, b, k[3], 14, -187363961);
            b = gg(b, c, d, a, k[8], 20, 1163531501);
            a = gg(a, b, c, d, k[13], 5, -1444681467);
            d = gg(d, a, b, c, k[2], 9, -51403784);
            c = gg(c, d, a, b, k[7], 14, 1735328473);
            b = gg(b, c, d, a, k[12], 20, -1926607734);

            a = hh(a, b, c, d, k[5], 4, -378558);
            d = hh(d, a, b, c, k[8], 11, -2022574463);
            c = hh(c, d, a, b, k[11], 16, 1839030562);
            b = hh(b, c, d, a, k[14], 23, -35309556);
            a = hh(a, b, c, d, k[1], 4, -1530992060);
            d = hh(d, a, b, c, k[4], 11, 1272893353);
            c = hh(c, d, a, b, k[7], 16, -155497632);
            b = hh(b, c, d, a, k[10], 23, -1094730640);
            a = hh(a, b, c, d, k[13], 4, 681279174);
            d = hh(d, a, b, c, k[0], 11, -358537222);
            c = hh(c, d, a, b, k[3], 16, -722521979);
            b = hh(b, c, d, a, k[6], 23, 76029189);
            a = hh(a, b, c, d, k[9], 4, -640364487);
            d = hh(d, a, b, c, k[12], 11, -421815835);
            c = hh(c, d, a, b, k[15], 16, 530742520);
            b = hh(b, c, d, a, k[2], 23, -995338651);

            a = ii(a, b, c, d, k[0], 6, -198630844);
            d = ii(d, a, b, c, k[7], 10, 1126891415);
            c = ii(c, d, a, b, k[14], 15, -1416354905);
            b = ii(b, c, d, a, k[5], 21, -57434055);
            a = ii(a, b, c, d, k[12], 6, 1700485571);
            d = ii(d, a, b, c, k[3], 10, -1894986606);
            c = ii(c, d, a, b, k[10], 15, -1051523);
            b = ii(b, c, d, a, k[1], 21, -2054922799);
            a = ii(a, b, c, d, k[8], 6, 1873313359);
            d = ii(d, a, b, c, k[15], 10, -30611744);
            c = ii(c, d, a, b, k[6], 15, -1560198380);
            b = ii(b, c, d, a, k[13], 21, 1309151649);
            a = ii(a, b, c, d, k[4], 6, -145523070);
            d = ii(d, a, b, c, k[11], 10, -1120210379);
            c = ii(c, d, a, b, k[2], 15, 718787259);
            b = ii(b, c, d, a, k[9], 21, -343485551);

            x[0] = add32(a, x[0]);
            x[1] = add32(b, x[1]);
            x[2] = add32(c, x[2]);
            x[3] = add32(d, x[3]);
        }

        function cmn(q, a, b, x, s, t) {
            a = add32(add32(a, q), add32(x, t));
            return add32((a << s) | (a >>> (32 - s)), b);
        }

        function ff(a, b, c, d, x, s, t) {
            return cmn((b & c) | ((~b) & d), a, b, x, s, t);
        }

        function gg(a, b, c, d, x, s, t) {
            return cmn((b & d) | (c & (~d)), a, b, x, s, t);
        }

        function hh(a, b, c, d, x, s, t) {
            return cmn(b ^ c ^ d, a, b, x, s, t);
        }

        function ii(a, b, c, d, x, s, t) {
            return cmn(c ^ (b | (~d)), a, b, x, s, t);
        }

        function md51(s) {
            var n = s.length,
                state = [1732584193, -271733879, -1732584194, 271733878],
                i;
            for (i = 64; i <= s.length; i += 64) {
                md5cycle(state, md5blk(s.substring(i - 64, i)));
            }
            s = s.substring(i - 64);
            var tail = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
            for (i = 0; i < s.length; i++)
                tail[i >> 2] |= s.charCodeAt(i) << ((i % 4) << 3);
            tail[i >> 2] |= 0x80 << ((i % 4) << 3);
            if (i > 55) md5cycle(state, tail);
            tail[14] = n * 8;
            md5cycle(state, tail);
            return state;
        }

        function md5blk(s) {
            var md5blks = [],
                i;
            for (i = 0; i < 64; i += 4) {
                md5blks[i >> 2] = s.charCodeAt(i)
                    + (s.charCodeAt(i + 1) << 8)
                    + (s.charCodeAt(i + 2) << 16)
                    + (s.charCodeAt(i + 3) << 24);
            }
            return md5blks;
        }

        var hex_chr = '0123456789abcdef'.split('');

        function rhex(n) {
            var s = '',
                j = 0;
            for (; j < 4; j++)
                s += hex_chr[(n >> (j * 8 + 4)) & 0x0F]
                    + hex_chr[(n >> (j * 8)) & 0x0F];
            return s;
        }

        function hex(x) {
            for (var j = 0; j < x.length; j++)
                x[j] = rhex(x[j]);
            return x.join('');
        }

        function add32(a, b) {
            return (a + b) & 0xFFFFFFFF;
        }

        return hex(md51(string));
    }

    /**
     * 通用API请求方法
     */
    async request(url, options = {}) {
        const {
            method = 'GET',
            params = {},
            data = null,
            needWBI = false,
            needAuth = false
        } = options;

        let finalParams = { ...params };

        // 添加WBI签名
        if (needWBI) {
            finalParams = await this.calcWBI(finalParams);
        }

        // 构建URL
        let fullUrl = url;
        if (Object.keys(finalParams).length > 0) {
            const query = Object.entries(finalParams)
                .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
                .join('&');
            fullUrl += (url.includes('?') ? '&' : '?') + query;
        }

        // 构建请求头
        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Referer': 'https://www.bilibili.com',
            'User-Agent': navigator.userAgent
        };

        // 添加Cookie
        if (needAuth && this.cookie.SESSDATA) {
            headers['Cookie'] = this.buildCookieString();
        }

        const fetchOptions = {
            method,
            headers
        };

        if (data) {
            fetchOptions.body = JSON.stringify(data);
        }

        try {
            console.log('[BiliBiliAPI] Request:', fullUrl);
            const response = await fetch(fullUrl, fetchOptions);
            const result = await response.json();

            if (result.code !== 0) {
                console.error('[BiliBiliAPI] API Error:', result.code, result.message);
                throw new Error(`API Error: ${result.code} - ${result.message}`);
            }

            return result.data;
        } catch (e) {
            console.error('[BiliBiliAPI] Request failed:', url, e);
            throw e;
        }
    }

    buildCookieString() {
        return Object.entries(this.cookie)
            .map(([k, v]) => `${k}=${v}`)
            .join('; ');
    }

    // ========== 视频相关 API ==========

    /**
     * 获取视频信息
     */
    async getVideoInfo(bvid) {
        console.log('[BiliBiliAPI] Getting video info for:', bvid);
        return await this.request(
            `https://api.bilibili.com/x/web-interface/view`,
            { params: { bvid }, needAuth: true }
        );
    }

    /**
     * 获取视频字幕 - 修复版 (参考 bilibili-api Python 实现)
     * API: https://api.bilibili.com/x/player/wbi/v2
     */
    async getVideoSubtitle(bvid, cid) {
        console.log('[BiliBiliAPI] Getting subtitle for:', bvid, cid);

        try {
            // 获取视频信息以获取 aid
            const videoInfo = await this.getVideoInfo(bvid);
            if (!videoInfo || !videoInfo.aid) {
                console.error('[BiliBiliAPI] Cannot get aid from video info');
                return null;
            }

            const aid = videoInfo.aid;

            // 使用 /x/player/wbi/v2 接口 (需要 WBI 签名)
            console.log('[BiliBiliAPI] Fetching player info with WBI...');
            const data = await this.request(
                `https://api.bilibili.com/x/player/wbi/v2`,
                {
                    params: {
                        aid: aid,
                        cid: cid,
                        isGaiaAvoided: false
                    },
                    needWBI: true,
                    needAuth: true
                }
            );

            console.log('[BiliBiliAPI] Player info response keys:', Object.keys(data));
            console.log('[BiliBiliAPI] Subtitle data:', data?.subtitle);

            // 检查字幕数据
            if (data?.subtitle?.subtitles && data.subtitle.subtitles.length > 0) {
                const subtitles = data.subtitle.subtitles;
                console.log('[BiliBiliAPI] Found subtitles:', subtitles.length, subtitles.map(s => ({ lan: s.lan, url: s.subtitle_url })));

                // 优先获取中文
                const targetSub = subtitles.find(s => s.lan && s.lan.includes('zh')) || subtitles[0];

                if (targetSub) {
                    const subUrl = 'https:' + targetSub.subtitle_url;
                    console.log('[BiliBiliAPI] Fetching subtitle from:', subUrl);

                    const resp = await fetch(subUrl);
                    if (!resp.ok) {
                        console.error('[BiliBiliAPI] Failed to fetch subtitle file:', resp.status);
                        return null;
                    }

                    const subtitleData = await resp.json();
                    console.log('[BiliBiliAPI] Subtitle data loaded, body length:', subtitleData.body?.length || 0);

                    // 返回统一格式
                    return {
                        body: subtitleData.body || [],
                        lan_doc: data.subtitle.lan_doc || '中文'
                    };
                }
            } else {
                console.log('[BiliBiliAPI] No subtitles in response. subtitle field:', data?.subtitle);
            }

            console.log('[BiliBiliAPI] No subtitle found');
            return null;
        } catch (e) {
            console.error('[BiliBiliAPI] Get subtitle failed:', e);
            return null;
        }
    }

    /**
     * 获取视频弹幕 - 修复版 (不使用 WBI 签名)
     * API: https://api.bilibili.com/x/v2/dm/web/seg.so
     */
    async getVideoDanmaku(bvid, cid, segmentIndex = 0) {
        console.log('[BiliBiliAPI] Getting danmaku for:', bvid, cid, segmentIndex);

        try {
            // 获取视频信息以获取 aid
            const videoInfo = await this.getVideoInfo(bvid);
            const aid = videoInfo?.aid;

            if (!aid) {
                console.error('[BiliBiliAPI] Cannot get aid for danmaku');
                return [];
            }

            // 弹幕接口不需要 WBI 签名，直接请求
            const url = `https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid=${cid}&segment_index=${segmentIndex}`;

            console.log('[BiliBiliAPI] Fetching danmaku from:', url);

            const response = await fetch(url, {
                headers: {
                    'Referer': 'https://www.bilibili.com',
                    'User-Agent': navigator.userAgent
                }
            });

            if (!response.ok) {
                console.warn('[BiliBiliAPI] Danmaku request failed:', response.status);
                return [];
            }

            const buffer = await response.arrayBuffer();
            console.log('[BiliBiliAPI] Danmaku protobuf data received, size:', buffer.byteLength);

            return this.parseDanmakuProto(buffer);
        } catch (e) {
            console.error('[BiliBiliAPI] Get danmaku failed:', e);
            return [];
        }
    }

    /**
     * 解析弹幕protobuf - 完整版 (参考 bilibili-api Python 实现)
     */
    parseDanmakuProto(buffer) {
        const danmakus = [];

        try {
            const reader = new BytesReader(new Uint8Array(buffer));

            while (!reader.hasEnd()) {
                const type = reader.varint() >> 3;

                if (type !== 1) {
                    // type=4: 未知字段, type=5: 大会员专属颜色
                    // type=13, type=15: 其他字段，跳过
                    if (type === 4) {
                        reader.bytesString();
                    } else if (type === 5) {
                        reader.varint();
                        reader.varint();
                        reader.varint();
                        reader.bytesString();
                    }
                    // 其他未知类型跳过，不要中断
                    continue;
                }

                // 解析弹幕数据
                const dmData = reader.bytesString();
                const dmReader = new BytesReader(dmData);
                const dm = {
                    text: '',
                    time: 0,
                    mode: 1,
                    fontSize: 25,
                    color: 'ffffff',
                    sendTime: 0
                };

                while (!dmReader.hasEnd()) {
                    const dataType = dmReader.varint() >> 3;

                    switch (dataType) {
                        case 1: // id
                            dmReader.varint();
                            break;
                        case 2: // dm_time (毫秒)
                            dm.time = dmReader.varint() / 1000;
                            break;
                        case 3: // mode
                            dm.mode = dmReader.varint();
                            break;
                        case 4: // font_size
                            dm.fontSize = dmReader.varint();
                            break;
                        case 5: // color
                            let color = dmReader.varint();
                            dm.color = (color !== 60001) ? color.toString(16) : 'special';
                            break;
                        case 6: // crc32_id
                            dmReader.string();
                            break;
                        case 7: // text (弹幕文本)
                            dm.text = dmReader.string();
                            break;
                        case 8: // send_time
                            dm.sendTime = dmReader.varint();
                            break;
                        case 9: // weight
                            dmReader.varint();
                            break;
                        case 10: // action
                            dmReader.string();
                            break;
                        case 11: // pool
                            dmReader.varint();
                            break;
                        case 12: // id_str
                            dmReader.string();
                            break;
                        case 13: // attr
                            dmReader.varint();
                            break;
                        case 14: // uid
                            dmReader.varint();
                            break;
                        case 15:
                            dmReader.varint();
                            break;
                        case 20:
                        case 21:
                        case 22:
                            dmReader.bytesString();
                            break;
                        case 25:
                        case 26:
                            dmReader.varint();
                            break;
                        default:
                            break;
                    }
                }

                // 只添加有文本的弹幕
                if (dm.text && dm.text.trim().length > 0) {
                    danmakus.push(dm);
                }
            }

            console.log('[BiliBiliAPI] Parsed danmaku count:', danmakus.length);
            return danmakus;
        } catch (e) {
            console.error('[BiliBiliAPI] Parse danmaku failed:', e);
            return [];
        }
    }

    /**
     * 获取视频评论 - 修复版 (参考 bilibili-api Python 实现)
     * API: https://api.bilibili.com/x/v2/reply
     */
    async getVideoComments(oid, next = '') {
        console.log('[BiliBiliAPI] Getting comments for:', oid, 'next:', next);

        const params = {
            oid: oid,      // av 号
            type: 1,       // 1 = 视频评论
            mode: 3,       // 3 = 仅按热度
            pn: next || 1, // 页码
            ps: 20         // 每页数量
        };

        const result = await this.request(
            'https://api.bilibili.com/x/v2/reply',
            { params, needAuth: false }
        );

        console.log('[BiliBiliAPI] Comments response keys:', Object.keys(result));
        console.log('[BiliBiliAPI] Page info:', result?.page);
        console.log('[BiliBiliAPI] Replies count:', result?.replies?.length || 0);
        console.log('[BiliBiliAPI] Top replies:', result?.top);
        console.log('[BiliBiliAPI] Upper replies:', result?.upper?.replies?.length || 0);

        return result;
    }

    /**
     * 获取视频在线人数
     */
    async getVideoOnline(bvid, cid) {
        return await this.request(
            `https://api.bilibili.com/x/player/online/total`,
            { params: { bvid, cid }, needAuth: true }
        );
    }

    /**
     * 获取相关推荐视频
     */
    async getRelatedVideos(bvid) {
        return await this.request(
            `https://api.bilibili.com/x/web-interface/archive/related`,
            { params: { bvid }, needAuth: true }
        );
    }

    // ========== 专栏相关 API ==========

    /**
     * 获取专栏文章信息
     */
    async getArticleInfo(cvid) {
        return await this.request(
            `https://api.bilibili.com/x/article/info`,
            { params: { cvid }, needAuth: true }
        );
    }

    // ========== 用户相关 API ==========

    /**
     * 获取用户信息
     */
    async getUserInfo(uid) {
        return await this.request(
            `https://api.bilibili.com/x/space/acc/info`,
            { params: { mid: uid }, needAuth: true }
        );
    }

    /**
     * 获取用户关系
     */
    async getUserRelation(uid) {
        return await this.request(
            `https://api.bilibili.com/x/relation/stat`,
            { params: { mid: uid }, needAuth: true }
        );
    }

    /**
     * 获取用户视频
     */
    async getUserVideos(uid, pn = 1, ps = 20) {
        return await this.request(
            `https://api.bilibili.com/x/space/arc/search`,
            { params: { mid: uid, ps, pn }, needAuth: true }
        );
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BiliBiliAPI;
}
