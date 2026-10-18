"""Environment-backed settings for local API startup."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


load_dotenv()


def _csv_setting(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _float_setting(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    cors_origins: list[str]
    ai_enabled: bool = False
    ai_provider: str = "openai"
    ai_model: str = "gpt-4o-mini"
    ai_api_key: str | None = field(default=None, repr=False)
    ai_base_url: str = "https://api.openai.com/v1"
    ai_timeout_seconds: float = 18.0

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            cors_origins=_csv_setting(
                "ARTERIA_CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
            ),
            ai_enabled=os.getenv("ARTERIA_AI_ENABLED", "false").strip().lower() in {"1", "true", "yes"},
            ai_provider=os.getenv("ARTERIA_AI_PROVIDER", "openai").strip().lower(),
            ai_model=os.getenv("ARTERIA_AI_MODEL", "gpt-4o-mini").strip(),
            ai_api_key=(os.getenv("ARTERIA_AI_API_KEY", "").strip()
                        or os.getenv("OPENAI_API_KEY", "").strip() or None),
            ai_base_url=os.getenv("ARTERIA_AI_BASE_URL", "https://api.openai.com/v1").strip(),
            ai_timeout_seconds=_float_setting("ARTERIA_AI_TIMEOUT_SECONDS", 18.0),
        )


settings = Settings.from_environment()
