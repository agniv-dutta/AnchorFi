from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssessRequest(BaseModel):
    target: str = Field(..., description="Contract address (0x...) or protocol name/URL")
    coverage_amount: float = Field(10000, gt=0)
    coverage_days: int = Field(30, ge=1, le=365)


class RiskCategory(BaseModel):
    score: int = Field(..., ge=0, le=100)
    flags: list[str] = Field(default_factory=list)


class AiNarrative(BaseModel):
    summary: str
    top_risks: list[str] = Field(min_length=1, max_length=10)
    confidence: Literal["High", "Medium", "Low"]
    recommended_action: Literal["Safe to insure", "Insure with caution", "High risk — avoid"]


class AssessResponse(BaseModel):
    target: str
    resolved: dict[str, Any] = Field(default_factory=dict)
    as_of: datetime

    code_risk: RiskCategory
    liquidity_risk: RiskCategory
    team_risk: RiskCategory
    track_record: RiskCategory
    composite_risk_score: int = Field(..., ge=0, le=100)

    premium_usdc: float
    premium_details: dict[str, Any]

    ai: AiNarrative | None = None
    raw_signals: dict[str, Any] = Field(default_factory=dict)
    cached: bool = False


class HistoryItem(BaseModel):
    id: int
    target: str
    as_of: datetime
    composite_risk_score: int
    premium_usdc: float


class HistoryResponse(BaseModel):
    items: list[HistoryItem]

