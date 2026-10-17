"""Environment-backed settings for local API startup."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _csv_setting(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    cors_origins: list[str]

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            cors_origins=_csv_setting(
                "ARTERIA_CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            )
        )


settings = Settings.from_environment()
