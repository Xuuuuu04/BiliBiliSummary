from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from src.backend_fastapi.api.schemas import ResearchRequest
from src.backend_fastapi.api.utils import sse_data
from src.backend_fastapi.dependencies import get_research_service
from src.backend_fastapi.services.research_service import ResearchService

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/research")
def start_deep_research(
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

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/research/history")
def list_research_history(research_service: ResearchService = Depends(get_research_service)):
    return research_service.list_history()


@router.get("/research/download/{file_id}/{format}")
def download_research_report(
    file_id: str,
    format: str,
    research_service: ResearchService = Depends(get_research_service),
):
    filepath, filename = research_service.resolve_download_path(file_id, format)
    return FileResponse(path=filepath, filename=filename, media_type="application/octet-stream")


@router.get("/research/report/{filename}")
def get_research_report(
    filename: str, research_service: ResearchService = Depends(get_research_service)
):
    return research_service.read_report(filename)
