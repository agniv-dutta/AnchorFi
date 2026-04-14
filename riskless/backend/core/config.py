from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_PATH), env_file_encoding="utf-8")

    APP_ENV: str = "development"
    GROQ_API_KEY: str = ""
    ETHERSCAN_API_KEY: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./anchorfi.db"


settings = Settings()


def validate_runtime_settings() -> list[str]:
    issues: list[str] = []
    env = (settings.APP_ENV or "development").strip().lower()
    if env in {"production", "staging"} and not settings.GROQ_API_KEY:
        issues.append("GROQ_API_KEY is required when APP_ENV is production or staging")
    if not settings.DATABASE_URL:
        issues.append("DATABASE_URL must be set")
    return issues

