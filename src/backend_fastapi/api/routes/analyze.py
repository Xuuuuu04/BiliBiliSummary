from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from src.backend.services.ai import AIService
from src.backend_fastapi.api.schemas import AnalyzeRequest, AnalyzeStreamRequest, ChatStreamRequest
from src.backend_fastapi.api.utils import sse_data
from src.backend_fastapi.dependencies import get_ai_service, get_analyze_service
from src.backend_fastapi.services.analyze_service import AnalyzeService

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/chat/stream")
async def chat_video_stream(
    payload: ChatStreamRequest, ai_service: AIService = Depends(get_ai_service)
):
    if not payload.question or not payload.context:
        return JSONResponse(status_code=400, content={"success": False, "error": "缺少必要参数"})

    def generate():
        try:
            for chunk in ai_service.chat_stream(
                payload.question, payload.context, payload.video_info, payload.history
            ):
                yield sse_data(chunk, ensure_ascii=False)
        except Exception as e:
            yield sse_data({"type": "error", "error": str(e)}, ensure_ascii=False)

    return StreamingResponse(iterate_in_threadpool(generate()), media_type="text/event-stream")


@router.post("/analyze")
async def analyze_video(
    payload: AnalyzeRequest,
    analyze_service: AnalyzeService = Depends(get_analyze_service),
):
    return await run_in_threadpool(analyze_service.analyze_video, payload.url)


@router.post("/analyze/stream")
async def analyze_video_stream(
    payload: AnalyzeStreamRequest,
    analyze_service: AnalyzeService = Depends(get_analyze_service),
):
    if not payload.url:
        return JSONResponse(
            status_code=400, content={"success": False, "error": "请提供B站视频或专栏链接"}
        )

    return StreamingResponse(
        iterate_in_threadpool(analyze_service.stream_analyze(payload.url, payload.mode)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )
