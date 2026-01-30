from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool

from src.backend.http.api.schemas import QAStreamRequest
from src.backend.http.api.utils import sse_data
from src.backend.http.dependencies import get_ai_service
from src.backend.services.ai import AIService

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/qa/stream")
async def qa_stream(payload: QAStreamRequest, ai_service: AIService = Depends(get_ai_service)):
    if not payload.question or not payload.context:
        return JSONResponse(status_code=400, content={"success": False, "error": "缺少必要参数"})

    def generate():
        try:
            for chunk in ai_service.context_qa_stream(
                mode=payload.mode,
                question=payload.question,
                context=payload.context,
                meta=payload.meta,
                history=payload.history,
            ):
                yield sse_data(chunk, ensure_ascii=False)
        except Exception as e:
            yield sse_data({"type": "error", "error": str(e)}, ensure_ascii=False)

    return StreamingResponse(iterate_in_threadpool(generate()), media_type="text/event-stream")

