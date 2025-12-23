"""
B站用户服务模块
提供用户信息、投稿视频等功能
"""
from bilibili_api import user
from typing import Dict
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """
    B站用户服务类

    提供用户相关的功能：信息获取、最近投稿等
    """

    def __init__(self, credential=None):
        """
        初始化用户服务

        Args:
            credential: B站登录凭据（可选）
        """
        self.credential = credential

    async def get_info(self, uid: int) -> Dict:
        """
        获取用户基本信息

        Args:
            uid: 用户UID

        Returns:
            {'success': bool, 'data': {用户信息}} 或 {'success': False, 'error': str}
        """
        try:
            u = user.User(uid=uid, credential=self.credential)
            info = await u.get_user_info()
            # 获取粉丝数等关系数据
            rel = await u.get_relation_info()
            return {
                'success': True,
                'data': {
                    'mid': info.get('mid'),
                    'name': info.get('name'),
                    'face': info.get('face'),
                    'sign': info.get('sign'),
                    'level': info.get('level'),
                    'follower': rel.get('follower', 0),
                    'official': info.get('official', {}).get('title')
                }
            }
        except Exception as e:
            return {'success': False, 'error': f'获取用户信息失败: {str(e)}'}

    async def get_recent_videos(self, uid: int, limit: int = 10) -> Dict:
        """
        获取用户最近投稿

        Args:
            uid: 用户UID
            limit: 获取视频数量

        Returns:
            {'success': bool, 'data': [视频列表]} 或 {'success': False, 'error': str}
        """
        try:
            u = user.User(uid=uid, credential=self.credential)
            # get_videos 返回的是一个生成器或者分页对象，通常直接调用拿到第一页
            # 注意：bilibili-api 的 user.get_videos 接口行为可能随版本变动，这里假设它返回标准结构
            res = await u.get_videos(ps=limit)
            v_list = res.get('list', {}).get('vlist', [])

            processed = []
            for v in v_list:
                processed.append({
                    'bvid': v.get('bvid'),
                    'title': v.get('title'),
                    'pic': v.get('pic'),
                    'play': v.get('play'),
                    'length': v.get('length')
                })
            return {'success': True, 'data': processed}
        except Exception as e:
            return {'success': False, 'error': f'获取用户投稿失败: {str(e)}'}
