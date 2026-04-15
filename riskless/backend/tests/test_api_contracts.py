from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import create_app


def test_assess_contract_includes_freshness_and_ai_provider(monkeypatch):
    import backend.routers.assess as assess_router

    async def fake_fetch_contract_data(_target: str):
        return {
            "is_address": False,
            "is_verified": True,
            "tx_count": 100,
            "contract_age_days": 800,
            "is_honeypot": False,
            "has_mint_function": False,
            "owner_can_change_balance": False,
            "hidden_owner": False,
            "can_take_back_ownership": False,
            "raw_goplus": {},
        }

    async def fake_fetch_defi_data(_target: str):
        return {
            "found_on_defillama": True,
            "tvl_usd": 2_500_000_000,
            "audit_count": 3,
            "audit_firms": ["firm-a", "firm-b", "firm-c"],
            "protocol_age_days": 1200,
            "was_hacked": False,
            "hack_amount_usd": 0,
            "similar_hacks_count": 0,
            "category": "Lending",
        }

    async def fake_get_ai_analysis(_signals: dict, _target: str | None = None):
        return {
            "summary": "Mock AI summary for contract tests.",
            "top_risks": ["mock risk"],
            "positive_signals": ["mock strength"],
            "confidence": "High",
            "recommended_action": "Safe to insure",
            "underwriter_note": "Mock underwriter note",
            "ai_provider": "groq",
        }

    monkeypatch.setattr(assess_router, "fetch_contract_data", fake_fetch_contract_data)
    monkeypatch.setattr(assess_router, "fetch_defi_data", fake_fetch_defi_data)
    monkeypatch.setattr(assess_router, "get_ai_analysis", fake_get_ai_analysis)

    app = create_app()
    client = TestClient(app)

    payload = {
        "target": f"pytest-{uuid4().hex[:8]}",
        "coverage_amount": 10000,
        "coverage_days": 30,
    }
    res = client.post("/api/assess", json=payload)
    assert res.status_code == 200
    body = res.json()

    assert body["target"].startswith("pytest-")
    assert "data_freshness" in body
    assert "fetched_at" in body["data_freshness"]
    assert "source_age_seconds" in body["data_freshness"]
    assert isinstance(body["data_freshness"]["partial_data_flags"], list)
    assert body["ai"]["ai_provider"] == "groq"
    assert "score_breakdown" in body
    assert body["score_breakdown"]["code_risk"]["weight"] == 0.35


def test_compare_contract_returns_results_and_recommended(monkeypatch):
    import backend.routers.assess as assess_router

    async def fake_fetch_contract_data(_target: str):
        return {
            "is_address": False,
            "is_verified": True,
            "tx_count": 100,
            "contract_age_days": 800,
            "is_honeypot": False,
            "has_mint_function": False,
            "owner_can_change_balance": False,
            "hidden_owner": False,
            "can_take_back_ownership": False,
            "raw_goplus": {},
        }

    async def fake_fetch_defi_data(target: str):
        # Deterministic TVL differences to produce one winner.
        tvls = {
            "aave": 2_000_000_000,
            "compound": 1_500_000_000,
            "uniswap": 800_000_000,
        }
        return {
            "found_on_defillama": True,
            "tvl_usd": tvls.get(target.lower(), 100_000_000),
            "audit_count": 2,
            "audit_firms": ["firm-a", "firm-b"],
            "protocol_age_days": 900,
            "was_hacked": False,
            "hack_amount_usd": 0,
            "similar_hacks_count": 0,
            "category": "DEX",
        }

    async def fake_get_ai_analysis(_signals: dict, _target: str | None = None):
        return {
            "summary": "Compare test summary.",
            "top_risks": ["mock risk"],
            "positive_signals": ["mock strength"],
            "confidence": "Medium",
            "recommended_action": "Insure with caution",
            "underwriter_note": "Mock note",
            "ai_provider": "groq",
        }

    monkeypatch.setattr(assess_router, "fetch_contract_data", fake_fetch_contract_data)
    monkeypatch.setattr(assess_router, "fetch_defi_data", fake_fetch_defi_data)
    monkeypatch.setattr(assess_router, "get_ai_analysis", fake_get_ai_analysis)

    app = create_app()
    client = TestClient(app)

    res = client.post(
        "/api/compare",
        json={
            "targets": ["aave", "compound", "uniswap"],
            "coverage_amount": 10000,
            "coverage_days": 30,
        },
    )
    assert res.status_code == 200
    body = res.json()

    assert "results" in body
    assert isinstance(body["results"], list)
    assert len(body["results"]) == 3
    assert "recommended" in body
    assert any(item.get("is_safest") for item in body["results"])


def test_assess_degrades_confidence_when_data_is_partial(monkeypatch):
    import backend.routers.assess as assess_router

    async def fake_fetch_contract_data(_target: str):
        return {
            "is_address": True,
            "is_verified": True,
            "tx_count": 0,
            "contract_age_days": 1,
            "is_honeypot": False,
            "has_mint_function": False,
            "owner_can_change_balance": False,
            "hidden_owner": False,
            "can_take_back_ownership": False,
            "raw_goplus": {},
        }

    async def fake_fetch_defi_data(_target: str):
        return {
            "found_on_defillama": False,
            "tvl_usd": 0,
            "audit_count": 0,
            "audit_firms": [],
            "protocol_age_days": 10,
            "was_hacked": False,
            "hack_amount_usd": 0,
            "similar_hacks_count": 0,
            "category": "Unknown",
        }

    async def fake_get_ai_analysis(_signals: dict, _target: str | None = None):
        return {
            "summary": "Mock AI summary for partial-data confidence degradation test.",
            "top_risks": ["mock risk"],
            "positive_signals": [],
            "confidence": "High",
            "recommended_action": "Insure with caution",
            "underwriter_note": "Mock note",
            "ai_provider": "groq",
        }

    monkeypatch.setattr(assess_router, "fetch_contract_data", fake_fetch_contract_data)
    monkeypatch.setattr(assess_router, "fetch_defi_data", fake_fetch_defi_data)
    monkeypatch.setattr(assess_router, "get_ai_analysis", fake_get_ai_analysis)

    app = create_app()
    client = TestClient(app)

    res = client.post(
        "/api/assess",
        json={"target": f"partial-{uuid4().hex[:8]}", "coverage_amount": 10000, "coverage_days": 30},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ai"]["confidence"] == "Low"
    assert len(body["data_freshness"]["partial_data_flags"]) >= 2
