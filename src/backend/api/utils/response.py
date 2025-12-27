"""
统一 API 响应格式工具

提供标准化的 API 响应格式
"""

from typing import Any, Optional, Dict
from flask import jsonify, Response


class APIResponse:
    """统一 API 响应格式"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = None,
        meta: Dict[str, Any] = None
    ) -> Response:
        """
        成功响应

        Args:
            data: 响应数据
            message: 提示消息
            meta: 元数据（分页、统计等）

        Returns:
            Flask JSON 响应
        """
        response = {
            'success': True,
            'data': data
        }

        if message:
            response['message'] = message

        if meta:
            response['meta'] = meta

        return jsonify(response), 200

    @staticmethod
    def created(
        data: Any = None,
        message: str = "资源创建成功"
    ) -> Response:
        """
        201 Created 响应

        Args:
            data: 响应数据
            message: 提示消息

        Returns:
            Flask JSON 响应（201）
        """
        return jsonify({
            'success': True,
            'data': data,
            'message': message
        }), 201

    @staticmethod
    def no_content() -> Response:
        """
        204 No Content 响应

        Returns:
            空响应（204）
        """
        return '', 204

    @staticmethod
    def error(
        error_msg: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        status_code: int = 400
    ) -> Response:
        """
        错误响应

        Args:
            error_msg: 错误消息
            error_code: 错误代码
            details: 错误详情
            status_code: HTTP 状态码

        Returns:
            Flask JSON 响应
        """
        response = {
            'success': False,
            'error': error_msg
        }

        if error_code:
            response['error_code'] = error_code

        if details:
            response['details'] = details

        return jsonify(response), status_code

    @staticmethod
    def paginated(
        data: list,
        page: int,
        page_size: int,
        total: int,
        **kwargs
    ) -> Response:
        """
        分页响应

        Args:
            data: 数据列表
            page: 当前页码
            page_size: 每页数量
            total: 总数
            **kwargs: 其他元数据

        Returns:
            Flask JSON 响应
        """
        total_pages = (total + page_size - 1) // page_size

        meta = {
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }

        # 添加额外的元数据
        meta.update(kwargs)

        return APIResponse.success(data=data, meta=meta)

    @staticmethod
    def validation_error(errors: Dict[str, Any]) -> Response:
        """
        参数验证错误响应

        Args:
            errors: 验证错误字典

        Returns:
            Flask JSON 响应（400）
        """
        return APIResponse.error(
            error_msg='请求参数验证失败',
            error_code='VALIDATION_ERROR',
            details=errors,
            status_code=400
        )

    @staticmethod
    def not_found(resource: str = "资源") -> Response:
        """
        404 Not Found 响应

        Args:
            resource: 资源名称

        Returns:
            Flask JSON 响应（404）
        """
        return APIResponse.error(
            error_msg=f'{resource}不存在',
            error_code='NOT_FOUND',
            status_code=404
        )

    @staticmethod
    def unauthorized(message: str = "未授权访问") -> Response:
        """
        401 Unauthorized 响应

        Args:
            message: 错误消息

        Returns:
            Flask JSON 响应（401）
        """
        return APIResponse.error(
            error_msg=message,
            error_code='UNAUTHORIZED',
            status_code=401
        )

    @staticmethod
    def forbidden(message: str = "禁止访问") -> Response:
        """
        403 Forbidden 响应

        Args:
            message: 错误消息

        Returns:
            Flask JSON 响应（403）
        """
        return APIResponse.error(
            error_msg=message,
            error_code='FORBIDDEN',
            status_code=403
        )

    @staticmethod
    def rate_limit_exceeded(retry_after: int = None) -> Response:
        """
        429 Too Many Requests 响应

        Args:
            retry_after: 重试等待时间（秒）

        Returns:
            Flask JSON 响应（429）
        """
        details = {}
        if retry_after:
            details['retry_after'] = retry_after

        return APIResponse.error(
            error_msg='请求过于频繁，请稍后再试',
            error_code='RATE_LIMIT_EXCEEDED',
            details=details,
            status_code=429
        )

    @staticmethod
    def internal_error(message: str = "服务器内部错误") -> Response:
        """
        500 Internal Server Error 响应

        Args:
            message: 错误消息

        Returns:
            Flask JSON 响应（500）
        """
        return APIResponse.error(
            error_msg=message,
            error_code='INTERNAL_ERROR',
            status_code=500
        )
