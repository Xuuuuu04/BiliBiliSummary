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

    def generate_user_analysis(self, user_info: Dict, recent_videos: List[Dict]) -> str:
        """生成UP主深度画像（同步返回字符串）"""
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
            return self._extract_content(response)
        except Exception as e:
            return f"暂时无法生成UP主画像: {str(e)}"
    
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

