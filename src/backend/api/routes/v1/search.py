"""
搜索相关路由

提供视频、用户、专栏搜索接口
"""

from flask import request
from src.backend.api.utils.response import APIResponse
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_search_routes(app, bilibili_service):
    """
    初始化搜索相关路由

    Args:
        app: Flask 应用实例
        bilibili_service: B站服务实例
    """

    @app.route('/api/v1/search/videos', methods=['GET'])
    def search_videos():
        """搜索视频"""
        try:
            keyword = request.args.get('keyword', '')
            limit = request.args.get('limit', 20, type=int)
            limit = min(max(1, limit), 100)

            if not keyword:
                return APIResponse.error("缺少搜索关键词")

            result = bilibili_service.run_async(
                bilibili_service.search.search_videos(keyword, limit=limit)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"搜索视频失败: {str(e)}")
            return APIResponse.error("搜索视频失败")

    @app.route('/api/v1/search/users', methods=['GET'])
    def search_users():
        """搜索用户"""
        try:
            keyword = request.args.get('keyword', '')
            limit = request.args.get('limit', 5, type=int)
            limit = min(max(1, limit), 50)

            if not keyword:
                return APIResponse.error("缺少搜索关键词")

            result = bilibili_service.run_async(
                bilibili_service.search.search_users(keyword, limit=limit)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"搜索用户失败: {str(e)}")
            return APIResponse.error("搜索用户失败")

    @app.route('/api/v1/search/articles', methods=['GET'])
    def search_articles():
        """搜索专栏"""
        try:
            keyword = request.args.get('keyword', '')
            limit = request.args.get('limit', 5, type=int)
            limit = min(max(1, limit), 50)

            if not keyword:
                return APIResponse.error("缺少搜索关键词")

            result = bilibili_service.run_async(
                bilibili_service.search.search_articles(keyword, limit=limit)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"搜索专栏失败: {str(e)}")
            return APIResponse.error("搜索专栏失败")
