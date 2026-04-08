from __future__ import annotations

import asyncio
from typing import Any

from backend.services.blockchain import fetch_onchain_signals
from backend.services.defi_data import fetch_defi_signals


async def fetch_all_signals(target: str) -> dict[str, Any]:
    blockchain_task = fetch_onchain_signals(target)
    defi_task = fetch_defi_signals(target)
    blockchain, defi = await asyncio.gather(blockchain_task, defi_task)
    return {"blockchain": blockchain, "defi": defi}

