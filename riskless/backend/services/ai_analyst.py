from __future__ import annotations

import json
from typing import Any

import httpx

from backend.core.config import settings


SYSTEM_PROMPT = (
    "You are AnchorFi's AI underwriter — a DeFi insurance expert who explains "
    "risk in plain English to non-technical users. You are precise, honest, and "
    "never alarmist without reason. "
    "Given structured risk signals, respond ONLY with valid JSON (no markdown fences, "
    "no preamble) in exactly this shape: "
    "{"
    '"summary":"2-3 sentence plain English risk summary.",'
    '"top_risks":["specific risk 1","specific risk 2","specific risk 3"],'
    '"positive_signals":["good thing 1","good thing 2"],'
    '"confidence":"High|Medium|Low",'
    '"recommended_action":"Safe to insure|Insure with caution|High risk — avoid",'
    '"underwriter_note":"One sentence underwriter note."'
    "}"
)


def _placeholder(error: str) -> dict[str, Any]:
    return {
        "summary": "AnchorFi could not reach Groq, so this summary uses deterministic risk signals only.",
        "top_risks": ["AI provider unavailable"],
        "positive_signals": [],
        "confidence": "Low",
        "recommended_action": "Insure with caution",
        "underwriter_note": "Fallback mode was used because Groq was unavailable.",
        "error": error,
    }


def _parse_json_or_none(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


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


async def _call_groq(signals: dict[str, Any]) -> dict[str, Any] | None:
    if not settings.GROQ_API_KEY:
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(signals)},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 600,
                    "response_format": {"type": "json_object"},
                },
                timeout=30,
            )
            resp.raise_for_status()
            text = (((resp.json() or {}).get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            return _parse_json_or_none(text)
    except Exception:
        return None


async def get_ai_analysis(signals: dict[str, Any], target: str) -> dict[str, Any]:
    groq = await _call_groq(signals)
    if groq:
        return _normalize(groq, target)

    return _placeholder("Groq unavailable")
