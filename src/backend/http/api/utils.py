import json
from typing import Any


def sse_data(payload: dict[str, Any], ensure_ascii: bool = False) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=ensure_ascii)}\n\n"

