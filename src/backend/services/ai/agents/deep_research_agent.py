"""
深度研究 Agent模块
提供全方位深度调研和报告撰写功能
"""
import json
import asyncio
from typing import Generator, Dict
from openai import OpenAI
from src.config import Config
from src.backend.services.ai.prompts import get_deep_research_system_prompt
from src.backend.services.ai.ai_helpers import web_search_exa, save_research_report
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class DeepResearchAgent:
    """
    深度研究 Agent

    针对课题进行全方位深度调研，撰写专业研究报告
    """

    def __init__(self, client: OpenAI, model: str, vl_model: str = None):
        """
        初始化深度研究 Agent

        Args:
            client: OpenAI客户端
            model: 使用的模型（深度研究）
            vl_model: 视觉语言模型（可选，用于视频帧分析）
        """
        self.client = client
        self.model = model
        self.vl_model = vl_model or model  # 如果未指定，使用普通模型

    def stream_research(self, topic: str, bilibili_service) -> Generator[Dict, None, None]:
        """
        流式深度研究

        Args:
            topic: 研究课题
            bilibili_service: B站服务实例

        Yields:
            Dict: 包含状态、进度、内容等信息的字典
        """
        try:
            from src.backend.services.bilibili.bilibili_service import run_async

            system_prompt = get_deep_research_system_prompt(topic)

            tools = self._get_tools_definition()

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请针对以下课题开始深度研究：{topic}"}
            ]

            # 最大轮次限制，防止无限循环
            max_rounds = 100  # 深度研究提升至100轮
            round_count = 0

            for _ in range(max_rounds):
                round_count += 1
                yield {'type': 'round_start', 'round': round_count}

                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    stream=True
                )

                tool_calls = []
                full_content = ""

                # 处理流式响应
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    # 处理思考过程
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        yield {'type': 'thinking', 'content': delta.reasoning_content}

                    if delta.content:
                        full_content += delta.content
                        yield {'type': 'content', 'content': delta.content}

                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            if len(tool_calls) <= tool_call.index:
                                tool_calls.append({
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                })
                            if tool_call.id:
                                tool_calls[tool_call.index]["id"] = tool_call.id
                            if tool_call.function.name:
                                tool_calls[tool_call.index]["function"]["name"] += tool_call.function.name
                            if tool_call.function.arguments:
                                tool_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments

                # 如果没有工具调用，说明研究完成或模型直接给出了结论
                if not tool_calls:
                    # 核心修复：如果模型直接给出了内容但没有调用 finish 工具
                    if not any(msg.get('role') == 'tool' and msg.get('name') == 'finish_research_and_write_report' for msg in messages):
                        if round_count < max_rounds:
                            messages.append({"role": "assistant", "content": full_content})
                            messages.append({
                                "role": "user",
                                "content": "研究尚未结束。请继续使用工具（如搜索相关视频、分析视频、搜索UP主或作品集）进行深入调研。只有当你认为资料完全充足时，请【务必调用】`finish_research_and_write_report` 工具来启动正式报告的撰写。不要直接在对话中结束。"
                            })
                            continue
                    messages.append({"role": "assistant", "content": full_content})
                    break

                # 处理工具调用
                messages.append({
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": tool_calls
                })

                is_final_report_triggered = False
                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    try:
                        args = json.loads(tool_call["function"]["arguments"])
                    except:
                        args = {}

                    yield {'type': 'tool_start', 'tool': func_name, 'args': args}

                    result = ""
                    try:
                        result = yield from self._execute_tool(
                            func_name, args, bilibili_service, topic
                        )
                    except Exception as e:
                        result = f"执行工具出错: {str(e)}"
                        yield {'type': 'error', 'error': result}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": func_name,
                        "content": result
                    })

                    # 检查是否触发了最终报告
                    if func_name == "finish_research_and_write_report":
                        is_final_report_triggered = True

                # 如果触发了最终报告撰写，进入最后一段生成
                if is_final_report_triggered:
                    yield {'type': 'report_start'}
                    final_stream = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        stream=True
                    )
                    final_report = ""
                    for chunk in final_stream:
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                            yield {'type': 'thinking', 'content': delta.reasoning_content}
                        if delta.content:
                            final_report += delta.content
                            yield {'type': 'content', 'content': delta.content}

                    # 持久化报告
                    try:
                        save_research_report(topic, final_report)
                    except Exception as e:
                        logger.warning(f"保存报告失败: {e}")

                    break

            yield {'type': 'done'}

        except Exception as e:
            logger.error(f"深度研究失败: {str(e)}")
            import traceback
            traceback.print_exc()
            yield {'type': 'error', 'error': str(e)}

    def _get_tools_definition(self) -> list:
        """获取工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_videos",
                    "description": "搜索 B 站视频以获取相关研究素材",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "搜索关键词"}
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_users",
                    "description": "根据关键词/昵称模糊搜索 B 站 UP 主",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "UP 主昵称或相关关键词"}
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_user_recent_videos",
                    "description": "获取指定 UP 主的最近投稿视频列表，用于系统性研究该 UP 主的专业内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mid": {"type": "integer", "description": "UP 主的 UID (mid)", "default": 10},
                            "limit": {"type": "integer", "description": "获取视频的数量，默认 10"}
                        },
                        "required": ["mid"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_video",
                    "description": "对指定的 B 站视频进行深度 AI 内容分析",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "bvid": {"type": "string", "description": "视频的 BV 号"}
                        },
                        "required": ["bvid"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "使用 Exa AI 进行全网深度搜索，获取最新资讯、技术文档或 B 站以外的补充信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索查询语句"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finish_research_and_write_report",
                    "description": "完成所有资料搜集，开始撰写最终详尽的研究报告",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary_of_findings": {"type": "string", "description": "对研究发现的简要概述"}
                        },
                        "required": ["summary_of_findings"]
                    }
                }
            }
        ]

    def _execute_tool(self, func_name: str, args: Dict, bilibili_service, topic: str):
        """
        执行工具调用

        Args:
            func_name: 工具名称
            args: 工具参数
            bilibili_service: B站服务实例
            topic: 研究课题

        Yields:
            Dict: 工具执行结果
        """
        from src.backend.services.bilibili.bilibili_service import run_async
        from src.backend.utils.bilibili_helpers import extract_bvid
        from src.backend.services.ai.prompts import get_video_analysis_prompt

        if func_name == "search_videos":
            keyword = args.get("keyword")
            search_res = run_async(bilibili_service.search_videos(keyword, limit=5))
            if search_res['success']:
                result = json.dumps(search_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': search_res['data'][:3]}
            else:
                result = f"搜索失败: {search_res['error']}"

        elif func_name == "web_search":
            query = args.get("query")
            search_res = web_search_exa(query)
            if search_res['success']:
                result = json.dumps(search_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': search_res['data']}
            else:
                result = f"网络搜索失败: {search_res['error']}"
                yield {'type': 'error', 'error': result}

        elif func_name == "analyze_video":
            bvid = args.get("bvid")
            # 清理BVID
            if bvid and ('bilibili.com' in bvid or 'http' in bvid):
                bvid = extract_bvid(bvid) or bvid

            logger.info(f"[工具] 深度研究 Agent 发起视频分析: {bvid}")

            # 1. 获取视频信息
            v_info_res = run_async(bilibili_service.get_video_info(bvid))
            if not v_info_res['success']:
                result = f"获取视频信息失败: {v_info_res['error']}"
            else:
                v_info = v_info_res['data']
                v_title = v_info.get('title', bvid)

                # 2. 并行获取所有多维内容
                yield {'type': 'tool_progress', 'tool': func_name, 'bvid': bvid, 'title': v_title, 'message': f'已获取视频标题: {v_title}。正在搜集全维信息...'}

                tasks = [
                    bilibili_service.get_video_subtitles(bvid),
                    bilibili_service.get_video_danmaku(bvid, limit=1000),
                    bilibili_service.get_video_comments(bvid, max_pages=10),
                    bilibili_service.extract_video_frames(bvid)
                ]

                # 并发执行
                sub_res, danmaku_res, comments_res, frames_res = run_async(asyncio.gather(*tasks, return_exceptions=True))

                # 数据解析
                subtitle_text = sub_res['data']['full_text'] if (not isinstance(sub_res, Exception) and sub_res.get('success') and sub_res['data'].get('has_subtitle')) else ""

                danmaku_text = ""
                if not isinstance(danmaku_res, Exception) and danmaku_res.get('success'):
                    danmaku_list = danmaku_res['data']['danmakus']
                    danmaku_text = f"\n\n【弹幕内容（部分）】\n" + "\n".join(danmaku_list[:100])

                comments_text = ""
                if not isinstance(comments_res, Exception) and comments_res.get('success'):
                    comments_list = [f"{c['username']}: {c['message']}" for c in comments_res['data']['comments'][:50]]
                    comments_text = f"\n\n【视频评论（部分）】\n" + "\n".join(comments_list)

                video_frames = frames_res['data']['frames'] if (not isinstance(frames_res, Exception) and frames_res.get('success')) else None

                # 整合原材料
                full_raw_content = subtitle_text if subtitle_text else f"简介: {v_info.get('desc', '无')}"
                full_raw_content += danmaku_text + comments_text

                # 3. 调用 AI 深度分析（流式反馈进度）
                yield {'type': 'tool_progress', 'tool': func_name, 'bvid': bvid, 'message': '全维素材就绪，正在进行视觉与文本交叉建模...'}

                prompt = get_video_analysis_prompt(
                    v_info,
                    full_raw_content,
                    has_video_frames=bool(video_frames),
                    danmaku_content=danmaku_text if danmaku_text else None
                )

                # 构建多模态内容
                user_content = [{"type": "text", "text": prompt}]
                if video_frames:
                    for frame_base64 in video_frames:
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{frame_base64}",
                                "detail": "low"
                            }
                        })

                analysis_stream = self.client.chat.completions.create(
                    model=self.vl_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一位资深的B站视频内容分析专家，擅长结合视频画面、字幕和舆情进行全维度分析。"
                        },
                        {"role": "user", "content": user_content}
                    ],
                    stream=True
                )

                result_text = ""
                current_analysis_tokens = 0
                for analysis_chunk in analysis_stream:
                    if not analysis_chunk.choices:
                        continue
                    delta = analysis_chunk.choices[0].delta
                    if delta.content:
                        result_text += delta.content
                        current_analysis_tokens = len(result_text)
                        yield {
                            'type': 'tool_progress',
                            'tool': func_name,
                            'bvid': bvid,
                            'tokens': current_analysis_tokens,
                            'content': delta.content
                        }

                result = result_text
                yield {
                    'type': 'tool_result',
                    'tool': func_name,
                    'result': {'bvid': bvid, 'title': v_info['title'], 'summary': result},
                    'tokens': current_analysis_tokens
                }

        elif func_name == "search_users":
            keyword = args.get("keyword")
            search_res = run_async(bilibili_service.search_users(keyword, limit=5))
            if search_res['success']:
                result = json.dumps(search_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': search_res['data']}
            else:
                result = f"搜索用户失败: {search_res['error']}"

        elif func_name == "get_user_recent_videos":
            mid = args.get("mid")
            limit = args.get("limit", 10)
            v_res = run_async(bilibili_service.get_user_recent_videos(mid, limit=limit))
            if v_res['success']:
                result = json.dumps(v_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': v_res['data']}
            else:
                result = f"获取用户作品失败: {v_res['error']}"

        elif func_name == "finish_research_and_write_report":
            result = "资料搜集阶段结束。请现在撰写全方位、深度的研究报告，并严格遵守参考来源标注规范。"
            yield {'type': 'tool_result', 'tool': func_name, 'result': '进入撰写报告阶段...'}

        return result
