from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from backend.models.db import Assessment, SessionLocal
from backend.models.schemas import AssessRequest, AssessResponse
from backend.services.ai_analyst import get_ai_analysis
from backend.services.blockchain import fetch_contract_data
from backend.services.defi_data import fetch_defi_data
from backend.services.risk_scorer import compute_risk_score

router = APIRouter()


def _to_response(row: Assessment, cached: bool) -> AssessResponse:
    payload = json.loads(row.raw_payload or "{}")
    return AssessResponse(
        id=row.id,
        target=row.target,
        created_at=row.created_at,
        code_risk={"score": row.code_risk_score, "flags": row.code_flags or []},
        liquidity_risk={"score": row.liquidity_risk_score, "flags": row.liquidity_flags or []},
        team_risk={"score": row.team_risk_score, "flags": row.team_flags or []},
        track_record={"score": row.track_record_score, "flags": row.track_record_flags or []},
        composite_risk_score=row.composite_risk_score,
        premium=row.premium,
        coverage_amount=row.coverage_amount,
        coverage_days=row.coverage_days,
        ai={
            "summary": row.ai_summary,
            "top_risks": row.ai_top_risks or [],
            "positive_signals": row.ai_positive_signals or [],
            "confidence": row.ai_confidence,
            "recommended_action": row.ai_recommended_action,
            "underwriter_note": row.ai_underwriter_note,
            "error": payload.get("ai", {}).get("error"),
        },
        raw_signals=payload.get("raw_signals", {}),
        cached=cached,
    )


@router.post("/assess", response_model=AssessResponse)
async def assess(req: AssessRequest):
    try:
        target = req.target.strip()
        today = date.today().isoformat()

        async with SessionLocal() as session:
            cached = (
                await session.execute(
                    select(Assessment)
                    .where(Assessment.target == target.lower())
                    .where(func.date(Assessment.created_at) == today)
                    .order_by(Assessment.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if cached:
                return _to_response(cached, cached=True)

        blockchain, defi = await asyncio.gather(
            fetch_contract_data(target),
            fetch_defi_data(target),
        )

        scored = compute_risk_score(blockchain, defi)
        ai = await get_ai_analysis(scored, target)

        base_rate = 0.002
        risk_multiplier = 1 + (scored["composite_risk_score"] / 100) * 15
        premium = round(req.coverage_amount * base_rate * risk_multiplier * (req.coverage_days / 30), 2)
        premium = min(premium, req.coverage_amount * 0.25)

        raw_payload = {
            "raw_signals": scored.get("raw_signals", {}),
            "ai": ai,
        }

        row = Assessment(
            target=target.lower(),
            composite_risk_score=scored["composite_risk_score"],
            code_risk_score=scored["code_risk"]["score"],
            liquidity_risk_score=scored["liquidity_risk"]["score"],
            team_risk_score=scored["team_risk"]["score"],
            track_record_score=scored["track_record"]["score"],
            code_flags=scored["code_risk"]["flags"],
            liquidity_flags=scored["liquidity_risk"]["flags"],
            team_flags=scored["team_risk"]["flags"],
            track_record_flags=scored["track_record"]["flags"],
            ai_summary=ai.get("summary") or "",
            ai_top_risks=ai.get("top_risks") or [],
            ai_positive_signals=ai.get("positive_signals") or [],
            ai_confidence=ai.get("confidence") or "Low",
            ai_recommended_action=ai.get("recommended_action") or "Insure with caution",
            ai_underwriter_note=ai.get("underwriter_note") or "",
            premium=float(premium),
            coverage_amount=req.coverage_amount,
            coverage_days=req.coverage_days,
            raw_payload=json.dumps(raw_payload, ensure_ascii=False),
            created_at=datetime.now(timezone.utc),
        )

        async with SessionLocal() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)

        return _to_response(row, cached=False)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)},
        )

