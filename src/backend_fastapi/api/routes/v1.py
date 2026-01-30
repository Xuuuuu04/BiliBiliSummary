from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.backend.services.bilibili import BilibiliService
from src.backend_fastapi.dependencies import get_bilibili_service

router = APIRouter(prefix="/api/v1", tags=["api-v1"])


@router.get("/health")
def health():
    return {"success": True, "data": {"status": "ok"}}


@router.get("/health/detailed")
async def health_detailed(bilibili_service: BilibiliService = Depends(get_bilibili_service)):
    try:
        has_credentials = bool(bilibili_service.credential)
        return {
            "success": True,
            "data": {"status": "ok", "bilibili_credential_loaded": has_credentials},
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@router.get("/video/{bvid}/info")
async def v1_video_info(
    bvid: str, bilibili_service: BilibiliService = Depends(get_bilibili_service)
):
    res = await bilibili_service.get_video_info(bvid)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/video/{bvid}/subtitles")
async def v1_video_subtitles(
    bvid: str, bilibili_service: BilibiliService = Depends(get_bilibili_service)
):
    res = await bilibili_service.get_video_subtitles(bvid)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/video/{bvid}/danmaku")
async def v1_video_danmaku(
    bvid: str,
    limit: int = Query(1000, ge=1, le=5000),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    res = await bilibili_service.get_video_danmaku(bvid, limit=limit)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/video/{bvid}/comments")
async def v1_video_comments(
    bvid: str,
    limit: int = Query(50, ge=1, le=200),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    max_pages = 30
    target_count = limit
    res = await bilibili_service.get_video_comments(
        bvid, max_pages=max_pages, target_count=target_count
    )
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )

    data = res.get("data") or {}
    if "comments" in data and isinstance(data["comments"], list):
        data["comments"] = data["comments"][:limit]
    return {"success": True, "data": data}


@router.get("/video/{bvid}/stats")
async def v1_video_stats(
    bvid: str, bilibili_service: BilibiliService = Depends(get_bilibili_service)
):
    res = await bilibili_service.get_video_stats(bvid)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/video/{bvid}/related")
async def v1_video_related(
    bvid: str, bilibili_service: BilibiliService = Depends(get_bilibili_service)
):
    res = await bilibili_service.get_related_videos(bvid)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/video/{bvid}/frames")
async def v1_video_frames(
    bvid: str,
    max_frames: int | None = Query(None, ge=1, le=200),
    interval: int | None = Query(None, ge=1, le=60),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    res = await bilibili_service.extract_video_frames(
        bvid, max_frames=max_frames, interval=interval
    )
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/user/{uid}/info")
async def v1_user_info(uid: int, bilibili_service: BilibiliService = Depends(get_bilibili_service)):
    res = await bilibili_service.get_user_info(uid)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/user/{uid}/videos")
async def v1_user_videos(
    uid: int,
    limit: int = Query(10, ge=1, le=50),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    res = await bilibili_service.get_user_recent_videos(uid, limit=limit)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/user/{uid}/dynamics")
async def v1_user_dynamics(
    uid: int,
    limit: int = Query(10, ge=1, le=50),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    res = await bilibili_service.get_user_dynamics(uid, limit=limit)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/search/videos")
async def v1_search_videos(
    keyword: str = Query(min_length=1),
    limit: int = Query(20, ge=1, le=100),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    res = await bilibili_service.search_videos(keyword, limit=limit)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/search/users")
async def v1_search_users(
    keyword: str = Query(min_length=1),
    limit: int = Query(5, ge=1, le=50),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    res = await bilibili_service.search_users(keyword, limit=limit)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/search/articles")
async def v1_search_articles(
    keyword: str = Query(min_length=1),
    limit: int = Query(5, ge=1, le=50),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    res = await bilibili_service.search_articles(keyword, limit=limit)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/hot/videos")
async def v1_hot_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    try:
        from src.backend.services.bilibili.hot_service import HotService
    except Exception:
        return JSONResponse(
            status_code=501, content={"success": False, "error": "热门内容服务不可用"}
        )

    hot_service = HotService(credential=bilibili_service.credential)
    res = await hot_service.get_hot_videos(pn=page, ps=page_size)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/hot/buzzwords")
async def v1_hot_buzzwords(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    try:
        from src.backend.services.bilibili.hot_service import HotService
    except Exception:
        return JSONResponse(
            status_code=501, content={"success": False, "error": "热门内容服务不可用"}
        )

    hot_service = HotService(credential=bilibili_service.credential)
    res = await hot_service.get_hot_buzzwords(page_num=page, page_size=page_size)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/rank/videos")
async def v1_rank_videos(
    day: Literal[3, 7] = Query(3),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    try:
        from src.backend.services.bilibili.rank_service import RankService
    except Exception:
        return JSONResponse(
            status_code=501, content={"success": False, "error": "排行榜服务不可用"}
        )

    rank_service = RankService(credential=bilibili_service.credential)
    res = await rank_service.get_rank_videos(type_="all", day=day)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.get("/rank/videos/{type_}")
async def v1_rank_videos_by_type(
    type_: str,
    day: Literal[3, 7] = Query(3),
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
):
    try:
        from src.backend.services.bilibili.rank_service import RankService
    except Exception:
        return JSONResponse(
            status_code=501, content={"success": False, "error": "排行榜服务不可用"}
        )

    rank_service = RankService(credential=bilibili_service.credential)
    res = await rank_service.get_rank_videos(type_=type_, day=day)
    if not res.get("success"):
        return JSONResponse(
            status_code=400, content={"success": False, "error": res.get("error", "请求失败")}
        )
    return {"success": True, "data": res.get("data")}


@router.post("/ai/chat")
def v1_ai_chat():
    return JSONResponse(status_code=501, content={"success": False, "error": "Not implemented"})


@router.post("/ai/analyze")
def v1_ai_analyze():
    return JSONResponse(status_code=501, content={"success": False, "error": "Not implemented"})
