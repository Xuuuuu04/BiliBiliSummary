from fastapi import APIRouter, Depends

from src.backend_fastapi.api.schemas import SettingsUpdateRequest
from src.backend_fastapi.dependencies import get_settings_service
from src.backend_fastapi.services.settings_service import SettingsService

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/settings")
def get_settings(settings_service: SettingsService = Depends(get_settings_service)):
    return settings_service.get_settings()


@router.post("/settings")
def update_settings(
    payload: SettingsUpdateRequest,
    settings_service: SettingsService = Depends(get_settings_service),
):
    data = payload.model_dump(exclude_unset=True)
    return settings_service.update_settings(data)
