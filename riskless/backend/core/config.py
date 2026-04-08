from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "AnchorFi"
    environment: str = "dev"

    # API keys
    etherscan_api_key: str | None = None
    goplus_api_key: str | None = None

    # AI provider (Groq only)
    groq_api_key: str | None = None
    ai_provider: str = "groq"  # groq|none

    # SQLite
    sqlite_path: str = "anchorfi_cache.sqlite3"


settings = Settings()

