from src.backend.services.ai.agents.deep_research_agent import DeepResearchAgent
from src.backend.services.ai.prompts import get_video_analysis_prompt
from src.backend.services.ai.toolkit import ToolRegistry


class _FakeDelta:
    def __init__(self, content=None, tool_calls=None, reasoning_content=None):
        self.content = content
        self.tool_calls = tool_calls
        self.reasoning_content = reasoning_content


class _FakeFunction:
    def __init__(self, name=None, arguments=None):
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, index, tool_id, name=None, arguments=None):
        self.index = index
        self.id = tool_id
        self.function = _FakeFunction(name=name, arguments=arguments)


class _FakeChoice:
    def __init__(self, delta):
        self.delta = delta


class _FakeChunk:
    def __init__(self, delta):
        self.choices = [_FakeChoice(delta)]


class _FakeChatCompletions:
    def __init__(self, streams):
        self._streams = list(streams)

    def create(self, **_kwargs):
        if not self._streams:
            raise RuntimeError("No more fake streams configured")
        return self._streams.pop(0)


class _FakeChat:
    def __init__(self, streams):
        self.completions = _FakeChatCompletions(streams)


class _FakeOpenAIClient:
    def __init__(self, streams):
        self.chat = _FakeChat(streams)


class _FakeBilibiliService:
    async def get_hot_videos(self, pn: int = 1, ps: int = 20):
        return {
            "success": True,
            "data": [{"bvid": "BV1xx411c7mD", "title": "t", "author": "u"}],
        }


def _stream_with_tool_call(tool_id: str, name: str, arguments: str):
    def gen():
        yield _FakeChunk(
            _FakeDelta(
                content="",
                tool_calls=[_FakeToolCall(index=0, tool_id=tool_id, name=name, arguments=arguments)],
            )
        )

    return gen()


def _stream_with_content(text: str):
    def gen():
        for ch in text:
            yield _FakeChunk(_FakeDelta(content=ch))

    return gen()


def test_video_analysis_prompt_professional_style():
    prompt = get_video_analysis_prompt({"title": "t"}, "c", style="professional")
    assert "Emoji" not in prompt
    assert "📋" not in prompt


def test_deep_research_registers_expected_tools():
    fake_client = _FakeOpenAIClient(streams=[_stream_with_content("x")])
    _ = DeepResearchAgent(fake_client, model="m", vl_model="vl")
    schemas = ToolRegistry.list_tools_schema()
    tool_names = {s["function"]["name"] for s in schemas}
    assert "get_hot_videos" in tool_names
    assert "get_rank_videos" in tool_names
    assert "get_video_tags" in tool_names


def test_deep_research_stream_smoke_executes_tool_and_finishes():
    streams = [
        _stream_with_tool_call("tc1", "get_hot_videos", '{"page": 1, "limit": 1}'),
        _stream_with_tool_call(
            "tc2",
            "finish_research_and_write_report",
            '{"summary_of_findings": "ok"}',
        ),
        _stream_with_content("FINAL_REPORT"),
    ]
    fake_client = _FakeOpenAIClient(streams=streams)
    agent = DeepResearchAgent(fake_client, model="m", vl_model="vl")

    bilibili = _FakeBilibiliService()
    events = list(agent.stream_research("topic", bilibili))

    assert any(e.get("type") == "tool_result" and e.get("tool") == "get_hot_videos" for e in events)
    assert any(e.get("type") == "report_start" for e in events)
    report_text = "".join(e.get("content", "") for e in events if e.get("type") == "content")
    assert "FINAL_REPORT" in report_text
    assert events[-1].get("type") == "done"
