from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter

from backend.core.cache import MemoryCache, dumps_json
from backend.models.schemas import AssessRequest, AssessResponse
from backend.models.db import Assessment, SessionLocal
from backend.services.aggregator import fetch_all_signals
from backend.services.claude_analyst import generate_ai_narrative
from backend.services.risk_scorer import estimate_premium_usdc, score_signals

router = APIRouter()

_mem_cache = MemoryCache()

@router.post("/assess", response_model=AssessResponse)
async def assess(req: AssessRequest) -> AssessResponse:
    now = datetime.now(tz=timezone.utc)
    today = date.today()

    cached = _mem_cache.get(req.target, today)
    if cached:
        obj = dict(cached)
        obj["cached"] = True
        return AssessResponse(**obj)

    # SQLite cache by (target, day)
    day_s = today.isoformat()
    async with SessionLocal() as session:
        row = (
            await session.execute(
                Assessment.__table__.select().where(
                    Assessment.target == req.target.strip().lower(),
                    Assessment.day == day_s,
                )
            )
        ).first()
        if row:
            response_json = row._mapping.get("response_json")
            if response_json:
                obj = __import__("json").loads(response_json)
                _mem_cache.set(req.target, today, obj)
                obj = dict(obj)
                obj["cached"] = True
                return AssessResponse(**obj)

    raw_signals = await fetch_all_signals(req.target)
    scored = score_signals(raw_signals)
    premium = estimate_premium_usdc(req.coverage_amount, req.coverage_days, scored["composite_risk_score"])
    ai = await generate_ai_narrative(req.target, scored)

    payload = {
        "target": req.target,
        "resolved": {
            "is_address": (raw_signals.get("blockchain") or {}).get("is_address", False),
            "address": (raw_signals.get("blockchain") or {}).get("address"),
            "protocol_slug": (((raw_signals.get("defi") or {}).get("protocol") or {}).get("slug")),
        },
        "as_of": now,
        "code_risk": scored["code_risk"],
        "liquidity_risk": scored["liquidity_risk"],
        "team_risk": scored["team_risk"],
        "track_record": scored["track_record"],
        "composite_risk_score": scored["composite_risk_score"],
        "premium_usdc": premium["premium_usdc"],
        "premium_details": premium["details"],
        "ai": ai,
        "raw_signals": scored["raw_signals"],
        "cached": False,
    }

    # Persist
    async with SessionLocal() as session:
        target_key = req.target.strip().lower()
        record = Assessment(
            target=target_key,
            day=day_s,
            composite_risk_score=scored["composite_risk_score"],
            premium_usdc=premium["premium_usdc"],
            response_json=dumps_json(_serialize(payload)),
        )
        session.add(record)
        try:
            await session.commit()
        except Exception:
            await session.rollback()

    payload = _serialize(payload)
    _mem_cache.set(req.target, today, payload)
    return AssessResponse(**payload)


def _serialize(obj: object) -> object:
    # Ensure datetimes are JSON-able and pydantic can ingest
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

