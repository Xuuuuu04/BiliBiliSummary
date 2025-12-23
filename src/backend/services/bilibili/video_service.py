"""
B站视频服务模块
提供视频信息、字幕、弹幕、评论、统计等功能
"""
import asyncio
import aiohttp
import numpy as np
import cv2
import base64
from bilibili_api import video, comment
from typing import Dict, List, Optional
from src.config import Config
from src.backend.utils.logger import get_logger
from src.backend.utils.bilibili_helpers import (
    format_duration,
    calculate_optimal_frame_params,
    smart_sample_danmaku,
    smart_sample_comments,
    get_next_offset_from_comment_response
)

logger = get_logger(__name__)


class VideoService:
    """
    B站视频服务类

    提供视频相关的所有功能：信息获取、字幕、弹幕、评论、统计、相关视频、热门推荐、视频帧提取
    """

    def __init__(self, credential=None):
        """
        初始化视频服务

        Args:
            credential: B站登录凭据（可选）
        """
        self.credential = credential

    async def get_info(self, bvid: str) -> Dict:
        """
        获取视频基本信息

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': {视频信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            duration = info.get('duration', 0)

            return {
                'success': True,
                'data': {
                    'bvid': info.get('bvid'),
                    'title': info.get('title'),
                    'desc': info.get('desc'),
                    'duration': duration,
                    'duration_str': format_duration(duration),
                    'author': info.get('owner', {}).get('name'),
                    'view': info.get('stat', {}).get('view'),
                    'like': info.get('stat', {}).get('like'),
                    'cover': info.get('pic'),
                    'pubdate': info.get('pubdate'),
                    'aid': info.get('aid')
                }
            }
        except Exception as e:
            return {'success': False, 'error': f'获取视频信息失败: {str(e)}'}

    async def get_subtitles(self, bvid: str) -> Dict:
        """
        获取视频字幕

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': {字幕信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            cid = info.get('cid')
            if not cid:
                return {'success': True, 'data': {'has_subtitle': False, 'subtitles': []}}

            subtitle_info = await v.get_subtitle(cid=cid)
            if not subtitle_info or 'subtitles' not in subtitle_info or not subtitle_info['subtitles']:
                return {'success': True, 'data': {'has_subtitle': False, 'subtitles': []}}

            subtitles_list = subtitle_info['subtitles']
            target_sub = next((s for s in subtitles_list if 'zh' in s['lan']), subtitles_list[0])
            subtitle_url = 'https:' + target_sub['subtitle_url']

            async with aiohttp.ClientSession() as session:
                async with session.get(subtitle_url) as resp:
                    subtitle_data = await resp.json()

            subtitle_text = [item.get('content', '').strip() for item in subtitle_data.get('body', []) if item.get('content', '').strip()]

            return {
                'success': True,
                'data': {
                    'has_subtitle': True,
                    'subtitles': subtitle_text,
                    'full_text': '\n'.join(subtitle_text),
                    'language': target_sub.get('lan_doc', '中文'),
                    'is_ai': 'AI' in target_sub.get('lan_doc', '')
                }
            }
        except Exception as e:
            return {'success': False, 'error': f'获取字幕失败: {str(e)}'}

    async def get_danmaku(self, bvid: str, limit: int = 1000) -> Dict:
        """
        获取视频弹幕

        Args:
            bvid: 视频BVID
            limit: 获取弹幕数量限制

        Returns:
            {'success': bool, 'data': {弹幕信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            # 检查凭据状态
            has_credential = self.credential is not None

            # 根据是否登录决定实际获取数量
            actual_limit = limit if has_credential else 100

            info = await v.get_info()
            duration = info.get('duration', 0)
            total_segments = (duration // 360) + 1

            all_danmaku_list = []
            segments_to_fetch = total_segments if has_credential else 1
            if segments_to_fetch > 10:
                segments_to_fetch = 10

            for i in range(segments_to_fetch):
                try:
                    danmaku_list = await v.get_danmakus(page_index=0, segment_index=i+1)
                    all_danmaku_list.extend(danmaku_list)
                    if len(all_danmaku_list) >= actual_limit * 1.5:
                        break
                except:
                    break

            if not all_danmaku_list:
                try:
                    all_danmaku_list = await v.get_danmakus(0)
                except:
                    pass

            danmaku_texts = smart_sample_danmaku(all_danmaku_list, actual_limit)
            return {
                'success': True,
                'data': {
                    'danmaku_count': len(danmaku_texts),
                    'danmakus': danmaku_texts,
                    'full_text': '\n'.join(danmaku_texts),
                    'has_credential': has_credential
                }
            }
        except Exception as e:
            return {'success': False, 'error': f'获取弹幕失败: {str(e)}'}

    async def get_comments(self, bvid: str, max_pages: int = 10, target_count: int = 100) -> Dict:
        """
        获取视频评论 (极致加固版：适配新版分页结构)

        Args:
            bvid: 视频BVID
            max_pages: 最大获取页数
            target_count: 目标评论数量

        Returns:
            {'success': bool, 'data': {评论信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            aid = info.get('aid')
            if not aid:
                return {'success': False, 'error': '无法获取视频aid'}

            has_credential = self.credential is not None
            # 深度研究模式下不建议开启地毯式抓取，见好就收
            actual_max_pages = max_pages if has_credential else 3
            actual_target = target_count if has_credential else 50

            all_comments_list = []
            seen_rpids = set()

            # 抓取逻辑：优先尝试热门，不再暴力补全
            def get_next_offset(res):
                cursor = res.get('cursor', {})
                # 新版结构在 pagination_reply 内部
                if 'pagination_reply' in cursor:
                    return cursor['pagination_reply'].get('next_offset', '')
                # 旧版可能直接在 cursor 下
                return cursor.get('next_offset', '')

            # --- 阶段 1：获取热门/置顶 ---
            try:
                # 热门模式 (Mode 3 通常代表热度排序)
                res_hot = await comment.get_comments_lazy(
                    aid,
                    comment.CommentResourceType.VIDEO,
                    order=comment.OrderType.LIKE,
                    credential=self.credential
                )
                replies = res_hot.get('replies') or []
                # 包含置顶
                if res_hot.get('top', {}).get('reply'):
                    replies.insert(0, res_hot['top']['reply'])

                for r in replies:
                    if r and r.get('rpid') not in seen_rpids:
                        seen_rpids.add(r.get('rpid'))
                        all_comments_list.append(r)

                # 如果热门还有下一页，多抓几页热门
                curr_pag = get_next_offset(res_hot)
                page_count = 1
                while curr_pag and page_count < actual_max_pages and len(all_comments_list) < actual_target:
                    res_hot = await comment.get_comments_lazy(
                        aid,
                        comment.CommentResourceType.VIDEO,
                        offset=curr_pag,
                        order=comment.OrderType.LIKE,
                        credential=self.credential
                    )
                    replies = res_hot.get('replies') or []
                    if not replies:
                        break
                    for r in replies:
                        if r and r.get('rpid') not in seen_rpids:
                            seen_rpids.add(r.get('rpid'))
                            all_comments_list.append(r)
                    curr_pag = get_next_offset(res_hot)
                    page_count += 1
            except Exception as e:
                logger.warning(f"抓取热门评论失败: {e}")

            # 采样与处理
            sampled_comments = all_comments_list[:actual_target]
            processed_comments = []
            for cmt in sampled_comments:
                member = cmt.get('member', {})
                content = cmt.get('content', {})
                processed_comments.append({
                    'username': member.get('uname', '未知用户'),
                    'message': content.get('message', ''),
                    'like': cmt.get('like', 0),
                    'reply_count': cmt.get('rcount', 0),
                    'time': cmt.get('ctime', 0),
                    'user_level': member.get('level_info', {}).get('current_level', 0),
                    'mid': member.get('mid', ''),
                    'avatar': member.get('avatar', '')
                })

            logger.info(f"评论抓取完成: 实际获取 {len(processed_comments)} 条")

            return {
                'success': True,
                'data': {
                    'comments': processed_comments,
                    'total_count': len(all_comments_list),
                    'has_credential': has_credential
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_stats(self, bvid: str) -> Dict:
        """
        获取视频统计信息

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': {统计信息}} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            stats = info.get('stat', {})
            online_info = None
            try:
                online = await v.get_online()
                online_info = {'total': online.get('total', 0), 'web_count': online.get('count', 0)}
            except:
                pass

            return {
                'success': True,
                'data': {
                    'view': stats.get('view', 0),
                    'like': stats.get('like', 0),
                    'coin': stats.get('coin', 0),
                    'favorite': stats.get('favorite', 0),
                    'share': stats.get('share', 0),
                    'danmaku': stats.get('danmaku', 0),
                    'reply': stats.get('reply', 0),
                    'online': online_info
                }
            }
        except Exception as e:
            return {'success': False, 'error': f'获取统计信息失败: {str(e)}'}

    async def get_related(self, bvid: str) -> Dict:
        """
        获取相关推荐视频

        Args:
            bvid: 视频BVID

        Returns:
            {'success': bool, 'data': [相关视频列表]} 或 {'success': False, 'error': str}
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            related = await v.get_related()
            processed_related = []
            for item in related[:10]:
                processed_related.append({
                    'bvid': item.get('bvid'),
                    'title': item.get('title'),
                    'author': item.get('owner', {}).get('name'),
                    'cover': item.get('pic'),
                    'duration': item.get('duration'),
                    'duration_str': format_duration(item.get('duration', 0)),
                    'view': item.get('stat', {}).get('view', 0)
                })
            return {'success': True, 'data': processed_related}
        except Exception as e:
            return {'success': False, 'error': f'获取相关视频失败: {str(e)}'}

    async def get_cid(self, bvid: str) -> Optional[int]:
        """
        获取视频CID

        Args:
            bvid: 视频BVID

        Returns:
            CID，失败返回None
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            return info.get('cid')
        except:
            return None

    async def extract_frames(self, bvid: str, max_frames: Optional[int] = None, interval: Optional[int] = None) -> Dict:
        """
        快速提取视频关键帧

        Args:
            bvid: 视频BVID
            max_frames: 最大帧数（可选）
            interval: 提取间隔（可选）

        Returns:
            {'success': bool, 'data': {帧信息}} 或 {'success': False, 'error': str}
        """
        try:
            cid = await self.get_cid(bvid)
            if not cid:
                return {'success': False, 'error': '无法获取视频CID'}

            api_url = f"https://api.bilibili.com/x/player/videoshot?bvid={bvid}&cid={cid}"
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com'}

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as resp:
                    data = await resp.json()

            if data['code'] != 0 or 'data' not in data:
                return {'success': False, 'error': '该视频不支持预览图'}

            shot_data = data['data']
            image_urls = shot_data.get('image', [])
            if not image_urls:
                return {'success': False, 'error': '未找到预览图数据'}

            v_info = await self.get_info(bvid)
            duration = v_info['data'].get('duration', 600)
            target_frames, _ = calculate_optimal_frame_params(duration)
            if max_frames:
                target_frames = max_frames

            frames_base64 = []
            count = 0
            for img_url in image_urls[:2]:
                if count >= target_frames:
                    break
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                async with aiohttp.ClientSession() as session:
                    async with session.get(img_url) as resp:
                        if resp.status != 200:
                            continue
                        img_bytes = await resp.read()

                nparr = np.frombuffer(img_bytes, np.uint8)
                sprite_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if sprite_img is None:
                    continue

                s_h, s_w = sprite_img.shape[:2]
                cols = 10
                single_w = s_w // cols
                single_h = s_h // 10
                rows = s_h // single_h

                for r in range(rows):
                    for c in range(cols):
                        if count >= target_frames:
                            break
                        if (r * cols + c) % 3 != 0:
                            continue
                        y, x = r * single_h, c * single_w
                        crop = sprite_img[y:y+single_h, x:x+single_w]
                        _, buffer = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, 40])
                        frames_base64.append(base64.b64encode(buffer).decode('utf-8'))
                        count += 1

            return {
                'success': True,
                'data': {
                    'frames': frames_base64,
                    'frame_count': len(frames_base64),
                    'video_duration': duration
                }
            }
        except Exception as e:
            return {'success': False, 'error': f'提取视频帧失败: {str(e)}'}
