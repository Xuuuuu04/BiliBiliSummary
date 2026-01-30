from fastapi import APIRouter

from src.backend.http.api.routes import analyze, bilibili, qa, research, settings, user

api_router = APIRouter()

api_router.include_router(analyze.router)
api_router.include_router(bilibili.router)
api_router.include_router(qa.router)
api_router.include_router(research.router)
api_router.include_router(settings.router)
api_router.include_router(user.router)

