"""
健康检查路由

提供服务健康状态检查端点
"""

from datetime import datetime
from flask import jsonify
from src.backend.api.utils.response import APIResponse
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_health_routes(app):
    """
    初始化健康检查路由

    Args:
        app: Flask 应用实例
    """

    @app.route('/api/v1/health', endpoint='health_check_v1')
    def health_check():
        """
        基础健康检查

        返回服务的基本健康状态
        """
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })

    @app.route('/api/v1/health/detailed', endpoint='health_check_detailed_v1')
    def detailed_health_check():
        """
        详细健康检查

        返回各个服务的详细健康状态
        """
        health_status = {
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': {}
        }

        # 检查 B站 API 连接
        try:
            from src.backend.services.bilibili.bilibili_service import BilibiliService
            bilibili_service = BilibiliService()
            # 简单检查服务是否可初始化
            health_status['services']['bilibili_api'] = 'healthy'
        except Exception as e:
            health_status['services']['bilibili_api'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
            logger.warning(f"B站 API health check failed: {str(e)}")

        # 检查 AI 服务
        try:
            from src.config import Config
            if Config.OPENAI_API_KEY and Config.OPENAI_API_BASE:
                health_status['services']['ai_service'] = 'healthy'
            else:
                health_status['services']['ai_service'] = 'not_configured'
        except Exception as e:
            health_status['services']['ai_service'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
            logger.warning(f"AI service health check failed: {str(e)}")

        # 检查缓存服务
        try:
            from src.config import Config
            if Config.CACHE_ENABLED:
                health_status['services']['cache'] = 'healthy'
            else:
                health_status['services']['cache'] = 'disabled'
        except Exception as e:
            health_status['services']['cache'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
            logger.warning(f"Cache service health check failed: {str(e)}")

        # 根据服务状态设置 HTTP 状态码
        status_code = 200 if health_status['status'] == 'healthy' else 503

        return jsonify(health_status), status_code
