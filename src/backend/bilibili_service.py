import asyncio
import re
import os
import base64
import tempfile
from bilibili_api import video, Credential
from typing import Dict, List, Optional
import aiohttp
import cv2
from PIL import Image
import io
from src.config import Config


class BilibiliService:
    """B站视频服务类"""
    
    def __init__(self):
        self.credential = self._init_credential()

    def refresh_credential(self):
        """刷新登录凭据（从Config重新加载）"""
        self.credential = self._init_credential()
        print(f"[信息] B站服务凭据已刷新 (登录状态: {bool(self.credential)})")

    def _init_credential(self) -> Optional[Credential]:
        """初始化B站登录凭据"""
        try:
            if all([
                Config.BILIBILI_SESSDATA,
                Config.BILIBILI_BILI_JCT,
                Config.BILIBILI_DEDEUSERID
            ]):
                credential = Credential(
                    sessdata=Config.BILIBILI_SESSDATA,
                    bili_jct=Config.BILIBILI_BILI_JCT,
                    buvid3=Config.BILIBILI_BUVID3 or "",
                    dedeuserid=Config.BILIBILI_DEDEUSERID
                )
                print("[信息] 已加载B站登录凭据，将获取完整数据")
                return credential
            else:
                print("[信息] 未配置B站登录凭据，将获取有限的公开数据")
                return None
        except Exception as e:
            print(f"[警告] 初始化B站凭据失败: {e}")
            return None

    async def check_credential_valid(self) -> bool:
        """检查凭据是否有效"""
        if not self.credential:
            return False
        try:
            is_valid = await self.credential.check_valid()
            return is_valid
        except Exception as e:
            print(f"[警告] 检查凭据有效性失败: {e}")
            return False

    def _format_duration(self, seconds: int) -> str:
        """格式化秒数为 时:分:秒"""
        if not seconds: return "00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def _calculate_optimal_frame_params(self, duration_seconds: int) -> tuple[int, int]:
        """根据视频时长智能计算最优的帧提取参数"""
        if duration_seconds <= 120:
            max_frames = min(15, max(8, duration_seconds // 10))
            interval = max(5, duration_seconds // max_frames)
        elif duration_seconds <= 600:
            max_frames = 25
            interval = duration_seconds // max_frames
        elif duration_seconds <= 1800:
            max_frames = 40
            interval = duration_seconds // max_frames
        elif duration_seconds <= 3600:
            max_frames = 60
            interval = duration_seconds // max_frames
        else:
            max_frames = 80
            interval = max(60, duration_seconds // max_frames)
        max_frames = min(max_frames, 100)
        interval = max(5, interval)
        return max_frames, interval

    def _smart_sample_danmaku(self, danmaku_list: List, max_limit: int) -> List[str]:
        """智能采样弹幕"""
        if not danmaku_list: return []
        total_count = len(danmaku_list)
        if total_count <= max_limit:
            return [d.text for d in danmaku_list]
        step = total_count / max_limit
        return [danmaku_list[int(i * step)].text for i in range(max_limit)]

    def _smart_sample_comments(self, comments_list: List, target_count: int) -> List:
        """智能采样评论"""
        if not comments_list: return []
        total_count = len(comments_list)
        if total_count <= target_count: return comments_list
        step = total_count / target_count
        return [comments_list[int(i * step)] for i in range(target_count)]

    @staticmethod
    def extract_bvid(url: str) -> Optional[str]:
        """从B站链接中提取BVID"""
        patterns = [r'BV[a-zA-Z0-9]+', r'bilibili\.com/video/(BV[a-zA-Z0-9]+)', r'b23\.tv/(\w+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                bvid = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if bvid.startswith('BV'): return bvid
        return None

    async def get_video_info(self, bvid: str) -> Dict:
        """获取视频基本信息"""
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
                    'duration_str': self._format_duration(duration),
                    'author': info.get('owner', {}).get('name'),
                    'view': info.get('stat', {}).get('view'),
                    'like': info.get('stat', {}).get('like'),
                    'cover': info.get('pic'),
                    'pubdate': info.get('pubdate'),
                }
            }
        except Exception as e:
            return {'success': False, 'error': f'获取视频信息失败: {str(e)}'}

    async def get_video_subtitles(self, bvid: str) -> Dict:
        """获取视频字幕"""
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            cid = info.get('cid')
            if not cid: return {'success': True, 'data': {'has_subtitle': False, 'subtitles': []}}
            
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

    async def get_video_danmaku(self, bvid: str, limit: int = 1000) -> Dict:
        """获取视频弹幕"""
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            has_credential = await self.check_credential_valid()
            actual_limit = limit if has_credential else 100
            
            info = await v.get_info()
            duration = info.get('duration', 0)
            total_segments = (duration // 360) + 1
            
            all_danmaku_list = []
            segments_to_fetch = total_segments if has_credential else 1
            if segments_to_fetch > 10: segments_to_fetch = 10

            for i in range(segments_to_fetch):
                try:
                    danmaku_list = await v.get_danmakus(page_index=0, segment_index=i+1)
                    all_danmaku_list.extend(danmaku_list)
                    if len(all_danmaku_list) >= actual_limit * 1.5: break
                except: break

            if not all_danmaku_list:
                try: all_danmaku_list = await v.get_danmakus(0)
                except: pass

            danmaku_texts = self._smart_sample_danmaku(all_danmaku_list, actual_limit)
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

    async def get_video_comments(self, bvid: str, max_pages: int = 30, target_count: int = 500) -> Dict:
        """获取视频评论 (极致加固版：适配新版分页结构)"""
        try:
            from bilibili_api import comment
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            aid = info.get('aid')
            if not aid: return {'success': False, 'error': '无法获取视频aid'}

            has_credential = await self.check_credential_valid()
            actual_max_pages = max_pages if has_credential else 5
            actual_target = target_count if has_credential else 100

            all_comments_list = []
            seen_rpids = set()

            # 抓取逻辑：优先尝试热门，然后暴力补全
            # 兼容新旧结构的 offset 提取函数
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
                res_hot = await comment.get_comments_lazy(aid, comment.CommentResourceType.VIDEO, order=comment.OrderType.LIKE, credential=self.credential)
                replies = res_hot.get('replies') or []
                # 包含置顶
                if res_hot.get('top', {}).get('reply'):
                    replies.insert(0, res_hot['top']['reply'])
                
                for r in replies:
                    if r and r.get('rpid') not in seen_rpids:
                        seen_rpids.add(r.get('rpid'))
                        all_comments_list.append(r)
                
                # 如果热门还有下一页，多抓一两页热门
                curr_pag = get_next_offset(res_hot)
                if curr_pag and len(all_comments_list) < 100:
                    for _ in range(2):
                        res_hot = await comment.get_comments_lazy(aid, comment.CommentResourceType.VIDEO, offset=curr_pag, order=comment.OrderType.LIKE, credential=self.credential)
                        replies = res_hot.get('replies') or []
                        for r in replies:
                            if r and r.get('rpid') not in seen_rpids:
                                seen_rpids.add(r.get('rpid'))
                                all_comments_list.append(r)
                        curr_pag = get_next_offset(res_hot)
                        if not curr_pag: break
            except Exception as e:
                print(f"[警告] 抓取热门评论失败: {e}")

            # --- 阶段 2：如果还没凑够，切换到时间轴模式进行“地毯式”搜索 ---
            if len(all_comments_list) < actual_target:
                print(f"[信息] 评论数仍不足，切换到时间流模式继续抓取...")
                pag_time = ""
                page_count = 0
                while page_count < actual_max_pages:
                    try:
                        res = await comment.get_comments_lazy(
                            aid, 
                            comment.CommentResourceType.VIDEO, 
                            offset=pag_time, 
                            order=comment.OrderType.TIME,
                            credential=self.credential
                        )
                        
                        replies = res.get('replies') or []
                        # 核心修复：使用新的提取逻辑
                        pag_time = get_next_offset(res)
                        
                        count_before = len(all_comments_list)
                        for r in replies:
                            if r and r.get('rpid') not in seen_rpids:
                                seen_rpids.add(r.get('rpid'))
                                all_comments_list.append(r)
                        
                        page_count += 1
                        print(f"  - 页面 {page_count}: 抓取 {len(replies)} 条, 总数 {len(all_comments_list)}")

                        if len(all_comments_list) >= actual_target or not pag_time:
                            break
                    except Exception as e:
                        print(f"  - [错误] 时间流翻页异常: {e}")
                        break

            # 智能采样
            sampled_comments = self._smart_sample_comments(all_comments_list, actual_target)
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

            print(f"[信息] 评论抓取任务完成: 共计搜寻到 {len(all_comments_list)} 条原始素材")

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

    async def get_video_stats(self, bvid: str) -> Dict:
        """获取视频统计信息"""
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            stats = info.get('stat', {})
            online_info = None
            try:
                online = await v.get_online()
                online_info = {'total': online.get('total', 0), 'web_count': online.get('count', 0)}
            except: pass
            
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

    async def get_related_videos(self, bvid: str) -> Dict:
        """获取相关推荐视频"""
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
                    'duration_str': self._format_duration(item.get('duration', 0)),
                    'view': item.get('stat', {}).get('view', 0)
                })
            return {'success': True, 'data': processed_related}
        except Exception as e:
            return {'success': False, 'error': f'获取相关视频失败: {str(e)}'}

    async def get_popular_videos(self) -> Dict:
        """获取热门推荐视频 (用于首页展示)"""
        try:
            # 修正：使用 hot 模块获取热门视频
            from bilibili_api import hot
            res = await hot.get_hot_videos(pn=1, ps=12)
            
            processed = []
            for item in res.get('list', []):
                processed.append({
                    'bvid': item.get('bvid'),
                    'title': item.get('title'),
                    'author': item.get('owner', {}).get('name'),
                    'cover': item.get('pic'),
                    'duration': item.get('duration'),
                    'duration_str': self._format_duration(item.get('duration', 0)),
                    'view': item.get('stat', {}).get('view', 0)
                })
            return {'success': True, 'data': processed}
        except Exception as e:
            print(f"[警告] 获取热门视频失败: {e}")
            return {'success': False, 'error': str(e)}

    async def _get_cid(self, bvid: str) -> Optional[int]:
        """获取视频CID"""
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            return info.get('cid')
        except: return None

    async def extract_video_frames(self, bvid: str, max_frames: Optional[int] = None, interval: Optional[int] = None) -> Dict:
        """快速提取视频关键帧"""
        try:
            cid = await self._get_cid(bvid)
            if not cid: return {'success': False, 'error': '无法获取视频CID'}
            
            api_url = f"https://api.bilibili.com/x/player/videoshot?bvid={bvid}&cid={cid}"
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as resp:
                    data = await resp.json()
            
            if data['code'] != 0 or 'data' not in data: return {'success': False, 'error': '该视频不支持预览图'}
            
            shot_data = data['data']
            image_urls = shot_data.get('image', [])
            if not image_urls: return {'success': False, 'error': '未找到预览图数据'}
            
            v_info = await self.get_video_info(bvid)
            duration = v_info['data'].get('duration', 600)
            target_frames, _ = self._calculate_optimal_frame_params(duration)
            if max_frames: target_frames = max_frames
            
            frames_base64 = []
            import numpy as np
            count = 0
            for img_url in image_urls[:2]:
                if count >= target_frames: break
                if img_url.startswith('//'): img_url = 'https:' + img_url
                async with aiohttp.ClientSession() as session:
                    async with session.get(img_url) as resp:
                        if resp.status != 200: continue
                        img_bytes = await resp.read()
                
                nparr = np.frombuffer(img_bytes, np.uint8)
                sprite_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if sprite_img is None: continue
                
                s_h, s_w = sprite_img.shape[:2]
                cols = 10
                single_w = s_w // cols
                single_h = s_h // 10
                rows = s_h // single_h 
                
                for r in range(rows):
                    for c in range(cols):
                        if count >= target_frames: break
                        if (r * cols + c) % 3 != 0: continue
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


def run_async(coro):
    """运行异步函数的辅助函数"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)