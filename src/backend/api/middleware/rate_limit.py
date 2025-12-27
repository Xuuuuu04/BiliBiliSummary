"""
请求限流中间件

基于内存的请求限流实现，防止 API 被滥用
"""

import time
from collections import defaultdict
from flask import request, jsonify
from typing import Tuple, Optional
from src.backend.utils.logger import get_logger
from src.config import Config

logger = get_logger(__name__)


class RateLimiter:
    """请求限流器"""

    def __init__(self, app=None):
        """
        初始化限流器

        Args:
            app: Flask 应用实例（可选，稍后可以使用 init_app 方法）
        """
        self.app = app
        # 存储每个客户端的请求记录 {client_id: [(timestamp, count)]}
        self.requests = defaultdict(list)

        # 限流配置
        self.limits = {
            'default': (Config.API_RATE_LIMIT_DEFAULT, Config.API_RATE_LIMIT_WINDOW),
            'api_key': (1000, 60),  # 1000 请求/分钟 (API Key)
            'premium': (5000, 60),  # 5000 请求/分钟 (高级用户)
        }

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        初始化 Flask 应用

        Args:
            app: Flask 应用实例
        """
        self.app = app
        app.before_request(self._check_rate_limit)

    def is_allowed(self, client_id: str, tier: str = 'default') -> Tuple[bool, int]:
        """
        检查是否允许请求

        Args:
            client_id: 客户端标识
            tier: 用户层级 (default, api_key, premium)

        Returns:
            (是否允许, 剩余请求数)
        """
        limit, window = self.limits.get(tier, self.limits['default'])
        now = time.time()

        # 清理过期记录
        self.requests[client_id] = [
            (ts, count) for ts, count in self.requests[client_id]
            if now - ts < window
        ]

        # 计算当前窗口内的请求总数
        total_requests = sum(count for _, count in self.requests[client_id])

        if total_requests >= limit:
            return False, 0

        # 记录本次请求
        self.requests[client_id].append((now, 1))
        return True, limit - total_requests - 1

    def get_client_id(self) -> Tuple[str, str]:
        """
        获取客户端标识

        Returns:
            (client_id, tier)
        """
        # 优先使用 API Key
        api_key = request.headers.get(Config.API_KEY_HEADER)
        if api_key:
            return f"apikey:{api_key}", 'api_key'

        # 其次使用 IP
        ip = request.remote_addr
        return f"ip:{ip}", 'default'

    def _check_rate_limit(self):
        """
        请求前检查限流（before_request 钩子）

        如果超过限流，返回 429 错误
        """
        # 如果限流未启用，跳过
        if not Config.API_RATE_LIMIT_ENABLED:
            return

        # 获取客户端标识
        client_id, tier = self.get_client_id()

        # 检查是否允许请求
        allowed, remaining = self.is_allowed(client_id, tier)

        if not allowed:
            limit, window = self.limits.get(tier, self.limits['default'])

            logger.warning(f"Rate limit exceeded for {client_id}")

            response = jsonify({
                'success': False,
                'error': '请求过于频繁，请稍后再试',
                'error_code': 'RATE_LIMIT_EXCEEDED',
                'details': {
                    'limit': limit,
                    'window': window,
                    'tier': tier
                }
            })

            response.status_code = 429
            # 添加限流响应头
            response.headers['X-RateLimit-Limit'] = str(limit)
            response.headers['X-RateLimit-Remaining'] = '0'
            response.headers['X-RateLimit-Reset'] = str(int(time.time()) + window)

            return response

        # 添加限流信息到响应头（允许请求时）
        # 注意：这里需要使用 after_request 钩子，我们将在 logging 中间件中处理

    def reset_client(self, client_id: str):
        """
        重置指定客户端的限流记录

        Args:
            client_id: 客户端标识
        """
        if client_id in self.requests:
            del self.requests[client_id]

    def get_stats(self, client_id: str) -> dict:
        """
        获取客户端限流统计信息

        Args:
            client_id: 客户端标识

        Returns:
            统计信息字典
        """
        if client_id not in self.requests:
            return {
                'total_requests': 0,
                'requests_in_window': 0,
                'tier': 'unknown'
            }

        limit, window = self.limits.get('default', self.limits['default'])
        now = time.time()

        # 清理过期记录
        self.requests[client_id] = [
            (ts, count) for ts, count in self.requests[client_id]
            if now - ts < window
        ]

        total_requests = sum(count for _, count in self.requests[client_id])

        return {
            'total_requests': total_requests,
            'requests_in_window': len(self.requests[client_id]),
            'limit': limit,
            'remaining': max(0, limit - total_requests),
            'tier': 'default'
        }
