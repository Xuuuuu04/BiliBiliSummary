"""
热门内容路由

提供热门视频、热词图鉴等接口
"""

from flask import request
from src.backend.api.utils.response import APIResponse
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_hot_routes(app, bilibili_service):
    """
    初始化热门内容路由

    Args:
        app: Flask 应用实例
        bilibili_service: B站服务实例
    """

    @app.route('/api/v1/hot/videos', methods=['GET'])
    def get_hot_videos():
        """获取热门视频"""
        try:
            pn = request.args.get('page', 1, type=int)
            ps = request.args.get('page_size', 20, type=int)
            ps = min(max(1, ps), 100)

            # 使用 hot service（如果已创建）
            # 否则返回提示信息
            try:
                from src.backend.services.bilibili.hot_service import HotService
                hot_service = HotService(credential=bilibili_service.credential)
                result = bilibili_service.run_async(
                    hot_service.get_hot_videos(pn=pn, ps=ps)
                )

                if not result['success']:
                    return APIResponse.error(result['error'])

                return APIResponse.success(result['data'])
            except ImportError:
                # 如果 hot_service 还未创建，返回提示
                return APIResponse.error("热门内容服务正在开发中")

        except Exception as e:
            logger.error(f"获取热门视频失败: {str(e)}")
            return APIResponse.error("获取热门视频失败")

    @app.route('/api/v1/hot/buzzwords', methods=['GET'])
    def get_hot_buzzwords():
        """获取热词图鉴"""
        try:
            page_num = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 20, type=int)
            page_size = min(max(1, page_size), 100)

            try:
                from src.backend.services.bilibili.hot_service import HotService
                hot_service = HotService(credential=bilibili_service.credential)
                result = bilibili_service.run_async(
                    hot_service.get_hot_buzzwords(page_num=page_num, page_size=page_size)
                )

                if not result['success']:
                    return APIResponse.error(result['error'])

                return APIResponse.success(result['data'])
            except ImportError:
                return APIResponse.error("热词图鉴服务正在开发中")

        except Exception as e:
            logger.error(f"获取热词图鉴失败: {str(e)}")
            return APIResponse.error("获取热词图鉴失败")
