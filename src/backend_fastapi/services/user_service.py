from src.backend.services.ai import AIService
from src.backend.services.bilibili import BilibiliService, run_async
from src.backend_fastapi.core.errors import BadRequestError, NotFoundError


class UserService:
    def __init__(self, bilibili_service: BilibiliService, ai_service: AIService):
        self._bilibili = bilibili_service
        self._ai = ai_service

    def get_portrait(self, input_val: str):
        if not input_val:
            raise BadRequestError("缺少输入内容")

        target_uid: int | None = None
        if str(input_val).isdigit():
            target_uid = int(input_val)
        else:
            search_res = run_async(self._bilibili.search_users(str(input_val), limit=1))
            if search_res.get("success") and search_res.get("data"):
                target_uid = search_res["data"][0]["mid"]
            else:
                raise NotFoundError(f'未找到名为 "{input_val}" 的用户')

        user_info_res = run_async(self._bilibili.get_user_info(target_uid))
        if not user_info_res.get("success"):
            raise NotFoundError(user_info_res.get("error", "用户不存在"))

        recent_videos_res = run_async(self._bilibili.get_user_recent_videos(target_uid))
        recent_videos = (
            recent_videos_res.get("data", []) if recent_videos_res.get("success") else []
        )

        portrait_data = self._ai.generate_user_analysis(user_info_res["data"], recent_videos)
        return {
            "success": True,
            "data": {
                "info": user_info_res["data"],
                "portrait": portrait_data["portrait"],
                "tokens_used": portrait_data["tokens_used"],
                "recent_videos": recent_videos,
            },
        }
