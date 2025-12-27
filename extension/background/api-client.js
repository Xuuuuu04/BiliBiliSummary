/**
 * API 客户端
 *
 * 负责与后端 Flask API 服务通信
 */

export class APIClient {
    constructor(baseURL = 'http://localhost:5000') {
        this.baseURL = baseURL;
        this.timeout = 30000; // 30秒超时
    }

    async request(method, endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const { params, data, headers } = options;

        // 构建查询字符串
        let queryString = '';
        if (params) {
            queryString = '?' + new URLSearchParams(params).toString();
        }

        const config = {
            method: method.toUpperCase(),
            headers: {
                'Content-Type': 'application/json',
                ...headers
            }
        };

        if (data) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url + queryString, config);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API 请求失败:', error);
            throw error;
        }
    }

    get(endpoint, options = {}) {
        return this.request('GET', endpoint, options);
    }

    post(endpoint, options = {}) {
        return this.request('POST', endpoint, options);
    }

    put(endpoint, options = {}) {
        return this.request('PUT', endpoint, options);
    }

    delete(endpoint, options = {}) {
        return this.request('DELETE', endpoint, options);
    }
}

// 导出单例
export const apiClient = new APIClient();
