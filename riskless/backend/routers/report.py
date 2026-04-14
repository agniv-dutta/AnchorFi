from __future__ import annotations

import json
from html import escape

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from backend.models.db import Assessment, SessionLocal

router = APIRouter()


def _risk_badge(score: int) -> str:
    if score >= 70:
        return "HIGH RISK"
    if score >= 40:
        return "MEDIUM RISK"
    return "LOW RISK"


@router.get("/api/report/{assessment_id}")
async def report_json(assessment_id: str):
    async with SessionLocal() as session:
        row = (await session.execute(select(Assessment).where(Assessment.id == assessment_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": row.id,
        "target": row.target,
        "composite_risk_score": row.composite_risk_score,
        "code_risk": {"score": row.code_risk_score, "flags": row.code_flags or []},
        "liquidity_risk": {"score": row.liquidity_risk_score, "flags": row.liquidity_flags or []},
        "team_risk": {"score": row.team_risk_score, "flags": row.team_flags or []},
        "track_record": {"score": row.track_record_score, "flags": row.track_record_flags or []},
        "ai": {
            "summary": row.ai_summary,
            "top_risks": row.ai_top_risks or [],
            "positive_signals": row.ai_positive_signals or [],
            "confidence": row.ai_confidence,
            "recommended_action": row.ai_recommended_action,
            "underwriter_note": row.ai_underwriter_note,
        },
        "premium": row.premium,
        "coverage_amount": row.coverage_amount,
        "coverage_days": row.coverage_days,
        "created_at": row.created_at,
        "raw_payload": json.loads(row.raw_payload or "{}"),
    }


@router.get("/report/{assessment_id}", response_class=HTMLResponse, include_in_schema=False)
async def report_html(assessment_id: str):
    async with SessionLocal() as session:
        row = (await session.execute(select(Assessment).where(Assessment.id == assessment_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    summary = escape(row.ai_summary or "No summary")
    return f"""<!doctype html>
<html><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' />
<title>AnchorFi Report</title>
<style>
body{{background:#f5f0e8;color:#111;font-family:system-ui;padding:24px;}}
.card{{border:2px solid #111;box-shadow:4px 4px 0 #111;padding:20px;margin-bottom:16px;}}
.h{{font-family:Georgia,serif;font-size:28px;font-weight:900;text-transform:uppercase;}}
.mono{{font-family:'Courier New',monospace;}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:10px;}}
.badge{{display:inline-block;padding:4px 8px;border:2px solid #111;font-family:'Courier New',monospace;font-size:10px;}}
ul{{padding-left:18px;}}
</style></head><body>
<div class='card'><div class='h'>ANCHORFI REPORT</div><div class='mono'>ID: {escape(row.id)}</div></div>
<div class='card'><div class='mono'>TARGET: {escape(row.target)}</div><div class='mono'>SCORE: {row.composite_risk_score}/100</div><div class='badge'>{_risk_badge(row.composite_risk_score)}</div><div class='mono'>PREMIUM: ${row.premium}</div></div>
<div class='card'><h3>Summary</h3><p>{summary}</p><div class='mono'>VERDICT: {escape(row.ai_recommended_action or '')}</div></div>
<div class='card row'>
<div><h4>Code</h4><ul>{''.join(f'<li>{escape(str(x))}</li>' for x in (row.code_flags or []))}</ul></div>
<div><h4>Liquidity</h4><ul>{''.join(f'<li>{escape(str(x))}</li>' for x in (row.liquidity_flags or []))}</ul></div>
<div><h4>Team</h4><ul>{''.join(f'<li>{escape(str(x))}</li>' for x in (row.team_flags or []))}</ul></div>
<div><h4>Track Record</h4><ul>{''.join(f'<li>{escape(str(x))}</li>' for x in (row.track_record_flags or []))}</ul></div>
</div>
</body></html>"""
