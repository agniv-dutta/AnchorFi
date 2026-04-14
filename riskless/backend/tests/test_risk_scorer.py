from backend.services.risk_scorer import compute_risk_score


def test_force_high_risk_override_for_known_exploiter():
    blockchain = {
        "force_high_risk": True,
        "exploiter_label": "Known exploit wallet",
    }
    defi = {
        "found_on_defillama": True,
        "tvl_usd": 2_000_000_000,
        "audit_count": 2,
        "protocol_age_days": 1000,
    }

    scored = compute_risk_score(blockchain, defi, "0xdeadbeef")

    assert scored["composite_risk_score"] == 95
    assert scored["code_risk"]["score"] == 95
    assert scored["team_risk"]["score"] == 100
    assert scored["track_record"]["score"] == 100
    assert "DO NOT INSURE" in scored["code_risk"]["flags"][1]


def test_liquidity_thresholds_reduce_risk_for_large_tvl():
    blockchain = {
        "is_verified": True,
        "is_honeypot": False,
        "has_mint_function": False,
        "owner_can_change_balance": False,
        "hidden_owner": False,
        "can_take_back_ownership": False,
    }
    defi = {
        "found_on_defillama": True,
        "tvl_usd": 1_500_000_000,
        "audit_count": 2,
        "protocol_age_days": 1200,
        "was_hacked": False,
        "similar_hacks_count": 0,
    }

    scored = compute_risk_score(blockchain, defi, "compound")

    assert scored["liquidity_risk"]["score"] <= 30
    assert scored["composite_risk_score"] <= 40
    assert scored["protocol_name"] == "COMPOUND"
