import json
from openai import OpenAI
from src.config import Config
from typing import Dict, Optional, Callable, Generator, List
import time


class AIService:
    """AI服务类，用于调用大模型生成总结"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_API_BASE,
            timeout=180.0  # 优化：减少到3分钟超时，提高响应速度
        )
        self.model = Config.OPENAI_MODEL
        self.qa_model = Config.QA_MODEL
        self.research_model = Config.DEEP_RESEARCH_MODEL

    def smart_up_stream(self, question: str, bilibili_service, history: list = None) -> Generator[Dict, None, None]:
        """智能小UP 逻辑：自适应快速 Q&A，深度复用工具"""
        try:
            from src.backend.bilibili_service import run_async
            from datetime import datetime
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            system_prompt = f"""你是一个智能、敏捷且富有洞察力的“B站全能小UP”助手。
你的任务是根据用户问题的复杂程度，自适应地调整搜索和分析深度，提供最精准、最高质量的回答。

现在的时间是：{current_time}。

【核心原则：COT（思维链）与 TOT（思维树）自适应应用】
1. **问题复杂度评估 (TOT)**：在开始前，快速评估问题的广度与深度。
   - **简单事实类**：直接检索相关视频或网页，快速给出结论。
   - **综合分析类**：拆解问题维度（思维树），通过多点搜索验证，整合跨领域信息。
   - **前沿/争议类**：搜索不同立场的视频与评论，对比分析，给出多维视角。
2. **推理透明化 (COT)**：在调用工具前，你应该在内部思考（如果模型支持 reasoning_content）或通过简洁的工具选择展现你的逻辑。解释为什么这个特定的搜索路径能解决用户的核心痛点。
3. **效率优先**：不要为了多轮而多轮。如果 1-2 次搜索已能完美解决，请立即总结。只有在信息存在明显缺口或需要深度挖掘时才继续。

【工作核心准则】
1. **纯工具输出**：在中间决策轮次，你**必须且只能**输出工具调用。严禁在工具调用之外输出任何“我现在去查一下”之类的废话。
2. **来源意识**：所有的核心事实、数据、观点，**必须**标注来源（如：视频《...》、UP主[@...]、或 [网页链接](url)）。
3. **B站生态优先**：优先搜索 B 站视频，捕捉社区弹幕热梗和高赞评论，体现 B 站社区特色。

【工具指令】
- `search_videos`: 搜索 B 站视频素材。
- `analyze_video`: 深度解析单个视频（字幕、弹幕、评论）。
- `web_search`: 全网深度搜索（Exa Search），用于补充时效性信息或专业文档。
- `search_users`: 根据关键词/昵称模糊搜索 B 站 UP 主。
- `get_user_recent_videos`: 获取指定 UP 主的最近投稿视频列表，用于系统性研究该 UP 主的作品。

【回答规范】
1. **记忆与关联**：你具有上下文记忆能力。如果用户的问题涉及到之前的对话，你应该结合历史信息进行回答。
2. **语气**：专业、博学、幽默，像在做一期高质量的“硬核视频”。
3. **格式**：重点内容**加粗**。结论先行，逻辑分明。
4. **结尾**：必须列出 3-5 个最有价值的推荐视频/网页链接。

用户的问题是：{question}
"""
            
            tools = [
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
                                "mid": {"type": "integer", "description": "UP 主的 UID (mid)"},
                                "limit": {"type": "integer", "description": "获取视频的数量，默认 10", "default": 10}
                            },
                            "required": ["mid"]
                        }
                    }
                }
            ]

            # 组装消息列表，包含历史记录
            messages = [{"role": "system", "content": system_prompt}]
            if history:
                messages.extend(history)
            
            # 如果最后一项不是当前问题，则添加
            if not messages or messages[-1].get('content') != question:
                messages.append({"role": "user", "content": question})
            
            max_rounds = 15 # 智能小UP限制 15 轮
            round_count = 0
            
            for i in range(max_rounds):
                round_count += 1
                yield {'type': 'round_start', 'round': round_count}
                
                # 如果是最后一轮，强制要求 AI 总结并给出回答
                if round_count == max_rounds:
                    messages.append({"role": "user", "content": "由于分析轮次已达上限（15次），请不要再调用任何工具，直接根据以上已收集到的所有信息，为用户提供最终的、最完整的回答。"})
                
                stream = self.client.chat.completions.create(
                    model=self.research_model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    stream=True
                )

                tool_calls = []
                full_content = ""
                
                for chunk in stream:
                    if not chunk.choices: continue
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

                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    import json
                    try:
                        args = json.loads(tool_call["function"]["arguments"])
                    except:
                        args = {}
                    
                    yield {'type': 'tool_start', 'tool': func_name, 'args': args}
                    
                    result = ""
                    try:
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
                            search_res = self._web_search_exa(query)
                            if search_res['success']:
                                result = json.dumps(search_res['data'], ensure_ascii=False)
                                yield {'type': 'tool_result', 'tool': func_name, 'result': search_res['data']}
                            else:
                                result = f"网络搜索失败: {search_res['error']}"
                                yield {'type': 'error', 'error': result}
                        
                        elif func_name == "analyze_video":
                            bvid = args.get("bvid")
                            if bvid and ('bilibili.com' in bvid or 'http' in bvid):
                                from src.backend.bilibili_service import BilibiliService
                                bvid = BilibiliService.extract_bvid(bvid) or bvid
                            
                            v_info_res = run_async(bilibili_service.get_video_info(bvid))
                            if not v_info_res['success']:
                                result = f"获取视频信息失败: {v_info_res['error']}"
                            else:
                                v_info = v_info_res['data']
                                v_title = v_info.get('title', bvid)
                                yield {'type': 'tool_progress', 'tool': func_name, 'bvid': bvid, 'title': v_title, 'message': f'正在搜集视频《{v_title}》的详情...'}
                                
                                import asyncio
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
                                
                                # 智能小UP使用简化的分析提示词以提高速度
                                analysis_prompt = f"请简要总结视频《{v_title}》中关于“{question}”的相关信息。如果没有相关信息，请说明。内容要精炼。"
                                
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
                                    if not analysis_chunk.choices: continue
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
            print(f"[错误] 智能小UP失败: {error_msg}")
            import traceback
            traceback.print_exc()
            yield {'type': 'error', 'error': error_msg}

    def deep_research_stream(self, topic: str, bilibili_service) -> Generator[Dict, None, None]:
        """深度研究 Agent 逻辑"""
        try:
            from src.backend.bilibili_service import run_async
            from datetime import datetime
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            system_prompt = f"""你是一个顶级的深度研究专家。你的任务是针对用户给出的课题进行全方位的深度调研，并撰写一份具有专业深度的研究报告。
现在的时间是：{current_time}。请确保研究内容具有时效性。

【核心原则：思维链 (COT) 与 思维树 (TOT)】
1. **多路径探索**：在每一轮决策前，请先内部模拟 2-3 种不同的调研路径（TOT），选择信息增益最大的路径。
2. **深度推理**：在调用工具前，必须详细说明你的推理逻辑（COT），解释为什么这个特定的视频或搜索词能够填补当前的信息缺口。
3. **信息饱和度评估**：在决定是否结束研究前，请评估当前收集的信息是否已经达到“饱和”。如果新搜索到的资料无法提供显著的新观点或数据，则视为信息饱和。

【核心指令】
1. **拆分研究方向**：首先将课题拆分为 **至少 5 个** 具体的、互补的研究维度（上不封顶，模型应根据课题深度自行决定维度数量）。
2. **全网联动调研与并行执行**：你可以自由、灵活地结合 B 站视频搜索与 Exa 全网搜索。**为了最大限度提高效率，请务必充分利用并行调用能力**，在单轮回复中同时执行多个工具调用（例如：同时搜索多个不同的关键词，或在请求分析视频的同时发起网页搜索）。不要拘泥于先后顺序，应根据信息需求交叉验证。
3. **深入分析 B 站生态**：
    - **阅读量要求**：你**必须**至少深入分析 5 个以上的 B 站视频。
    - **舆情洞察**：**必须** 结合视频下的“高赞评论”和“弹幕热梗”来分析大众对该课题的普遍看法和舆情趋势。
    - **UP 主深度挖掘**：如果你发现某个 UP 主是该领域的专家，可以使用 `search_users` 找到他，并用 `get_user_recent_videos` 查看他的更多相关作品，以便获取更系统、更具连贯性的专业信息。
4. **综合联网搜索**：使用 `web_search` 来补充背景知识、最新新闻、技术文档或 B 站以外的深度分析。
5. **严禁直接总结**：**绝对禁止** 在没有调用 `finish_research_and_write_report` 工具的情况下直接给出研究报告。只有调用该工具后，你才会正式进入“撰写报告”阶段。
6. **工具使用说明**：
   - `search_videos`: 搜索与研究维度相关的 B 站视频。
   - `analyze_video`: 对指定的 B 站视频进行深度 AI 内容分析（包含视觉、字幕、评论、弹幕）。
   - `web_search`: 使用 Exa AI 进行全网深度搜索。
   - `search_users`: 根据昵称模糊搜索 B 站 UP 主。
   - `get_user_recent_videos`: 获取指定 UP 主（UID）的最近投稿视频列表。
   - `finish_research_and_write_report`: **必须调用**。仅在资料搜集完全充足时调用，调用后将撰写最终报告。

【最终报告规范】
1. **深度与篇幅（极重要）**：每一章节必须 **非常详尽**，内容越丰富越好。**绝对禁止** 仅使用简短的列表（Bullet points）加几句话的形式作为主体。必须撰写 **长篇幅、连贯、专业** 的段落进行深度论述，对每个观点进行充分的展开和论证。
2. **格式化要求 (极重要)**：
    - **大量使用加粗**：对核心观点、关键数据、重要结论进行 **加粗处理**。
    - **必须包含至少一个 Markdown 表格** 用于多维度横向对比。
    - 适当使用引用（Blockquotes）来强调专家结论或典型评论。
    - **文内引用**：在报告正文中引用特定观点、数据或案例时，**必须** 使用 Markdown 链接或脚注形式（如 `[标题](URL)` 或 `[^1]`）明确指向文末的参考来源，确保论据有据可查。
    - 确保层级分明，使用二级标题（##）和三级标题（###）。
3. **结构化呈现**：
    - **研究摘要**：置于顶部，高度凝练核心发现。
    - **详细章节**：针对每个研究方向，进行详细讲解。
    - **舆情洞察与用户观点**：汇总分析 B 站用户在相关视频下的评论倾向、弹幕热词以及讨论热度。
    - **参考来源列表**：末尾必须列出所有参考视频和网页链接。

【研究课题】
{topic}
"""
            
            tools = [
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
                                "mid": {"type": "integer", "description": "UP 主的 UID (mid)"},
                                "limit": {"type": "integer", "description": "获取视频的数量，默认 10", "default": 10}
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

            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"请针对以下课题开始深度研究：{topic}"}]
            
            # 最大轮次限制，防止无限循环
            max_rounds = 100 # 深度研究提升至 100 轮
            round_count = 0
            
            for _ in range(max_rounds):
                round_count += 1
                yield {'type': 'round_start', 'round': round_count}
                
                # 调优：使用研究模型开始推理
                stream = self.client.chat.completions.create(
                    model=self.research_model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    stream=True
                )

                tool_calls = []
                full_content = ""
                
                # 发送开始思考信号
                for chunk in stream:
                    if not chunk.choices: continue
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
                    # 核心修复：如果模型直接给出了内容但没有调用 finish 工具，我们强制它调用或者补一轮
                    if not any(msg.get('role') == 'tool' and msg.get('name') == 'finish_research_and_write_report' for msg in messages):
                         if round_count < max_rounds:
                            messages.append({"role": "assistant", "content": full_content})
                            messages.append({"role": "user", "content": "研究尚未结束。请继续使用工具（如搜索相关视频、分析视频、搜索UP主或作品集）进行深入调研。只有当你认为资料完全充足时，请【务必调用】`finish_research_and_write_report` 工具来启动正式报告的撰写。不要直接在对话中结束。"})
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
                    import json
                    try:
                        args = json.loads(tool_call["function"]["arguments"])
                    except:
                        args = {}
                    
                    yield {'type': 'tool_start', 'tool': func_name, 'args': args}
                    
                    result = ""
                    try:
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
                            search_res = self._web_search_exa(query)
                            if search_res['success']:
                                result = json.dumps(search_res['data'], ensure_ascii=False)
                                yield {'type': 'tool_result', 'tool': func_name, 'result': search_res['data']}
                            else:
                                result = f"网络搜索失败: {search_res['error']}"
                                yield {'type': 'error', 'error': result}
                        
                        elif func_name == "analyze_video":
                            bvid = args.get("bvid")
                            # 极致加固：清理 BVID，防止 Agent 传错格式
                            if bvid and ('bilibili.com' in bvid or 'http' in bvid):
                                from src.backend.bilibili_service import BilibiliService
                                bvid = BilibiliService.extract_bvid(bvid) or bvid
                            
                            print(f"[工具] 深度研究 Agent 发起视频分析: {bvid}")
                            
                            # 1. 获取视频信息 (这一步很快，先拿基础信息)
                            v_info_res = run_async(bilibili_service.get_video_info(bvid))
                            if not v_info_res['success']:
                                result = f"获取视频信息失败: {v_info_res['error']}"
                            else:
                                v_info = v_info_res['data']
                                v_title = v_info.get('title', bvid)
                                
                                # 2. 并行获取所有多维内容 (字幕 + 弹幕 + 评论 + 关键帧)
                                # 显著优化：由串行改为并发，大幅减少阻塞时间
                                yield {'type': 'tool_progress', 'tool': func_name, 'bvid': bvid, 'title': v_title, 'message': f'已获取视频标题: {v_title}。正在搜集全维信息...'}
                                
                                import asyncio
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
                                
                                prompt = self._build_full_analysis_prompt(
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
                                    model=self.model,
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
                                    if not analysis_chunk.choices: continue
                                    delta = analysis_chunk.choices[0].delta
                                    if delta.content:
                                        result_text += delta.content
                                        # 实时反馈 token 增长及内容片段（用于幻影流式预览）
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
                            is_final_report_triggered = True
                            yield {'type': 'tool_result', 'tool': func_name, 'result': '进入撰写报告阶段...'}

                    except Exception as e:
                        result = f"执行工具出错: {str(e)}"
                        yield {'type': 'error', 'error': result}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": func_name,
                        "content": result
                    })
                
                # 如果触发了最终报告撰写，进入最后一段生成
                if is_final_report_triggered:
                    yield {'type': 'report_start'}
                    final_stream = self.client.chat.completions.create(
                        model=self.research_model,
                        messages=messages,
                        stream=True
                    )
                    final_report = ""
                    for chunk in final_stream:
                        if not chunk.choices: continue
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                            yield {'type': 'thinking', 'content': delta.reasoning_content}
                        if delta.content:
                            final_report += delta.content
                            yield {'type': 'content', 'content': delta.content}
                    
                    # 持久化报告 (Markdown 和 PDF)
                    try:
                        self._save_research_report(topic, final_report)
                    except Exception as e:
                        print(f"[警告] 保存报告失败: {e}")
                    
                    break

            yield {'type': 'done'}

        except Exception as e:
            print(f"[错误] 深度研究失败: {str(e)}")
            import traceback
            traceback.print_exc()
            yield {'type': 'error', 'error': str(e)}

    def _save_research_report(self, topic: str, content: str):
        """将研究报告保存到本地并生成 PDF"""
        import os
        from datetime import datetime
        import re
        
        report_dir = "research_reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        # 清理文件名
        safe_topic = re.sub(r'[\\/*?:"<>|]', '_', topic)[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"{timestamp}_{safe_topic}"
        
        # 1. 保存 Markdown
        md_filepath = os.path.join(report_dir, f"{filename_base}.md")
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(f"# 研究课题：{topic}\n")
            f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(content)
        
        # 2. 生成 PDF
        try:
            pdf_path = os.path.join(report_dir, f"{filename_base}.pdf")
            self._generate_bili_style_pdf(topic, content, pdf_path)
        except Exception as e:
            print(f"[警告] PDF 生成失败: {e}")
        
        print(f"[信息] 研究报告已持久化: {md_filepath}")

    def _web_search_exa(self, query: str) -> Dict:
        """使用 Exa AI 进行网络搜索"""
        try:
            import requests
            api_key = Config.EXA_API_KEY
            if not api_key:
                return {'success': False, 'error': '未配置 Exa API Key'}

            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "query": query,
                "useAutoprompt": True,
                "numResults": 5,
                "type": "neural"
            }
            
            print(f"[工具] Exa 网络搜索: {query}")
            response = requests.post("https://api.exa.ai/search", json=payload, headers=headers, timeout=20)
            res_data = response.json()
            
            if response.status_code == 200 and 'results' in res_data:
                results = []
                for item in res_data['results']:
                    results.append({
                        'title': item.get('title', '无标题'),
                        'url': item.get('url', ''),
                        'published_date': item.get('publishedDate', '未知')
                    })
                return {'success': True, 'data': results}
            else:
                return {'success': False, 'error': res_data.get('error', '未知错误')}
        except Exception as e:
            print(f"[错误] Exa 搜索失败: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_bili_style_pdf(self, topic: str, content: str, output_path: str):
        """生成 Bilibili 风格的 PDF 报告"""
        try:
            import markdown2
            from xhtml2pdf import pisa
            from datetime import datetime
            import os
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.fonts import addMapping
            
            # --- 1. 更加健壮的字体注册逻辑 ---
            font_registered = False
            current_font_name = "SimHei" # 默认使用黑体，因为它是 .ttf 格式，兼容性最好
            
            # 路径列表 (Windows) - 优先选择 .ttf 格式避开权限问题
            font_configs = [
                ("SimHei", "C:/Windows/Fonts/simhei.ttf"), # 黑体 (.ttf) - 兼容性王者
                ("YaHei", "C:/Windows/Fonts/msyh.ttc"),    # 微软雅黑 (.ttc)
                ("SimSun", "C:/Windows/Fonts/simsun.ttc")   # 宋体 (.ttc)
            ]
            
            for name, path in font_configs:
                if os.path.exists(path):
                    try:
                        # 注册字体
                        from reportlab.pdfbase.ttfonts import TTFont
                        pdfmetrics.registerFont(TTFont(name, path))
                        
                        # 强制映射加粗、斜体到同一个字体文件，防止跳回 Helvetica
                        addMapping(name, 0, 0, name) # normal
                        addMapping(name, 1, 0, name) # bold
                        addMapping(name, 0, 1, name) # italic
                        addMapping(name, 1, 1, name) # bold italic
                        
                        current_font_name = name
                        font_registered = True
                        print(f"[PDF] 成功注册并映射字体: {name} (路径: {path})")
                        break # 只要注册成功一个就退出循环
                    except Exception as e:
                        print(f"[PDF] 尝试注册字体 {name} 失败: {e}")
            
            if not font_registered:
                # 最后的保底：使用内置的 STSong-Light (无需外部文件)
                from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
                current_font_name = "STSong-Light"
                print(f"[PDF] 未找到系统字体，使用内置保底字体: {current_font_name}")

            # --- 2. 准备 HTML 内容 ---
            # 强化加粗内容的样式，使其在 PDF 中呈现 B 站粉色
            html_content = markdown2.markdown(content, extras=["tables", "fenced-code-blocks", "break-on-newline"])
            
            # 注入项目 LOGO (SVG 路径)
            logo_svg = """
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="40" height="40" rx="8" fill="#FB7299"/>
                <path d="M11 15H29V27H11V15Z" fill="white"/>
                <path d="M14 11L18 15" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
                <path d="M26 11L22 15" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
                <circle cx="16" cy="20" r="1.5" fill="#FB7299"/>
                <circle cx="24" cy="20" r="1.5" fill="#FB7299"/>
                <path d="M18 23.5H22" stroke="#FB7299" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            """

            # Bilibili 风格 CSS
            # 关键修复：添加 -pdf-font-encoding: identity-H; 以支持中文字符
            bili_css = f"""
            @page {{
                size: a4;
                margin: 2cm;
                @frame footer {{
                    -pdf-frame-content: footerContent;
                    bottom: 1cm;
                    margin-left: 2cm;
                    margin-right: 2cm;
                    height: 1cm;
                }}
            }}
            body {{
                font-family: "{current_font_name}";
                -pdf-font-encoding: identity-H;
                color: #18191C;
                line-height: 1.6;
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #FB7299;
                padding-bottom: 20px;
                margin-bottom: 30px;
                position: relative;
            }}
            .logo-box {{
                margin-bottom: 10px;
            }}
            .logo-text {{
                color: #FB7299;
                font-size: 24px;
                font-weight: bold;
            }}
            h1 {{ 
                color: #FB7299; 
                font-size: 26px; 
                margin-top: 10px;
                font-family: "{current_font_name}";
                -pdf-font-encoding: identity-H;
            }}
            h2 {{ 
                color: #00AEEC; 
                border-left: 5px solid #00AEEC; 
                padding-left: 10px; 
                margin-top: 25px; 
                font-size: 20px; 
                font-family: "{current_font_name}";
                -pdf-font-encoding: identity-H;
            }}
            h3 {{ 
                color: #18191C; 
                font-size: 18px; 
                margin-top: 20px; 
                border-bottom: 1px solid #E3E5E7; 
                padding-bottom: 5px; 
                font-family: "{current_font_name}";
                -pdf-font-encoding: identity-H;
            }}
            p {{ 
                margin-bottom: 12px; 
                font-size: 13px; 
                text-align: justify; 
                font-family: "{current_font_name}";
                -pdf-font-encoding: identity-H;
            }}
            
            /* 强化加粗样式：B站粉色且加粗 */
            strong, b {{
                color: #FB7299;
                font-weight: bold;
                font-family: "{current_font_name}";
                -pdf-font-encoding: identity-H;
            }}
            
            .meta {{
                font-size: 11px;
                color: #9499A0;
                margin-bottom: 20px;
            }}
            .footer {{
                text-align: center;
                font-size: 10px;
                color: #9499A0;
                border-top: 1px solid #E3E5E7;
                padding-top: 10px;
            }}
            blockquote {{
                background-color: #F6F7F8;
                border-left: 4px solid #FB7299;
                padding: 10px 20px;
                margin: 20px 0;
                font-style: italic;
                color: #61666D;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 11px;
            }}
            th {{
                background-color: #FB7299;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #FB7299;
                font-family: "{current_font_name}";
                -pdf-font-encoding: identity-H;
            }}
            td {{
                padding: 8px;
                border: 1px solid #E3E5E7;
                text-align: left;
                font-family: "{current_font_name}";
                -pdf-font-encoding: identity-H;
            }}
            tr:nth-child(even) {{
                background-color: #FAFAFA;
            }}
            img {{
                max-width: 100%;
            }}
            """
            
            full_html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>{bili_css}</style>
            </head>
            <body>
                <div class="header">
                    <div class="logo-box">
                        <div style="background-color: #FB7299; padding: 10px; border-radius: 8px; display: inline-block; margin-bottom: 5px;">
                            <span style="color: white; font-size: 20px; font-weight: bold;">BiliBili Summarize</span>
                        </div>
                    </div>
                    <h1>{topic}</h1>
                    <div class="meta">
                        报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                        AI 深度研究专家 | 
                        内容驱动：Bilibili Data
                    </div>
                </div>
                
                <div class="content">
                    {html_content}
                </div>
                
                <div id="footerContent" class="footer">
                    © 2025 BiliBili Summarize - 掌握视频，深挖价值 | 由 AI 驱动的深度研究引擎 | 第 <pdf:pagenumber> 页
                </div>
            </body>
            </html>
            """
            
            # 生成 PDF
            with open(output_path, "wb") as f:
                # 关键：指定 encoding='utf-8' 并在 pisa 中处理
                pisa_status = pisa.CreatePDF(
                    full_html, 
                    dest=f, 
                    encoding='utf-8'
                )
                
            if pisa_status.err:
                print(f"[错误] PDF 生成过程中出现错误")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"PDF 渲染出错: {str(e)}")

    def chat_stream(self, question: str, context: str, video_info: Dict, history: List[Dict] = None) -> Generator[Dict, None, None]:
        """视频内容流式问答
        
        Args:
            question: 用户提问
            context: 视频分析结果上下文
            video_info: 视频基本信息
            history: 对话历史
        """
        try:
            # 安全检查：确保 video_info 不为 None
            if video_info is None:
                video_info = {}
                
            system_prompt = f"""你是一个基于B站视频分析结果的问答助手。

【核心指令】
1. **绝对忠于上下文**：你的知识库仅限于下方提供的【视频分析报告】。
2. **严禁编造**：如果报告中没有提到用户提问的细节（如具体的数字、人名、画面细节等），你**必须**回答“根据当前的分析报告，我没有找到相关信息”，严禁基于常识或猜测进行回答。
3. **不确定性处理**：如果信息模糊，请如实描述报告中的模糊之处，不要将其确认为事实。

【视频基本信息】
标题: {video_info.get('title', '未知')}
UP主: {video_info.get('author', '未知')}

【视频分析报告】
{context}
"""
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加历史记录
            if history:
                messages.extend(history)
            
            # 添加当前问题
            messages.append({"role": "user", "content": question})

            stream = self.client.chat.completions.create(
                model=self.qa_model,
                messages=messages,
                temperature=0.4, # QA可以稍微高一点点保持对话连贯，但仍需控制在低位
                stream=True
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield {'type': 'content', 'content': delta.content}
            
            yield {'type': 'done'}

        except Exception as e:
            print(f"[错误] QA问答失败: {str(e)}")
            yield {'type': 'error', 'error': str(e)}

    def generate_summary(self, video_info: Dict, content: str) -> Dict:
        """生成视频总结"""
        try:
            # 构建提示词
            prompt = self._build_summary_prompt(video_info, content)
            
            # 调用大模型
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的视频内容分析助手，擅长总结视频内容并提取关键信息。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            # 处理不同API响应格式
            summary_text = self._extract_content(response)
            tokens_used = self._extract_tokens(response)
            
            return {
                'success': True,
                'data': {
                    'summary': summary_text,
                    'tokens_used': tokens_used
                }
            }
        except Exception as e:
            print(f"[错误] 生成总结失败: {str(e)}")
            print(f"[调试] 错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'生成总结失败: {str(e)}'
            }
    
    def generate_mindmap(self, video_info: Dict, content: str, summary: Optional[str] = None) -> Dict:
        """生成思维导图（Markdown格式）"""
        try:
            prompt = self._build_mindmap_prompt(video_info, content, summary)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的思维导图设计师，擅长将复杂内容结构化为清晰的思维导图。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # 处理不同API响应格式
            mindmap_text = self._extract_content(response)
            tokens_used = self._extract_tokens(response)
            
            return {
                'success': True,
                'data': {
                    'mindmap': mindmap_text,
                    'tokens_used': tokens_used
                }
            }
        except Exception as e:
            print(f"[错误] 生成思维导图失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'生成思维导图失败: {str(e)}'
            }
    
    def generate_full_analysis(self, video_info: Dict, content: str, video_frames: Optional[list] = None, retry_count: int = 0) -> Dict:
        """生成完整分析（包括总结和思维导图）

        Args:
            video_info: 视频信息
            content: 文本内容（字幕/弹幕）
            video_frames: 可选的视频帧（base64编码列表）
        """
        try:
            print(f"[调试] 开始生成分析 - 模型: {self.model}")
            print(f"[调试] API Base: {Config.OPENAI_API_BASE}")
            print(f"[调试] 视频帧数量: {len(video_frames) if video_frames else 0}")

            # 构建综合提示词（支持弹幕内容）
            danmaku_preview = None
            if content and '【弹幕内容（部分）】' in content:
                # 提取弹幕预览用于分析
                danmaku_preview = content
            prompt = self._build_full_analysis_prompt(video_info, content, has_video_frames=bool(video_frames), danmaku_content=danmaku_preview)
            print(f"[调试] 提示词长度: {len(prompt)}")

            # 构建消息内容 - 适配新的多模态格式
            user_content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]

            # 添加视频帧（如果有的话）
            if video_frames and len(video_frames) > 0:
                for idx, frame_base64 in enumerate(video_frames):
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{frame_base64}",
                            "detail": "low"  # 使用low detail以节省token
                        }
                    })
                    print(f"[调试] 添加第 {idx+1} 帧到消息中")

            # 使用新的消息格式调用API
            messages = [
                {
                    "role": "system",
                    "content": """你是一位资深的B站视频内容分析专家，擅长：
1. 深度内容解析 - 提取所有知识点、分析目的和含义
2. 结构化呈现 - 清晰的思维导图和层次结构
3. 互动数据分析 - 弹幕情感、热点、词云分析
4. 综合评价 - 多维度评分和学习建议

你能同时分析视频画面、文字内容和弹幕互动，提供全面、专业、易读的四大板块分析报告。
请严格按照要求的四大板块结构输出，内容详实、格式规范、逻辑清晰。"""
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ]

            print(f"[调试] 发送请求到API...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,  # 极致优化：极低温度减少幻觉
                max_tokens=8000,
                timeout=240
            )
            
            print(f"[调试] API响应类型: {type(response)}")
            print(f"[调试] API响应前100字符: {str(response)[:100]}")
            
            # 处理不同API响应格式
            analysis_text = self._extract_content(response)
            tokens_used = self._extract_tokens(response)
            
            # 尝试解析结构化内容
            parsed_content = self._parse_analysis_response(analysis_text)
            
            return {
                'success': True,
                'data': {
                    'full_analysis': analysis_text,
                    'parsed': parsed_content,
                    'tokens_used': tokens_used
                }
            }
        except Exception as e:
            print(f"[错误] 生成完整分析失败: {str(e)}")
            print(f"[调试] 错误类型: {type(e).__name__}")

            # 针对网络和超时错误的特殊处理
            if any(keyword in str(e).lower() for keyword in ['timeout', 'connection', 'network', '504', '502', '500']):
                if retry_count < 2:  # 最多重试2次
                    print(f"[重试] 检测到网络错误，正在进行第{retry_count + 1}次重试...")
                    print(f"[重试] 错误详情: {str(e)}")

                    if video_frames and len(video_frames) > 4:  # 如果帧数太多，减少到4帧
                        reduced_frames = video_frames[:4]
                        print(f"[降级] 减少视频帧数量: {len(video_frames)} → {len(reduced_frames)}")
                        return self.generate_full_analysis(video_info, content, reduced_frames, retry_count + 1)
                    elif video_frames and retry_count == 0:  # 第一次重试，去除视频帧
                        print(f"[降级] 放弃视频帧，仅使用文本分析")
                        return self.generate_full_analysis(video_info, content, None, retry_count + 1)

            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'生成分析失败: {str(e)}'
            }

    def generate_full_analysis_stream(self, video_info: Dict, content: str, video_frames: Optional[list] = None,
                                    progress_callback: Optional[Callable] = None) -> Generator[Dict, None, None]:
        """流式生成完整分析，支持实时进度回调

        Args:
            video_info: 视频信息
            content: 文本内容（字幕/弹幕）
            video_frames: 可选的视频帧（base64编码列表）
            progress_callback: 进度回调函数，接收 (stage, progress, message, tokens_used)

        Yields:
            Dict: 包含状态、进度、内容块等信息的字典
        """
        try:
            # 发送开始信号
            yield {
                'type': 'start',
                'stage': 'preparing',
                'progress': 0,
                'message': '准备生成分析...',
                'tokens_used': 0,
                'timestamp': time.time()
            }

            if progress_callback:
                progress_callback('preparing', 0, '准备生成分析...', 0)

            print(f"[调试] 开始流式生成分析 - 模型: {self.model}")
            print(f"[调试] API Base: {Config.OPENAI_API_BASE}")
            print(f"[调试] 视频帧数量: {len(video_frames) if video_frames else 0}")

            # 构建综合提示词
            danmaku_preview = None
            if content and '【弹幕内容（部分）】' in content:
                danmaku_preview = content
            prompt = self._build_full_analysis_prompt(video_info, content, has_video_frames=bool(video_frames), danmaku_content=danmaku_preview)

            yield {
                'type': 'progress',
                'stage': 'building_prompt',
                'progress': 10,
                'message': '构建分析提示词...',
                'tokens_used': 0,
                'timestamp': time.time()
            }

            if progress_callback:
                progress_callback('building_prompt', 10, '构建分析提示词...', 0)

            # 构建消息内容
            user_content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]

            # 添加视频帧
            if video_frames and len(video_frames) > 0:
                for idx, frame_base64 in enumerate(video_frames):
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{frame_base64}",
                            "detail": "low"
                        }
                    })
                    print(f"[调试] 添加第 {idx+1} 帧到消息中")

            messages = [
                {
                    "role": "system",
                    "content": """你是一位资深的B站视频内容分析专家，擅长：
1. 深度内容解析 - 提取所有知识点、分析目的和含义
2. 结构化呈现 - 清晰的思维导图和层次结构
3. 互动数据分析 - 弹幕情感、热点、词云分析
4. 综合评价 - 多维度评分和学习建议

你能同时分析视频画面、文字内容和弹幕互动，提供全面、专业、易读的四大板块分析报告。
请严格按照要求的四大板块结构输出，内容详实、格式规范、逻辑清晰。"""
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ]

            yield {
                'type': 'progress',
                'stage': 'calling_api',
                'progress': 20,
                'message': '调用AI模型生成分析...',
                'tokens_used': 0,
                'timestamp': time.time()
            }

            if progress_callback:
                progress_callback('calling_api', 20, '调用AI模型生成分析...', 0)

            print(f"[调试] 发送流式请求到API...")

            # 流式调用API
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # 极致优化：低温度降低流式输出幻觉
                max_tokens=8000,
                timeout=240,
                stream=True  # 启用流式传输
            )

            full_content = ""
            chunk_count = 0
            last_progress_update = time.time()

            yield {
                'type': 'progress',
                'stage': 'streaming',
                'progress': 30,
                'message': '正在接收AI分析结果...',
                'tokens_used': 0,
                'timestamp': time.time()
            }

            if progress_callback:
                progress_callback('streaming', 30, '正在接收AI分析结果...', 0)

            # 处理流式响应
            for chunk in stream:
                chunk_count += 1

                # 提取内容块
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_piece = delta.content
                        full_content += content_piece

                        # 每隔一定时间或一定数量的chunk发送进度更新
                        current_time = time.time()
                        if current_time - last_progress_update > 0.5 or chunk_count % 10 == 0:
                            progress = min(30 + (chunk_count * 2), 90)  # 30%-90%

                            yield {
                                'type': 'progress',
                                'stage': 'streaming',
                                'progress': progress,
                                'message': f'正在深度解析内容...',
                                'tokens_used': chunk_count * 10,  # 估算token数
                                'content_length': len(full_content),
                                'timestamp': current_time
                            }

                            if progress_callback:
                                progress_callback('streaming', progress, f'正在深度解析内容...', chunk_count * 10)

                            last_progress_update = current_time

                # 发送内容块（可选，用于实时显示部分内容）
                if chunk_count % 20 == 0:  # 每20个chunk发送一次内容预览
                    yield {
                        'type': 'content_preview',
                        'stage': 'streaming',
                        'progress': min(30 + (chunk_count * 2), 90),
                        'message': '更新内容预览...',
                        'content_preview': full_content[-500:] if len(full_content) > 500 else full_content,
                        'content_length': len(full_content),
                        'timestamp': time.time()
                    }

            # 最终处理
            yield {
                'type': 'progress',
                'stage': 'processing',
                'progress': 95,
                'message': '处理最终结果...',
                'tokens_used': chunk_count * 10,
                'timestamp': time.time()
            }

            if progress_callback:
                progress_callback('processing', 95, '处理最终结果...', chunk_count * 10)

            # 解析最终结果
            parsed_content = self._parse_analysis_response(full_content)
            total_tokens = chunk_count * 15  # 更准确的token估算

            yield {
                'type': 'complete',
                'stage': 'completed',
                'progress': 100,
                'message': '分析完成！',
                'tokens_used': total_tokens,
                'content_length': len(full_content),
                'full_analysis': full_content,
                'parsed': parsed_content,
                'chunk_count': chunk_count,
                'timestamp': time.time()
            }

            if progress_callback:
                progress_callback('completed', 100, '分析完成！', total_tokens)

            print(f"[调试] 流式分析完成 - 总共 {chunk_count} 个chunk, 约 {total_tokens} tokens")

        except Exception as e:
            print(f"[错误] 流式生成分析失败: {str(e)}")
            print(f"[调试] 错误类型: {type(e).__name__}")

            # 错误处理和降级策略
            if any(keyword in str(e).lower() for keyword in ['timeout', 'connection', 'network', '504', '502', '500']):
                yield {
                    'type': 'error',
                    'stage': 'retrying',
                    'progress': 0,
                    'message': f'网络错误，尝试降级处理... 错误: {str(e)}',
                    'error_type': 'network',
                    'timestamp': time.time()
                }

                # 降级到文本分析
                if video_frames:
                    yield {
                        'type': 'progress',
                        'stage': 'fallback',
                        'progress': 10,
                        'message': '降级到纯文本分析...',
                        'timestamp': time.time()
                    }

                    # 递归调用，不使用视频帧
                    yield from self.generate_full_analysis_stream(video_info, content, None, progress_callback)
                    return

            import traceback
            traceback.print_exc()

            yield {
                'type': 'error',
                'stage': 'failed',
                'progress': 0,
                'message': f'分析失败: {str(e)}',
                'error_type': type(e).__name__,
                'timestamp': time.time()
            }

    def generate_article_analysis_stream(self, article_info: Dict, content: str) -> Generator[Dict, None, None]:
        """专栏文章深度分析"""
        try:
            if article_info is None:
                article_info = {}
            prompt = f"""你是一位专业的深度报道评论员。请为以下B站专栏文章生成一份详尽的分析报告。

【文章信息】
标题：{article_info.get('title', '未知')}
作者：{article_info.get('author', '未知')}

【文章完整内容】
{content[:Config.MAX_SUBTITLE_LENGTH]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
请严格按照以下结构提供分析报告：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 文章深度解析
- **核心论点**：用一句话概括文章想要表达的最核心观点。
- **内容精要**：系统性地总结文章的分点论述，逻辑清晰，内容充实。
- **深度点评**：分析文章的写作风格、专业深度以及对行业/读者的启发意义。

## 💡 知识图谱
- 提取并解释文章中提到的专业术语或背景知识。

## 🚀 阅读建议
- 适合哪类人群深度阅读？
- 相关的延伸阅读方向。
"""
            messages = [
                {"role": "system", "content": "你是一位资深的B站专栏分析专家，擅长逻辑分析与深度总结。"},
                {"role": "user", "content": prompt}
            ]

            stream = self.client.chat.completions.create(
                model=self.qa_model, # 使用逻辑更强的QA模型进行文章分析
                messages=messages,
                temperature=0.3,
                stream=True
            )

            full_content = ""
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_content += delta.content
                        yield {'type': 'content', 'content': delta.content}
            
            # 解析文章内容
            sections = {'summary': full_content, 'danmaku': '专栏文章暂无弹幕分析', 'comments': '专栏文章暂无评论分析'}
            yield {'type': 'final', 'parsed': sections, 'full_analysis': full_content}

        except Exception as e:
            yield {'type': 'error', 'error': str(e)}

    def generate_user_analysis(self, user_info: Dict, recent_videos: List[Dict]) -> Dict:
        """生成UP主深度画像（同步返回字典）"""
        try:
            videos_text = "\n".join([f"- {v['title']} (播放: {v['play']}, 时长: {v['length']})" for v in recent_videos])
            prompt = f"""你是一位资深的自媒体行业分析师。请根据以下UP主的公开信息和近期作品数据，生成一份**深度、专业且具有洞察力**的UP主画像报告。

【UP主基础信息】
- 昵称：{user_info.get('name')}
- 签名：{user_info.get('sign')}
- 等级：L{user_info.get('level')}
- 认证信息：{user_info.get('official') or '普通用户'}

【近期作品数据（采样）】
{videos_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
请按以下结构输出深度分析（使用 Markdown 格式，多用 Emoji）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🎭 创作者标签
- 用 3-5 个关键词精准定义该 UP 主（如：硬核技术流、极简主义者、高产赛母猪等）。

### 📈 内容风格与调性
- 分析其视频的标题风格、选题偏好及内容深度。
- 观察其作品的生命力（从播放量与选题的关联度分析）。

### 💎 核心价值主张
- 该 UP 主为粉丝提供了什么独特价值？（是知识获取、情绪价值还是审美共鸣？）

### 🚀 发展潜力评估
- 基于近期作品的表现，分析其内容的垂直度及未来增长空间。

### 💡 合作/关注建议
- 给想关注该 UP 主或与其合作的品牌方提供一条诚恳的建议。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
请保持专业、客观且富有文学色彩的笔触，字数在 300-500 字左右。"""
            
            response = self.client.chat.completions.create(
                model=self.qa_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=1000
            )
            
            content = self._extract_content(response)
            tokens = self._extract_tokens(response)
            
            return {
                'portrait': content,
                'tokens_used': tokens
            }
        except Exception as e:
            return {
                'portrait': f"暂时无法生成UP主画像: {str(e)}",
                'tokens_used': 0
            }
    
    def _build_summary_prompt(self, video_info: Dict, content: str) -> str:
        """构建总结提示词"""
        return f"""请为以下B站视频生成详细的总结报告：

【视频信息】
标题：{video_info.get('title', '未知')}
作者：{video_info.get('author', '未知')}
简介：{video_info.get('desc', '无')}

【视频内容】
{content[:Config.MAX_SUBTITLE_LENGTH]}

请提供以下内容：
1. **内容概述**（3-5句话概括视频主要内容）
2. **详细总结**（按逻辑结构详细总结视频内容，分段呈现）
3. **关键要点**（列出5-10个核心知识点）
4. **适用人群**（说明这个视频适合什么人观看）
5. **学习建议**（给出具体的学习建议）

请用清晰的Markdown格式输出，使用标题、列表等格式化元素。"""
    
    def _build_mindmap_prompt(self, video_info: Dict, content: str, summary: Optional[str]) -> str:
        """构建思维导图提示词"""
        base_content = f"""请为以下视频内容生成思维导图（使用Markdown格式）：

【视频标题】
{video_info.get('title', '未知')}

【视频内容】
{content[:Config.MAX_SUBTITLE_LENGTH]}
"""
        
        if summary:
            base_content += f"\n【已有总结】\n{summary}\n"
        
        base_content += """
请用Markdown格式的层级列表生成思维导图，结构清晰，层次分明。

格式示例：
# 视频标题
## 第一部分：核心概念
- 要点1
  - 子要点1.1
  - 子要点1.2
- 要点2
## 第二部分：具体内容
- 要点3
  - 子要点3.1

请确保：
1. 最多4层层级
2. 每个节点简洁明了
3. 逻辑结构清晰
4. 涵盖主要内容"""
        
        return base_content
    
    def _build_full_analysis_prompt(self, video_info: Dict, content: str, has_video_frames: bool = False, danmaku_content: str = None) -> str:
        """构建完整分析提示词（极致防幻觉优化版）"""
        video_analysis_hint = ""
        if has_video_frames:
            video_analysis_hint = """

**视觉分析指令 (重要)**：
- 我提供了视频的关键帧截图。
- 只有在画面中**明确看到**的元素（如具体的PPT文字、代码片段、特定的人物动作、图标）才能写入报告。
- 禁止脑补画面中没有出现的背景或细节。
"""
        
        danmaku_hint = ""
        if danmaku_content:
            danmaku_hint = f"""

【弹幕内容预览】
{danmaku_content[:500]}...
"""
        
        comments_hint = ""
        if content and '【视频评论（部分）】' in content:
             comments_hint = "\n我已经提供了部分精彩评论内容，请在第三板块进行深入分析。"

        return f"""你是一位严谨的B站视频分析专家。你的任务是基于我提供的素材生成一份**准确无误**的报告。

【分析准则 - 严禁幻觉】
1. **仅限素材**：所有结论必须直接来源于提供的【视频信息】、【视频内容（字幕/文案）】、【关键帧】或【弹幕评论】。
2. **禁止推测**：如果素材中没有提到某项数据（如具体收入、未公开的日期、未提及的品牌等），严禁编造。
3. **视觉一致性**：如果字幕内容与画面内容冲突，以画面显示的文字/实物为准，并注明。
4. **诚实告知**：如果某个分析点在素材中完全缺失，请直接跳过或说明“素材未提及”。

【视频基本信息】
标题：{video_info.get('title', '未知')}
UP主：{video_info.get('author', '未知')}
视频简介：{video_info.get('desc', '无')}

【视频完整内容（字幕/文案）】
{content[:Config.MAX_SUBTITLE_LENGTH]}{video_analysis_hint}{danmaku_hint}{comments_hint}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
请严格按照以下**三大板块**提供深度分析报告：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 第一板块：内容深度总结与分析

### 1. 视频核心概览
- **核心主旨**：用一句话精准概括视频。
- **目标价值**：视频解决了什么核心问题？为观众提供了什么独特价值（认知、技能、情感）？

### 2. 结构化内容详述
**要求**：
- 按视频逻辑逻辑，**精细化**提取核心论据、关键步骤、数据支撑和典型案例。
- 分章节进行详尽总结，字数需充实，不仅概括“讲了什么”，更要解释“是怎么讲的”以及“背后的逻辑”。
- 每个核心观点请配合对应的视频事实进行论证。

### 3. 关键知识点与深度见解
- **事实罗列**：列出视频中明确提到的知识点或重要事实。
- **深度延伸**：基于视频内容，分析其在更广阔背景下的意义，或提供补充性的背景知识。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 💬 第二板块：弹幕互动与舆情分析
- **氛围洞察**：分析弹幕的情绪曲线，识别观众在哪一时刻反响最热烈。
- **高频词云**：提取真实的重复关键词汇，并解读背后的观众心理。
- **互动槽点**：捕捉视频中的“梗”、争议点或共鸣点。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📝 第三板块：评论区深度解析与建议
- **评论画像**：分析高赞评论的构成，观众是在补充干货、表达感谢还是进行理性讨论？
- **精选解读**：深入分析提供的精彩评论，提取其中最有价值的观点或纠错信息。
- **后续优化建议**：基于目前的观众反馈，为UP主提供具体可执行的改进方案或新选题灵感。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**输出格式**：
- 使用Markdown，多用 Emoji。
- 保持专业、客观的语气。
- 如果信息不足以支撑某个子标题，请删除该标题。"""

    
    def _extract_content(self, response) -> str:
        """提取响应内容，兼容不同API格式"""
        try:
            print(f"[调试] _extract_content - 响应类型: {type(response)}")
            
            # 尝试标准OpenAI格式
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                print(f"[调试] 提取到内容长度: {len(content) if content else 0}")
                
                # 检查是否是HTML（错误响应）
                if content and content.strip().startswith('<!doctype') or content.strip().startswith('<html'):
                    raise ValueError("API返回了HTML页面而不是文本内容，请检查API配置和网络连接")
                
                return content
            
            # 如果是字符串，直接返回
            if isinstance(response, str):
                # 检查是否是HTML
                if response.strip().startswith('<!doctype') or response.strip().startswith('<html'):
                    raise ValueError("API返回了HTML页面，请检查OPENAI_API_BASE配置")
                return response
            
            # 如果是字典，尝试提取内容
            if isinstance(response, dict):
                if 'choices' in response and response['choices']:
                    return response['choices'][0]['message']['content']
                if 'content' in response:
                    return response['content']
                if 'text' in response:
                    return response['text']
                # 如果字典中有error
                if 'error' in response:
                    raise ValueError(f"API返回错误: {response['error']}")
            
            # 尝试转换为字符串
            result = str(response)
            print(f"[警告] 响应格式未知，转为字符串: {result[:200]}")
            return result
        except Exception as e:
            print(f"[错误] 提取内容失败: {str(e)}, 响应类型: {type(response)}")
            raise
    
    def _extract_tokens(self, response) -> int:
        """提取token使用量，兼容不同API格式"""
        try:
            if hasattr(response, 'usage') and response.usage:
                if hasattr(response.usage, 'total_tokens'):
                    return response.usage.total_tokens
            
            if isinstance(response, dict):
                if 'usage' in response:
                    return response['usage'].get('total_tokens', 0)
            
            return 0
        except Exception as e:
            print(f"[警告] 提取tokens失败: {str(e)}")
            return 0
    
    def _parse_analysis_response(self, analysis_text: str) -> Dict:
        """解析分析响应，提取结构化内容"""
        sections = {
            'summary': '',
            'danmaku': '',
            'comments': ''
        }
        
        current_section = None
        lines = analysis_text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            # 匹配第一板块：内容总结
            if '内容深度总结' in line or '第一板块' in line:
                current_section = 'summary'
            # 匹配第二板块：弹幕分析
            elif '弹幕互动' in line or '第二板块' in line or '舆情分析' in line:
                current_section = 'danmaku'
            # 匹配第三板块：评论分析
            elif '评论区深度' in line or '第三板块' in line or '评论解析' in line:
                current_section = 'comments'
            elif current_section:
                sections[current_section] += line + '\n'
        
        return sections

