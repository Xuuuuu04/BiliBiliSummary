"""
B站数据和登录路由模块
提供搜索、视频信息、登录认证等接口
"""
import asyncio
import urllib.parse
import requests
from flask import request, jsonify, Response
from src.config import Config
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_bilibili_routes(app, bilibili_service, login_service):
    """
    初始化B站相关路由

    Args:
        app: Flask 应用实例
        bilibili_service: BilibiliService 实例
        login_service: BilibiliLoginService 实例
    """
    from src.backend.bilibili_service import BilibiliService, run_async

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

        # 解码URL参数
        image_url = urllib.parse.unquote(image_url)

        # 如果URL缺少协议，添加https://
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif not image_url.startswith(('http://', 'https://')):
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
                'Accept-Encoding': 'identity',
                'Connection': 'close'
            }

            logger.debug(f" 代理图片: {image_url}")
            response = requests.get(image_url, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error(f" 图片请求失败: HTTP {response.status_code}")
                return jsonify({'error': f'获取图片失败: {response.status_code}'}), 404

            # 获取图片类型
            content_type = response.headers.get('content-type', 'image/jpeg')

            # 返回图片内容
            return Response(response.content, mimetype=content_type)

        except Exception as e:
            logger.error(f" 图片代理失败: {str(e)}")
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
                is_valid = run_async(bilibili_service.check_credential_valid())

                if is_valid:
                    # 获取当前登录用户的详细资料
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
