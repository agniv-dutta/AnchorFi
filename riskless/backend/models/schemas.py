from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssessRequest(BaseModel):
    target: str = Field(..., description="Contract address (0x...) or protocol name/URL")
    coverage_amount: float = Field(10000, gt=0)
    coverage_days: int = Field(30, ge=1, le=365)
    wallet_value: float | None = Field(default=None, gt=0)


class RiskCategory(BaseModel):
    score: int = Field(..., ge=0, le=100)
    flags: list[str] = Field(default_factory=list)


class AiNarrative(BaseModel):
    summary: str
    top_risks: list[str] = Field(min_length=1, max_length=10)
    confidence: Literal["High", "Medium", "Low"]
    recommended_action: Literal["Safe to insure", "Insure with caution", "High risk — avoid"]
    recommended_coverage_percentage: int | None = Field(default=None, ge=0, le=100)
    recommended_coverage_amount: float | None = Field(default=None, ge=0)


class AssessResponse(BaseModel):
    report_uuid: str
    target: str
    wallet_value: float | None = None
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


class CompareRequest(BaseModel):
    targets: list[str] = Field(..., min_length=2, max_length=3)
    coverage_amount: float = Field(10000, gt=0)
    coverage_days: int = Field(30, ge=1, le=365)
    wallet_value: float | None = Field(default=None, gt=0)


class CompareResponse(BaseModel):
    items: list[AssessResponse]
    winner_report_uuid: str | None = None
    winner_target: str | None = None


class HistoryItem(BaseModel):
    id: int
    report_uuid: str | None = None
    target: str
    as_of: datetime
    composite_risk_score: int
    premium_usdc: float


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


class WatchlistCreateResponse(BaseModel):
    address: str
    added: bool


class WatchlistItem(BaseModel):
    address: str
    report_uuid: str | None = None
    current_score: int | None = None
    previous_score: int | None = None
    score_delta: int | None = None
    risk_increased: bool = False
    last_checked_at: datetime | None = None


class WatchlistResponse(BaseModel):
    items: list[WatchlistItem]

