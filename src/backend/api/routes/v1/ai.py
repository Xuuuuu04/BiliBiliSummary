"""
AI相关路由

提供AI分析、智能问答等接口（预留）
"""

from flask import request
from src.backend.api.utils.response import APIResponse
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_ai_routes(app, ai_service, bilibili_service):
    """
    初始化 AI 相关路由

    Args:
        app: Flask 应用实例
        ai_service: AI 服务实例
        bilibili_service: B站服务实例
    """

    @app.route('/api/v1/ai/chat', methods=['POST'], endpoint='ai_chat_v1')
    def ai_chat():
        """
        AI 对话接口

        接收用户问题并返回 AI 回答
        """
        # 预留接口，暂未实现
        return APIResponse.error("AI 聊天功能暂未实现", status_code=501)

    @app.route('/api/v1/ai/analyze', methods=['POST'], endpoint='ai_analyze_v1')
    def ai_analyze():
        """
        AI 分析接口

        对视频内容进行 AI 分析
        """
        # 预留接口，暂未实现
        return APIResponse.error("AI 分析功能暂未实现", status_code=501)

    logger.info("AI 路由已注册（v1，预留接口）")
