"""
用户相关路由

提供用户信息、投稿、动态等接口
"""

from flask import request
from src.backend.api.utils.response import APIResponse
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_user_routes(app, bilibili_service):
    """
    初始化用户相关路由

    Args:
        app: Flask 应用实例
        bilibili_service: B站服务实例
    """

    @app.route('/api/v1/user/<uid>/info', methods=['GET'])
    def get_user_info(uid):
        """获取用户信息"""
        try:
            result = bilibili_service.run_async(
                bilibili_service.user.get_info(int(uid))
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return APIResponse.error("获取用户信息失败")

    @app.route('/api/v1/user/<uid>/videos', methods=['GET'])
    def get_user_videos(uid):
        """获取用户投稿"""
        try:
            limit = request.args.get('limit', 10, type=int)
            limit = min(max(1, limit), 50)

            result = bilibili_service.run_async(
                bilibili_service.user.get_recent_videos(int(uid), limit=limit)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"获取用户投稿失败: {str(e)}")
            return APIResponse.error("获取用户投稿失败")

    @app.route('/api/v1/user/<uid>/dynamics', methods=['GET'])
    def get_user_dynamics(uid):
        """获取用户动态"""
        try:
            limit = request.args.get('limit', 10, type=int)
            limit = min(max(1, limit), 50)

            result = bilibili_service.run_async(
                bilibili_service.user.get_user_dynamics(int(uid), limit=limit)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"获取用户动态失败: {str(e)}")
            return APIResponse.error("获取用户动态失败")
