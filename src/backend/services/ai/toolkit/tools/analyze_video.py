"""
分析B站视频工具
"""

import asyncio
from typing import Dict, Generator

from src.backend.services.ai.toolkit.base_tool import StreamableTool
from src.backend.services.ai.ai_helpers import (
    BILIBILI_CACHE,
    BILIBILI_FRAMES_SEMAPHORE,
    openai_chat_completions_stream,
)
from src.backend.utils.bilibili_helpers import extract_bvid
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyzeVideoTool(StreamableTool):
    """深度分析B站视频工具"""

    @property
    def name(self) -> str:
        return "analyze_video"

    @property
    def description(self) -> str:
        return "对指定的 B 站视频进行深度 AI 内容分析"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {"bvid": {"type": "string", "description": "视频的 BV 号"}},
                    "required": ["bvid"],
                },
            },
        }

    async def execute_stream(self, bvid: str, **kwargs) -> Generator[Dict, None, None]:
        """
        流式执行视频分析

        Args:
            bvid: 视频BV号

        Yields:
            Dict: 分析进度和结果
        """
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        if not self._client:
            raise RuntimeError("AI client 未初始化")

        # 清理BVID
        if bvid and ("bilibili.com" in bvid or "http" in bvid):
            bvid = extract_bvid(bvid) or bvid

        logger.info(f"[工具] 分析视频: {bvid}")

        # 1. 获取视频信息
        v_info_res = BILIBILI_CACHE.get(("video_info", bvid))
        if v_info_res is None:
            v_info_res = await self._bilibili_service.get_video_info(bvid)
            if v_info_res.get("success"):
                BILIBILI_CACHE.set(("video_info", bvid), v_info_res, ttl_seconds=86400)
        if not v_info_res["success"]:
            yield {
                "type": "error",
                "tool": self.name,
                "error": f"获取视频信息失败: {v_info_res['error']}",
            }
            return

        v_info = v_info_res["data"]
        v_title = v_info.get("title", bvid)

        yield {
            "type": "tool_progress",
            "tool": self.name,
            "bvid": bvid,
            "title": v_title,
            "message": f"正在搜集视频《{v_title}》的详情...",
        }

        # 2. 并行获取多维内容
        async def cached_call(key, ttl_seconds: int, coro_factory):
            cached = BILIBILI_CACHE.get(key)
            if cached is not None:
                return cached
            res = await coro_factory()
            if isinstance(res, dict) and res.get("success"):
                BILIBILI_CACHE.set(key, res, ttl_seconds=ttl_seconds)
            return res

        tasks = [
            cached_call(
                ("video_subtitles", bvid),
                86400,
                lambda: self._bilibili_service.get_video_subtitles(bvid),
            ),
            cached_call(
                ("video_danmaku", bvid, 1000),
                1800,
                lambda: self._bilibili_service.get_video_danmaku(bvid, limit=1000),
            ),
            cached_call(
                ("video_comments", bvid, 10),
                1800,
                lambda: self._bilibili_service.get_video_comments(bvid, max_pages=10),
            ),
        ]

        sub_res, danmaku_res, comments_res = await asyncio.gather(*tasks, return_exceptions=True)
        frames_res = None
        cached_frames = BILIBILI_CACHE.get(("video_frames", bvid))
        if cached_frames is not None:
            frames_res = cached_frames
        else:
            try:
                BILIBILI_FRAMES_SEMAPHORE.acquire()
                frames_res = await self._bilibili_service.extract_video_frames(bvid)
                if isinstance(frames_res, dict) and frames_res.get("success"):
                    BILIBILI_CACHE.set(("video_frames", bvid), frames_res, ttl_seconds=86400)
            except Exception as e:
                frames_res = e
            finally:
                BILIBILI_FRAMES_SEMAPHORE.release()

        # 3. 解析内容
        subtitle_text = ""
        if (
            not isinstance(sub_res, Exception)
            and sub_res.get("success")
            and sub_res["data"].get("has_subtitle")
        ):
            subtitle_text = sub_res["data"]["full_text"]

        danmaku_text = ""
        if not isinstance(danmaku_res, Exception) and danmaku_res.get("success"):
            danmaku_list = danmaku_res["data"]["danmakus"]
            danmaku_text = "\n\n【弹幕】\n" + "\n".join(danmaku_list[:50])

        comments_text = ""
        if not isinstance(comments_res, Exception) and comments_res.get("success"):
            comments_list = [
                f"{c['username']}: {c['message']}" for c in comments_res["data"]["comments"][:30]
            ]
            comments_text = "\n\n【评论】\n" + "\n".join(comments_list)

        video_frames = (
            frames_res["data"]["frames"]
            if (not isinstance(frames_res, Exception) and frames_res.get("success"))
            else None
        )

        # 整合原材料
        full_raw_content = subtitle_text if subtitle_text else f"简介: {v_info.get('desc', '无')}"
        full_raw_content += danmaku_text + comments_text

        yield {
            "type": "tool_progress",
            "tool": self.name,
            "bvid": bvid,
            "message": "正在提炼视频关键点...",
        }

        # 4. AI分析
        from src.backend.services.ai.prompts import get_video_analysis_prompt

        question = kwargs.get("question")
        analysis_prompt = get_video_analysis_prompt(
            v_info,
            full_raw_content,
            has_video_frames=bool(video_frames),
            danmaku_content=danmaku_text if danmaku_text else None,
            style="professional",
        )
        if question:
            analysis_prompt = f"额外关注点：{question}\n\n{analysis_prompt}"

        vl_model = kwargs.get("vl_model") or self._model
        if video_frames:
            user_content = [{"type": "text", "text": analysis_prompt}]
            for frame_base64 in video_frames:
                user_content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{frame_base64}",
                            "detail": "low",
                        },
                    }
                )
            messages = [
                {"role": "system", "content": "你是一位资深的B站视频内容分析专家，擅长结合视频画面、字幕和舆情进行全维度分析。"},
                {"role": "user", "content": user_content},
            ]
            model_to_use = vl_model
        else:
            messages = [
                {"role": "system", "content": "你是一个高效的视频内容提炼专家。"},
                {"role": "user", "content": analysis_prompt},
            ]
            model_to_use = self._model

        analysis_stream = openai_chat_completions_stream(
            self._client,
            model=model_to_use,
            messages=messages,
            stream=True,
        )

        result_text = ""
        for analysis_chunk in analysis_stream:
            if not analysis_chunk.choices:
                continue
            delta = analysis_chunk.choices[0].delta
            if delta.content:
                result_text += delta.content
                yield {
                    "type": "tool_progress",
                    "tool": self.name,
                    "bvid": bvid,
                    "tokens": len(result_text),
                    "content": delta.content,
                }

        # 返回最终结果
        yield {
            "type": "tool_result",
            "tool": self.name,
            "data": {"bvid": bvid, "title": v_title, "summary": result_text},
        }
