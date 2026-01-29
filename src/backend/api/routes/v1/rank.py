"""
排行榜路由

提供各分区视频排行榜接口
"""

from flask import request
from src.backend.api.utils.response import APIResponse
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_rank_routes(app, bilibili_service):
    """
    初始化排行榜路由

    Args:
        app: Flask 应用实例
        bilibili_service: B站服务实例
    """

    @app.route('/api/v1/rank/videos', methods=['GET'])
    def get_rank_videos():
        """获取全站排行榜"""
        try:
            day = request.args.get('day', 3, type=int)
            day = 3 if day == 3 else 7  # 仅支持 3 天或 7 天

            try:
                from src.backend.services.bilibili.rank_service import RankService
                rank_service = RankService(credential=bilibili_service.credential)
                result = bilibili_service.run_async(
                    rank_service.get_rank_videos(type_='all', day=day)
                )

                if not result['success']:
                    return APIResponse.error(result['error'])

                return APIResponse.success(result['data'])
            except ImportError:
                return APIResponse.error("排行榜服务正在开发中")

        except Exception as e:
            logger.error(f"获取排行榜失败: {str(e)}")
            return APIResponse.error("获取排行榜失败")

    @app.route('/api/v1/rank/videos/<type_>', methods=['GET'])
    def get_rank_videos_by_type(type_):
        """获取指定分区排行榜"""
        try:
            day = request.args.get('day', 3, type=int)
            day = 3 if day == 3 else 7

            try:
                from src.backend.services.bilibili.rank_service import RankService
                rank_service = RankService(credential=bilibili_service.credential)
                result = bilibili_service.run_async(
                    rank_service.get_rank_videos(type_=type_, day=day)
                )

                if not result['success']:
                    return APIResponse.error(result['error'])

                return APIResponse.success(result['data'])
            except ImportError:
                return APIResponse.error("排行榜服务正在开发中")

        except Exception as e:
            logger.error(f"获取分区排行榜失败: {str(e)}")
            return APIResponse.error("获取分区排行榜失败")
