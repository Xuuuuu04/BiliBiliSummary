"""
统一错误处理模块

提供标准化的错误响应格式和异常类
"""
from typing import Dict, Any, Optional
from functools import wraps
from flask import jsonify


class BaseAppException(Exception):
    """应用基础异常类"""

    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None, status_code: int = 500):
        """
        初始化应用异常

        Args:
            message: 错误消息（对用户友好的描述）
            error_code: 错误码（用于程序识别）
            details: 错误详细信息
            status_code: HTTP状态码
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code


class ValidationError(BaseAppException):
    """输入验证错误"""

    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(message, error_code="VALIDATION_ERROR", details=details, status_code=400)
        self.details['field'] = field


class NotFoundError(BaseAppException):
    """资源未找到错误"""

    def __init__(self, resource_type: str, resource_id: str = None):
        message = f"{resource_type} 不存在"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, error_code="NOT_FOUND", status_code=404)
        self.details['resource_type'] = resource_type
        self.details['resource_id'] = resource_id


class ExternalServiceError(BaseAppException):
    """外部服务错误"""

    def __init__(self, service_name: str, message: str = None):
        message = message or f"{service_name} 服务暂时不可用"
        super().__init__(message, error_code="EXTERNAL_SERVICE_ERROR", status_code=503)
        self.details['service'] = service_name


class ConfigurationError(BaseAppException):
    """配置错误"""

    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, error_code="CONFIGURATION_ERROR", status_code=500)
        if config_key:
            self.details['config_key'] = config_key


class ErrorResponse:
    """统一错误响应构建器"""

    @staticmethod
    def error(
        error_msg: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        status_code: int = 500
    ) -> tuple[Dict[str, Any], int]:
        """
        构建标准错误响应

        Args:
            error_msg: 错误消息
            error_code: 错误码
            details: 详细信息
            status_code: HTTP状态码

        Returns:
            (response_dict, status_code)
        """
        response = {
            'success': False,
            'error': error_msg,
        }

        if error_code:
            response['error_code'] = error_code

        if details:
            response['details'] = details

        return response, status_code

    @staticmethod
    def sse_error(error_msg: str, error_type: str = None) -> str:
        """
        构建SSE格式的错误响应

        Args:
            error_msg: 错误消息
            error_type: 错误类型

        Returns:
            SSE格式的错误消息
        """
        import json
        error_data = {
            'type': 'error',
            'error': error_msg
        }
        if error_type:
            error_data['error_type'] = error_type

        return f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    @staticmethod
    def from_exception(e: Exception) -> tuple[Dict[str, Any], int]:
        """
        从异常对象构建错误响应

        Args:
            e: 异常对象

        Returns:
            (response_dict, status_code)
        """
        if isinstance(e, BaseAppException):
            return ErrorResponse.error(
                error_msg=e.message,
                error_code=e.error_code,
                details=e.details,
                status_code=e.status_code
            )
        else:
            # 未预期的异常，返回通用错误信息（避免泄露内部实现）
            return ErrorResponse.error(
                error_msg="服务器内部错误",
                error_code="INTERNAL_ERROR",
                status_code=500
            )


def handle_errors(f):
    """
    路由错误处理装饰器

    自动捕获异常并返回标准格式的错误响应

    Usage:
        @app.route('/api/example')
        @handle_errors
        def example():
            # ...
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseAppException as e:
            # 已知的应用异常，返回标准格式
            response, status_code = ErrorResponse.from_exception(e)
            return jsonify(response), status_code
        except Exception as e:
            # 未预期的异常，记录日志并返回通用错误
            from src.backend.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"未处理的异常: {type(e).__name__}: {str(e)}")

            response, status_code = ErrorResponse.from_exception(e)
            return jsonify(response), status_code

    return wrapper


def sanitize_error_message(error: Exception) -> str:
    """
    过滤敏感信息后的错误消息

    移除文件路径、行号等可能泄露系统内部信息的敏感内容

    Args:
        error: 异常对象

    Returns:
        过滤后的错误消息
    """
    import re

    error_str = str(error)

    # 移除文件路径 (如 "File 'path/to/file.py'")
    error_str = re.sub(r"File '.*?'", '', error_str)

    # 移除行号 (如 ", line 123")
    error_str = re.sub(r", line \d+", '', error_str)

    return error_str.strip()
