import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置类"""

    # OpenAI API配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    _api_base = os.getenv("OPENAI_API_BASE")
    # 自动处理 API Base：确保不以斜杠结尾，并根据需要添加 /v1
    if _api_base:
        _api_base = _api_base.rstrip("/")
        if not _api_base.endswith("/v1") and "openai.com" in _api_base:
            OPENAI_API_BASE = _api_base + "/v1"
        else:
            OPENAI_API_BASE = _api_base
    else:
        OPENAI_API_BASE = None
    OPENAI_MODEL = os.getenv("model")
    QA_MODEL = os.getenv("QA_MODEL", "Qwen/Qwen2.5-72B-Instruct")
    DEEP_RESEARCH_MODEL = os.getenv("DEEP_RESEARCH_MODEL", "moonshotai/Kimi-K2-Thinking")
    EXA_API_KEY = os.getenv("EXA_API_KEY")

    # 服务监听配置（FastAPI / Uvicorn）
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5001))

    # B站API配置
    BILIBILI_SESSDATA = os.getenv("BILIBILI_SESSDATA")
    BILIBILI_BILI_JCT = os.getenv("BILIBILI_BILI_JCT")
    BILIBILI_BUVID3 = os.getenv("BILIBILI_BUVID3")
    BILIBILI_DEDEUSERID = os.getenv("BILIBILI_DEDEUSERID")

    # 小红书配置
    XHS_COOKIE = os.getenv("XHS_COOKIE")

    # 应用配置
    MAX_SUBTITLE_LENGTH = 50000  # 最大字幕长度
    REQUEST_TIMEOUT = 300  # 请求超时时间（秒）

    ENABLE_RESEARCH_THINKING = os.getenv("ENABLE_RESEARCH_THINKING", "false").lower() == "true"

    # ========== API 服务配置 ==========
    API_RATE_LIMIT_ENABLED = os.getenv("API_RATE_LIMIT_ENABLED", "True").lower() == "true"
    API_RATE_LIMIT_DEFAULT = int(os.getenv("API_RATE_LIMIT_DEFAULT", 100))
    API_RATE_LIMIT_WINDOW = int(os.getenv("API_RATE_LIMIT_WINDOW", 60))

    # ========== 认证配置 ==========
    API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-secret-key-change-in-production")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

    # ========== 缓存配置 ==========
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    CACHE_TYPE = os.getenv("CACHE_TYPE", "memory")  # memory 或 redis
    CACHE_DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", 3600))

    # Redis 配置
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    # ========== CORS 配置 ==========
    CORS_ENABLED = os.getenv("CORS_ENABLED", "True").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # ========== 日志配置 ==========
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    LOG_DIR = os.getenv("LOG_DIR", "logs")
