import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.backend_fastapi.api.router import api_router
from src.backend_fastapi.core.errors import AppError
from src.config import Config


def create_app() -> FastAPI:
    app = FastAPI(title="Bilibili Analysis Helper", version="1.0.0")

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code, content={"success": False, "error": exc.message}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, __: RequestValidationError):
        return JSONResponse(
            status_code=400, content={"success": False, "error": "请求参数验证失败"}
        )

    if Config.CORS_ENABLED:
        origins = [origin.strip() for origin in (Config.CORS_ORIGINS or "*").split(",")]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins if origins != ["*"] else ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    static_dir = os.path.join(base_dir, "src", "frontend")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

    return app
