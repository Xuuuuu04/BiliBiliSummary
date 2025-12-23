"""
API 路由模块
提供所有 RESTful API 接口
"""
from flask import Blueprint

# 创建 API 蓝图
api_bp = Blueprint('api', __name__)

# 导入所有路由模块
from .routes import settings, research, analyze, bilibili, user

__all__ = ['api_bp']
