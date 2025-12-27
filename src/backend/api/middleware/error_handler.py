"""
全局错误处理中间件

统一处理所有异常，返回标准格式的错误响应
"""

from flask import jsonify
from typing import Tuple, Dict, Any
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorHandler:
    """全局错误处理器"""

    def __init__(self, app):
        """
        初始化错误处理器

        Args:
            app: Flask 应用实例
        """
        self.app = app
        self._register_error_handlers()

    def _register_error_handlers(self):
        """注册错误处理器"""

        # 处理所有未捕获的异常
        @self.app.errorhandler(Exception)
        def handle_error(error):
            return self._handle_exception(error)

        # 处理 404 错误
        @self.app.errorhandler(404)
        def handle_404(error):
            return jsonify({
                'success': False,
                'error': '请求的资源不存在',
                'error_code': 'NOT_FOUND'
            }), 404

        # 处理 500 错误
        @self.app.errorhandler(500)
        def handle_500(error):
            return jsonify({
                'success': False,
                'error': '服务器内部错误',
                'error_code': 'INTERNAL_ERROR'
            }), 500

        # 处理 400 错误
        @self.app.errorhandler(400)
        def handle_400(error):
            return jsonify({
                'success': False,
                'error': str(error) or '请求参数错误',
                'error_code': 'BAD_REQUEST'
            }), 400

        # 处理 405 错误
        @self.app.errorhandler(405)
        def handle_405(error):
            return jsonify({
                'success': False,
                'error': '不支持的请求方法',
                'error_code': 'METHOD_NOT_ALLOWED'
            }), 405

    def _handle_exception(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """
        处理所有异常

        Args:
            error: 异常对象

        Returns:
            (响应字典, HTTP状态码)
        """
        # 记录错误日志
        logger.error(f"Unhandled exception: {type(error).__name__}: {str(error)}", exc_info=True)

        # 返回错误响应
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'error_code': 'INTERNAL_ERROR',
            'details': str(error) if self.app.debug else None
        }), 500


class APIException(Exception):
    """API 异常基类"""

    def __init__(self, message: str, error_code: str = None, status_code: int = 400):
        """
        初始化 API 异常

        Args:
            message: 错误消息
            error_code: 错误代码
            status_code: HTTP 状态码
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or 'API_ERROR'
        self.status_code = status_code

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'success': False,
            'error': self.message,
            'error_code': self.error_code
        }


class ValidationError(APIException):
    """参数验证错误"""

    def __init__(self, message: str):
        super().__init__(message, error_code='VALIDATION_ERROR', status_code=400)


class AuthenticationError(APIException):
    """认证错误"""

    def __init__(self, message: str = '认证失败'):
        super().__init__(message, error_code='AUTHENTICATION_ERROR', status_code=401)


class RateLimitError(APIException):
    """限流错误"""

    def __init__(self, message: str = '请求过于频繁，请稍后再试'):
        super().__init__(message, error_code='RATE_LIMIT_EXCEEDED', status_code=429)


class NotFoundError(APIException):
    """资源未找到错误"""

    def __init__(self, message: str = '资源不存在'):
        super().__init__(message, error_code='NOT_FOUND', status_code=404)
