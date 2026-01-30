import os

from dotenv import set_key

from src.config import Config


class SettingsService:
    def get_settings(self) -> dict:
        return {
            "success": True,
            "data": {
                "openai_api_base": os.getenv("OPENAI_API_BASE"),
                "openai_api_key": os.getenv("OPENAI_API_KEY") or "",
                "model": os.getenv("model"),
                "qa_model": os.getenv("QA_MODEL"),
                "deep_research_model": os.getenv(
                    "DEEP_RESEARCH_MODEL", "moonshotai/Kimi-K2-Thinking"
                ),
                "exa_api_key": os.getenv("EXA_API_KEY") or "",
                "enable_research_thinking": os.getenv("ENABLE_RESEARCH_THINKING", "false").lower()
                == "true",
                "dark_mode": os.getenv("DARK_MODE", "false").lower() == "true",
            },
        }

    def update_settings(self, data: dict) -> dict:
        env_path = ".env"

        if "openai_api_base" in data:
            base_url = data["openai_api_base"]
            if base_url:
                base_url = base_url.rstrip("/")
                if not base_url.endswith("/v1") and "openai.com" in base_url:
                    base_url = base_url + "/v1"
            set_key(env_path, "OPENAI_API_BASE", base_url or "")
            os.environ["OPENAI_API_BASE"] = base_url or ""
            Config.OPENAI_API_BASE = base_url or ""

        if "openai_api_key" in data:
            set_key(env_path, "OPENAI_API_KEY", data["openai_api_key"] or "")
            os.environ["OPENAI_API_KEY"] = data["openai_api_key"] or ""
            Config.OPENAI_API_KEY = data["openai_api_key"] or ""

        if "model" in data:
            set_key(env_path, "model", data["model"] or "")
            os.environ["model"] = data["model"] or ""
            Config.OPENAI_MODEL = data["model"] or ""

        if "qa_model" in data:
            set_key(env_path, "QA_MODEL", data["qa_model"] or "")
            os.environ["QA_MODEL"] = data["qa_model"] or ""
            Config.QA_MODEL = data["qa_model"] or ""

        if "deep_research_model" in data:
            set_key(env_path, "DEEP_RESEARCH_MODEL", data["deep_research_model"] or "")
            os.environ["DEEP_RESEARCH_MODEL"] = data["deep_research_model"] or ""
            Config.DEEP_RESEARCH_MODEL = data["deep_research_model"] or ""

        if "exa_api_key" in data:
            set_key(env_path, "EXA_API_KEY", data["exa_api_key"] or "")
            os.environ["EXA_API_KEY"] = data["exa_api_key"] or ""
            Config.EXA_API_KEY = data["exa_api_key"] or ""

        if "dark_mode" in data:
            set_key(env_path, "DARK_MODE", str(data["dark_mode"]).lower())
            os.environ["DARK_MODE"] = str(data["dark_mode"]).lower()

        if "enable_research_thinking" in data:
            set_key(
                env_path, "ENABLE_RESEARCH_THINKING", str(data["enable_research_thinking"]).lower()
            )
            os.environ["ENABLE_RESEARCH_THINKING"] = str(data["enable_research_thinking"]).lower()

        from src.backend_fastapi.dependencies import get_ai_service

        get_ai_service.cache_clear()
        return {"success": True, "message": "设置已更新"}
