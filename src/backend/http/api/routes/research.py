from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from src.backend.http.api.schemas import ResearchRequest
from src.backend.http.api.utils import sse_data
from src.backend.http.dependencies import get_research_service
from src.backend.http.usecases.research_service import ResearchService

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/research")
async def start_deep_research(
    payload: ResearchRequest,
    research_service: ResearchService = Depends(get_research_service),
):
    if not payload.topic:
        return JSONResponse(status_code=400, content={"success": False, "error": "请输入研究课题"})

    def generate():
        try:
            for chunk in research_service.stream(payload.topic):
                yield sse_data(chunk, ensure_ascii=False)
        except Exception as e:
            yield sse_data({"type": "error", "error": str(e)}, ensure_ascii=False)

    return StreamingResponse(iterate_in_threadpool(generate()), media_type="text/event-stream")


@router.get("/research/history")
async def list_research_history(research_service: ResearchService = Depends(get_research_service)):
    return await run_in_threadpool(research_service.list_history)


@router.get("/research/download/{file_id}/{format}")
async def download_research_report(
    file_id: str,
    format: str,
    research_service: ResearchService = Depends(get_research_service),
):
    filepath, filename = await run_in_threadpool(research_service.resolve_download_path, file_id, format)
    return FileResponse(path=filepath, filename=filename, media_type="application/octet-stream")


@router.get("/research/report/{filename}")
async def get_research_report(
    filename: str, research_service: ResearchService = Depends(get_research_service)
):
    return await run_in_threadpool(research_service.read_report, filename)

