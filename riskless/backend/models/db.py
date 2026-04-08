from __future__ import annotations

import json
from uuid import uuid4
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func, Index
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
    report_uuid: Mapped[str | None] = mapped_column(String(36), unique=True, index=True, nullable=True)

    composite_risk_score: Mapped[int] = mapped_column(Integer)
    premium_usdc: Mapped[float] = mapped_column(Float)
    response_json: Mapped[str] = mapped_column(Text)


Index("ix_assessments_target_day", Assessment.target, Assessment.day, unique=True)


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_report_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_composite_risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)


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
        await conn.run_sync(_migrate_legacy_schema)


def _migrate_legacy_schema(conn) -> None:
    table_info = conn.exec_driver_sql("PRAGMA table_info(assessments)").fetchall()
    columns = {row[1] for row in table_info}
    if "report_uuid" not in columns:
        conn.exec_driver_sql("ALTER TABLE assessments ADD COLUMN report_uuid VARCHAR(36)")

    conn.exec_driver_sql(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_assessments_report_uuid ON assessments(report_uuid)"
    )

    rows = conn.exec_driver_sql(
        "SELECT id, report_uuid, response_json FROM assessments WHERE report_uuid IS NULL OR report_uuid = ''"
    ).fetchall()
    for row in rows:
        report_uuid = str(uuid4())
        response_json = row[2] or "{}"
        try:
            payload = json.loads(response_json)
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            payload["report_uuid"] = report_uuid
            response_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        conn.exec_driver_sql(
            "UPDATE assessments SET report_uuid = ?, response_json = ? WHERE id = ?",
            (report_uuid, response_json, row[0]),
        )

