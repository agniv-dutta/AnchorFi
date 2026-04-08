from __future__ import annotations

from fastapi import APIRouter

from sqlalchemy import select, desc

from backend.models.db import Assessment, SessionLocal
from backend.models.schemas import HistoryItem, HistoryResponse

router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def history(limit: int = 25) -> HistoryResponse:
    limit = max(1, min(200, int(limit)))
    async with SessionLocal() as session:
        q = select(Assessment).order_by(desc(Assessment.as_of)).limit(limit)
        rows = (await session.execute(q)).scalars().all()
    items = [
        HistoryItem(
            id=r.id,
            target=r.target,
            as_of=r.as_of,
            composite_risk_score=r.composite_risk_score,
            premium_usdc=r.premium_usdc,
        )
        for r in rows
    ]
    return HistoryResponse(items=items)

