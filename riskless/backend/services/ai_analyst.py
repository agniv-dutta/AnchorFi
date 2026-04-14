from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)


def _normalize(payload: dict[str, Any], target: str) -> dict[str, Any]:
    summary = str(payload.get("summary") or "").strip()
    if not summary:
        summary = f"{target} was assessed using available on-chain and protocol signals."

    confidence = str(payload.get("confidence") or "Medium").capitalize()
    if confidence not in {"High", "Medium", "Low"}:
        confidence = "Medium"

    action = str(payload.get("recommended_action") or "Insure with caution")
    allowed_actions = {"Safe to insure", "Insure with caution", "High risk — avoid"}
    if action not in allowed_actions:
        action = "Insure with caution"

    top_risks = payload.get("top_risks") if isinstance(payload.get("top_risks"), list) else []
    positive = payload.get("positive_signals") if isinstance(payload.get("positive_signals"), list) else []

    return {
        "summary": summary,
        "top_risks": [str(x) for x in top_risks[:3]],
        "positive_signals": [str(x) for x in positive[:3]],
        "confidence": confidence,
        "recommended_action": action,
        "underwriter_note": str(payload.get("underwriter_note") or ""),
    }


async def call_groq(signals: dict[str, Any]) -> dict[str, Any]:
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")

    system_prompt = """You are AnchorFi's AI underwriter — a DeFi insurance 
expert. Given structured risk signals, respond ONLY with valid JSON, 
no markdown, no backticks, no explanation. Use exactly this shape:
{
  "summary": "2-3 sentences about this specific protocol's risk for a 
              non-technical user. Be specific — mention TVL, audits, age.",
  "top_risks": ["most important risk", "second risk", "third risk"],
  "positive_signals": ["strength 1", "strength 2"],
  "confidence": "High",
  "recommended_action": "Safe to insure",
  "underwriter_note": "One specific technical observation."
}
For recommended_action use ONLY one of:
  "Safe to insure" | "Insure with caution" | "High risk — avoid"
"""
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Risk signals: {json.dumps(signals)}"},
        ],
        "temperature": 0.2,
        "max_tokens": 600,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) > 1:
                raw = parts[1]
                if raw.startswith("json"):
                    raw = raw[4:]
        return json.loads(raw.strip())


def _deterministic_fallback(signals: dict[str, Any], target: str) -> dict[str, Any]:
    score = int(signals.get("composite_risk_score", 50) or 50)
    protocol = str(signals.get("protocol_name") or target or "This protocol")

    if score < 40:
        action = "Safe to insure"
        summary = (
            f"{protocol} shows a relatively low risk profile based on "
            f"on-chain signals. With a composite score of {score}/100, "
            f"the protocol demonstrates acceptable security characteristics "
            f"for coverage consideration."
        )
    elif score < 70:
        action = "Insure with caution"
        summary = (
            f"{protocol} presents moderate risk with a score of {score}/100. "
            f"Some risk factors were identified that warrant careful review "
            f"before committing to coverage at higher amounts."
        )
    else:
        action = "High risk — avoid"
        summary = (
            f"{protocol} carries significant risk indicators with a score "
            f"of {score}/100. Multiple red flags suggest this protocol "
            f"should be approached with extreme caution or avoided."
        )

    all_flags = (
        signals.get("code_risk", {}).get("flags", [])
        + signals.get("liquidity_risk", {}).get("flags", [])
        + signals.get("team_risk", {}).get("flags", [])
    )
    top_risks = all_flags[:3] if all_flags else ["Insufficient data to assess"]

    return {
        "summary": summary,
        "top_risks": top_risks,
        "positive_signals": [],
        "confidence": "Low",
        "recommended_action": action,
        "underwriter_note": "Assessment based on on-chain signals only. "
        "AI provider unavailable — add GROQ_API_KEY to .env "
        "for enhanced analysis.",
        "ai_provider": "deterministic_fallback",
    }


async def get_ai_analysis(signals: dict[str, Any], target: str | None = None) -> dict[str, Any]:
    logger.info(f"ANTHROPIC_API_KEY set: {bool(getattr(settings, 'ANTHROPIC_API_KEY', ''))}")
    logger.info(f"GROQ_API_KEY set: {bool(settings.GROQ_API_KEY)}")

    protocol = str(signals.get("protocol_name") or target or "This protocol")

    if settings.GROQ_API_KEY:
        try:
            groq_result = await call_groq(signals)
            return _normalize(groq_result, protocol)
        except Exception as e:
            logger.warning(f"Groq failed: {e}")

    return _deterministic_fallback(signals, protocol)
