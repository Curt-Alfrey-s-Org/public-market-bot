"""
Trust-boundary tests for the Ask AI narrative feature.

These assert the safety invariants that must hold regardless of the LLM:
- Sensitive keys (Schwab tokens, balances, account numbers, API keys) are
  stripped from any context before it could be sent to the brain.
- Only an allow-list of pages may use Ask AI.
- The NOT FINANCIAL ADVICE disclaimer and "no advice" system prompt exist.
"""

import json

from api.services.market_ask_ai_context import (
    build_page_context,
    is_allowed_page,
    sanitize_context,
    ALLOWED_PAGES,
)


def test_sanitize_strips_sensitive_keys():
    payload = {
        "win_rate": 0.62,
        "symbol": "AAPL",
        "schwab_access_token": "change-me",
        "account_number": "123456789",
        "cash_balance": 10432.55,
        "api_key": "change-me",
        "nested": {
            "refresh_token": "change-me",
            "factor": "RSI < 30",
            "BOT_API_KEY": "change-me",
        },
    }
    out = sanitize_context(payload)
    flat = json.dumps(out).lower()
    for forbidden in ("tok-secret", "123456789", "10432", "sk-leak", "r-leak", "leak"):
        assert forbidden not in flat, f"sensitive value {forbidden!r} leaked: {flat}"
    # Domain data preserved
    assert out["win_rate"] == 0.62
    assert out["symbol"] == "AAPL"
    assert out["nested"]["factor"] == "RSI < 30"
    # sensitive keys removed entirely
    assert "schwab_access_token" not in out
    assert "account_number" not in out
    assert "cash_balance" not in out
    assert "api_key" not in out
    assert "refresh_token" not in out["nested"]
    assert "BOT_API_KEY" not in out["nested"]


def test_build_page_context_shape():
    ctx = build_page_context("dashboard", {"win_rate": 0.5, "token": "change-me"})
    assert ctx["page"] == "dashboard"
    assert "token" not in ctx["context"]
    assert ctx["context"]["win_rate"] == 0.5


def test_allowed_pages_only():
    assert is_allowed_page("dashboard")
    assert is_allowed_page("DECISION-REPORT")  # case-insensitive
    assert not is_allowed_page("admin/user-settings")
    assert not is_allowed_page("")
    assert ALLOWED_PAGES  # non-empty


def test_disclaimer_and_no_advice_prompt_present():
    from api.routes.ai_narrative import DISCLAIMER, _SYSTEM_PROMPT

    assert "NOT FINANCIAL ADVICE" in DISCLAIMER
    low = _SYSTEM_PROMPT.lower()
    assert "never give financial advice" in low or "not give financial advice" in low
    assert "buy/sell" in low or "recommendation" in low


def test_degraded_response_still_has_disclaimer():
    from api.routes.ai_narrative import _degraded, DISCLAIMER

    r = _degraded("unavailable")
    assert r["disclaimer"] == DISCLAIMER
    assert r["degraded"] is True
    assert r["model"] is None
