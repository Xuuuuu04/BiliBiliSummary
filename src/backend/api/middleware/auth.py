"""
API 认证中间件

支持 API Key、JWT Token 和 Session Cookie 多种认证方式
"""

from flask import request, g
from src.config import Config
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class AuthMiddleware:
    """API 认证中间件"""

    def __init__(self, app=None):
        """
        初始化认证中间件

        Args:
            app: Flask 应用实例（可选）
        """
        self.app = app
        # 公开路径（不需要认证）
        self.public_paths = [
            '/api/v1/health',
            '/api/v1/auth/login',
            '/docs',
            '/openapi.yaml',
            '/static'
        ]

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        初始化 Flask 应用

        Args:
            app: Flask 应用实例
        """
        self.app = app
        app.before_request(self._authenticate)

    def is_public_path(self, path: str) -> bool:
        """
        检查是否为公开路径

        Args:
            path: 请求路径

        Returns:
            是否为公开路径
        """
        return any(path.startswith(p) for p in self.public_paths)

    def _authenticate(self):
        """
        认证请求（before_request 钩子）

        检查请求是否包含有效的认证信息
        """
        # 跳过公开路径
        if self.is_public_path(request.path):
            return

        # 跳过 OPTIONS 请求（CORS 预检）
        if request.method == 'OPTIONS':
            return

        # 尝试多种认证方式
        auth_result = None

        # 1. 检查 API Key
        api_key = request.headers.get(Config.API_KEY_HEADER)
        if api_key:
            auth_result = self._validate_api_key(api_key)
            if auth_result:
                g.auth_type = 'api_key'
                g.auth_info = auth_result
                return

        # 2. 检查 Bearer Token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_result = self._validate_token(token)
            if auth_result:
                g.auth_type = 'bearer_token'
                g.auth_info = auth_result
                return

        # 3. 检查 Session Cookie (Web UI)
        session_id = request.cookies.get('session_id')
        if session_id:
            auth_result = self._validate_session(session_id)
            if auth_result:
                g.auth_type = 'session'
                g.auth_info = auth_result
                return

        # 4. 如果没有提供认证信息，记录为匿名用户（可选）
        # 如果需要强制认证，可以返回 401 错误
        # 目前允许匿名访问，但在日志中记录
        g.auth_type = 'anonymous'
        g.auth_info = None
        logger.debug(f"Anonymous access to {request.path}")

    def _validate_api_key(self, api_key: str) -> dict:
        """
        验证 API Key

        Args:
            api_key: API Key

        Returns:
            认证信息字典，验证失败返回 None
        """
        # TODO: 实现实际的 API Key 验证逻辑
        # 可以从数据库或配置文件中验证

        # 示例：简单的硬编码验证（不推荐生产环境使用）
        valid_api_keys = {
            'test-key-123': {'user_id': 'test_user', 'tier': 'default'},
            'premium-key-456': {'user_id': 'premium_user', 'tier': 'premium'}
        }

        if api_key in valid_api_keys:
            return valid_api_keys[api_key]

        logger.warning(f"Invalid API Key: {api_key[:10]}***")
        return None

    def _validate_token(self, token: str) -> dict:
        """
        验证 JWT Token

        Args:
            token: JWT Token

        Returns:
            认证信息字典，验证失败返回 None
        """
        # TODO: 实现 JWT Token 验证逻辑
        # 使用 PyJWT 库验证签名和过期时间

        try:
            import jwt
            payload = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            return {
                'user_id': payload.get('user_id'),
                'tier': payload.get('tier', 'default')
            }
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return None

    def _validate_session(self, session_id: str) -> dict:
        """
        验证 Session

        Args:
            session_id: Session ID

        Returns:
            认证信息字典，验证失败返回 None
        """
        # TODO: 实现 Session 验证逻辑
        # 可以从 Flask Session 或 Redis 中验证

        # 示例：简单的验证（生产环境应使用 Flask-Session 或 Redis）
        if session_id and len(session_id) > 10:
            return {
                'user_id': 'session_user',
                'tier': 'default'
            }

        return None

    def add_public_path(self, path: str):
        """
        添加公开路径

        Args:
            path: 公开路径
        """
        if path not in self.public_paths:
            self.public_paths.append(path)

    def remove_public_path(self, path: str):
        """
        移除公开路径

        Args:
            path: 要移除的路径
        """
        if path in self.public_paths:
            self.public_paths.remove(path)
