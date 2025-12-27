"""
视频相关路由

提供视频信息、字幕、弹幕、评论等接口
"""

from flask import request
from src.backend.api.utils.response import APIResponse
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_video_routes(app, bilibili_service):
    """
    初始化视频相关路由

    Args:
        app: Flask 应用实例
        bilibili_service: B站服务实例
    """

    @app.route('/api/v1/video/<bvid>/info', methods=['GET'], endpoint='get_video_info_v1')
    def get_video_info(bvid):
        """
        获取视频基本信息

        Args:
            bvid: 视频 BVID

        Returns:
            视频信息
        """
        try:
            logger.info(f"获取视频信息: {bvid}")

            result = bilibili_service.run_async(
                bilibili_service.video.get_info(bvid)
            )

            if not result['success']:
                return APIResponse.error(result['error'], status_code=404)

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return APIResponse.error("获取视频信息失败")

    @app.route('/api/v1/video/<bvid>/subtitles', methods=['GET'], endpoint='get_video_subtitles_v1')
    def get_video_subtitles(bvid):
        """
        获取视频字幕

        Args:
            bvid: 视频 BVID

        Returns:
            字幕数据
        """
        try:
            logger.info(f"获取视频字幕: {bvid}")

            result = bilibili_service.run_async(
                bilibili_service.video.get_subtitles(bvid)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"获取字幕失败: {str(e)}")
            return APIResponse.error("获取字幕失败")

    @app.route('/api/v1/video/<bvid>/danmaku', methods=['GET'], endpoint='get_video_danmaku_v1')
    def get_video_danmaku(bvid):
        """
        获取视频弹幕

        Args:
            bvid: 视频 BVID
            limit: 限制数量（查询参数，默认 1000）

        Returns:
            弹幕数据
        """
        try:
            limit = request.args.get('limit', 1000, type=int)
            limit = min(max(1, limit), 5000)  # 限制在 1-5000 之间

            logger.info(f"获取视频弹幕: {bvid}, limit={limit}")

            result = bilibili_service.run_async(
                bilibili_service.video.get_danmaku(bvid, limit=limit)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"获取弹幕失败: {str(e)}")
            return APIResponse.error("获取弹幕失败")

    @app.route('/api/v1/video/<bvid>/comments', methods=['GET'], endpoint='get_video_comments_v1')
    def get_video_comments(bvid):
        """
        获取视频评论

        Args:
            bvid: 视频 BVID
            limit: 限制数量（查询参数，默认 50）

        Returns:
            评论数据
        """
        try:
            limit = request.args.get('limit', 50, type=int)
            limit = min(max(1, limit), 200)  # 限制在 1-200 之间

            logger.info(f"获取视频评论: {bvid}, limit={limit}")

            result = bilibili_service.run_async(
                bilibili_service.video.get_comments(bvid, target_count=limit)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"获取评论失败: {str(e)}")
            return APIResponse.error("获取评论失败")

    @app.route('/api/v1/video/<bvid>/stats', methods=['GET'], endpoint='get_video_stats_v1')
    def get_video_stats(bvid):
        """
        获取视频统计数据

        Args:
            bvid: 视频 BVID

        Returns:
            视频统计数据
        """
        try:
            logger.info(f"获取视频统计: {bvid}")

            result = bilibili_service.run_async(
                bilibili_service.video.get_stats(bvid)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"获取统计数据失败: {str(e)}")
            return APIResponse.error("获取统计数据失败")

    @app.route('/api/v1/video/<bvid>/related', methods=['GET'], endpoint='get_video_related_v1')
    def get_video_related(bvid):
        """
        获取相关推荐视频

        Args:
            bvid: 视频 BVID

        Returns:
            相关视频列表
        """
        try:
            logger.info(f"获取相关视频: {bvid}")

            result = bilibili_service.run_async(
                bilibili_service.video.get_related(bvid)
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"获取相关视频失败: {str(e)}")
            return APIResponse.error("获取相关视频失败")

    @app.route('/api/v1/video/<bvid>/frames', methods=['GET'], endpoint='get_video_frames_v1')
    def get_video_frames(bvid):
        """
        提取视频关键帧

        Args:
            bvid: 视频 BVID
            max_frames: 最大帧数（查询参数，可选）
            interval: 间隔秒数（查询参数，可选）

        Returns:
            视频帧数据
        """
        try:
            max_frames = request.args.get('max_frames', type=int)
            interval = request.args.get('interval', type=int)

            logger.info(f"提取视频帧: {bvid}, max_frames={max_frames}, interval={interval}")

            result = bilibili_service.run_async(
                bilibili_service.video.extract_frames(
                    bvid,
                    max_frames=max_frames,
                    interval=interval
                )
            )

            if not result['success']:
                return APIResponse.error(result['error'])

            return APIResponse.success(result['data'])

        except Exception as e:
            logger.error(f"提取视频帧失败: {str(e)}")
            return APIResponse.error("提取视频帧失败")
