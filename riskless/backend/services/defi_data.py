from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx


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


def _best_protocol_match(target: str, protocols: list[dict[str, Any]]) -> dict[str, Any] | None:
    query = (target or "").strip().lower()
    if not query:
        return None
    for item in protocols:
        name = str(item.get("name") or "").strip().lower()
        slug = str(item.get("slug") or "").strip().lower()
        if query == name or query == slug:
            return item
    for item in protocols:
        name = str(item.get("name") or "").strip().lower()
        slug = str(item.get("slug") or "").strip().lower()
        if name.startswith(query) or slug.startswith(query) or query in name:
            return item
    return None


async def fetch_defi_data(target: str) -> dict[str, Any]:
    result = _default_defi()
    protocol_data: dict[str, Any] = {}
    slug = None

    async with httpx.AsyncClient() as client:
        try:
            protocols_resp = await client.get("https://api.llama.fi/protocols", timeout=20)
            protocols_resp.raise_for_status()
            protocols = protocols_resp.json() if isinstance(protocols_resp.json(), list) else []
            matched = _best_protocol_match(target, protocols)
            slug = (matched or {}).get("slug")
        except Exception:
            protocols = []

        if slug:
            try:
                protocol_resp = await client.get(f"https://api.llama.fi/protocol/{slug}", timeout=20)
                protocol_resp.raise_for_status()
                protocol_data = protocol_resp.json() or {}
                result["found_on_defillama"] = True

                tvl = protocol_data.get("tvl")
                if isinstance(tvl, (int, float)):
                    result["tvl_usd"] = float(tvl)

                audits = protocol_data.get("audits")
                if isinstance(audits, list):
                    result["audit_count"] = len(audits)
                    result["audit_firms"] = [str(a) for a in audits if a]
                elif isinstance(audits, (int, float)):
                    result["audit_count"] = int(audits)

                if protocol_data.get("chain"):
                    result["chain"] = str(protocol_data.get("chain"))
                result["category"] = str(protocol_data.get("category") or "Unknown")

                tvl_hist = protocol_data.get("tvlHistory") or []
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

