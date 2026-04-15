from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssessRequest(BaseModel):
    target: str = Field(..., description="Contract address (0x...) or protocol name")
    coverage_amount: float = Field(10000, gt=0)
    coverage_days: int = Field(30, ge=1, le=365)


class RiskCategory(BaseModel):
    score: int = Field(..., ge=0, le=100)
    flags: list[str] = Field(default_factory=list)


class AiNarrative(BaseModel):
    summary: str
    top_risks: list[str] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)
    confidence: Literal["High", "Medium", "Low"]
    recommended_action: Literal["Safe to insure", "Insure with caution", "High risk — avoid"]
    underwriter_note: str = ""
    ai_provider: str | None = None
    error: str | None = None


class DataFreshness(BaseModel):
    fetched_at: datetime
    source_age_seconds: int = 0
    partial_data_flags: list[str] = Field(default_factory=list)
    source_timestamps: dict[str, str | None] = Field(default_factory=dict)


class ScoreBreakdownItem(BaseModel):
    score: int = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0)
    weighted_points: float = Field(..., ge=0)


class ScoreBreakdown(BaseModel):
    code_risk: ScoreBreakdownItem
    liquidity_risk: ScoreBreakdownItem
    team_risk: ScoreBreakdownItem
    track_record: ScoreBreakdownItem
    total_weighted_points: float = Field(..., ge=0)


class AssessResponse(BaseModel):
    id: str
    target: str
    created_at: datetime

    code_risk: RiskCategory
    liquidity_risk: RiskCategory
    team_risk: RiskCategory
    track_record: RiskCategory
    composite_risk_score: int = Field(..., ge=0, le=100)

    premium: float
    coverage_amount: float
    coverage_days: int

    ai: AiNarrative | None = None
    data_freshness: DataFreshness | None = None
    score_breakdown: ScoreBreakdown | None = None
    raw_signals: dict[str, Any] = Field(default_factory=dict)
    cached: bool = False


class CompareRequest(BaseModel):
    targets: list[str] = Field(..., min_length=2, max_length=3)
    coverage_amount: float = Field(10000, gt=0)
    coverage_days: int = Field(30, ge=1, le=365)


class CompareResponse(BaseModel):
    results: list[dict[str, Any]]
    recommended: str | None = None


class HistoryItem(BaseModel):
    id: str
    target: str
    created_at: datetime
    composite_risk_score: int
    premium: float


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


class WatchlistCreateResponse(BaseModel):
    address: str
    added: bool = True


class WatchlistItem(BaseModel):
    address: str
    latest_score: int | None = None
    previous_score: int | None = None
    risk_change_pct: float | None = None
    risk_increased: bool = False
    last_checked_at: datetime | None = None


class WatchlistResponse(BaseModel):
    items: list[WatchlistItem]

