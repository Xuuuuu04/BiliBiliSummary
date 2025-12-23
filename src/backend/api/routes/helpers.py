"""
辅助路由模块
提供静态资源和首页服务
"""
import os
from flask import send_from_directory


def init_helper_routes(app):
    """
    初始化辅助路由

    Args:
        app: Flask 应用实例
    """

    @app.route('/')
    def index():
        """返回首页"""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """托管资源文件"""
        return send_from_directory('assets', filename)
