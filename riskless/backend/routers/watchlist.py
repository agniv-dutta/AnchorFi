from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select

from backend.models.db import SessionLocal, WatchlistItem as WatchRow
from backend.models.schemas import AssessRequest
from backend.routers.assess import assess as assess_handler

router = APIRouter()


@router.post("/watchlist")
async def add_watchlist(payload: dict):
    address = str((payload or {}).get("address") or "").strip().lower()
    if not address:
        return JSONResponse(status_code=400, content={"error": "address is required"})

    async with SessionLocal() as session:
        exists = (await session.execute(select(WatchRow).where(WatchRow.address == address))).scalar_one_or_none()
        if exists:
            return {"address": address, "added": False}
        session.add(WatchRow(address=address))
        await session.commit()
    return {"address": address, "added": True}


@router.get("/watchlist")
async def list_watchlist():
    async with SessionLocal() as session:
        rows = (await session.execute(select(WatchRow).order_by(WatchRow.created_at.desc()))).scalars().all()
    return {
        "items": [
            {
                "address": row.address,
                "latest_score": row.latest_score,
                "last_checked_at": row.last_checked_at,
            }
            for row in rows
        ]
    }


@router.delete("/watchlist/{address}")
async def delete_watchlist(address: str):
    address = address.strip().lower()
    async with SessionLocal() as session:
        row = (await session.execute(select(WatchRow).where(WatchRow.address == address))).scalar_one_or_none()
        if row:
            await session.delete(row)
            await session.commit()
    return {"removed": True, "address": address}


@router.get("/watchlist/refresh")
async def refresh_watchlist():
    async with SessionLocal() as session:
        rows = (await session.execute(select(WatchRow))).scalars().all()

    out = []
    for row in rows:
        previous = row.latest_score
        assessed = await assess_handler(AssessRequest(target=row.address, coverage_amount=10000, coverage_days=30))
        data = assessed.model_dump() if hasattr(assessed, "model_dump") else assessed
        latest = int(data.get("composite_risk_score") or 0)
        increased = previous is not None and latest > previous + 10

        async with SessionLocal() as session:
            db_row = (await session.execute(select(WatchRow).where(WatchRow.address == row.address))).scalar_one_or_none()
            if db_row:
                db_row.latest_score = latest
                db_row.last_checked_at = datetime.now(timezone.utc)
                await session.commit()

        out.append(
            {
                "address": row.address,
                "previous_score": previous,
                "latest_score": latest,
                "risk_increased": bool(increased),
            }
        )

    return {"items": out}
