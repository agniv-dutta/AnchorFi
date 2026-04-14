from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_PATH), env_file_encoding="utf-8")

    GROQ_API_KEY: str = ""
    ETHERSCAN_API_KEY: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./anchorfi.db"


settings = Settings()

