from __future__ import annotations

import json
from typing import Any

import httpx

from backend.core.config import settings


SYSTEM_PROMPT = (
    "You are RiskLens, an expert DeFi insurance underwriter. "
    "You receive structured risk signals about a DeFi protocol and produce: "
    "(1) a 3-sentence plain-English risk summary for a non-technical user, "
    "(2) the top 3 specific risk factors, "
    "(3) a confidence level (High/Medium/Low) in the assessment, "
    "(4) a recommended action: [Safe to insure / Insure with caution / High risk — avoid]. "
    "Respond only in JSON with keys: summary, top_risks, confidence, recommended_action."
)


def _provider() -> str:
    if settings.ai_provider != "auto":
        return settings.ai_provider
    if settings.groq_api_key:
        return "groq"
    if settings.anthropic_api_key:
        return "anthropic"
    return "none"


async def generate_ai_narrative(target: str, risk_signals: dict[str, Any]) -> dict[str, Any] | None:
    provider = _provider()
    if provider == "none":
        return None
    if provider == "groq":
        return await _groq_chat(target, risk_signals)
    if provider == "anthropic":
        return await _anthropic_claude(target, risk_signals)
    return None


async def _anthropic_claude(target: str, risk_signals: dict[str, Any]) -> dict[str, Any] | None:
    if not settings.anthropic_api_key:
        return None
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 600,
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": f"Assess this protocol/contract '{target}':\n{json.dumps(risk_signals, indent=2)}",
            }
        ],
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()

    # Anthropic returns content blocks; we expect a JSON string in first text block.
    content = data.get("content") or []
    text = None
    if isinstance(content, list):
        for b in content:
            if (b or {}).get("type") == "text":
                text = (b or {}).get("text")
                break
    if not text:
        return None
    return _safe_parse_json(text)


async def _groq_chat(target: str, risk_signals: dict[str, Any]) -> dict[str, Any] | None:
    if not settings.groq_api_key:
        return None
    # Groq is OpenAI-chat compatible
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "authorization": f"Bearer {settings.groq_api_key}",
        "content-type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.2,
        "max_tokens": 500,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Assess this protocol/contract '{target}':\n{json.dumps(risk_signals, indent=2)}",
            },
        ],
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
    choice = ((data or {}).get("choices") or [{}])[0]
    msg = (choice.get("message") or {})
    text = msg.get("content")
    if not text:
        return None
    return _safe_parse_json(text)


def _safe_parse_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
        return None
    except Exception:
        # Try to extract first {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                obj = json.loads(text[start : end + 1])
                return obj if isinstance(obj, dict) else None
            except Exception:
                return None
        return None

