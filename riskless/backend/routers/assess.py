from __future__ import annotations

import traceback
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from sqlalchemy import select

from backend.models.db import SessionLocal, WatchlistEntry
from backend.models.schemas import (
    AssessRequest,
    AssessResponse,
    WatchlistCreateResponse,
    WatchlistItem,
    WatchlistResponse,
)
from backend.services.assessment_engine import (
    evaluate_target,
    get_report_payload,
    render_report_html,
)
from backend.services.blockchain import is_eth_address

router = APIRouter()

@router.post("/assess", response_model=AssessResponse)
async def assess(req: AssessRequest) -> AssessResponse:
    try:
        payload = await evaluate_target(
            req.target,
            req.coverage_amount,
            req.coverage_days,
            wallet_value=req.wallet_value,
        )
        return AssessResponse(**payload)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "detail": traceback.format_exc()},
        )


@router.get("/report/{report_uuid}", response_class=HTMLResponse)
async def report(report_uuid: str):
    try:
        UUID(report_uuid)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid report UUID") from exc

    payload = await get_report_payload(report_uuid)
    if not payload:
        raise HTTPException(status_code=404, detail="Report not found")
    return HTMLResponse(render_report_html(payload))


@router.post("/watchlist/{address}", response_model=WatchlistCreateResponse)
async def add_watchlist(address: str) -> WatchlistCreateResponse:
    if not is_eth_address(address):
        raise HTTPException(status_code=400, detail="Watchlist only accepts Ethereum addresses")

    address_key = address.strip().lower()
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(WatchlistEntry).where(WatchlistEntry.address == address_key)
            )
        ).scalar_one_or_none()
        if row:
            return WatchlistCreateResponse(address=row.address, added=False)

        entry = WatchlistEntry(address=address_key)
        session.add(entry)
        await session.commit()
    return WatchlistCreateResponse(address=address_key, added=True)


@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist() -> WatchlistResponse:
    async with SessionLocal() as session:
        rows = (await session.execute(select(WatchlistEntry).order_by(WatchlistEntry.created_at.desc()))).scalars().all()

    items: list[WatchlistItem] = []
    for row in rows:
        previous_score = row.last_composite_risk_score
        assessment = await evaluate_target(
            row.address,
            coverage_amount=10000,
            coverage_days=30,
            use_cache=False,
            persist=False,
        )
        current_score = int(assessment.get("composite_risk_score") or 0)
        delta = current_score - previous_score if previous_score is not None else None
        risk_increased = bool(delta is not None and delta > 10)

        async with SessionLocal() as session:
            db_row = (
                await session.execute(
                    select(WatchlistEntry).where(WatchlistEntry.address == row.address)
                )
            ).scalar_one_or_none()
            if db_row:
                db_row.last_checked_at = datetime.fromisoformat(str(assessment["as_of"])) if isinstance(assessment.get("as_of"), str) else assessment.get("as_of")
                db_row.last_report_uuid = assessment.get("report_uuid")
                db_row.last_composite_risk_score = current_score
                await session.commit()

        items.append(
            WatchlistItem(
                address=row.address,
                report_uuid=assessment.get("report_uuid"),
                current_score=current_score,
                previous_score=previous_score,
                score_delta=delta,
                risk_increased=risk_increased,
                last_checked_at=assessment.get("as_of"),
            )
        )

    return WatchlistResponse(items=items)

