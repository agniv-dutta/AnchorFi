from __future__ import annotations

from fastapi import APIRouter

from backend.models.schemas import HistoryItem, HistoryResponse
from backend.services.assessment_engine import list_history

router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def history(limit: int = 25) -> HistoryResponse:
    limit = max(1, min(200, int(limit)))
    items = [
        HistoryItem(
            id=r["id"],
            report_uuid=r.get("report_uuid"),
            target=r["target"],
            as_of=r["as_of"],
            composite_risk_score=r["composite_risk_score"],
            premium_usdc=r["premium_usdc"],
        )
        for r in await list_history(limit)
    ]
    return HistoryResponse(items=items)

