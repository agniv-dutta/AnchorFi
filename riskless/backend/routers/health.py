from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
import httpx

from backend.core.config import settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _probe(url: str, timeout: float = 6.0) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
        latency = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        return {
            "status": "ok" if response.status_code < 500 else "degraded",
            "latency_ms": latency,
            "http_status": response.status_code,
            "error": None,
        }
    except Exception as exc:
        latency = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        return {
            "status": "down",
            "latency_ms": latency,
            "http_status": None,
            "error": str(exc),
        }


@router.get("/health/providers")
async def provider_health() -> dict[str, Any]:
    groq = await _probe("https://api.groq.com/openai/v1/models")
    defillama = await _probe("https://api.llama.fi/protocols")
    etherscan = await _probe("https://api.etherscan.io/api?module=stats&action=ethprice")
    goplus = await _probe("https://api.gopluslabs.io/api/v1/token_security/1?contract_addresses=0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "APP_ENV": settings.APP_ENV,
            "GROQ_API_KEY_set": bool(settings.GROQ_API_KEY),
            "ETHERSCAN_API_KEY_set": bool(settings.ETHERSCAN_API_KEY),
        },
        "providers": {
            "groq": groq,
            "defillama": defillama,
            "etherscan": etherscan,
            "goplus": goplus,
        },
    }

