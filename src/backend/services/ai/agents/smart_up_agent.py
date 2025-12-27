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
from src.backend.utils.async_helpers import run_async
from src.backend.utils.logger import get_logger
from src.backend.services.ai.toolkit import ToolRegistry
from src.backend.services.ai.toolkit.tools import (
    SearchVideosTool,
    AnalyzeVideoTool,
    WebSearchTool,
    SearchUsersTool,
    GetUserRecentVideosTool
)

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
            GetUserRecentVideosTool()
        ]

        for tool in tools:
            ToolRegistry.register(tool)
            # 设置AI客户端
            tool.set_ai_client(self.client, self.model)

        logger.info(f"[SmartUpAgent] 已注册 {ToolRegistry.count()} 个工具")

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
            # 设置工具的bilibili_service
            ToolRegistry.set_services(bilibili_service=bilibili_service)

            system_prompt = get_smart_up_system_prompt(question)

            tools = ToolRegistry.list_tools_schema()

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
        """获取工具定义（已废弃，使用ToolRegistry）"""
        return ToolRegistry.list_tools_schema()

    def _execute_tool(self, func_name: str, args: Dict, bilibili_service, question: str):
        """
        执行工具调用（使用工具注册中心）

        Args:
            func_name: 工具名称
            args: 工具参数
            bilibili_service: B站服务实例
            question: 用户问题

        Yields:
            Dict: 工具执行结果
        """
        # 检查工具是否已注册
        if not ToolRegistry.has_tool(func_name):
            yield {'type': 'error', 'error': f"工具 '{func_name}' 未注册"}
            return

        # 获取工具实例
        tool = ToolRegistry.get_tool(func_name)

        # 如果是 analyze_video 工具，需要传递 question 参数
        if func_name == "analyze_video":
            args['question'] = question

        # 执行工具
        try:
            # 检查是否是流式工具
            from src.backend.services.ai.toolkit.base_tool import StreamableTool
            if isinstance(tool, StreamableTool):
                # 流式执行 - 创建一个辅助函数来收集所有结果
                async def collect_stream_results():
                    results = []
                    async for item in tool.execute_stream(**args):
                        results.append(item)
                    return results

                results = run_async(collect_stream_results())

                # 逐个yield结果
                for item in results:
                    # 转换结果格式以兼容现有代码
                    if item.get('type') == 'tool_result':
                        yield {'type': 'tool_result', 'tool': func_name, 'result': item.get('data')}
                    elif item.get('type') == 'tool_progress':
                        yield item
                    elif item.get('type') == 'error':
                        yield item
            else:
                # 非流式工具，直接执行
                result = run_async(tool.execute(**args))

                if result.get('type') == 'error':
                    yield {'type': 'error', 'error': result.get('error')}
                else:
                    yield {'type': 'tool_result', 'tool': func_name, 'result': result.get('data')}

        except Exception as e:
            error_msg = f"执行工具 '{func_name}' 出错: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            yield {'type': 'error', 'error': error_msg}
