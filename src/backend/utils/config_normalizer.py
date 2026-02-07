def normalize_openai_api_base(base_url: str | None) -> str | None:
    if not base_url:
        return None
    normalized = base_url.rstrip("/")
    if not normalized.endswith("/v1") and "openai.com" in normalized:
        return normalized + "/v1"
    return normalized
