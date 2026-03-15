"""
tests/test_finance_onboarding.py
FIN-01 integration tests: goals persistence and reset.

Tests use the FastAPI TestClient from conftest.py.
Tests are written RED: they will skip/xfail until app/finance.py is implemented.

Run:
    python -m pytest tests/test_finance_onboarding.py -v
"""
import json
import pytest

# ---------------------------------------------------------------------------
# Import guard
# ---------------------------------------------------------------------------
try:
    import app.finance  # noqa: F401
    _FINANCE_AVAILABLE = True
except ImportError:
    _FINANCE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Sample goals payload (matches the onboarding spec from CONTEXT.md)
# ---------------------------------------------------------------------------

GOALS_PAYLOAD = {
    "goal_type": "save",
    "life_events": ["vacation", "emergency_fund"],
    "budgets": {
        "Food": 400,
        "Transport": 150,
        "Shopping": 200,
        "Utilities": 100,
        "Entertainment": 80,
        "Other": 50,
    },
    "horizon": "12 months",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _FINANCE_AVAILABLE, reason="app.finance not yet implemented")
def test_goals_persist(client):
    """
    POST /finance/goals with a full goals payload.
    Expected: 200, DB row exists in fin_goals, app_settings fin_onboarding_done='true'.
    """
    resp = client.post("/finance/goals", json=GOALS_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True or data.get("status") == "saved"

    # Verify the completion flag is set via the settings endpoint
    settings_resp = client.get("/api/settings")
    assert settings_resp.status_code == 200
    settings = settings_resp.json()
    assert settings.get("fin_onboarding_done") == "true"


@pytest.mark.skipif(not _FINANCE_AVAILABLE, reason="app.finance not yet implemented")
def test_reset(client):
    """
    POST /finance/reset_goals.
    Expected: fin_goals cleared, fin_onboarding_done set to 'false'.
    """
    # First ensure there's a goal to reset
    client.post("/finance/goals", json=GOALS_PAYLOAD)

    # Reset
    resp = client.post("/finance/reset_goals")
    assert resp.status_code == 200

    # Verify flag cleared
    settings_resp = client.get("/api/settings")
    assert settings_resp.status_code == 200
    settings = settings_resp.json()
    assert settings.get("fin_onboarding_done") in ("false", None, "")
