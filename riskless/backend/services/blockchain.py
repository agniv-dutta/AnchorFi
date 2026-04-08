from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from backend.core.config import settings


_ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def is_eth_address(value: str) -> bool:
    return bool(_ETH_ADDRESS_RE.match(value.strip()))


async def _etherscan_get(client: httpx.AsyncClient, params: dict[str, Any]) -> dict[str, Any]:
    base = "https://api.etherscan.io/api"
    merged = dict(params)
    if settings.etherscan_api_key:
        merged["apikey"] = settings.etherscan_api_key
    r = await client.get(base, params=merged, timeout=20)
    r.raise_for_status()
    return r.json()


async def fetch_contract_source_verified(
    client: httpx.AsyncClient, address: str
) -> dict[str, Any]:
    """
    Returns: { verified: bool, contract_name: str|None, is_proxy: bool|None }
    """
    data = await _etherscan_get(
        client,
        {
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
        },
    )
    result = (data or {}).get("result") or []
    item = result[0] if isinstance(result, list) and result else {}
    source = (item.get("SourceCode") or "").strip()
    contract_name = (item.get("ContractName") or "").strip() or None
    proxy = (item.get("Proxy") or "").strip()
    verified = bool(source)
    is_proxy = True if proxy == "1" else False if proxy in {"0", ""} else None
    return {
        "verified": verified,
        "contract_name": contract_name,
        "is_proxy": is_proxy,
    }


async def fetch_tx_count(client: httpx.AsyncClient, address: str) -> dict[str, Any]:
    # Free-tier friendly: fetch last page of txlist and infer count if possible.
    data = await _etherscan_get(
        client,
        {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 1,
            "sort": "asc",
        },
    )
    status = (data or {}).get("status")
    result = (data or {}).get("result")
    if status == "0" and isinstance(result, str) and "No transactions" in result:
        return {"tx_count": 0}
    if isinstance(result, list) and result:
        return {"tx_count": None}  # unknown without paging; we keep signals minimal
    return {"tx_count": None}


async def fetch_first_tx_timestamp(client: httpx.AsyncClient, address: str) -> dict[str, Any]:
    data = await _etherscan_get(
        client,
        {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 1,
            "sort": "asc",
        },
    )
    result = (data or {}).get("result")
    if isinstance(result, list) and result:
        ts = int(result[0].get("timeStamp"))
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return {"first_tx_at": dt.isoformat()}
    return {"first_tx_at": None}


async def fetch_creator_info(client: httpx.AsyncClient, address: str) -> dict[str, Any]:
    # Etherscan "contract creation" endpoint isn't in the classic API; use getcontractcreation if available.
    data = await _etherscan_get(
        client,
        {
            "module": "contract",
            "action": "getcontractcreation",
            "contractaddresses": address,
        },
    )
    result = (data or {}).get("result")
    if isinstance(result, list) and result:
        item = result[0]
        creator = item.get("contractCreator")
        tx_hash = item.get("txHash")
        return {"creator": creator, "creation_tx": tx_hash}
    return {"creator": None, "creation_tx": None}


async def fetch_goplus_security(client: httpx.AsyncClient, address: str) -> dict[str, Any]:
    # GoPlus contract security: https://gopluslabs.io/ (Ethereum chain_id=1)
    # Some tiers work without a key; include if provided.
    url = "https://api.gopluslabs.io/api/v1/contract_security/1"
    headers = {}
    if settings.goplus_api_key:
        headers["Authorization"] = settings.goplus_api_key
    r = await client.get(url, params={"contract_addresses": address}, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    result = ((data or {}).get("result") or {}).get(address.lower()) or {}
    return {"raw": result}


async def fetch_onchain_signals(target: str) -> dict[str, Any]:
    """
    For Ethereum mainnet addresses only. Returns a structured dict under raw_signals.blockchain.
    """
    address = target.strip()
    if not is_eth_address(address):
        return {"is_address": False}

    async with httpx.AsyncClient() as client:
        verified_task = fetch_contract_source_verified(client, address)
        first_tx_task = fetch_first_tx_timestamp(client, address)
        tx_count_task = fetch_tx_count(client, address)
        creator_task = fetch_creator_info(client, address)
        goplus_task = fetch_goplus_security(client, address)

        verified, first_tx, tx_count, creator, goplus = await asyncio.gather(
            verified_task, first_tx_task, tx_count_task, creator_task, goplus_task
        )

    return {
        "is_address": True,
        "address": address,
        "etherscan": {
            **verified,
            **first_tx,
            **tx_count,
            **creator,
        },
        "goplus": goplus,
    }

