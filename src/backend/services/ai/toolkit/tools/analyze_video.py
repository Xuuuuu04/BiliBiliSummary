"""
分析B站视频工具
"""
import asyncio
from typing import Dict, Generator
from src.backend.services.ai.toolkit.base_tool import StreamableTool
from src.backend.utils.async_helpers import run_async
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
                    "properties": {
                        "bvid": {
                            "type": "string",
                            "description": "视频的 BV 号"
                        }
                    },
                    "required": ["bvid"]
                }
            }
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
        if bvid and ('bilibili.com' in bvid or 'http' in bvid):
            bvid = extract_bvid(bvid) or bvid

        logger.info(f"[工具] 分析视频: {bvid}")

        # 1. 获取视频信息
        v_info_res = run_async(self._bilibili_service.get_video_info(bvid))
        if not v_info_res['success']:
            yield {
                'type': 'error',
                'tool': self.name,
                'error': f"获取视频信息失败: {v_info_res['error']}"
            }
            return

        v_info = v_info_res['data']
        v_title = v_info.get('title', bvid)

        yield {
            'type': 'tool_progress',
            'tool': self.name,
            'bvid': bvid,
            'title': v_title,
            'message': f'正在搜集视频《{v_title}》的详情...'
        }

        # 2. 并行获取多维内容
        tasks = [
            self._bilibili_service.get_video_subtitles(bvid),
            self._bilibili_service.get_video_danmaku(bvid, limit=500),
            self._bilibili_service.get_video_comments(bvid, max_pages=5)
        ]

        sub_res, danmaku_res, comments_res = run_async(
            asyncio.gather(*tasks, return_exceptions=True)
        )

        # 3. 解析内容
        subtitle_text = ""
        if not isinstance(sub_res, Exception) and sub_res.get('success') and sub_res['data'].get('has_subtitle'):
            subtitle_text = sub_res['data']['full_text']

        danmaku_text = ""
        if not isinstance(danmaku_res, Exception) and danmaku_res.get('success'):
            danmaku_list = danmaku_res['data']['danmakus']
            danmaku_text = f"\n\n【弹幕】\n" + "\n".join(danmaku_list[:50])

        comments_text = ""
        if not isinstance(comments_res, Exception) and comments_res.get('success'):
            comments_list = [f"{c['username']}: {c['message']}" for c in comments_res['data']['comments'][:30]]
            comments_text = f"\n\n【评论】\n" + "\n".join(comments_list)

        # 整合原材料
        full_raw_content = subtitle_text if subtitle_text else f"简介: {v_info.get('desc', '无')}"
        full_raw_content += danmaku_text + comments_text

        yield {
            'type': 'tool_progress',
            'tool': self.name,
            'bvid': bvid,
            'message': '正在提炼视频关键点...'
        }

        # 4. AI分析
        from src.backend.services.ai.prompts import get_video_analyzer_for_agent_prompt

        question = kwargs.get('question', '请分析这个视频的内容')
        analysis_prompt = get_video_analyzer_for_agent_prompt(v_title, question, full_raw_content)

        analysis_stream = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "你是一个高效的视频内容提炼专家。"},
                {"role": "user", "content": f"视频内容：\n{full_raw_content[:15000]}\n\n任务：{analysis_prompt}"}
            ],
            stream=True
        )

        result_text = ""
        for analysis_chunk in analysis_stream:
            if not analysis_chunk.choices:
                continue
            delta = analysis_chunk.choices[0].delta
            if delta.content:
                result_text += delta.content
                yield {
                    'type': 'tool_progress',
                    'tool': self.name,
                    'bvid': bvid,
                    'tokens': len(result_text),
                    'content': delta.content
                }

        # 返回最终结果
        yield {
            'type': 'tool_result',
            'tool': self.name,
            'data': {
                'bvid': bvid,
                'title': v_title,
                'summary': result_text
            }
        }
