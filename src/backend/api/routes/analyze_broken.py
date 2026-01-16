"""
视频分析路由模块
提供视频分析、智能小UP和对话问答接口
"""
import asyncio
import json
from flask import request, jsonify, Response
from src.backend.utils.logger import get_logger
from src.backend.utils.validators import validate_question_input, validate_json_data, validate_bvid, ValidationError
from src.backend.utils.error_handler import ErrorResponse, handle_errors

logger = get_logger(__name__)


def init_analyze_routes(app, bilibili_service, ai_service):
    """
    初始化分析相关路由

    Args:
        app: Flask 应用实例
        bilibili_service: BilibiliService 实例
        ai_service: AIService 实例
    """
    from src.backend.services.bilibili import BilibiliService, run_async

    @app.route('/api/smart_up/stream', methods=['POST'])
    @handle_errors
    def smart_up_stream():
        """智能小UP 快速问答流"""
        # 验证输入
        data = validate_json_data(request.json, required_fields=['question'])
        question = validate_question_input(data.get('question'))
        history = data.get('history', [])

        def generate():
            try:
                for chunk in ai_service.smart_up_stream(question, bilibili_service, history):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"智能小UP流式输出错误: {str(e)}")
                yield ErrorResponse.sse_error(f"分析过程中发生错误: {str(e)}")

        return Response(generate(), mimetype='text/event-stream')

    @app.route('/api/chat/stream', methods=['POST'])
    @handle_errors
    def chat_video_stream():
        """视频内容流式问答"""
        # 验证输入
        data = validate_json_data(request.json, required_fields=['question', 'context'])
        question = validate_question_input(data.get('question'))
        context = validate_question_input(data.get('context'))
        video_info = data.get('video_info', {})
        history = data.get('history', [])

        def generate():
            try:
                for chunk in ai_service.chat_stream(question, context, video_info, history):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"视频对话流式输出错误: {str(e)}")
                yield ErrorResponse.sse_error(f"对话过程中发生错误: {str(e)}")

        return Response(generate(), mimetype='text/event-stream')

    @app.route('/api/analyze', methods=['POST'])
    @handle_errors
    def analyze_video():
        """分析视频的主接口"""
        # 验证输入
        data = validate_json_data(request.json, required_fields=['url'])
        url = data.get('url', '')

        # 提取BVID
        try:
            bvid = validate_bvid(url)
        except ValidationError as e:
            logger.error(f"无效的B站链接: {url}")
            return jsonify(ErrorResponse.error(str(e), error_code="INVALID_URL", status_code=400)[0]), 400

            # 获取视频信息
            video_info_result = run_async(bilibili_service.get_video_info(bvid))
            if not video_info_result['success']:
                return jsonify(video_info_result), 400

            video_info = video_info_result['data']

            # 获取字幕
            logger.info("开始获取字幕...")
            subtitle_result = run_async(bilibili_service.get_video_subtitles(bvid))

            # 获取弹幕（用于分析）
            logger.info("开始获取弹幕...")
            danmaku_result = run_async(bilibili_service.get_video_danmaku(bvid, limit=200))
            danmaku_texts = []
            if danmaku_result['success']:
                danmaku_texts = danmaku_result['data']['danmakus']
                logger.info("获取到 {} 条弹幕".format(len(danmaku_texts)))

            # 获取评论（用于分析）
            logger.info("开始获取评论...")
            comments_result = run_async(bilibili_service.get_video_comments(bvid, max_pages=10))
            comments_data = []
            if comments_result['success']:
                comments_data = comments_result['data']['comments']
                logger.info("获取到 {} 条评论".format(len(comments_data)))

            # 获取统计数据
            logger.info("开始获取统计数据...")
            stats_result = run_async(bilibili_service.get_video_stats(bvid))
            stats_data = stats_result['data'] if stats_result['success'] else {}

            # 构建内容
            content = ''
            has_subtitle = False

            if subtitle_result['success'] and subtitle_result['data'].get('has_subtitle'):
                content = subtitle_result['data']['full_text']
                has_subtitle = True
                logger.info("使用字幕作为主要内容（{}字）".format(len(content)))
            else:
                # 使用弹幕和简介
                if danmaku_texts:
                    content = '\n'.join(danmaku_texts)
                    content = f"【视频简介】\n{video_info.get('desc', '')}\n\n【弹幕内容】\n{content}"
                    logger.info("使用弹幕作为内容（{}条）".format(len(danmaku_texts)))
                else:
                    content = f"【视频简介】\n{video_info.get('desc', '')}"

            if not content or len(content) < 50:
                return jsonify({
                    'success': False,
                    'error': '无法获取视频内容（无字幕且无有效弹幕）'
                }), 400

            # 获取视频帧进行多模态分析
            logger.info("开始提取视频关键帧...")
            frames_result = run_async(bilibili_service.extract_video_frames(bvid))

            video_frames = None
            if frames_result['success']:
                video_frames = frames_result['data']['frames']
                logger.info("成功提取 {} 帧画面".format(len(video_frames)))
            else:
                logger.warning("视频帧提取失败: {}".format(frames_result['error']))
                logger.info("📝 将仅使用文本内容进行分析")

            # 调用AI生成分析
            analysis_result = ai_service.generate_full_analysis(video_info, content, video_frames)

            if not analysis_result['success']:
                return jsonify(analysis_result), 500

            # 返回完整结果
            return jsonify({
                'success': True,
                'data': {
                    'video_info': video_info,
                    'stats': stats_data,
                    'has_subtitle': has_subtitle,
                    'has_video_frames': bool(video_frames),
                    'frame_count': len(video_frames) if video_frames else 0,
                    'content': content,
                    'content_length': len(content),
                    'danmaku_count': len(danmaku_texts),
                    'comment_count': len(comments_data),
                    'danmaku_preview': danmaku_texts[:20] if danmaku_texts else [],
                    'comments_preview': comments_data[:10] if comments_data else [],
                    'analysis': analysis_result['data']['full_analysis'],
                    'parsed': analysis_result['data']['parsed'],
                    'tokens_used': analysis_result['data']['tokens_used']
                }
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'服务器错误: {str(e)}'
            }), 500

    @app.route('/api/analyze/stream', methods=['POST'])
    def analyze_video_stream():
        """流式分析接口，支持视频 (BV)、专栏 (CV) 及动态 (Opus)"""
        try:
            data = request.get_json()
            url = data.get('url', '')

            if not url:
                return jsonify({'success': False, 'error': '请提供B站视频或专栏链接'}), 400

            # 尝试提取各种 ID
            bvid = BilibiliService.extract_bvid(url)
            article_meta = BilibiliService.extract_article_id(url)

            def generate_stream():
                try:
                    nonlocal bvid, article_meta

                    # 智能搜索逻辑：如果输入的不是 ID，则视为关键词搜索
                    if not bvid and not article_meta:
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'searching', 'message': f'正在为您搜索相关内容...', 'progress': 5})}\n\n"

                        mode = data.get('mode', 'video')

                        if mode == 'article':
                            search_res = run_async(bilibili_service.search_articles(url, limit=1))
                            if search_res['success'] and search_res['data']:
                                article_meta = {'type': 'cv', 'id': search_res['data'][0]['cvid']}
                                yield f"data: {json.dumps({'type': 'stage', 'stage': 'search_complete', 'message': f'为您找到专栏: {search_res['data'][0]['title']}', 'progress': 10})}\n\n"
                            else:
                                yield f"data: {json.dumps({'type': 'error', 'error': '未找到相关专栏内容'})}\n\n"
                                return
                        else:
                            search_res = run_async(bilibili_service.search_videos(url, limit=1))
                            if search_res['success'] and search_res['data']:
                                bvid = search_res['data'][0]['bvid']
                                yield f"data: {json.dumps({'type': 'stage', 'stage': 'search_complete', 'message': f'为您找到视频: {search_res['data'][0]['title']}', 'progress': 10})}\n\n"
                            else:
                                yield f"data: {json.dumps({'type': 'error', 'error': '未找到相关视频'})}\n\n"
                                return

                    # 专栏 / Opus 分析逻辑
                    if article_meta:
                        a_type = article_meta['type']
                        a_id = article_meta['id']

                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'fetching_info', 'message': f'获取{a_type}信息...', 'progress': 10})}\n\n"

                        if a_type == 'cv':
                            res = run_async(bilibili_service.get_article_content(a_id))
                        else:
                            res = run_async(bilibili_service.get_opus_content(a_id))

                        if not res['success']:
                            yield f"data: {json.dumps({'type': 'error', 'error': res['error']})}\n\n"
                            return

                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'info_complete', 'message': f'已获取内容: {res['data']['title']}', 'progress': 20, 'info': res['data']})}\n\n"
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'starting_analysis', 'message': '正在深度解析内容...', 'progress': 40})}\n\n"

                        article_full_content = res['data']['content']
                        article_res_data = res['data']

                        for chunk in ai_service.generate_article_analysis_stream(res['data'], res['data']['content']):
                            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

                        yield f"data: {json.dumps({
                            'type': 'final',
                            'stage': 'completed',
                            'message': '专栏分析完成！',
                            'progress': 100,
                            'content': article_full_content,
                            'info': article_res_data
                        }, ensure_ascii=False)}\n\n"
                        return

                    # 视频分析逻辑
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'fetching_info', 'message': '获取视频信息...', 'progress': 5})}\n\n"
                    video_info_result = run_async(bilibili_service.get_video_info(bvid))
                    if not video_info_result['success']:
                        yield f"data: {json.dumps({'type': 'error', 'error': video_info_result['error']})}\n\n"
                        return

                    video_info = video_info_result['data']
                    video_title = video_info.get('title', '')
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'info_complete', 'message': f'已获取视频信息: {video_title}', 'progress': 15})}\n\n"

                    # 阶段2: 获取内容数据
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'fetching_content', 'message': '获取字幕和弹幕...', 'progress': 20})}\n\n"

                    tasks = [
                        bilibili_service.get_video_subtitles(bvid),
                        bilibili_service.get_video_danmaku(bvid, limit=1000),
                        bilibili_service.get_video_comments(bvid, max_pages=30, target_count=500),
                        bilibili_service.get_video_stats(bvid)
                    ]

                    results = run_async(asyncio.gather(*tasks, return_exceptions=True))
                    subtitle_result, danmaku_result, comments_result, stats_result = results

                    # 处理弹幕数据
                    danmaku_texts = []
                    if danmaku_result and hasattr(danmaku_result, 'get') and danmaku_result.get('success'):
                        danmaku_texts = danmaku_result['data']['danmakus']

                    # 处理评论数据
                    comments_data = []
                    if comments_result and hasattr(comments_result, 'get') and comments_result.get('success'):
                        comments_data = comments_result['data']['comments']

                    # 处理统计数据
                    stats_data = stats_result['data'] if stats_result and hasattr(stats_result, 'get') and stats_result.get('success') else {}

                    # 构建内容
                    content = ''
                    has_subtitle = False

                    if subtitle_result and hasattr(subtitle_result, 'get') and subtitle_result.get('success') and subtitle_result['data'].get('has_subtitle'):
                        content = subtitle_result['data']['full_text']
                        has_subtitle = True
                        text_source = "字幕"

                        extra_context = ""
                        if danmaku_texts:
                            extra_context += f"\n\n【弹幕内容（部分）】\n" + "\n".join(danmaku_texts[:100])
                        if comments_data:
                            comment_texts = [f"{c['username']}: {c['message']}" for c in comments_data[:50]]
                            extra_context += f"\n\n【视频评论（部分）】\n" + "\n".join(comment_texts)

                        content += extra_context
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'content_ready', 'message': '使用字幕内容（{}字）'.format(len(content)), 'progress': 35, 'content': content, 'has_subtitle': True, 'text_source': text_source})}\n\n"
                    else:
                        text_source = "文案"
                        base_content = f"【视频简介】\n{video_info.get('desc', '')}"
                        if danmaku_texts:
                            base_content += f"\n\n【弹幕内容】\n" + "\n".join(danmaku_texts)
                        if comments_data:
                            comment_texts = [f"{c['username']}: {c['message']}" for c in comments_data]
                            base_content += f"\n\n【视频评论】\n" + "\n".join(comment_texts)

                        content = base_content
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'content_ready', 'message': '使用视频文案进行分析', 'progress': 35, 'content': content, 'has_subtitle': False, 'text_source': text_source})}\n\n"

                    if not content or len(content) < 50:
                        yield f"data: {json.dumps({'type': 'error', 'error': '无法获取视频内容（无字幕且无有效弹幕）'})}\n\n"
                        return

                    # 阶段3: 提取视频帧
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'extracting_frames', 'message': '提取视频关键帧...', 'progress': 40})}\n\n"

                    frames_result = run_async(bilibili_service.extract_video_frames(bvid))
                    video_frames = None
                    frame_count = 0

                    if frames_result and frames_result.get('success'):
                        video_frames = frames_result['data']['frames']
                        frame_count = len(video_frames)
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'frames_ready', 'message': '成功提取 {} 帧画面'.format(frame_count), 'progress': 50, 'has_frames': True, 'frame_count': frame_count})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'frames_ready', 'message': '将仅使用文本内容进行分析', 'progress': 50, 'has_frames': False, 'frame_count': 0})}\n\n"

                    # 阶段4: 开始AI分析（流式）
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'starting_analysis', 'message': '开始AI智能分析...', 'progress': 55})}\n\n"

                    for chunk in ai_service.generate_full_analysis_stream(video_info, content, video_frames):
                        chunk_json = json.dumps(chunk, ensure_ascii=False)
                        yield f"data: {chunk_json}\n\n"

                    # 发送最终完整结果
                    top_comments = []
                    comments_count = len(comments_data) if comments_data else 0
                    danmaku_count = len(danmaku_texts) if danmaku_texts else 0

                    if comments_data:
                        sorted_comments = sorted(comments_data, key=lambda x: x.get('like', 0), reverse=True)
                        top_comments = sorted_comments[:8]

                    login_info = " (已登录)" if bilibili_service.credential else " (未登录)"
                    yield f"data: {json.dumps({
                        'type': 'final',
                        'stage': 'completed',
                        'message': f'分析完成！{login_info}',
                        'progress': 100,
                        'content': content,
                        'top_comments': top_comments,
                        'danmaku_preview': danmaku_texts[:200] if danmaku_texts else [],
                        'frame_count': frame_count,
                        'comments_count': comments_count,
                        'danmaku_count': danmaku_count
                    })}\n\n"

                except Exception as e:
                    logger.error("流式分析异常: {}".format(str(e)))
                    import traceback
                    traceback.print_exc()
                    yield f"data: {json.dumps({'type': 'error', 'error': f'分析过程中发生错误: {str(e)}'})}\n\n"

            return Response(
                generate_stream(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Cache-Control'
                }
            )

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'服务器错误: {str(e)}'
            }), 500
