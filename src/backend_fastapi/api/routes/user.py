from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.backend_fastapi.api.schemas import UserPortraitRequest
from src.backend_fastapi.dependencies import get_user_service
from src.backend_fastapi.services.user_service import UserService

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/user/portrait")
def user_portrait(
    payload: UserPortraitRequest, user_service: UserService = Depends(get_user_service)
):
    if not payload.uid:
        return JSONResponse(status_code=400, content={"success": False, "error": "缺少输入内容"})
    return user_service.get_portrait(payload.uid)
