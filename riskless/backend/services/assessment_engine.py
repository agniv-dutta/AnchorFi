from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, timezone
from html import escape
from typing import Any
from uuid import uuid4

from backend.core.cache import MemoryCache, dumps_json
from backend.models.db import Assessment, SessionLocal
from backend.services.aggregator import fetch_all_signals
from backend.services.claude_analyst import generate_ai_narrative
from backend.services.risk_scorer import estimate_premium_usdc, score_signals


_mem_cache = MemoryCache()


def _serialize(obj: object) -> object:
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _today_cache_key(target: str) -> tuple[str, date]:
    return target.strip(), date.today()


def _load_payload_from_row(row) -> dict[str, Any] | None:
    response_json = row._mapping.get("response_json")
    if not response_json:
        return None
    try:
        payload = json.loads(response_json)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _apply_wallet_recommendation(payload: dict[str, Any], wallet_value: float | None) -> dict[str, Any]:
    enriched = deepcopy(payload)
    if wallet_value is not None:
        enriched["wallet_value"] = wallet_value
    ai = enriched.get("ai")
    if isinstance(ai, dict) and wallet_value is not None:
        pct = ai.get("recommended_coverage_percentage")
        if isinstance(pct, (int, float)):
            ai["recommended_coverage_amount"] = round((wallet_value * float(pct)) / 100.0, 2)
        enriched["ai"] = ai
    return enriched


async def evaluate_target(
    target: str,
    coverage_amount: float,
    coverage_days: int,
    wallet_value: float | None = None,
    *,
    use_cache: bool = True,
    persist: bool = True,
    existing_report_uuid: str | None = None,
) -> dict[str, Any]:
    target_key, today = _today_cache_key(target)
    now = datetime.now(tz=timezone.utc)

    if use_cache:
        cached = _mem_cache.get(target_key, today)
        if cached:
            payload = _apply_wallet_recommendation(dict(cached), wallet_value)
            payload["cached"] = True
            return payload

        day_s = today.isoformat()
        async with SessionLocal() as session:
            row = (
                await session.execute(
                    Assessment.__table__.select().where(
                        Assessment.target == target_key.lower(),
                        Assessment.day == day_s,
                    )
                )
            ).first()
            if row:
                payload = _load_payload_from_row(row)
                if payload:
                    _mem_cache.set(target_key, today, payload)
                    payload = _apply_wallet_recommendation(payload, wallet_value)
                    payload["cached"] = True
                    return payload

    raw_signals = await fetch_all_signals(target)
    scored = score_signals(raw_signals)
    premium = estimate_premium_usdc(
        coverage_amount, coverage_days, scored["composite_risk_score"]
    )
    ai = await generate_ai_narrative(target, scored, wallet_value=wallet_value)

    report_uuid = existing_report_uuid or str(uuid4())
    payload: dict[str, Any] = {
        "report_uuid": report_uuid,
        "target": target,
        "wallet_value": wallet_value,
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
    payload = _apply_wallet_recommendation(payload, wallet_value)

    if persist:
        async with SessionLocal() as session:
            record = Assessment(
                target=target_key.lower(),
                day=today.isoformat(),
                report_uuid=report_uuid,
                composite_risk_score=scored["composite_risk_score"],
                premium_usdc=premium["premium_usdc"],
                response_json=dumps_json(_serialize(payload)),
            )
            session.add(record)
            try:
                await session.commit()
            except Exception:
                await session.rollback()

    serializable = _serialize(payload)
    _mem_cache.set(target_key, today, serializable)
    return serializable


async def get_report_payload(report_uuid: str) -> dict[str, Any] | None:
    async with SessionLocal() as session:
        row = (
            await session.execute(
                Assessment.__table__.select().where(Assessment.report_uuid == report_uuid)
            )
        ).first()
    if not row:
        return None
    payload = _load_payload_from_row(row)
    if payload is None:
        return None
    return payload


async def list_history(limit: int) -> list[dict[str, Any]]:
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                Assessment.__table__.select().order_by(Assessment.as_of.desc()).limit(limit)
            )
        ).fetchall()
    return [dict(r._mapping) for r in rows]


def render_report_html(payload: dict[str, Any]) -> str:
    target = escape(str(payload.get("target", "Unknown")))
    report_uuid = escape(str(payload.get("report_uuid", "")))
    score = escape(str(payload.get("composite_risk_score", "-")))
    premium = escape(str(payload.get("premium_usdc", "-")))
    as_of = escape(str(payload.get("as_of", "")))
    ai = payload.get("ai") or {}
    summary = escape(str(ai.get("summary", "No AI summary available.")))
    action = escape(str(ai.get("recommended_action", "-")))
    pct = ai.get("recommended_coverage_percentage")
    amount = ai.get("recommended_coverage_amount")
    wallet_value = payload.get("wallet_value")
    track_flags = (payload.get("track_record") or {}).get("flags") or []
    liq_flags = (payload.get("liquidity_risk") or {}).get("flags") or []
    code_flags = (payload.get("code_risk") or {}).get("flags") or []
    team_flags = (payload.get("team_risk") or {}).get("flags") or []
    near_misses = (((payload.get("raw_signals") or {}).get("defi") or {}).get("protocol") or {}).get(
        "near_misses"
    ) or []

    def render_flags(items: list[Any]) -> str:
        if not items:
            return "<li class='muted'>No flags</li>"
        return "".join(f"<li>{escape(str(item))}</li>" for item in items[:5])

    near_miss_line = (
        f"<p class='muted strong'>{len(near_misses)} similar protocols were exploited in the past 2 years.</p>"
        if near_misses
        else "<p class='muted'>No similar protocols were found in the two-year hack history sample.</p>"
    )

    return f"""<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8' />
    <meta name='viewport' content='width=device-width, initial-scale=1' />
    <title>AnchorFi Report</title>
    <style>
      :root {{ color-scheme: dark; }}
      body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #020617; color: #e2e8f0; }}
      .wrap {{ max-width: 960px; margin: 0 auto; padding: 40px 20px 64px; }}
      .card {{ background: rgba(2, 6, 23, 0.75); border: 1px solid rgba(51, 65, 85, 0.9); border-radius: 20px; padding: 24px; margin-top: 20px; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
      .pill {{ display: inline-block; border: 1px solid rgba(71, 85, 105, 0.9); border-radius: 999px; padding: 6px 12px; font-size: 12px; color: #cbd5e1; }}
      .title {{ font-size: 40px; font-weight: 700; margin: 8px 0 0; }}
      .muted {{ color: #94a3b8; }}
      .strong {{ color: #e2e8f0; }}
      ul {{ margin: 10px 0 0; padding-left: 20px; }}
      li {{ margin: 4px 0; }}
      .kpi {{ font-size: 28px; font-weight: 700; }}
      .small {{ font-size: 13px; color: #94a3b8; }}
      .badge {{ background: rgba(99, 102, 241, 0.16); border-color: rgba(99, 102, 241, 0.4); color: #c7d2fe; }}
      .section-title {{ font-size: 18px; font-weight: 600; margin: 0 0 8px; }}
      .summary {{ line-height: 1.7; font-size: 16px; }}
      .split {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
      @media (max-width: 720px) {{ .split {{ grid-template-columns: 1fr; }} .title {{ font-size: 32px; }} }}
    </style>
  </head>
  <body>
    <main class='wrap'>
      <span class='pill badge'>AnchorFi shareable report</span>
      <h1 class='title'>{target}</h1>
      <p class='muted'>Report ID: {report_uuid}</p>

      <section class='card grid'>
        <div>
          <div class='small'>Composite risk</div>
          <div class='kpi'>{score}/100</div>
        </div>
        <div>
          <div class='small'>Estimated premium</div>
          <div class='kpi'>{premium} USDC</div>
        </div>
        <div>
          <div class='small'>As of</div>
          <div class='kpi' style='font-size: 18px; font-weight: 600'>{as_of}</div>
        </div>
        <div>
          <div class='small'>Wallet value</div>
          <div class='kpi' style='font-size: 18px; font-weight: 600'>{escape(str(wallet_value)) if wallet_value is not None else 'Not provided'}</div>
        </div>
      </section>

      <section class='card'>
        <h2 class='section-title'>Underwriter note</h2>
        <p class='summary'>{summary}</p>
        <p><span class='strong'>Recommended action:</span> {action}</p>
        <p><span class='strong'>Coverage recommendation:</span> {escape(str(pct)) if pct is not None else 'Not available'}%{f" / {escape(str(amount))} USDC" if amount is not None else ''}</p>
        {near_miss_line}
      </section>

      <section class='card split'>
        <div>
          <h2 class='section-title'>Code risk</h2>
          <ul>{render_flags(code_flags)}</ul>
        </div>
        <div>
          <h2 class='section-title'>Liquidity risk</h2>
          <ul>{render_flags(liq_flags)}</ul>
        </div>
        <div>
          <h2 class='section-title'>Team risk</h2>
          <ul>{render_flags(team_flags)}</ul>
        </div>
        <div>
          <h2 class='section-title'>Track record</h2>
          <ul>{render_flags(track_flags)}</ul>
        </div>
      </section>

      <p class='small' style='margin-top: 18px;'>This report is read-only and intended for demo sharing. It is not a binding quote or investment advice.</p>
    </main>
  </body>
</html>"""
