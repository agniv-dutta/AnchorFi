from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

KNOWN_SLUGS = {
    "aave": "aave",
    "compound": "compound-finance",
    "uniswap": "uniswap",
    "curve": "curve-dex",
    "makerdao": "makerdao",
    "maker": "makerdao",
    "lido": "lido",
    "convex": "convex-finance",
    "yearn": "yearn-finance",
    "balancer": "balancer",
    "synthetix": "synthetix",
    "sushiswap": "sushi",
    "1inch": "1inch-network",
}


def _default_defi() -> dict[str, Any]:
    return {
        "found_on_defillama": False,
        "tvl_usd": 0.0,
        "audit_count": 0,
        "audit_firms": [],
        "protocol_age_days": 0,
        "was_hacked": False,
        "hack_amount_usd": 0.0,
        "similar_hacks_count": 0,
        "category": "Unknown",
    }


async def resolve_slug(target: str) -> str | None:
    target_lower = target.lower().strip()

    if target_lower in KNOWN_SLUGS:
        return KNOWN_SLUGS[target_lower]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get("https://api.llama.fi/protocols")
            r.raise_for_status()
            protocols = r.json()

        for p in protocols:
            if p.get("name", "").lower() == target_lower:
                return p.get("slug")

        for p in protocols:
            if p.get("name", "").lower().startswith(target_lower):
                return p.get("slug")

        for p in protocols:
            if target_lower in p.get("name", "").lower():
                return p.get("slug")
    except Exception:
        pass

    return None


async def fetch_defi_data(target: str) -> dict[str, Any]:
    result = _default_defi()
    protocol_data: dict[str, Any] = {}
    slug = await resolve_slug(target)

    async with httpx.AsyncClient() as client:
        if slug:
            try:
                protocol_resp = await client.get(f"https://api.llama.fi/protocol/{slug}", timeout=20)
                protocol_resp.raise_for_status()
                protocol_data = protocol_resp.json() or {}
                result["found_on_defillama"] = True

                tvl = protocol_data.get("tvl")
                if isinstance(tvl, (int, float)):
                    result["tvl_usd"] = float(tvl)
                elif isinstance(tvl, list) and tvl:
                    last_point = tvl[-1] if isinstance(tvl[-1], dict) else {}
                    latest_tvl = (
                        last_point.get("totalLiquidityUSD")
                        or last_point.get("tvl")
                        or last_point.get("totalLiquidity")
                        or 0
                    )
                    if isinstance(latest_tvl, (int, float)):
                        result["tvl_usd"] = float(latest_tvl)

                audits = protocol_data.get("audits")
                if isinstance(audits, list):
                    result["audit_count"] = len(audits)
                    result["audit_firms"] = [str(a) for a in audits if a]
                elif isinstance(audits, (int, float)):
                    result["audit_count"] = int(audits)

                if protocol_data.get("chain"):
                    result["chain"] = str(protocol_data.get("chain"))
                result["category"] = str(protocol_data.get("category") or "Unknown")

                tvl_hist = protocol_data.get("tvlHistory") or protocol_data.get("tvl") or []
                if isinstance(tvl_hist, list) and tvl_hist:
                    first = tvl_hist[0] or {}
                    dt = first.get("date")
                    if isinstance(dt, (int, float)):
                        launch_date = datetime.fromtimestamp(int(dt), tz=timezone.utc)
                        result["protocol_age_days"] = max(0, (datetime.now(tz=timezone.utc) - launch_date).days)
            except Exception:
                pass

        hacks = []
        try:
            hacks_resp = await client.get(
                "https://raw.githubusercontent.com/DefiLlama/defillama-server/master/defi/src/adaptors/data/hacks.json",
                timeout=20,
            )
            if hacks_resp.status_code == 200:
                data = hacks_resp.json()
                if isinstance(data, list):
                    hacks = data
        except Exception:
            hacks = []

    protocol_name = str(protocol_data.get("name") or target).strip().lower()
    category = str(result.get("category") or "Unknown").strip().lower()
    same_category_hacks = 0

    for hack in hacks:
        name = str(hack.get("name") or hack.get("protocol") or "").strip().lower()
        hacked_category = str(hack.get("category") or hack.get("type") or "").strip().lower()
        if category and hacked_category and category in hacked_category:
            same_category_hacks += 1
        if name and (name == protocol_name or protocol_name in name):
            result["was_hacked"] = True
            amount = hack.get("amount") or hack.get("amountUsd") or hack.get("stolen") or 0
            if isinstance(amount, (int, float)):
                result["hack_amount_usd"] = float(amount)

    result["similar_hacks_count"] = same_category_hacks
    return result

