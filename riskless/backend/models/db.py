from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from backend.core.config import settings


class Base(DeclarativeBase):
    pass


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target: Mapped[str] = mapped_column(String(256), index=True)

    composite_risk_score: Mapped[int] = mapped_column(Integer)
    code_risk_score: Mapped[int] = mapped_column(Integer)
    liquidity_risk_score: Mapped[int] = mapped_column(Integer)
    team_risk_score: Mapped[int] = mapped_column(Integer)
    track_record_score: Mapped[int] = mapped_column(Integer)

    code_flags: Mapped[list[str]] = mapped_column(JSON)
    liquidity_flags: Mapped[list[str]] = mapped_column(JSON)
    team_flags: Mapped[list[str]] = mapped_column(JSON)
    track_record_flags: Mapped[list[str]] = mapped_column(JSON)

    ai_summary: Mapped[str] = mapped_column(Text)
    ai_top_risks: Mapped[list[str]] = mapped_column(JSON)
    ai_positive_signals: Mapped[list[str]] = mapped_column(JSON)
    ai_confidence: Mapped[str] = mapped_column(String(16))
    ai_recommended_action: Mapped[str] = mapped_column(String(64))
    ai_underwriter_note: Mapped[str] = mapped_column(Text)

    premium: Mapped[float] = mapped_column(Float)
    coverage_amount: Mapped[float] = mapped_column(Float)
    coverage_days: Mapped[int] = mapped_column(Integer)

    raw_payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    latest_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


engine = create_async_engine(settings.DATABASE_URL, future=True)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(bind=engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

