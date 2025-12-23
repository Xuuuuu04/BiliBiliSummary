"""
设置管理路由模块
提供配置读取和更新接口
"""
import os
from flask import request, jsonify
from dotenv import set_key
from src.config import Config
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def init_settings_routes(app, ai_service_ref):
    """
    初始化设置相关路由

    Args:
        app: Flask 应用实例
        ai_service_ref: AI服务引用的字典 {'service': AIService实例}
    """

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
                'exa_api_key': os.getenv('EXA_API_KEY') or '',
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
                if base_url:
                    base_url = base_url.rstrip('/')
                    # 仅对 openai.com 的域名尝试补全 /v1，其他国内中转通常不需要或已有完整路径
                    if not base_url.endswith('/v1') and 'openai.com' in base_url:
                        base_url = base_url + '/v1'

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

            if 'exa_api_key' in data:
                set_key(env_path, 'EXA_API_KEY', data['exa_api_key'])
                os.environ['EXA_API_KEY'] = data['exa_api_key']
                Config.EXA_API_KEY = data['exa_api_key']

            if 'dark_mode' in data:
                set_key(env_path, 'DARK_MODE', str(data['dark_mode']).lower())
                os.environ['DARK_MODE'] = str(data['dark_mode']).lower()

            # 重新初始化 AI 服务以应用新配置
            from src.backend.services.ai import AIService

            ai_service_ref['service'] = AIService()

            logger.info(f"[设置] 配置已更新: Model={Config.OPENAI_MODEL}, QA_Model={Config.QA_MODEL}, Base={Config.OPENAI_API_BASE}")

            return jsonify({
                'success': True,
                'message': '设置已更新'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'更新设置失败: {str(e)}'
            }), 500
