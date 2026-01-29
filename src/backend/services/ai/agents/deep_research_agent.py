"""
深度研究 Agent模块
提供全方位深度调研和报告撰写功能
"""
import json
import asyncio
from typing import Generator, Dict
from openai import OpenAI
from src.config import Config
from src.backend.services.ai.prompts import get_deep_research_system_prompt, get_video_analysis_prompt
from src.backend.services.ai.ai_helpers import web_search_exa, save_research_report
from src.backend.utils.async_helpers import run_async
from src.backend.utils.logger import get_logger
from src.backend.services.ai.toolkit import ToolRegistry
from src.backend.services.ai.toolkit.tools import (
    SearchVideosTool,
    AnalyzeVideoTool,
    WebSearchTool,
    SearchUsersTool,
    GetUserRecentVideosTool,
    FinishResearchTool
)

logger = get_logger(__name__)


class DeepResearchAgent:
    """
    深度研究 Agent

    针对课题进行全方位深度调研，撰写专业研究报告
    """

    def __init__(self, client: OpenAI, model: str, vl_model: str = None, enable_thinking: bool = False):
        """
        初始化深度研究 Agent

        Args:
            client: OpenAI客户端
            model: 使用的模型（深度研究）
            vl_model: 视觉语言模型（可选，用于视频帧分析）
            enable_thinking: 是否启用思考模式（用于支持thinking的混合态模型）
        """
        self.client = client
        self.model = model
        self.vl_model = vl_model or model  # 如果未指定，使用普通模型
        self.enable_thinking = enable_thinking

        # 初始化工具注册中心
        self._initialize_tools()

    def _initialize_tools(self):
        """初始化并注册所有工具"""
        # 清空之前的注册
        ToolRegistry.clear()

        # 注册核心工具
        tools = [
            SearchVideosTool(),
            AnalyzeVideoTool(),
            WebSearchTool(),
            SearchUsersTool(),
            GetUserRecentVideosTool(),
            FinishResearchTool()
        ]

        for tool in tools:
            ToolRegistry.register(tool)
            # 设置AI客户端
            tool.set_ai_client(self.client, self.model)

        logger.info(f"[DeepResearchAgent] 已注册 {ToolRegistry.count()} 个工具")

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
            # 设置工具的bilibili_service
            ToolRegistry.set_services(bilibili_service=bilibili_service)

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

                # 检测是否所有的工具调用都是 analyze_video（用于智能并行执行）
                batch_analyze_detected = False
                if tool_calls and len(tool_calls) > 1:
                    analyze_video_calls = [tc for tc in tool_calls if tc.get("function", {}).get("name") == "analyze_video"]

                    # 如果所有的工具调用都是 analyze_video，则并行执行
                    if len(analyze_video_calls) == len(tool_calls) and len(analyze_video_calls) > 1:
                        batch_analyze_detected = True
                        logger.info(f"[智能并行] 检测到 {len(analyze_video_calls)} 个 analyze_video 调用，将并行执行")

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

                # 如果检测到批量 analyze_video 调用，执行智能并行
                if batch_analyze_detected:
                    yield {'type': 'batch_analyze_start', 'count': len(tool_calls)}

                    # 并行执行所有视频分析
                    from asyncio import gather

                    def analyze_single_video(bvid):
                        """分析单个视频（复用现有逻辑）- 同步版本"""
                        # 清理BVID
                        if bvid and ('bilibili.com' in bvid or 'http' in bvid):
                            bvid = extract_bvid(bvid) or bvid

                        # 1. 获取视频信息
                        v_info_res = run_async(bilibili_service.get_video_info(bvid))
                        if not v_info_res['success']:
                            return {'bvid': bvid, 'success': False, 'error': f"获取视频信息失败: {v_info_res['error']}"}

                        v_info = v_info_res['data']
                        v_title = v_info.get('title', bvid)

                        # 2. 逐个获取所有多维内容（避免嵌套事件循环）
                        sub_res = run_async(bilibili_service.get_video_subtitles(bvid))
                        danmaku_res = run_async(bilibili_service.get_video_danmaku(bvid, limit=1000))
                        comments_res = run_async(bilibili_service.get_video_comments(bvid, max_pages=10))
                        frames_res = run_async(bilibili_service.extract_video_frames(bvid))

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

                        # 3. 调用 AI 深度分析
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

                        # 调用AI分析
                        logger.info(f"[批量分析] 开始AI分析: {bvid} ({v_title})")
                        analysis_response = self.client.chat.completions.create(
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
                        logger.info(f"[批量分析] AI分析响应已接收: {bvid}")

                        result_text = ""
                        current_analysis_tokens = 0
                        token_count = 0  # 初始化

                        for chunk in analysis_response:
                            if not chunk.choices:
                                continue
                            delta = chunk.choices[0].delta
                            if delta.content:
                                result_text += delta.content
                            # 流式响应的最后一个chunk包含usage信息
                            if chunk.usage:
                                token_count = chunk.usage.total_tokens
                                # 不要立即break，继续处理可能的剩余内容

                        # 如果没有获取到usage，使用文本长度估算
                        if not token_count:
                            token_count = len(result_text)

                        # 调试日志：检查result_text实际内容
                        logger.info(f"[批量分析] AI分析完成: {bvid} ({v_title}), tokens: {token_count}, result_text长度: {len(result_text)}")
                        if len(result_text) == 0:
                            logger.error(f"[批量分析] ⚠️ result_text为空! bvid={bvid}, title={v_title}")
                        elif len(result_text) < 100:
                            logger.warning(f"[批量分析] ⚠️ result_text异常短: {len(result_text)}字符, 内容预览: {result_text[:200]}")
                        else:
                            logger.info(f"[批量分析] result_text内容预览（前200字符）: {result_text[:200]}")

                        return {
                            'bvid': bvid,
                            'success': True,
                            'title': v_info['title'],
                            'summary': result_text,
                            'tokens': token_count
                        }

                    # 并行执行所有视频分析（使用线程池）
                    bvids = [json.loads(tc["function"]["arguments"]).get("bvid") for tc in tool_calls]
                    logger.info(f"[批量分析] 准备并行分析 {len(bvids)} 个视频: {bvids}")

                    # 使用 ThreadPoolExecutor 并行执行同步函数
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(bvids), 5)) as executor:
                        future_to_bvid = {executor.submit(analyze_single_video, bvid): bvid for bvid in bvids}
                        results = []
                        for future in concurrent.futures.as_completed(future_to_bvid):
                            try:
                                result = future.result()
                                results.append(result)
                                logger.info(f"[批量分析] 单个视频分析完成: {result.get('bvid', 'unknown')}")
                            except Exception as e:
                                logger.error(f"[批量分析] 视频分析异常: {str(e)}")
                                import traceback
                                traceback.print_exc()
                                results.append(e)

                    logger.info(f"[批量分析] 所有视频分析完成，共 {len(results)} 个结果")

                    # 处理并返回结果
                    total_tokens = 0
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_calls[i]["id"],
                                "name": "analyze_video",
                                "content": f"分析失败: {str(result)}"
                            })
                        elif result.get('success'):
                            total_tokens += result.get('tokens', 0)
                            summary = result.get('summary', '')
                            # 🔍 调试日志：检查传递给AI的工具内容
                            logger.info(f"[批量分析] 构造工具消息: bvid={result['bvid']}, summary长度={len(summary)}")
                            if len(summary) == 0:
                                logger.error(f"[批量分析] ❌ summary为空! bvid={result['bvid']}, result keys={list(result.keys())}")
                            elif len(summary) < 100:
                                logger.warning(f"[批量分析] ⚠️ summary异常短: {len(summary)}字符, 内容: {summary[:200]}")
                            else:
                                logger.info(f"[批量分析] ✅ summary正常: {len(summary)}字符, 前100字符: {summary[:100]}")

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_calls[i]["id"],
                                "name": "analyze_video",
                                "content": f"视频分析完成: {result.get('title', result['bvid'])}\n\n分析结果:\n{summary}"
                            })
                            # 发送进度更新
                            yield {
                                'type': 'tool_progress',
                                'tool': 'analyze_video',
                                'bvid': result['bvid'],
                                'message': f"✅ {result.get('title', result['bvid'])} 分析完成",
                                'tokens': total_tokens,
                                'video_tokens': result.get('tokens', 0),
                                'title': result.get('title', '')
                            }
                        else:
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_calls[i]["id"],
                                "name": "analyze_video",
                                "content": f"分析失败: {result.get('error', '未知错误')}"
                            })

                    # 发送完成通知
                    success_count = sum(1 for r in results if not isinstance(r, Exception) and r.get('success'))
                    logger.info(f"[批量分析] 发送完成通知: total={len(tool_calls)}, success={success_count}, tokens={total_tokens}")

                    yield {
                        'type': 'batch_analyze_complete',
                        'total': len(tool_calls),
                        'success': success_count,
                        'tokens': total_tokens
                    }
                    continue  # 跳过普通的工具调用处理

                # 正常的工具调用处理
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
                        error_msg = str(e)
                        # 友好的401错误提示
                        if "401" in error_msg or "Invalid token" in error_msg:
                            error_msg = "API Key 校验失败（401 - Invalid token）。请在设置中检查您的 OpenAI API Key 和 API Base 是否正确。"
                        result = f"执行工具出错: {error_msg}"
                        yield {'type': 'error', 'error': error_msg}

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

                    # 构建API请求参数
                    final_request_params = {
                        "model": self.model,
                        "messages": messages,
                        "stream": True
                    }

                    # 如果启用思考模式，添加额外参数
                    if self.enable_thinking:
                        pass  # 模型会自动返回 reasoning_content

                    final_stream = self.client.chat.completions.create(**final_request_params)
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
            error_msg = str(e)
            # 友好的401错误提示
            if "401" in error_msg or "Invalid token" in error_msg:
                error_msg = "API Key 校验失败（401 - Invalid token）。请在设置中检查您的 OpenAI API Key 和 API Base 是否正确。"
            logger.error(f"深度研究失败: {error_msg}")
            import traceback
            traceback.print_exc()
            yield {'type': 'error', 'error': error_msg}

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
                    "name": "get_hot_videos",
                    "description": "获取B站当前热门视频，了解流行趋势和热点话题。适合研究当前热门内容、流行趋势等课题。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "page": {"type": "integer", "description": "页码，默认1"},
                            "limit": {"type": "integer", "description": "每页数量，默认20"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_hot_buzzwords",
                    "description": "获取B站热词图鉴，了解网络流行语、梗文化和社区热点话题。适合研究网络文化、语言特点、梗文化等课题。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "page": {"type": "integer", "description": "页码，默认1"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weekly_hot_videos",
                    "description": "获取B站每周精选优质视频（每周必看）。适合研究高质量内容标准、口碑视频特点、各分区代表作等课题。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "week": {"type": "integer", "description": "第几周，默认1"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_history_popular_videos",
                    "description": "获取B站入站必刷的85个经典视频。适合研究B站文化历史、经典作品特点、社区文化基因等课题。",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_rank_videos",
                    "description": "获取指定分区的视频排行榜。支持30+分区（知识、科技、游戏、音乐等）。适合垂直领域研究、分区内容特点分析等课题。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "分区类型，如 knowledge（知识）、technology（科技）、game（游戏）、music（音乐）等"},
                            "day": {"type": "integer", "description": "时间范围：3=三日排行，7=周排行"}
                        },
                        "required": ["category"]
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
            },
            {
                "type": "function",
                "function": {
                    "name": "get_search_suggestions",
                    "description": "获取搜索联想建议，优化搜索词以获得更精准的搜索结果",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "部分搜索关键词"}
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_hot_search_keywords",
                    "description": "获取当前 B 站热搜关键词，把握热点趋势和用户关注焦点",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_video_tags",
                    "description": "获取视频的标签信息，了解视频的分类、主题和关联内容",
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
                    "name": "get_video_series",
                    "description": "获取视频所属的合集信息，用于系统性学习系列教程或了解完整的知识体系",
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
                    "name": "get_user_dynamics",
                    "description": "获取 UP 主的最新动态，了解其日常运营、社交互动和最新想法",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mid": {"type": "integer", "description": "UP 主的 UID (mid)", "default": 10},
                            "limit": {"type": "integer", "description": "获取动态的数量，默认 10"}
                        },
                        "required": ["mid"]
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

                # 2. 逐个获取所有多维内容（避免嵌套事件循环）
                yield {'type': 'tool_progress', 'tool': func_name, 'bvid': bvid, 'title': v_title, 'message': f'已获取视频标题: {v_title}。正在搜集全维信息...'}

                sub_res = run_async(bilibili_service.get_video_subtitles(bvid))
                danmaku_res = run_async(bilibili_service.get_video_danmaku(bvid, limit=1000))
                comments_res = run_async(bilibili_service.get_video_comments(bvid, max_pages=10))
                frames_res = run_async(bilibili_service.extract_video_frames(bvid))

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

        elif func_name == "get_hot_videos":
            page = args.get("page", 1)
            limit = args.get("limit", 20)
            hot_res = run_async(bilibili_service.get_hot_videos(pn=page, ps=limit))
            if hot_res['success']:
                result = json.dumps(hot_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': hot_res['data']}
            else:
                result = f"获取热门视频失败: {hot_res['error']}"
                yield {'type': 'error', 'error': result}

        elif func_name == "get_hot_buzzwords":
            page = args.get("page", 1)
            buzz_res = run_async(bilibili_service.get_hot_buzzwords(page_num=page, page_size=20))
            if buzz_res['success']:
                result = json.dumps(buzz_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': buzz_res['data']}
            else:
                result = f"获取热词图鉴失败: {buzz_res['error']}"
                yield {'type': 'error', 'error': result}

        elif func_name == "get_weekly_hot_videos":
            week = args.get("week", 1)
            weekly_res = run_async(bilibili_service.get_weekly_hot_videos(week=week))
            if weekly_res['success']:
                result = json.dumps(weekly_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': weekly_res['data']}
            else:
                result = f"获取每周必看失败: {weekly_res['error']}"
                yield {'type': 'error', 'error': result}

        elif func_name == "get_history_popular_videos":
            history_res = run_async(bilibili_service.get_history_popular_videos())
            if history_res['success']:
                result = json.dumps(history_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': history_res['data']}
            else:
                result = f"获取入站必刷失败: {history_res['error']}"
                yield {'type': 'error', 'error': result}

        elif func_name == "get_rank_videos":
            category = args.get("category")
            day = args.get("day", 3)

            # 映射分区名称到 bilibili_api 的 RankType
            from bilibili_api import rank
            category_map = {
                'knowledge': rank.RankType.Knowledge,
                'technology': rank.RankType.Technology,
                'game': rank.RankType.Game,
                'music': rank.RankType.Music,
                'douga': rank.RankType.Douga,
                'dance': rank.RankType.Dance,
                'life': rank.RankType.Life,
                'food': rank.RankType.Food,
                'fashion': rank.RankType.Fashion,
                'ent': rank.RankType.Ent,
                'cinephile': rank.RankType.Cinephile,
                'sports': rank.RankType.Sports,
                'car': rank.RankType.Car,
                'animal': rank.RankType.Animal,
            }

            rank_type = category_map.get(category.lower())
            if not rank_type:
                result = f"不支持的分区类型: {category}。支持的分区包括: knowledge, technology, game, music, douga, dance, life, food, fashion, ent, cinephile, sports, car, animal"
                yield {'type': 'error', 'error': result}
            else:
                rank_res = run_async(bilibili_service.get_rank_videos(type_=rank_type))
                if rank_res['success']:
                    result = json.dumps(rank_res['data'], ensure_ascii=False)
                    yield {'type': 'tool_result', 'tool': func_name, 'result': rank_res['data']}
                else:
                    result = f"获取排行榜失败: {rank_res['error']}"
                    yield {'type': 'error', 'error': result}

        elif func_name == "finish_research_and_write_report":
            result = "资料搜集阶段结束。请现在撰写全方位、深度的研究报告，并严格遵守参考来源标注规范。"
            yield {'type': 'tool_result', 'tool': func_name, 'result': '进入撰写报告阶段...'}

        elif func_name == "get_search_suggestions":
            keyword = args.get("keyword")
            sug_res = run_async(bilibili_service.get_search_suggestions(keyword))
            if sug_res['success']:
                result = json.dumps(sug_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': sug_res['data']}
            else:
                result = f"获取搜索建议失败: {sug_res['error']}"

        elif func_name == "get_hot_search_keywords":
            hot_res = run_async(bilibili_service.get_hot_search_keywords())
            if hot_res['success']:
                result = json.dumps(hot_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': hot_res['data']}
            else:
                result = f"获取热搜关键词失败: {hot_res['error']}"

        elif func_name == "get_video_tags":
            bvid = args.get("bvid")
            tags_res = run_async(bilibili_service.get_video_tags(bvid))
            if tags_res['success']:
                result = json.dumps(tags_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': tags_res['data']}
            else:
                result = f"获取视频标签失败: {tags_res['error']}"

        elif func_name == "get_video_series":
            bvid = args.get("bvid")
            series_res = run_async(bilibili_service.get_video_series(bvid))
            if series_res['success']:
                result = json.dumps(series_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': series_res['data']}
            else:
                result = f"获取视频合集失败: {series_res['error']}"

        elif func_name == "get_user_dynamics":
            mid = args.get("mid")
            limit = args.get("limit", 10)
            dynamics_res = run_async(bilibili_service.get_user_dynamics(mid, limit=limit))
            if dynamics_res['success']:
                result = json.dumps(dynamics_res['data'], ensure_ascii=False)
                yield {'type': 'tool_result', 'tool': func_name, 'result': dynamics_res['data']}
            else:
                result = f"获取用户动态失败: {dynamics_res['error']}"

        return result
