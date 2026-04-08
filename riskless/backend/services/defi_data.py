from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx
import asyncio


def _slugify_protocol(target: str) -> str | None:
    # Accept "aave", "AAVE", "https://defillama.com/protocol/aave"
    t = target.strip()
    m = re.search(r"/protocol/([^/?#]+)", t, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    if t.startswith("http://") or t.startswith("https://"):
        return None
    # crude: defillama slugs are usually lowercase with dashes
    return t.lower().replace(" ", "-")


async def fetch_defillama_protocol(target: str) -> dict[str, Any]:
    slug = _slugify_protocol(target)
    if not slug:
        return {"slug": None, "found": False}

    url = f"https://api.llama.fi/protocol/{slug}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=20)
        if r.status_code != 200:
            return {"slug": slug, "found": False}
        data = r.json()

    # Derive age from "listedAt" if present (unix seconds)
    listed_at = data.get("listedAt")
    age_days = None
    if isinstance(listed_at, (int, float)):
        dt = datetime.fromtimestamp(int(listed_at), tz=timezone.utc)
        age_days = (datetime.now(tz=timezone.utc) - dt).days

    audits = data.get("audits")
    audit_count = None
    if isinstance(audits, str):
        audit_count = 0 if audits.strip() == "0" else None
    elif isinstance(audits, (int, float)):
        audit_count = int(audits)

    audit_links = data.get("audit_links") if isinstance(data.get("audit_links"), list) else []
    tvl = data.get("tvl")

    return {
        "slug": slug,
        "found": True,
        "name": data.get("name"),
        "chain": data.get("chain"),
        "symbol": data.get("symbol"),
        "tvl": tvl,
        "listed_at": listed_at,
        "age_days": age_days,
        "audit_count": audit_count,
        "audit_links": audit_links,
    }


async def fetch_defillama_hacks_index() -> list[dict[str, Any]]:
    # Unofficial but widely used JSON mirror
    url = "https://api.llama.fi/hacks"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
    if isinstance(data, list):
        return data
    return []


def match_hacks_for_protocol(hacks: list[dict[str, Any]], protocol_name: str | None) -> list[dict[str, Any]]:
    if not protocol_name:
        return []
    name = protocol_name.strip().lower()
    out: list[dict[str, Any]] = []
    for h in hacks:
        p = (h.get("protocol") or "").strip().lower()
        if p and (p == name or name in p or p in name):
            out.append(h)
    return out


async def fetch_defi_signals(target: str) -> dict[str, Any]:
    hacks_task = asyncio.create_task(fetch_defillama_hacks_index())
    protocol = await fetch_defillama_protocol(target)
    hacks: list[dict[str, Any]] = []
    if protocol.get("found"):
        all_hacks = await hacks_task
        hacks = match_hacks_for_protocol(all_hacks, protocol.get("name") or protocol.get("slug"))
    else:
        hacks_task.cancel()
    return {"protocol": protocol, "hacks": hacks}

