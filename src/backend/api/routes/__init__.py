"""
路由模块初始化
注册所有 API 路由
"""
from .settings import init_settings_routes
from .research import init_research_routes
from .analyze import init_analyze_routes
from .bilibili import init_bilibili_routes
from .user import init_user_routes

__all__ = [
    'init_settings_routes',
    'init_research_routes',
    'init_analyze_routes',
    'init_bilibili_routes',
    'init_user_routes'
]
