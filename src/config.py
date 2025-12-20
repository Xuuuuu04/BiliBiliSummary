import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""
    
    # OpenAI API配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    _api_base = os.getenv('OPENAI_API_BASE')
    # 自动处理 API Base：确保不以斜杠结尾，并根据需要添加 /v1
    if _api_base:
        _api_base = _api_base.rstrip('/')
        if not _api_base.endswith('/v1') and 'openai.com' in _api_base:
            OPENAI_API_BASE = _api_base + '/v1'
        else:
            OPENAI_API_BASE = _api_base
    else:
        OPENAI_API_BASE = None
    OPENAI_MODEL = os.getenv('model')
    QA_MODEL = os.getenv('QA_MODEL', 'Qwen/Qwen2.5-72B-Instruct')
    DEEP_RESEARCH_MODEL = os.getenv('DEEP_RESEARCH_MODEL', 'moonshotai/Kimi-K2-Thinking')
    EXA_API_KEY = os.getenv('EXA_API_KEY')
    
    # Flask配置
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # B站API配置
    BILIBILI_SESSDATA = os.getenv('BILIBILI_SESSDATA')
    BILIBILI_BILI_JCT = os.getenv('BILIBILI_BILI_JCT')
    BILIBILI_BUVID3 = os.getenv('BILIBILI_BUVID3')
    BILIBILI_DEDEUSERID = os.getenv('BILIBILI_DEDEUSERID')

    # 应用配置
    MAX_SUBTITLE_LENGTH = 50000  # 最大字幕长度
    REQUEST_TIMEOUT = 300  # 请求超时时间（秒）

