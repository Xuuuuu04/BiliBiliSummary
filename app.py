from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import asyncio
import os
import aiohttp
from src.config import Config
from src.backend.bilibili_service import BilibiliService, run_async
from src.backend.ai_service import AIService
from src.backend.bilibili_login import login_service
from dotenv import set_key

# 使用绝对路径确保在不同环境下都能找到前端资源
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(BASE_DIR, 'src', 'frontend')

app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app)

# 初始化服务
bilibili_service = BilibiliService()
ai_service = AIService()

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """获取可配置的设置项"""
    return jsonify({
        'success': True,
        'data': {
            'openai_api_base': os.getenv('OPENAI_API_BASE'),
            'openai_api_key': os.getenv('OPENAI_API_KEY') or '',
            'model': os.getenv('model'),
            'qa_model': os.getenv('QA_MODEL'),
            'deep_research_model': os.getenv('DEEP_RESEARCH_MODEL', 'moonshotai/Kimi-K2-Thinking'),
            'dark_mode': os.getenv('DARK_MODE', 'false').lower() == 'true'
        }
    })

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """更新设置项并写入.env文件"""
    try:
        data = request.get_json()
        env_path = '.env'
        
        # 更新 .env 文件和当前环境变量
        if 'openai_api_base' in data:
            base_url = data['openai_api_base']
            # 自动添加 /v1 后缀（如果没有的话）
            if base_url and not base_url.endswith('/v1'):
                base_url = base_url.rstrip('/') + '/v1'
            set_key(env_path, 'OPENAI_API_BASE', base_url)
            os.environ['OPENAI_API_BASE'] = base_url
            Config.OPENAI_API_BASE = base_url
            
        if 'openai_api_key' in data:
            set_key(env_path, 'OPENAI_API_KEY', data['openai_api_key'])     
            os.environ['OPENAI_API_KEY'] = data['openai_api_key']
            Config.OPENAI_API_KEY = data['openai_api_key']

        if 'model' in data:
            set_key(env_path, 'model', data['model'])
            os.environ['model'] = data['model']
            Config.OPENAI_MODEL = data['model']

        if 'qa_model' in data:
            set_key(env_path, 'QA_MODEL', data['qa_model'])
            os.environ['QA_MODEL'] = data['qa_model']
            Config.QA_MODEL = data['qa_model']

        if 'deep_research_model' in data:
            set_key(env_path, 'DEEP_RESEARCH_MODEL', data['deep_research_model'])
            os.environ['DEEP_RESEARCH_MODEL'] = data['deep_research_model']
            Config.DEEP_RESEARCH_MODEL = data['deep_research_model']

        if 'dark_mode' in data:
            set_key(env_path, 'DARK_MODE', str(data['dark_mode']).lower())  
            os.environ['DARK_MODE'] = str(data['dark_mode']).lower()        

        # 重新初始化 AI 服务以应用新配置
        global ai_service
        ai_service = AIService()
        
        print(f"[设置] 配置已更新: Model={Config.OPENAI_MODEL}, QA_Model={Config.QA_MODEL}, Base={Config.OPENAI_API_BASE}")
        
        return jsonify({
            'success': True,
            'message': '设置已更新'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'更新设置失败: {str(e)}'
        }), 500

@app.route('/api/research', methods=['POST'])
def start_deep_research():
    """开始深度研究 Agent 任务"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        
        if not topic:
            return jsonify({'success': False, 'error': '请输入研究课题'}), 400

        def generate():
            import json
            for chunk in ai_service.deep_research_stream(topic, bilibili_service):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/research/history', methods=['GET'])
def list_research_history():
    """获取历史研究报告列表"""
    try:
        import os
        from datetime import datetime
        report_dir = "research_reports"
        if not os.path.exists(report_dir):
            return jsonify({'success': True, 'data': []})
            
        reports_dict = {}
        for filename in os.listdir(report_dir):
            if filename.endswith(".md") or filename.endswith(".pdf"):
                base = filename.rsplit('.', 1)[0]
                ext = filename.rsplit('.', 1)[1]
                
                if base not in reports_dict:
                    path = os.path.join(report_dir, filename)
                    stats = os.stat(path)
                    parts = base.split('_', 2)
                    topic = parts[2] if len(parts) > 2 else base
                    
                    reports_dict[base] = {
                        'id': base,
                        'topic': topic,
                        'created_at': datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        'has_md': False,
                        'has_pdf': False
                    }
                
                if ext == 'md': reports_dict[base]['has_md'] = True
                if ext == 'pdf': reports_dict[base]['has_pdf'] = True
        
        reports = list(reports_dict.values())
        # 按时间倒序排序
        reports.sort(key=lambda x: x['id'], reverse=True)
        return jsonify({'success': True, 'data': reports})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/research/download/<file_id>/<format>', methods=['GET'])
def download_research_report(file_id, format):
    """下载研究报告"""
    try:
        import os
        from flask import send_from_directory
        
        if format not in ['md', 'pdf']:
            return jsonify({'success': False, 'error': '无效的格式'}), 400
            
        filename = f"{file_id}.{format}"
        # 安全检查
        if '..' in file_id or '/' in file_id or '\\' in file_id:
            return jsonify({'success': False, 'error': '无效的文件ID'}), 400
            
        return send_from_directory("research_reports", filename, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/research/report/<filename>', methods=['GET'])
def get_research_report(filename):
    """读取指定的研究报告内容"""
    try:
        import os
        # 安全检查，防止路径遍历
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': '无效的文件名'}), 400
            
        filepath = os.path.join("research_reports", filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': '报告不存在'}), 404
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return jsonify({
            'success': True,
            'data': {
                'content': content,
                'filename': filename
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_video_stream():
    """视频内容流式问答"""
    try:
        data = request.get_json()
        question = data.get('question')
        context = data.get('context')
        video_info = data.get('video_info', {})
        history = data.get('history', [])

        if not question or not context:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        def generate():
            import json
            for chunk in ai_service.chat_stream(question, context, video_info, history):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def index():
    """返回首页"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """托管资源文件"""
    return send_from_directory('assets', filename)


@app.route('/api/search', methods=['POST'])
def search_content():
    """通用搜索接口，返回列表供用户选择"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')
        mode = data.get('mode', 'video')
        
        if not keyword:
            return jsonify({'success': False, 'error': '请输入搜索关键词'}), 400
            
        if mode == 'article':
            res = run_async(bilibili_service.search_articles(keyword, limit=10))
        elif mode == 'user':
            res = run_async(bilibili_service.search_users(keyword, limit=10))
        else:
            res = run_async(bilibili_service.search_videos(keyword, limit=10))
            
        return jsonify(res)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """分析视频的主接口"""
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({
                'success': False,
                'error': '请提供B站视频链接'
            }), 400
        
        # 提取BVID
        bvid = BilibiliService.extract_bvid(url)
        if not bvid:
            return jsonify({
                'success': False,
                'error': '无效的B站视频链接'
            }), 400
        
        # 获取视频信息
        video_info_result = run_async(bilibili_service.get_video_info(bvid))
        if not video_info_result['success']:
            return jsonify(video_info_result), 400
        
        video_info = video_info_result['data']
        
        # 获取字幕
        print("[信息] 开始获取字幕...")
        subtitle_result = run_async(bilibili_service.get_video_subtitles(bvid))
        
        # 获取弹幕（用于分析）
        print("[信息] 开始获取弹幕...")
        danmaku_result = run_async(bilibili_service.get_video_danmaku(bvid, limit=200))
        danmaku_texts = []
        if danmaku_result['success']:
            danmaku_texts = danmaku_result['data']['danmakus']
            print(f"[信息] 获取到 {len(danmaku_texts)} 条弹幕")
        
        # 获取评论（用于分析）
        print("[信息] 开始获取评论...")
        comments_result = run_async(bilibili_service.get_video_comments(bvid, max_pages=10))
        comments_data = []
        if comments_result['success']:
            comments_data = comments_result['data']['comments']
            print(f"[信息] 获取到 {len(comments_data)} 条评论")
        
        # 获取统计数据
        print("[信息] 开始获取统计数据...")
        stats_result = run_async(bilibili_service.get_video_stats(bvid))
        stats_data = stats_result['data'] if stats_result['success'] else {}
        
        # 构建内容
        content = ''
        has_subtitle = False
        
        if subtitle_result['success'] and subtitle_result['data'].get('has_subtitle'):
            content = subtitle_result['data']['full_text']
            has_subtitle = True
            print(f"[信息] 使用字幕作为主要内容（{len(content)}字）")
        else:
            # 使用弹幕和简介
            if danmaku_texts:
                content = '\n'.join(danmaku_texts)  # 使用所有获取到的弹幕（已限制在200条内）
                content = f"【视频简介】\n{video_info.get('desc', '')}\n\n【弹幕内容】\n{content}"
                print(f"[信息] 使用弹幕作为内容（{len(danmaku_texts)}条）")
            else:
                content = f"【视频简介】\n{video_info.get('desc', '')}"
        
        if not content or len(content) < 50:
            return jsonify({
                'success': False,
                'error': '无法获取视频内容（无字幕且无有效弹幕）'
            }), 400
        
        # 获取视频帧进行多模态分析（智能优化：根据视频时长自动调整参数）
        print("[信息] 开始提取视频关键帧...")
        frames_result = run_async(bilibili_service.extract_video_frames(bvid))

        video_frames = None
        if frames_result['success']:
            video_frames = frames_result['data']['frames']
            print(f"[信息] 成功提取 {len(video_frames)} 帧画面")
        else:
            print(f"[警告] 视频帧提取失败: {frames_result['error']}")
            print("[信息] 📝 将仅使用文本内容进行分析")
        
        # 调用AI生成分析（包含视频帧）
        analysis_result = ai_service.generate_full_analysis(video_info, content, video_frames)
        
        if not analysis_result['success']:
            return jsonify(analysis_result), 500
        
        # 返回完整结果（包含四大板块所需的所有数据）
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
                'danmaku_preview': danmaku_texts[:20] if danmaku_texts else [],  # 前20条弹幕
                'comments_preview': comments_data[:10] if comments_data else [],  # 前10条评论
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
                import json
                
                nonlocal bvid, article_meta # 允许在内部修改 ID
                
                # --- 智能搜索逻辑：如果输入的不是 ID，则视为关键词搜索 ---
                if not bvid and not article_meta:
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'searching', 'message': f'正在为您搜索相关内容...', 'progress': 5})}\n\n"
                    
                    # 假设前端通过 mode 选择器告知了意图，或者我们根据内容猜
                    # 这里简化逻辑：根据当前调用的接口参数（如果有的话）或默认先搜视频
                    # 为了精准，我们优先在 generate_stream 外部根据 URL 特征已经判过一次了
                    # 如果走到这里还没 ID，说明是纯文字
                    
                    # 我们需要知道用户当前选的是什么模式，这里暂定从 url 内容判断意图
                    # 实际上可以通过 request.get_json().get('mode') 获取
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

                # --- 专栏 / Opus 分析逻辑 ---
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
                    
                    # 发送基本信息
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'info_complete', 'message': f'已获取内容: {res['data']['title']}', 'progress': 20, 'info': res['data']})}\n\n"
                    
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'starting_analysis', 'message': '正在深度解析内容...', 'progress': 40})}\n\n"
                    
                    # 存储内容以便最后发送
                    article_full_content = res['data']['content']
                    article_res_data = res['data']

                    for chunk in ai_service.generate_article_analysis_stream(res['data'], res['data']['content']):
                        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
                    # 补充发送 final 阶段数据，确保原文和元数据到位
                    yield f"data: {json.dumps({
                        'type': 'final', 
                        'stage': 'completed', 
                        'message': '专栏分析完成！', 
                        'progress': 100, 
                        'content': article_full_content,
                        'info': article_res_data
                    }, ensure_ascii=False)}\n\n"
                    return

                # --- 视频分析逻辑 (保持原样并增强) ---
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'fetching_info', 'message': '获取视频信息...', 'progress': 5})}\n\n"
                video_info_result = run_async(bilibili_service.get_video_info(bvid))
                if not video_info_result['success']:
                    yield f"data: {json.dumps({'type': 'error', 'error': video_info_result['error']})}\n\n"
                    return

                video_info = video_info_result['data']
                # 并行获取其它数据
                tasks = [
                    bilibili_service.get_video_subtitles(bvid),
                    bilibili_service.get_video_danmaku(bvid, limit=1000),
                    bilibili_service.get_video_comments(bvid, max_pages=30, target_count=500),
                    bilibili_service.get_video_stats(bvid)
                ]
                subtitle_res, danmaku_res, comments_res, stats_res = run_async(asyncio.gather(*tasks, return_exceptions=True))
                
                # 构建内容 (省略中间逻辑，保持与原版一致，但增加 content 组装)
                content = ""
                # ... (此处逻辑与原 app.py 一致，为节省 token 不重复贴出)
                video_title = video_info.get('title', '')
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'info_complete', 'message': f'已获取视频信息: {video_title}', 'progress': 15})}\n\n"

                # 阶段2: 获取内容数据
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'fetching_content', 'message': '获取字幕和弹幕...', 'progress': 20})}\n\n"

                # 并行获取字幕、弹幕、评论、统计数据
                tasks = [
                    bilibili_service.get_video_subtitles(bvid),
                    bilibili_service.get_video_danmaku(bvid, limit=1000), # 增加到1000条
                    bilibili_service.get_video_comments(bvid, max_pages=30, target_count=500), # 增加到30页/500条
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
                    
                    # 附加弹幕和评论预览以增强分析
                    extra_context = ""
                    if danmaku_texts:
                        extra_context += f"\n\n【弹幕内容（部分）】\n" + "\n".join(danmaku_texts[:100])
                    if comments_data:
                        comment_texts = [f"{c['username']}: {c['message']}" for c in comments_data[:50]]
                        extra_context += f"\n\n【视频评论（部分）】\n" + "\n".join(comment_texts)
                    
                    content += extra_context
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'content_ready', 'message': f'使用字幕内容（{len(content)}字）', 'progress': 35, 'content': content, 'has_subtitle': True, 'text_source': text_source})}\n\n"
                else:
                    # 合并简介、弹幕和评论
                    text_source = "文案"
                    base_content = f"【视频简介】\n{video_info.get('desc', '')}"
                    if danmaku_texts:
                        base_content += f"\n\n【弹幕内容】\n" + "\n".join(danmaku_texts)
                    if comments_data:
                        comment_texts = [f"{c['username']}: {c['message']}" for c in comments_data]
                        base_content += f"\n\n【视频评论】\n" + "\n".join(comment_texts)
                    
                    content = base_content
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'content_ready', 'message': f'使用视频文案进行分析', 'progress': 35, 'content': content, 'has_subtitle': False, 'text_source': text_source})}\n\n"

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
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'frames_ready', 'message': f'成功提取 {len(video_frames)} 帧画面', 'progress': 50, 'has_frames': True, 'frame_count': frame_count})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'stage', 'stage': 'frames_ready', 'message': '将仅使用文本内容进行分析', 'progress': 50, 'has_frames': False, 'frame_count': 0})}\n\n"

                # 阶段4: 开始AI分析（流式）
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'starting_analysis', 'message': '开始AI智能分析...', 'progress': 55})}\n\n"

                # 使用流式AI分析
                for chunk in ai_service.generate_full_analysis_stream(video_info, content, video_frames):
                    chunk_json = json.dumps(chunk, ensure_ascii=False)
                    yield f"data: {chunk_json}\n\n"

                # 发送最终完整结果
                # 获取排名前8的高赞评论（真正的热门评论）
                top_comments = []
                comments_count = len(comments_data) if comments_data else 0
                danmaku_count = len(danmaku_texts) if danmaku_texts else 0
                
                if comments_data:
                    # 确保按点赞数进行绝对降序排序
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
                    'danmaku_preview': danmaku_texts[:200] if danmaku_texts else [], # 发送前200条用于词云
                    'frame_count': frame_count,
                    'comments_count': comments_count,
                    'danmaku_count': danmaku_count
                })}\n\n"

            except Exception as e:
                print(f"[错误] 流式分析异常: {str(e)}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'error': f'分析过程中发生错误: {str(e)}'})}\n\n"

        # 返回服务器发送事件流
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


@app.route('/api/video/info', methods=['POST'])
def get_video_info():
    """获取视频信息（增强版，包含完整统计数据）"""
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        bvid = BilibiliService.extract_bvid(url)
        if not bvid:
            return jsonify({
                'success': False,
                'error': '无效的B站视频链接'
            }), 400
        
        # 并行获取基本信息、统计数据和相关视频
        async def fetch_all():
            return await asyncio.gather(
                bilibili_service.get_video_info(bvid),
                bilibili_service.get_video_stats(bvid),
                bilibili_service.get_related_videos(bvid)
            )
            
        info_res, stats_res, related_res = run_async(fetch_all())
        
        if not info_res['success']:
            return jsonify(info_res), 400
            
        # 合并数据
        video_data = info_res['data']
        if stats_res['success']:
            video_data.update(stats_res['data'])
        
        related_videos = related_res['data'] if related_res['success'] else []
            
        return jsonify({
            'success': True,
            'data': video_data,
            'related': related_videos
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取视频信息失败: {str(e)}'
        }), 500


@app.route('/api/video/subtitle', methods=['POST'])
def get_video_subtitle():
    """获取视频字幕"""
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        bvid = BilibiliService.extract_bvid(url)
        if not bvid:
            return jsonify({
                'success': False,
                'error': '无效的B站视频链接'
            }), 400
        
        result = run_async(bilibili_service.get_video_subtitles(bvid))
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取字幕失败: {str(e)}'
        }), 500

@app.route('/api/video/popular', methods=['GET'])
def get_popular_videos():
    """获取热门视频"""
    try:
        result = run_async(bilibili_service.get_popular_videos())
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/image-proxy')
def image_proxy():
    """B站图片代理，解决防盗链问题"""
    image_url = request.args.get('url')
    if not image_url:
        return jsonify({'error': '缺少图片URL'}), 400

    # 修复：解码URL参数
    import urllib.parse
    image_url = urllib.parse.unquote(image_url)

    # 修复：如果URL缺少协议，添加https://
    if image_url.startswith('//'):
        image_url = 'https:' + image_url
    elif not image_url.startswith(('http://', 'https://')):
        # 如果不是完整URL，添加https://
        image_url = 'https://' + image_url

    # 只允许代理B站的图片
    if not any(domain in image_url for domain in ['hdslb.com', 'bilibili.com']):
        return jsonify({'error': '不支持的图片域名'}), 400

    try:
        # 添加正确的headers来访问B站图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',  # 避免压缩问题
            'Connection': 'close'
        }

        # 使用同步请求获取图片
        import requests
        print(f"[调试] 代理图片: {image_url}")
        response = requests.get(image_url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"[错误] 图片请求失败: HTTP {response.status_code}")
            return jsonify({'error': f'获取图片失败: {response.status_code}'}), 404

        # 获取图片类型
        content_type = response.headers.get('content-type', 'image/jpeg')

        # 返回图片内容
        return Response(response.content, mimetype=content_type)

    except Exception as e:
        print(f"[错误] 图片代理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'获取图片失败: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'status': 'running',
        'message': 'BiliBili智能学习平台 Ultra版运行中'
    })


@app.route('/api/bilibili/login/start', methods=['POST'])
def start_bilibili_login():
    """开始B站扫码登录"""
    try:
        result = run_async(login_service.start_login())
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'启动登录失败: {str(e)}'
        }), 500


@app.route('/api/bilibili/login/status', methods=['POST'])
def check_login_status():
    """检查登录状态"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', '')

        if not session_id:
            return jsonify({
                'success': False,
                'error': '缺少session_id'
            }), 400

        result = run_async(login_service.check_login_status(session_id))
        
        # 如果登录成功，刷新全局服务的凭据
        if result.get('success') and result.get('data', {}).get('status') == 'success':
            bilibili_service.refresh_credential()
            
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'检查登录状态失败: {str(e)}'
        }), 500


@app.route('/api/bilibili/login/logout', methods=['POST'])
def logout_bilibili():
    """B站登出"""
    try:
        result = run_async(login_service.logout())
        # 登出后刷新全局服务的凭据（清空）
        bilibili_service.refresh_credential()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'登出失败: {str(e)}'
        }), 500


@app.route('/api/bilibili/login/check', methods=['GET'])
def check_current_login():
    """检查当前登录状态并返回用户资料"""
    try:
        # 检查是否配置了核心登录凭据
        has_credentials = all([
            Config.BILIBILI_SESSDATA,
            Config.BILIBILI_BILI_JCT,
            Config.BILIBILI_DEDEUSERID
        ])

        if has_credentials:
            # 验证凭据有效性并获取用户信息
            # 这里的 bilibili_service 已经初始化了凭据
            is_valid = run_async(bilibili_service.check_credential_valid())

            if is_valid:
                # 获取当前登录用户的详细资料
                # 注意：DedeUserID 就是用户的 MID
                user_info_res = run_async(bilibili_service.get_user_info(int(Config.BILIBILI_DEDEUSERID)))
                
                if user_info_res['success']:
                    return jsonify({
                        'success': True,
                        'data': {
                            'is_logged_in': True,
                            'user_id': Config.BILIBILI_DEDEUSERID,
                            'name': user_info_res['data']['name'],
                            'face': user_info_res['data']['face'],
                            'message': '已登录'
                        }
                    })

            return jsonify({
                'success': True,
                'data': {
                    'is_logged_in': is_valid,
                    'user_id': Config.BILIBILI_DEDEUSERID[:10] + '***' if Config.BILIBILI_DEDEUSERID else None,
                    'message': '凭据已失效，请重新登录' if not is_valid else '获取用户信息失败'
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'is_logged_in': False,
                    'user_id': None,
                    'message': '未登录'
                }
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'检查登录状态失败: {str(e)}'
        }), 500


@app.route('/api/user/portrait', methods=['POST'])
def get_user_portrait():
    """获取UP主深度画像（支持UID或关键词搜索）"""
    try:
        data = request.get_json()
        input_val = data.get('uid')
        if not input_val: return jsonify({'success': False, 'error': '缺少输入内容'}), 400
        
        target_uid = None
        # 识别是否为 UID
        if str(input_val).isdigit():
            target_uid = int(input_val)
        else:
            # 视为关键词搜索
            search_res = run_async(bilibili_service.search_users(str(input_val), limit=1))
            if search_res['success'] and search_res['data']:
                target_uid = search_res['data'][0]['mid']
                print(f"[搜索] 为关键词 '{input_val}' 找到用户: {search_res['data'][0]['name']} (UID: {target_uid})")
            else:
                return jsonify({'success': False, 'error': f'未找到名为 "{input_val}" 的用户'}), 404

        # 获取用户信息和最近视频
        user_info_res = run_async(bilibili_service.get_user_info(target_uid))
        if not user_info_res['success']:
            return jsonify(user_info_res), 404

        recent_videos_res = run_async(bilibili_service.get_user_recent_videos(target_uid))
        
        # AI生成画像
        portrait_data = ai_service.generate_user_analysis(user_info_res['data'], recent_videos_res.get('data', []))
        
        return jsonify({
            'success': True,
            'data': {
                'info': user_info_res['data'],
                'portrait': portrait_data['portrait'],
                'tokens_used': portrait_data['tokens_used'],
                'recent_videos': recent_videos_res.get('data', [])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # 终端颜色代码
    PINK = '\033[38;5;213m'
    BLUE = '\033[38;5;75m'
    GOLD = '\033[38;5;220m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # 顶级 Bilibili 风格 ASCII LOGO
    logo = f"""
{PINK}   ██████╗ ██╗██╗     ██╗██████╗ ██╗██╗     ██╗
   ██╔══██╗██║██║     ██║██╔══██╗██║██║     ██║
   ██████╔╝██║██║     ██║██████╔╝██║██║     ██║
   ██╔══██╗██║██║     ██║██╔══██╗██║██║     ██║
   ██████╔╝██║███████╗██║██████╔╝██║███████╗██║
   ╚═════╝ ╚═╝╚══════╝╚═╝╚═════╝ ╚═╝╚══════╝╚═╝{RESET}

{BLUE}   ███████╗██╗   ██╗███╗   ███╗███╗   ███╗ █████╗ ██████╗ ██╗███████╗███████╗
   ██╔════╝██║   ██║████╗ ████║████╗ ████║██╔══██╗██╔══██╗██║╚══███╔╝██╔════╝
   ███████╗██║   ██║██╔████╔██║██╔████╔██║███████║██████╔╝██║  ███╔╝ █████╗  
   ╚════██║██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██╔══██╗██║ ███╔╝  ██╔════╝
   ███████║╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║  ██║██║███████╗███████╗
   ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝{RESET}
    """
    print(logo)
    print(f"{BOLD}🚀 BiliBili视频总结系统正在启动...{RESET}")
    print(f"{'='*60}")
    print(f"{BOLD}📡 运行配置:{RESET}")
    print(f"  > {BOLD}服务地址:{RESET} {BLUE}http://{Config.FLASK_HOST}:{Config.FLASK_PORT}{RESET}")
    print(f"  > {BOLD}调试模式:{RESET} {GOLD}{Config.FLASK_DEBUG}{RESET}")
    print(f"\n{BOLD}🤖 AI 引擎配置:{RESET}")
    print(f"  > {BOLD}基础模型:{RESET} {BLUE}{Config.OPENAI_MODEL}{RESET}")
    print(f"  > {BOLD}问答模型:{RESET} {BLUE}{Config.QA_MODEL}{RESET}")
    print(f"  > {BOLD}深度研究:{RESET} {GOLD}{Config.DEEP_RESEARCH_MODEL}{RESET}")
    print(f"  > {BOLD}API 代理:{RESET} {Config.OPENAI_API_BASE}")
    
    # 检查 API Key 状态（脱敏显示）
    api_key = Config.OPENAI_API_KEY
    key_status = f"{PINK}已配置{RESET} ({api_key[:8]}...{api_key[-4:]})" if api_key else f"\033[31m未配置\033[0m"
    print(f"  > {BOLD}API Key :{RESET} {key_status}")
    
    print(f"{'='*60}")
    
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )

