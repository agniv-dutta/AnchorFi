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
    category = data.get("category") or data.get("categories") or data.get("type")

    return {
        "slug": slug,
        "found": True,
        "name": data.get("name"),
        "chain": data.get("chain"),
        "symbol": data.get("symbol"),
        "category": category,
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


def _parse_hack_date(hack: dict[str, Any]) -> datetime | None:
    for key in ("date", "hacked_at", "hackedAt", "timestamp", "exploit_date", "published_at"):
        value = hack.get(key)
        if not value:
            continue
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(float(value), tz=timezone.utc)
            except Exception:
                continue
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def _same_category(hack: dict[str, Any], category: str | None) -> bool:
    if not category:
        return False
    haystack = " ".join(
        str(hack.get(key) or "").strip().lower()
        for key in ("category", "categories", "sector", "sectors", "type", "tags")
    )
    return category.strip().lower() in haystack


def find_near_misses(protocol: dict[str, Any], hacks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    category = protocol.get("category")
    chain = (protocol.get("chain") or "").strip().lower()
    protocol_name = (protocol.get("name") or protocol.get("slug") or "").strip().lower()
    now = datetime.now(tz=timezone.utc)
    near_misses: list[dict[str, Any]] = []

    for hack in hacks:
        hacked_protocol = (hack.get("protocol") or hack.get("name") or "").strip().lower()
        if not hacked_protocol or hacked_protocol == protocol_name:
            continue

        hacked_chain = (hack.get("chain") or hack.get("chains") or "").strip().lower()
        if chain and hacked_chain and chain != hacked_chain and chain not in hacked_chain and hacked_chain not in chain:
            continue

        if category and not _same_category(hack, category):
            continue

        hack_dt = _parse_hack_date(hack)
        if hack_dt:
            days_ago = (now - hack_dt.astimezone(timezone.utc)).days
            if days_ago > 730:
                continue
        else:
            days_ago = None

        near_misses.append(
            {
                "protocol": hack.get("protocol") or hack.get("name"),
                "chain": hack.get("chain") or hack.get("chains"),
                "category": hack.get("category") or hack.get("categories") or hack.get("type"),
                "date": hack_dt.isoformat() if hack_dt else None,
                "days_ago": days_ago,
            }
        )

    return near_misses[:10]


async def fetch_defi_signals(target: str) -> dict[str, Any]:
    hacks_task = asyncio.create_task(fetch_defillama_hacks_index())
    protocol = await fetch_defillama_protocol(target)
    hacks: list[dict[str, Any]] = []
    near_misses: list[dict[str, Any]] = []
    if protocol.get("found"):
        all_hacks = await hacks_task
        hacks = match_hacks_for_protocol(all_hacks, protocol.get("name") or protocol.get("slug"))
        near_misses = find_near_misses(protocol, all_hacks)
    else:
        hacks_task.cancel()
    protocol["near_misses"] = near_misses
    protocol["near_misses_count"] = len(near_misses)
    return {"protocol": protocol, "hacks": hacks, "near_misses": near_misses}

