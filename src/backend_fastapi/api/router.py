from fastapi import APIRouter

from src.backend_fastapi.api.routes import analyze, bilibili, research, settings, user, v1

api_router = APIRouter()

api_router.include_router(analyze.router)
api_router.include_router(bilibili.router)
api_router.include_router(research.router)
api_router.include_router(settings.router)
api_router.include_router(user.router)
api_router.include_router(v1.router)
