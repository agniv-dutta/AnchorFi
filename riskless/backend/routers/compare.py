from __future__ import annotations

import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.models.schemas import AssessResponse, CompareRequest, CompareResponse
from backend.services.assessment_engine import evaluate_target

router = APIRouter()


@router.post("/compare", response_model=CompareResponse)
async def compare_protocols(req: CompareRequest):
    try:
        targets = [target.strip() for target in req.targets if target.strip()]
        if len(targets) < 2:
            raise HTTPException(status_code=400, detail="At least 2 targets are required")
        if len({target.lower() for target in targets}) != len(targets):
            raise HTTPException(status_code=400, detail="Targets must be unique")

        items = [
            await evaluate_target(
                target,
                req.coverage_amount,
                req.coverage_days,
                wallet_value=req.wallet_value,
            )
            for target in targets[:3]
        ]
        winner = min(items, key=lambda item: item.get("composite_risk_score", 1000)) if items else None
        if winner:
            winner["is_safest"] = True

        response_items = [AssessResponse(**item) for item in items]
        return CompareResponse(
            items=response_items,
            winner_report_uuid=winner.get("report_uuid") if winner else None,
            winner_target=winner.get("target") if winner else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "detail": traceback.format_exc()},
        )