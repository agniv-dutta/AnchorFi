from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from backend.models.schemas import HistoryItem, HistoryResponse
from backend.models.db import Assessment, SessionLocal

router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def history(limit: int = 20) -> HistoryResponse:
    limit = max(1, min(200, int(limit)))
    async with SessionLocal() as session:
        rows = (
            await session.execute(select(Assessment).order_by(Assessment.created_at.desc()).limit(limit))
        ).scalars().all()
    items = [
        HistoryItem(
            id=row.id,
            target=row.target,
            created_at=row.created_at,
            composite_risk_score=row.composite_risk_score,
            premium=row.premium,
        )
        for row in rows
    ]
    return HistoryResponse(items=items)

