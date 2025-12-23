"""
深度研究路由模块
提供研究任务、历史记录和报告管理接口
"""
import os
import json
from flask import request, jsonify, Response, send_from_directory


def init_research_routes(app, ai_service, bilibili_service):
    """
    初始化深度研究相关路由

    Args:
        app: Flask 应用实例
        ai_service: AIService 实例
        bilibili_service: BilibiliService 实例
    """

    @app.route('/api/research', methods=['POST'])
    def start_deep_research():
        """开始深度研究 Agent 任务"""
        try:
            data = request.get_json()
            topic = data.get('topic', '')

            if not topic:
                return jsonify({'success': False, 'error': '请输入研究课题'}), 400

            def generate():
                for chunk in ai_service.deep_research_stream(topic, bilibili_service):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            return Response(generate(), mimetype='text/event-stream')
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/research/history', methods=['GET'])
    def list_research_history():
        """获取历史研究报告列表"""
        try:
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
