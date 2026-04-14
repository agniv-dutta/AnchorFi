from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx

from backend.core.config import settings


_ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

KNOWN_BAD_ACTORS = {
    "0x098b716b8aaf21512996dc57eb0615e2383e2f96": {
        "label": "Ronin Bridge Exploiter ($625M hack, March 2022)",
        "force_high_risk": True,
    },
}


def is_eth_address(value: str) -> bool:
    return bool(_ETH_ADDRESS_RE.match((value or "").strip()))


def _safe_defaults(is_address: bool) -> dict[str, Any]:
    return {
        "is_address": is_address,
        "is_verified": False,
        "tx_count": 0,
        "contract_age_days": 0,
        "is_honeypot": False,
        "has_mint_function": False,
        "owner_can_change_balance": False,
        "hidden_owner": False,
        "can_take_back_ownership": False,
        "raw_goplus": {},
    }


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


async def fetch_contract_data(target: str) -> dict[str, Any]:
    target = (target or "").strip()
    addr_lower = target.lower()

    if addr_lower in KNOWN_BAD_ACTORS:
        default_safe_signals = _safe_defaults(True)
        return {
            **default_safe_signals,
            "is_known_exploiter": True,
            "exploiter_label": KNOWN_BAD_ACTORS[addr_lower]["label"],
            "force_high_risk": True,
        }

    if not is_eth_address(target):
        return _safe_defaults(False)

    out = _safe_defaults(True)
    params_key = {"apikey": settings.ETHERSCAN_API_KEY} if settings.ETHERSCAN_API_KEY else {}

    async with httpx.AsyncClient() as client:
        try:
            src = await client.get(
                "https://api.etherscan.io/api",
                params={
                    "module": "contract",
                    "action": "getsourcecode",
                    "address": target,
                    **params_key,
                },
                timeout=20,
            )
            src.raise_for_status()
            src_result = ((src.json() or {}).get("result") or [{}])[0]
            out["is_verified"] = bool((src_result.get("SourceCode") or "").strip())
        except Exception:
            pass

        try:
            tx = await client.get(
                "https://api.etherscan.io/api",
                params={
                    "module": "account",
                    "action": "txlist",
                    "address": target,
                    "startblock": 0,
                    "endblock": 99999999,
                    "page": 1,
                    "offset": 100,
                    "sort": "asc",
                    **params_key,
                },
                timeout=20,
            )
            tx.raise_for_status()
            tx_data = tx.json() or {}
            tx_result = tx_data.get("result")
            if isinstance(tx_result, list):
                out["tx_count"] = len(tx_result)
                if tx_result:
                    ts = int(tx_result[0].get("timeStamp") or 0)
                    if ts > 0:
                        created = datetime.fromtimestamp(ts, tz=timezone.utc)
                        out["contract_age_days"] = max(0, (datetime.now(tz=timezone.utc) - created).days)
            elif isinstance(tx_result, str) and "No transactions" in tx_result:
                out["tx_count"] = 0
        except Exception:
            pass

        try:
            gp = await client.get(
                "https://api.gopluslabs.io/api/v1/token_security/1",
                params={"contract_addresses": target},
                timeout=20,
            )
            gp.raise_for_status()
            raw = ((gp.json() or {}).get("result") or {}).get(target.lower()) or {}
            out["raw_goplus"] = raw
            out["is_honeypot"] = _truthy(raw.get("is_honeypot"))
            out["has_mint_function"] = _truthy(raw.get("has_mint_function")) or _truthy(raw.get("has_mint_method"))
            out["owner_can_change_balance"] = _truthy(raw.get("owner_change_balance"))
            out["hidden_owner"] = _truthy(raw.get("hidden_owner"))
            out["can_take_back_ownership"] = _truthy(raw.get("can_take_back_ownership"))
        except Exception:
            pass

    return out

