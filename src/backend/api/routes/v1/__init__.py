"""
API v1 路由模块

包含所有 v1 版本的 API 路由
"""

def init_routes(app, bilibili_service, ai_service=None):
    """
    初始化所有 v1 路由

    Args:
        app: Flask 应用实例
        bilibili_service: B站服务实例
        ai_service: AI 服务实例（可选）
    """
    from . import health, video, user, search, hot, rank

    # 初始化各个路由模块
    health.init_health_routes(app)
    video.init_video_routes(app, bilibili_service)
    user.init_user_routes(app, bilibili_service)
    search.init_search_routes(app, bilibili_service)
    hot.init_hot_routes(app, bilibili_service)
    rank.init_rank_routes(app, bilibili_service)

    # 如果提供了 AI 服务，初始化 AI 路由（如果 ai 模块存在）
    if ai_service:
        try:
            from . import ai
            ai.init_ai_routes(app, ai_service, bilibili_service)
        except ImportError:
            # AI 路由模块不存在，跳过
            pass
