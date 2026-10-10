"""
Trading insights via the ALFa AI brain — narrative and explanation only.

The LLM is used for tasks a general model is good at:
- Plain-English performance summaries (no parameter recommendations)
- Trade journal narration from recent fills
- Explaining backtest-driven parameter changes (human-readable, not authoritative)

It must NOT suggest buy/sell actions or emit JSON settings to auto-apply.
Parameter changes come from MLParameterOptimizer (backtest heuristics), not the LLM.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "NOT FINANCIAL ADVICE. This is an automated summary for a simulated/educational "
    "trading bot. It does not recommend buying or selling any security."
)

_NARRATIVE_SYSTEM = (
    "You are a factual reporting assistant for a simulated trading bot dashboard. "
    "Summarize the provided performance statistics in plain English. If a "
    "'decision_factors' block is provided, you may briefly describe which "
    "components drove the bot's decisions (e.g. ML signal filter, strategy "
    "weights, sentiment) using only the values given. "
    "STRICT RULES: (1) Do not recommend trades or parameter changes. "
    "(2) Do not predict future prices or returns. (3) Only describe the numbers given. "
    "(4) Be concise (under 200 words). (5) End with exactly: NOT FINANCIAL ADVICE."
)

_JOURNAL_SYSTEM = (
    "You are a trade journal assistant for a simulated trading bot. "
    "Summarize the recent trades listed (symbols, actions, P&L) in neutral, factual prose. "
    "Do not recommend future trades. Under 180 words. End with: NOT FINANCIAL ADVICE."
)

_EXPLAIN_OPT_SYSTEM = (
    "You explain bot configuration changes to a human operator. "
    "The changes were computed by backtest heuristics (not by you). "
    "Describe what changed and why the metrics might improve — use cautious language "
    "('may', 'could'). Do not claim guaranteed results. Under 150 words. "
    "End with: NOT FINANCIAL ADVICE."
)


def _insights_enabled() -> bool:
    return os.getenv("BOT_LLM_INSIGHTS_ENABLED", "true").lower() in ("true", "1", "yes")


def _chat(messages: List[Dict[str, str]], feature: str, max_tokens: int = 500) -> Dict[str, Any]:
    try:
        from api.services.litellm_client import (
            is_litellm_enabled,
            litellm_chat_completion_sync,
            litellm_model_for_trust_zone,
        )
    except Exception as e:
        return {"content": "", "error": f"litellm_unavailable: {e}"}

    if not _insights_enabled() or not is_litellm_enabled():
        return {"content": "", "error": "litellm_disabled"}

    model = litellm_model_for_trust_zone("app_authenticated")
    return litellm_chat_completion_sync(
        messages,
        model=model,
        temperature=0.2,
        max_tokens=max_tokens,
        feature=feature,
        trust_zone="app_authenticated",
    )


def generate_performance_narrative(
    track_record: Dict[str, Any],
    decision_factors: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Factual performance narrative from track-record stats. No settings JSON.

    Optional `decision_factors` (a read-only summary of the local ML layer:
    signal-filter status, strategy weights, sentiment source) is passed to the
    brain as context so it can describe *how* the bot decided, not just the
    outcome. It is never used to recommend trades.
    """
    summary = {
        "win_rate_pct": track_record.get("win_rate_pct") or track_record.get("Win Rate"),
        "total_trades": track_record.get("total_trades") or track_record.get("Total Trades"),
        "total_pnl": track_record.get("total_pnl") or track_record.get("Total P&L"),
        "initial_capital": track_record.get("initial_capital") or track_record.get("Initial Capital"),
        "final_capital": track_record.get("final_capital") or track_record.get("Final Capital"),
    }
    user = (
        "Summarize this simulated bot performance for the operator:\n"
        f"{json.dumps(summary, indent=2)}"
    )
    if decision_factors:
        user += (
            "\n\ndecision_factors (how the bot's local ML layer was configured "
            "during this record; describe briefly, do not advise):\n"
            f"{json.dumps(decision_factors, indent=2)}"
        )
    result = _chat(
        [{"role": "system", "content": _NARRATIVE_SYSTEM}, {"role": "user", "content": user}],
        feature="performance_narrative",
    )
    if result.get("error"):
        return {"error": result["error"], "response": "", "disclaimer": DISCLAIMER}
    text = (result.get("content") or "").strip()
    if DISCLAIMER not in text:
        text = f"{text}\n\n{DISCLAIMER}" if text else DISCLAIMER
    return {"response": text, "disclaimer": DISCLAIMER}


def generate_trade_journal(trades: List[Dict[str, Any]], limit: int = 20) -> Dict[str, Any]:
    """Narrate recent trades (symbol, action, pnl only — no secrets)."""
    safe: List[Dict[str, Any]] = []
    for t in (trades or [])[-limit:]:
        entry: Dict[str, Any] = {
            "symbol": t.get("symbol"),
            "action": t.get("action") or t.get("side"),
            "pnl": t.get("pnl"),
            "timestamp": str(t.get("timestamp") or t.get("time") or "")[:32],
        }
        # Include decision factors only when the trade record carries them, so
        # the brain can narrate what drove the trade (never advice).
        for key in ("strategy", "ml_confidence", "sentiment_signal"):
            if t.get(key) is not None:
                entry[key] = t.get(key)
        safe.append(entry)
    if not safe:
        return {
            "response": f"No recent trades to summarize.\n\n{DISCLAIMER}",
            "disclaimer": DISCLAIMER,
        }
    user = f"Recent trades:\n{json.dumps(safe, indent=2)}"
    result = _chat(
        [{"role": "system", "content": _JOURNAL_SYSTEM}, {"role": "user", "content": user}],
        feature="trade_journal",
    )
    if result.get("error"):
        return {"error": result["error"], "response": "", "disclaimer": DISCLAIMER}
    text = (result.get("content") or "").strip()
    if DISCLAIMER not in text:
        text = f"{text}\n\n{DISCLAIMER}" if text else DISCLAIMER
    return {"response": text, "disclaimer": DISCLAIMER}


def explain_parameter_changes(
    analysis: Dict[str, Any],
    before: Dict[str, Any],
    after: Dict[str, Any],
    predicted_metric: float,
    target_metric: str = "win_rate",
) -> Dict[str, Any]:
    """Explain heuristic optimizer output for humans (read-only)."""
    payload = {
        "backtest_analysis": analysis,
        "parameters_before": before,
        "parameters_after": after,
        "predicted_metric": predicted_metric,
        "target_metric": target_metric,
        "method": "backtest_heuristic",
    }
    user = (
        "Explain these configuration changes that were suggested by backtest heuristics:\n"
        f"{json.dumps(payload, indent=2)}"
    )
    result = _chat(
        [{"role": "system", "content": _EXPLAIN_OPT_SYSTEM}, {"role": "user", "content": user}],
        feature="optimization_explain",
        max_tokens=400,
    )
    if result.get("error"):
        return {"error": result["error"], "response": "", "disclaimer": DISCLAIMER}
    text = (result.get("content") or "").strip()
    if DISCLAIMER not in text:
        text = f"{text}\n\n{DISCLAIMER}" if text else DISCLAIMER
    return {"response": text, "disclaimer": DISCLAIMER}
