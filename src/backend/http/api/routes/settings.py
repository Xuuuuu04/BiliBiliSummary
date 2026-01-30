from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from src.backend.http.api.schemas import SettingsUpdateRequest
from src.backend.http.dependencies import get_settings_service
from src.backend.http.usecases.settings_service import SettingsService

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/settings")
async def get_settings(settings_service: SettingsService = Depends(get_settings_service)):
    return await run_in_threadpool(settings_service.get_settings)


@router.post("/settings")
async def update_settings(
    payload: SettingsUpdateRequest,
    settings_service: SettingsService = Depends(get_settings_service),
):
    data = payload.model_dump(exclude_unset=True)
    return await run_in_threadpool(settings_service.update_settings, data)

