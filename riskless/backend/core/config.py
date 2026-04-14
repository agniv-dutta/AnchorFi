from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ETHERSCAN_API_KEY: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./anchorfi.db"


settings = Settings()

