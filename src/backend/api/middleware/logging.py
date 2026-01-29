"""
请求日志中间件

记录所有 API 请求和响应的详细信息
"""

import time
from flask import request, g
from src.backend.utils.logger import get_logger
from src.config import Config

logger = get_logger('api.request')


class RequestLogger:
    """请求日志中间件"""

    def __init__(self, app=None):
        """
        初始化请求日志器

        Args:
            app: Flask 应用实例（可选）
        """
        self.app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        初始化 Flask 应用

        Args:
            app: Flask 应用实例
        """
        self.app = app
        app.before_request(self._log_request)
        app.after_request(self._log_response)

    def _log_request(self):
        """
        记录请求信息（before_request 钩子）
        """
        # 记录请求开始时间
        g.start_time = time.time()

        # 获取客户端标识
        api_key = request.headers.get(Config.API_KEY_HEADER)
        client_info = f"API Key: {api_key[:10]}***" if api_key else f"IP: {request.remote_addr}"

        # 构建日志消息
        log_msg = f"➤ {request.method} {request.path}"
        if request.query_string:
            log_msg += f"?{request.query_string.decode('utf-8')}"

        # 记录请求信息
        logger.info(
            log_msg,
            extra={
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string.decode('utf-8'),
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'api_key': api_key[:10] + '***' if api_key else None,
                'content_type': request.content_type,
                'content_length': request.content_length
            }
        )

    def _log_response(self, response):
        """
        记录响应信息（after_request 钩子）

        Args:
            response: Flask 响应对象

        Returns:
            响应对象（原样返回）
        """
        # 计算请求处理时长
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
        else:
            duration = 0

        # 添加响应时间到响应头
        response.headers['X-Response-Time'] = f'{duration:.3f}s'

        # 构建日志消息
        log_msg = f"◀ {request.method} {request.path} - {response.status_code} ({duration:.3f}s)"

        # 记录响应信息
        logger.info(
            log_msg,
            extra={
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration': duration,
                'response_size': response.content_length,
                'ip': request.remote_addr
            }
        )

        return response
