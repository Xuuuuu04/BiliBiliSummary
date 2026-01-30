from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    url: str = ""


class AnalyzeStreamRequest(BaseModel):
    url: str = ""
    mode: Literal["video", "article"] = "video"


class ChatStreamRequest(BaseModel):
    question: str = ""
    context: str = ""
    video_info: dict[str, Any] = Field(default_factory=dict)
    history: list[Any] = Field(default_factory=list)


class QAStreamRequest(BaseModel):
    question: str = ""
    mode: Literal["video", "article", "user", "research"] = "video"
    context: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)
    history: list[Any] = Field(default_factory=list)


class SearchRequest(BaseModel):
    keyword: str = ""
    mode: Literal["video", "article", "user"] = "video"


class VideoInfoRequest(BaseModel):
    url: str = ""


class VideoSubtitleRequest(BaseModel):
    url: str = ""


class LoginStatusRequest(BaseModel):
    session_id: str = ""


class ResearchRequest(BaseModel):
    topic: str = ""


class UserPortraitRequest(BaseModel):
    uid: str = ""


class SettingsUpdateRequest(BaseModel):
    openai_api_base: str | None = None
    openai_api_key: str | None = None
    model: str | None = None
    qa_model: str | None = None
    deep_research_model: str | None = None
    exa_api_key: str | None = None
    dark_mode: bool | None = None
    enable_research_thinking: bool | None = None

