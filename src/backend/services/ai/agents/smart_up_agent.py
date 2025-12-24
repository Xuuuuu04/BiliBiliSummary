"""
智能小UP Agent模块
提供自适应快速问答功能
"""
import json
import asyncio
from typing import Generator, Dict, List
from openai import OpenAI
from src.config import Config
from src.backend.services.ai.prompts import get_smart_up_system_prompt
from src.backend.services.ai.ai_helpers import web_search_exa
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class SmartUpAgent:
    """
    智能小UP Agent

    自适应快速Q&A，深度复用工具，根据问题复杂度调整搜索和分析深度
    """

    def __init__(self, client: OpenAI, model: str, enable_thinking: bool = False):
        """
        初始化智能小UP Agent

        Args:
            client: OpenAI客户端
            model: 使用的模型
            enable_thinking: 是否启用思考模式（用于支持thinking的混合态模型）
        """
        self.client = client
        self.model = model
        self.enable_thinking = enable_thinking

    def stream_chat(self, question: str, bilibili_service, history: List[Dict] = None) -> Generator[Dict, None, None]:
        """
        流式对话

        Args:
            question: 用户问题
            bilibili_service: B站服务实例
            history: 对话历史（可选）

        Yields:
            Dict: 包含状态、内容、工具调用等信息的字典
        """
        try:
            from src.backend.services.bilibili.bilibili_service import run_async

            system_prompt = get_smart_up_system_prompt(question)

            tools = self._get_tools_definition()

            # 组装消息列表，包含历史记录
            messages = [{"role": "system", "content": system_prompt}]
            if history:
                messages.extend(history)

            # 如果最后一项不是当前问题，则添加
            if not messages or messages[-1].get('content') != question:
                messages.append({"role": "user", "content": question})

            max_rounds = 15  # 智能小UP限制15轮
            round_count = 0

            for i in range(max_rounds):
                round_count += 1
                yield {'type': 'round_start', 'round': round_count}

                # 如果是最后一轮，强制要求AI总结并给出回答
                if round_count == max_rounds:
                    messages.append({
                        "role": "user",
                        "content": "由于分析轮次已达上限（15次），请不要再调用任何工具，直接根据以上已收集到的所有信息，为用户提供最终的、最完整的回答。"
                    })

                # 构建API请求参数
                request_params = {
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "stream": True
                }

                # 如果启用思考模式，添加额外参数
                # 注意：只有部分模型（如DeepSeek-V3、Kimi-K2）支持这些参数
                if self.enable_thinking:
                    # 对于支持的模型，启用思考模式通常不需要额外参数
                    # 模型会自动返回 reasoning_content 字段
                    pass  # 某些模型可能需要额外的 max_tokens 等参数

                stream = self.client.chat.completions.create(**request_params)

                tool_calls = []
                full_content = ""

                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

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

                if not tool_calls:
                    # 如果没有工具调用，说明回答完成
                    messages.append({"role": "assistant", "content": full_content})
                    break

                messages.append({
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": tool_calls
                })

                # 处理工具调用
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
                            func_name, args, bilibili_service, question
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

            yield {'type': 'done'}

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Invalid token" in error_msg:
                error_msg = "API Key 校验失败（401 - Invalid token）。请在设置中检查您的 OpenAI API Key 和 API Base 是否正确。"
            logger.error(f"智能小UP失败: {error_msg}")
            import traceback
            traceback.print_exc()
            yield {'type': 'error', 'error': error_msg}

    def _get_tools_definition(self) -> List[Dict]:
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
                            "query": {"type": "string", "description": "搜索查询语句，建议使用自然语言描述你想要找的内容"}
                        },
                        "required": ["query"]
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
                    "description": "获取指定 UP 主的最近投稿视频列表",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mid": {"type": "integer", "description": "UP 主的 UID (mid)", "default": 10},
                            "limit": {"type": "integer", "description": "获取视频的数量，默认 10"}
                        },
                        "required": ["mid"]
                    }
                }
            }
        ]

    def _execute_tool(self, func_name: str, args: Dict, bilibili_service, question: str):
        """
        执行工具调用

        Args:
            func_name: 工具名称
            args: 工具参数
            bilibili_service: B站服务实例
            question: 用户问题

        Yields:
            Dict: 工具执行结果
        """
        from src.backend.services.bilibili.bilibili_service import run_async

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
            if bvid and ('bilibili.com' in bvid or 'http' in bvid):
                from src.backend.utils.bilibili_helpers import extract_bvid
                bvid = extract_bvid(bvid) or bvid

            v_info_res = run_async(bilibili_service.get_video_info(bvid))
            if not v_info_res['success']:
                result = f"获取视频信息失败: {v_info_res['error']}"
            else:
                v_info = v_info_res['data']
                v_title = v_info.get('title', bvid)
                yield {'type': 'tool_progress', 'tool': func_name, 'bvid': bvid, 'title': v_title, 'message': f'正在搜集视频《{v_title}》的详情...'}

                tasks = [
                    bilibili_service.get_video_subtitles(bvid),
                    bilibili_service.get_video_danmaku(bvid, limit=500),
                    bilibili_service.get_video_comments(bvid, max_pages=5)
                ]
                sub_res, danmaku_res, comments_res = run_async(asyncio.gather(*tasks, return_exceptions=True))

                subtitle_text = sub_res['data']['full_text'] if (not isinstance(sub_res, Exception) and sub_res.get('success') and sub_res['data'].get('has_subtitle')) else ""
                danmaku_text = ""
                if not isinstance(danmaku_res, Exception) and danmaku_res.get('success'):
                    danmaku_text = f"\n\n【弹幕】\n" + "\n".join(danmaku_res['data']['danmakus'][:50])
                comments_text = ""
                if not isinstance(comments_res, Exception) and comments_res.get('success'):
                    comments_list = [f"{c['username']}: {c['message']}" for c in comments_res['data']['comments'][:30]]
                    comments_text = f"\n\n【评论】\n" + "\n".join(comments_list)

                full_raw_content = subtitle_text if subtitle_text else f"简介: {v_info.get('desc', '无')}"
                full_raw_content += danmaku_text + comments_text

                yield {'type': 'tool_progress', 'tool': func_name, 'bvid': bvid, 'message': '正在提炼视频关键点...'}

                from src.backend.services.ai.prompts import get_video_analyzer_for_agent_prompt
                analysis_prompt = get_video_analyzer_for_agent_prompt(v_title, question, full_raw_content)

                analysis_stream = self.client.chat.completions.create(
                    model=self.model,
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
                        yield {'type': 'tool_progress', 'tool': func_name, 'bvid': bvid, 'tokens': len(result_text), 'content': delta.content}

                result = result_text
                yield {'type': 'tool_result', 'tool': func_name, 'result': {'bvid': bvid, 'title': v_title, 'summary': result}}

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

        return result
