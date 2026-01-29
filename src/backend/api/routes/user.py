"""
用户相关路由模块
提供用户画像分析接口
"""
from flask import request, jsonify
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_user_routes(app, bilibili_service, ai_service_ref):
    """
    初始化用户相关路由

    Args:
        app: Flask 应用实例
        bilibili_service: BilibiliService 实例
        ai_service_ref: AI服务引用字典 {'service': AIService实例}
    """
    from src.backend.services.bilibili import run_async

    @app.route('/api/user/portrait', methods=['POST'])
    def get_user_portrait():
        """获取UP主深度画像（支持UID或关键词搜索）"""
        try:
            data = request.get_json()
            input_val = data.get('uid')
            if not input_val:
                return jsonify({'success': False, 'error': '缺少输入内容'}), 400

            target_uid = None
            # 识别是否为 UID
            if str(input_val).isdigit():
                target_uid = int(input_val)
            else:
                # 视为关键词搜索
                search_res = run_async(bilibili_service.search_users(str(input_val), limit=1))
                if search_res['success'] and search_res['data']:
                    target_uid = search_res['data'][0]['mid']
                    logger.info(f"[搜索] 为关键词 '{input_val}' 找到用户: {search_res['data'][0]['name']} (UID: {target_uid})")
                else:
                    return jsonify({'success': False, 'error': f'未找到名为 "{input_val}" 的用户'}), 404

            # 获取用户信息和最近视频
            user_info_res = run_async(bilibili_service.get_user_info(target_uid))
            if not user_info_res['success']:
                return jsonify(user_info_res), 404

            recent_videos_res = run_async(bilibili_service.get_user_recent_videos(target_uid))

            # AI生成画像
            ai_service = ai_service_ref['service']  # 动态获取最新的 AI 服务
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
