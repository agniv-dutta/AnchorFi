from __future__ import annotations

from datetime import datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, func, Index
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from backend.core.config import settings


class Base(DeclarativeBase):
    pass


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target: Mapped[str] = mapped_column(String(256), index=True)
    day: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    composite_risk_score: Mapped[int] = mapped_column(Integer)
    premium_usdc: Mapped[float] = mapped_column(Float)
    response_json: Mapped[str] = mapped_column(Text)


Index("ix_assessments_target_day", Assessment.target, Assessment.day, unique=True)


def _sqlite_url() -> str:
    # relative path is fine: stored next to backend working dir
    return f"sqlite+aiosqlite:///{settings.sqlite_path}"


engine: AsyncEngine = create_async_engine(_sqlite_url(), future=True)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

