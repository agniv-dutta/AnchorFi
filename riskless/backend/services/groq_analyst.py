from __future__ import annotations

import json
from typing import Any

import httpx

from backend.core.config import settings


SYSTEM_PROMPT = (
    "You are AnchorFi, an expert DeFi insurance underwriter. "
    "Given structured risk signals about a DeFi protocol, respond ONLY with valid JSON "
    "(no markdown, no backticks) with keys: summary, top_risks, confidence, recommended_action, "
    "recommended_coverage_percentage, recommended_coverage_amount. "
    "The summary must be 3 plain-English sentences for a non-technical user. "
    "If wallet_value is provided, recommend what percentage of the wallet should be insured "
    "(higher risk = insure more)."
)


async def generate_ai_narrative(
    target: str, risk_signals: dict[str, Any], wallet_value: float | None = None
) -> dict[str, Any] | None:
    if not settings.groq_api_key:
        return None
    return await _groq_chat(target, risk_signals, wallet_value)


async def get_ai_analysis(
    risk_signals: dict[str, Any],
    target: str = "",
    wallet_value: float | None = None,
) -> dict[str, Any] | None:
    return await generate_ai_narrative(target, risk_signals, wallet_value=wallet_value)


async def _groq_chat(
    target: str, risk_signals: dict[str, Any], wallet_value: float | None = None
) -> dict[str, Any] | None:
    if not settings.groq_api_key:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Assess this DeFi protocol risk data: {json.dumps(risk_signals)}"
                    + (
                        f"\nWallet value: {wallet_value:.2f} USDC"
                        if wallet_value is not None
                        else ""
                    )
                ),
            },
        ],
        "temperature": 0.3,
        "max_tokens": 500,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return None

    text = (((data or {}).get("choices") or [{}])[0].get("message") or {}).get("content")
    if not text:
        return None
    return _safe_parse_json(text)


def _safe_parse_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                obj = json.loads(text[start : end + 1])
                return obj if isinstance(obj, dict) else None
            except Exception:
                return None
        return None
