from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _clamp_int(x: float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(x))))


def score_signals(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Returns the structured risk dict described in the spec.
    """
    flags_code: list[str] = []
    flags_liq: list[str] = []
    flags_team: list[str] = []
    flags_track: list[str] = []

    blockchain = (raw or {}).get("blockchain") or {}
    defi = (raw or {}).get("defi") or {}
    protocol = (defi or {}).get("protocol") or {}
    hacks = (defi or {}).get("hacks") or []

    # --- Code risk ---
    code_score = 20.0
    is_address = bool(blockchain.get("is_address"))
    if is_address:
        etherscan = (blockchain.get("etherscan") or {})
        verified = bool(etherscan.get("verified"))
        if not verified:
            code_score += 45
            flags_code.append("unverified contract on Etherscan")
        proxy = etherscan.get("is_proxy")
        if proxy is True:
            code_score += 10
            flags_code.append("proxy pattern detected")

        goplus = ((blockchain.get("goplus") or {}).get("raw") or {})
        # common GoPlus flags are strings "0"/"1" or "true"/"false"
        def _truthy(v: Any) -> bool:
            return str(v).strip().lower() in {"1", "true", "yes"}

        if _truthy(goplus.get("is_honeypot")):
            code_score += 60
            flags_code.append("honeypot behavior flagged (GoPlus)")
        if _truthy(goplus.get("has_mint_method")) or _truthy(goplus.get("mintable")):
            code_score += 15
            flags_code.append("has mint functionality (GoPlus)")
        if _truthy(goplus.get("owner_change_balance")):
            code_score += 20
            flags_code.append("owner can change balances (GoPlus)")
        if _truthy(goplus.get("is_open_source")) is False and goplus.get("is_open_source") is not None:
            code_score += 10
            flags_code.append("not open source (GoPlus)")
    else:
        # protocol-by-name: we can't check contract verification directly
        code_score += 5
        flags_code.append("no contract address provided; limited code-level signals")

    # --- Liquidity risk ---
    liq_score = 25.0
    tvl = protocol.get("tvl")
    if isinstance(tvl, (int, float)):
        if tvl < 1_000_000:
            liq_score += 35
            flags_liq.append("TVL < $1M")
        elif tvl < 10_000_000:
            liq_score += 15
            flags_liq.append("TVL < $10M")
        elif tvl > 1_000_000_000:
            liq_score -= 10
            flags_liq.append("TVL > $1B")
    else:
        liq_score += 10
        flags_liq.append("TVL unavailable")

    age_days = protocol.get("age_days")
    if isinstance(age_days, int):
        if age_days < 90:
            liq_score += 25
            flags_liq.append("launched < 90 days ago")
        elif age_days > 365:
            liq_score -= 5
            flags_liq.append("live > 1 year")

    # --- Team risk ---
    team_score = 30.0
    audit_count = protocol.get("audit_count")
    if isinstance(audit_count, int):
        if audit_count <= 0:
            team_score += 25
            flags_team.append("no audits listed")
        elif audit_count >= 2:
            team_score -= 10
            flags_team.append("multiple audits listed")
    else:
        team_score += 10
        flags_team.append("audit info unavailable")

    # Heuristic: very new + low TVL often correlates with anonymous/untested teams
    if isinstance(age_days, int) and age_days < 30:
        team_score += 10
        flags_team.append("very new protocol/team")

    # --- Track record ---
    track_score = 40.0
    if hacks:
        track_score += 25
        flags_track.append("prior hack incidents reported")
    else:
        track_score -= 10
        flags_track.append("no prior hacks found (DefiLlama)")

    if isinstance(age_days, int) and age_days > 730:
        track_score -= 10
        flags_track.append("2+ years live")

    # If contract has first tx, reward age
    if is_address:
        first_tx_at = ((blockchain.get("etherscan") or {}).get("first_tx_at"))
        if isinstance(first_tx_at, str):
            try:
                dt = datetime.fromisoformat(first_tx_at.replace("Z", "+00:00"))
                days = (datetime.now(tz=timezone.utc) - dt.astimezone(timezone.utc)).days
                if days > 365:
                    track_score -= 5
                    flags_track.append("contract active > 1 year")
                elif days < 30:
                    track_score += 10
                    flags_track.append("contract very new")
            except Exception:
                pass

    # Clamp categories
    code_i = _clamp_int(code_score)
    liq_i = _clamp_int(liq_score)
    team_i = _clamp_int(team_score)
    track_i = _clamp_int(track_score)

    # Composite (weighted)
    composite = _clamp_int(
        code_i * 0.35 + liq_i * 0.25 + team_i * 0.25 + track_i * 0.15
    )

    return {
        "code_risk": {"score": code_i, "flags": flags_code},
        "liquidity_risk": {"score": liq_i, "flags": flags_liq},
        "team_risk": {"score": team_i, "flags": flags_team},
        "track_record": {"score": track_i, "flags": flags_track},
        "composite_risk_score": composite,
        "raw_signals": raw,
    }


def estimate_premium_usdc(
    coverage_amount: float, coverage_days: int, composite_risk_score: int
) -> dict[str, Any]:
    base_rate = 0.002  # 0.2% per 30 days at zero risk
    risk_multiplier = 1 + (composite_risk_score / 100.0) * 15.0
    premium = coverage_amount * base_rate * risk_multiplier * (coverage_days / 30.0)
    cap = coverage_amount * 0.20
    premium_capped = min(premium, cap)

    return {
        "premium_usdc": float(round(premium_capped, 2)),
        "details": {
            "base_rate": base_rate,
            "risk_multiplier": float(round(risk_multiplier, 4)),
            "uncapped_premium": float(round(premium, 2)),
            "cap": float(round(cap, 2)),
            "capped": premium_capped != premium,
        },
    }

