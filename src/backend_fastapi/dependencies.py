from functools import lru_cache

from src.backend.services.ai import AIService
from src.backend.services.bilibili import BilibiliService
from src.backend.services.bilibili.login_service import LoginService
from src.backend_fastapi.services.analyze_service import AnalyzeService
from src.backend_fastapi.services.research_service import ResearchService
from src.backend_fastapi.services.settings_service import SettingsService
from src.backend_fastapi.services.user_service import UserService


@lru_cache(maxsize=1)
def get_bilibili_service() -> BilibiliService:
    return BilibiliService()


@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    return AIService()


@lru_cache(maxsize=1)
def get_login_service() -> LoginService:
    return LoginService()


def get_analyze_service() -> AnalyzeService:
    return AnalyzeService(bilibili_service=get_bilibili_service(), ai_service=get_ai_service())


def get_research_service() -> ResearchService:
    return ResearchService(ai_service=get_ai_service(), bilibili_service=get_bilibili_service())


@lru_cache(maxsize=1)
def get_settings_service() -> SettingsService:
    return SettingsService()


def get_user_service() -> UserService:
    return UserService(bilibili_service=get_bilibili_service(), ai_service=get_ai_service())
