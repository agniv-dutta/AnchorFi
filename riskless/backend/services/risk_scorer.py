from __future__ import annotations

from typing import Any


def _clamp(value: int) -> int:
    return max(0, min(100, int(value)))


def compute_risk_score(blockchain: dict, defi: dict, target: str = "") -> dict[str, Any]:
    if blockchain.get("force_high_risk"):
        return {
            "composite_risk_score": 95,
            "code_risk": {
                "score": 95,
                "flags": [
                    blockchain.get("exploiter_label", "Known malicious address"),
                    "DO NOT INSURE — KNOWN EXPLOIT ADDRESS",
                ],
            },
            "liquidity_risk": {"score": 90, "flags": ["Associated with theft of funds"]},
            "team_risk": {"score": 100, "flags": ["Identified as attacker wallet"]},
            "track_record": {"score": 100, "flags": ["Directly involved in $625M Ronin hack"]},
            "protocol_name": target.upper() if target else "UNKNOWN",
            "raw_signals": {"blockchain": blockchain, "defi": defi},
        }

    code_flags: list[str] = []
    liq_flags: list[str] = []
    team_flags: list[str] = []
    track_flags: list[str] = []

    code = 0
    if not blockchain.get("is_verified", False):
        code += 30
        code_flags.append("Source code is not verified")
    if blockchain.get("is_honeypot", False):
        code += 20
        code_flags.append("GoPlus flagged possible honeypot behavior")
    if blockchain.get("has_mint_function", False):
        code += 15
        code_flags.append("Contract has a mint function")
    if blockchain.get("owner_can_change_balance", False):
        code += 15
        code_flags.append("Owner can modify token balances")
    if blockchain.get("hidden_owner", False):
        code += 10
        code_flags.append("Owner identity appears hidden")
    if blockchain.get("can_take_back_ownership", False):
        code += 10
        code_flags.append("Ownership can be reclaimed")
    if defi.get("audit_count", 0) >= 2:
        code -= 10
        code_flags.append("Multiple audits reduce code risk")
    elif defi.get("audit_count", 0) == 1:
        code -= 5
        code_flags.append("Single audit reduces code risk")
    code_score = _clamp(code)

    liquidity = 50
    tvl = float(defi.get("tvl_usd", 0) or 0)
    age = int(defi.get("protocol_age_days", 0) or 0)
    if tvl > 1_000_000_000:
        liquidity -= 30
        liq_flags.append("TVL above $1B")
    elif tvl > 100_000_000:
        liquidity -= 20
        liq_flags.append("TVL above $100M")
    elif tvl > 10_000_000:
        liquidity -= 10
        liq_flags.append("TVL above $10M")
    if tvl < 1_000_000:
        liquidity += 20
        liq_flags.append("TVL below $1M")
    if tvl == 0:
        liquidity += 15
        liq_flags.append("Protocol not found on DefiLlama")
    if age < 90:
        liquidity += 10
        liq_flags.append("Protocol younger than 90 days")
    liquidity_score = _clamp(liquidity)

    team = 40
    audits = int(defi.get("audit_count", 0) or 0)
    if audits >= 3:
        team -= 20
        team_flags.append("Three or more audits")
    elif audits >= 1:
        team -= 15
        team_flags.append("At least one audit")
    if age > 730:
        team -= 10
        team_flags.append("Protocol live for more than 2 years")
    if not defi.get("found_on_defillama", False):
        team += 20
        team_flags.append("Protocol reputation data unavailable")
    if age < 180:
        team += 15
        team_flags.append("Protocol younger than 180 days")
    team_score = _clamp(team)

    track = 20
    if defi.get("was_hacked", False):
        track += 50
        track_flags.append("Protocol has known hack history")
    similar_hacks = int(defi.get("similar_hacks_count", 0) or 0)
    if similar_hacks > 5:
        track += 10
        track_flags.append("Many hacks in similar category")
    elif similar_hacks > 2:
        track += 5
        track_flags.append("Several hacks in similar category")
    if age > 1095:
        track -= 20
        track_flags.append("Three years live reduces track-record risk")
    elif age > 365:
        track -= 10
        track_flags.append("One year live reduces track-record risk")
    track_score = _clamp(track)

    composite = round(code_score * 0.35 + liquidity_score * 0.25 + team_score * 0.25 + track_score * 0.15)

    return {
        "code_risk": {"score": code_score, "flags": code_flags},
        "liquidity_risk": {"score": liquidity_score, "flags": liq_flags},
        "team_risk": {"score": team_score, "flags": team_flags},
        "track_record": {"score": track_score, "flags": track_flags},
        "composite_risk_score": _clamp(composite),
        "protocol_name": target.upper() if target else "UNKNOWN",
        "raw_signals": {"blockchain": blockchain, "defi": defi},
    }

