from __future__ import annotations

import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.schemas import CompareRequest, CompareResponse
from backend.routers.assess import assess as assess_handler
from backend.models.schemas import AssessRequest

router = APIRouter()


@router.post("/compare", response_model=CompareResponse)
async def compare_protocols(req: CompareRequest):
    try:
        targets = [target.strip() for target in req.targets if target.strip()][:3]

        async def assess_one(target: str):
            data = await assess_handler(
                AssessRequest(
                    target=target,
                    coverage_amount=req.coverage_amount,
                    coverage_days=req.coverage_days,
                )
            )
            if hasattr(data, "model_dump"):
                return data.model_dump()
            return data

        results = await asyncio.gather(*[assess_one(target) for target in targets])
        valid = [result for result in results if isinstance(result, dict) and result.get("composite_risk_score") is not None]
        recommended = None
        if valid:
            winner = min(valid, key=lambda result: int(result.get("composite_risk_score") or 100))
            recommended = winner.get("target")
            for result in valid:
                result["is_safest"] = result.get("target") == recommended
        return CompareResponse(results=results, recommended=recommended)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)},
        )