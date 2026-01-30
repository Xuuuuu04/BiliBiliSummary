import asyncio
import json
from collections.abc import Iterator
from typing import Any, Literal

from src.backend.services.ai import AIService
from src.backend.services.bilibili import BilibiliService, run_async
from src.backend.utils.logger import get_logger
from src.backend_fastapi.core.errors import BadRequestError

logger = get_logger(__name__)


class AnalyzeService:
    def __init__(self, bilibili_service: BilibiliService, ai_service: AIService):
        self._bilibili = bilibili_service
        self._ai = ai_service

    def analyze_video(self, url: str) -> dict[str, Any]:
        if not url:
            raise BadRequestError("请提供B站视频链接")

        bvid = BilibiliService.extract_bvid(url)
        if not bvid:
            raise BadRequestError("无效的B站视频链接")

        video_info_result = run_async(self._bilibili.get_video_info(bvid))
        if not video_info_result.get("success"):
            raise BadRequestError(video_info_result.get("error", "获取视频信息失败"))

        video_info = video_info_result["data"]
        subtitle_result = run_async(self._bilibili.get_video_subtitles(bvid))

        danmaku_result = run_async(self._bilibili.get_video_danmaku(bvid, limit=200))
        danmaku_texts = danmaku_result["data"]["danmakus"] if danmaku_result.get("success") else []

        comments_result = run_async(self._bilibili.get_video_comments(bvid, max_pages=10))
        comments_data = (
            comments_result["data"]["comments"] if comments_result.get("success") else []
        )

        stats_result = run_async(self._bilibili.get_video_stats(bvid))
        stats_data = stats_result["data"] if stats_result.get("success") else {}

        content = ""
        has_subtitle = False
        if subtitle_result.get("success") and subtitle_result["data"].get("has_subtitle"):
            content = subtitle_result["data"]["full_text"]
            has_subtitle = True
        else:
            if danmaku_texts:
                content = "\n".join(danmaku_texts)
                content = f"【视频简介】\n{video_info.get('desc', '')}\n\n【弹幕内容】\n{content}"
            else:
                content = f"【视频简介】\n{video_info.get('desc', '')}"

        if not content or len(content) < 50:
            raise BadRequestError("无法获取视频内容（无字幕且无有效弹幕）")

        frames_result = run_async(self._bilibili.extract_video_frames(bvid))
        video_frames = frames_result["data"]["frames"] if frames_result.get("success") else None

        analysis_result = self._ai.generate_full_analysis(video_info, content, video_frames)
        if not analysis_result.get("success"):
            raise BadRequestError(analysis_result.get("error", "AI 分析失败"))

        return {
            "success": True,
            "data": {
                "video_info": video_info,
                "stats": stats_data,
                "has_subtitle": has_subtitle,
                "has_video_frames": bool(video_frames),
                "frame_count": len(video_frames) if video_frames else 0,
                "content": content,
                "content_length": len(content),
                "danmaku_count": len(danmaku_texts),
                "comment_count": len(comments_data),
                "danmaku_preview": danmaku_texts[:20] if danmaku_texts else [],
                "comments_preview": comments_data[:10] if comments_data else [],
                "analysis": analysis_result["data"]["full_analysis"],
                "parsed": analysis_result["data"]["parsed"],
                "tokens_used": analysis_result["data"]["tokens_used"],
            },
        }

    def stream_analyze(self, url: str, mode: Literal["video", "article"]) -> Iterator[str]:
        if not url:
            yield f"data: {json.dumps({'type': 'error', 'error': '请提供B站视频或专栏链接'}, ensure_ascii=False)}\n\n"
            return

        bvid = BilibiliService.extract_bvid(url)
        article_meta = BilibiliService.extract_article_id(url)

        try:
            if not bvid and not article_meta:
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'searching', 'message': '正在为您搜索相关内容...', 'progress': 5})}\n\n"

                if mode == "article":
                    search_res = run_async(self._bilibili.search_articles(url, limit=1))
                    if search_res.get("success") and search_res.get("data"):
                        article_meta = {"type": "cv", "id": search_res["data"][0]["cvid"]}
                        title = search_res["data"][0].get("title", "")
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'search_complete', 'message': f'为您找到专栏: {title}', 'progress': 10}, ensure_ascii=False)}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'error': '未找到相关专栏内容'})}\n\n"
                        return
                else:
                    search_res = run_async(self._bilibili.search_videos(url, limit=1))
                    if search_res.get("success") and search_res.get("data"):
                        bvid = search_res["data"][0]["bvid"]
                        title = search_res["data"][0].get("title", "")
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'search_complete', 'message': f'为您找到视频: {title}', 'progress': 10}, ensure_ascii=False)}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'error': '未找到相关视频'})}\n\n"
                        return

            if article_meta:
                a_type = article_meta["type"]
                a_id = article_meta["id"]

                yield f"data: {json.dumps({'type': 'stage', 'stage': 'fetching_info', 'message': f'获取{a_type}信息...', 'progress': 10})}\n\n"
                if a_type == "cv":
                    res = run_async(self._bilibili.get_article_content(a_id))
                else:
                    res = run_async(self._bilibili.get_opus_content(a_id))

                if not res.get("success"):
                    yield f"data: {json.dumps({'type': 'error', 'error': res.get('error', '未知错误')})}\n\n"
                    return

                info = res["data"]
                title = info.get("title", "")
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'info_complete', 'message': f'已获取内容: {title}', 'progress': 20, 'info': info}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'starting_analysis', 'message': '正在深度解析内容...', 'progress': 40})}\n\n"

                for chunk in self._ai.generate_article_analysis_stream(
                    res["data"], res["data"]["content"]
                ):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

                payload = {
                    "type": "final",
                    "stage": "completed",
                    "message": "专栏分析完成！",
                    "progress": 100,
                    "content": info.get("content", ""),
                    "info": info,
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                return

            yield f"data: {json.dumps({'type': 'stage', 'stage': 'fetching_info', 'message': '获取视频信息...', 'progress': 5})}\n\n"
            video_info_result = run_async(self._bilibili.get_video_info(bvid))
            if not video_info_result.get("success"):
                yield f"data: {json.dumps({'type': 'error', 'error': video_info_result.get('error', '获取视频信息失败')})}\n\n"
                return

            video_info = video_info_result["data"]
            video_title = video_info.get("title", "")
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'info_complete', 'message': f'已获取视频信息: {video_title}', 'progress': 15}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'stage', 'stage': 'fetching_content', 'message': '获取字幕和弹幕...', 'progress': 20})}\n\n"

            tasks = [
                self._bilibili.get_video_subtitles(bvid),
                self._bilibili.get_video_danmaku(bvid, limit=1000),
                self._bilibili.get_video_comments(bvid, max_pages=30, target_count=500),
                self._bilibili.get_video_stats(bvid),
            ]

            async def fetch_all():
                return await asyncio.gather(*tasks, return_exceptions=True)

            subtitle_result, danmaku_result, comments_result, stats_result = run_async(fetch_all())

            danmaku_texts = []
            if danmaku_result and hasattr(danmaku_result, "get") and danmaku_result.get("success"):
                danmaku_texts = danmaku_result["data"]["danmakus"]

            comments_data = []
            if (
                comments_result
                and hasattr(comments_result, "get")
                and comments_result.get("success")
            ):
                comments_data = comments_result["data"]["comments"]

            content = ""
            if (
                subtitle_result
                and hasattr(subtitle_result, "get")
                and subtitle_result.get("success")
                and subtitle_result["data"].get("has_subtitle")
            ):
                content = subtitle_result["data"]["full_text"]
                extra_context = ""
                if danmaku_texts:
                    extra_context += "\n\n【弹幕内容（部分）】\n" + "\n".join(danmaku_texts[:100])
                if comments_data:
                    comment_texts = [f"{c['username']}: {c['message']}" for c in comments_data[:50]]
                    extra_context += "\n\n【视频评论（部分）】\n" + "\n".join(comment_texts)
                content += extra_context
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'content_ready', 'message': '使用字幕内容（{}字）'.format(len(content)), 'progress': 35, 'content': content, 'has_subtitle': True, 'text_source': '字幕'})}\n\n"
            else:
                base_content = f"【视频简介】\n{video_info.get('desc', '')}"
                if danmaku_texts:
                    base_content += "\n\n【弹幕内容】\n" + "\n".join(danmaku_texts)
                if comments_data:
                    comment_texts = [f"{c['username']}: {c['message']}" for c in comments_data]
                    base_content += "\n\n【视频评论】\n" + "\n".join(comment_texts)
                content = base_content
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'content_ready', 'message': '使用视频文案进行分析', 'progress': 35, 'content': content, 'has_subtitle': False, 'text_source': '文案'})}\n\n"

            if not content or len(content) < 50:
                yield f"data: {json.dumps({'type': 'error', 'error': '无法获取视频内容（无字幕且无有效弹幕）'})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'stage', 'stage': 'extracting_frames', 'message': '提取视频关键帧...', 'progress': 40})}\n\n"
            frames_result = run_async(self._bilibili.extract_video_frames(bvid))
            video_frames = None
            frame_count = 0
            if frames_result and frames_result.get("success"):
                video_frames = frames_result["data"]["frames"]
                frame_count = len(video_frames)
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'frames_ready', 'message': '成功提取 {} 帧画面'.format(frame_count), 'progress': 50, 'has_frames': True, 'frame_count': frame_count})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'frames_ready', 'message': '将仅使用文本内容进行分析', 'progress': 50, 'has_frames': False, 'frame_count': 0})}\n\n"

            yield f"data: {json.dumps({'type': 'stage', 'stage': 'starting_analysis', 'message': '开始AI智能分析...', 'progress': 55})}\n\n"
            for chunk in self._ai.generate_full_analysis_stream(video_info, content, video_frames):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            top_comments = []
            if comments_data:
                top_comments = sorted(comments_data, key=lambda x: x.get("like", 0), reverse=True)[
                    :8
                ]

            login_info = " (已登录)" if self._bilibili.credential else " (未登录)"
            yield f"data: {json.dumps({'type': 'final', 'stage': 'completed', 'message': f'分析完成！{login_info}', 'progress': 100, 'content': content, 'top_comments': top_comments, 'danmaku_preview': danmaku_texts[:200] if danmaku_texts else [], 'frame_count': frame_count, 'comments_count': len(comments_data), 'danmaku_count': len(danmaku_texts)}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error("流式分析异常: {}".format(str(e)))
            yield f"data: {json.dumps({'type': 'error', 'error': f'分析过程中发生错误: {str(e)}'}, ensure_ascii=False)}\n\n"
