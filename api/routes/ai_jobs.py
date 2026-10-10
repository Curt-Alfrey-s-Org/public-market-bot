"""
Admin agentic jobs via the ALFa AI orchestrator (:8420 /api/runs).

Three factual, multi-step jobs:
- end-of-day summary   : narrate the day's trading activity
- anomaly digest       : flag unusual patterns in recent activity (factual)
- sector-rotation report: summarize sector exposure shifts

All jobs are FACTUAL ONLY: goals explicitly forbid buy/sell advice and price
predictions. Only sanitized domain data is sent (no Schwab tokens/balances).
Admin-only. Graceful degrade: returns a clear error if the brain is unreachable.
"""

import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from api.auth import require_admin
from api.services.market_ask_ai_context import sanitize_context

logger = logging.getLogger(__name__)

router = APIRouter()

_FACTUAL_RULES = (
    "STRICT RULES: Report only the facts present in the provided data. Do NOT "
    "give buy/sell recommendations, do NOT predict prices, do NOT give financial "
    "advice. This is for a simulated/educational trading bot. End with the line: "
    "'NOT FINANCIAL ADVICE.'"
)


def _gather_domain_facts() -> Dict[str, Any]:
    """Collect sanitized, factual domain data from the bot instance."""
    facts: Dict[str, Any] = {"trades": [], "stats": {}}
    try:
        from api.utils import get_bot_instance

        bot = get_bot_instance()
        if not bot:
            return facts
        history = list(getattr(bot, "trade_history", []) or [])
        total = len(history)
        wins = [t for t in history if (t.get("pnl", 0) or 0) > 0]
        facts["stats"] = {
            "total_trades": total,
            "win_rate_pct": round(len(wins) / total * 100, 2) if total else 0.0,
            "total_pnl": round(sum((t.get("pnl", 0) or 0) for t in history), 2),
        }
        # Last 25 trades, domain fields only
        recent: List[Dict[str, Any]] = []
        for t in history[-25:]:
            recent.append(
                {
                    "symbol": t.get("symbol"),
                    "action": t.get("action") or t.get("side"),
                    "pnl": t.get("pnl"),
                    "timestamp": str(t.get("timestamp") or t.get("time") or ""),
                    "sector": t.get("sector"),
                }
            )
        facts["trades"] = recent
    except Exception as e:
        logger.debug("ai_jobs: could not gather domain facts: %s", e)
    # Re-sanitize as defense-in-depth (drops any sensitive keys/sizes)
    return sanitize_context(facts)


def _build_goal(job: str, facts: Dict[str, Any]) -> str:
    data_json = json.dumps(facts)[:6000]
    intros = {
        "end-of-day-summary": (
            "Write a concise end-of-day summary of this simulated trading bot's "
            "activity (trades, win rate, P&L) in plain English."
        ),
        "anomaly-digest": (
            "Review the recent trading activity data and list any factual "
            "anomalies or unusual patterns you can observe (e.g. clusters of "
            "losses, repeated symbols, outlier P&L). Describe only what the data "
            "shows."
        ),
        "sector-rotation": (
            "Summarize the sector exposure in the recent trades and describe any "
            "factual shifts in which sectors were traded. Do not recommend changes."
        ),
    }
    intro = intros[job]
    return f"{intro}\n\n{_FACTUAL_RULES}\n\nData (sanitized domain-only JSON):\n{data_json}"


_JOBS = {"end-of-day-summary", "anomaly-digest", "sector-rotation"}


async def _submit(job: str) -> Dict[str, Any]:
    from api.services.alfa_orchestrator_client import create_run, is_orchestrator_enabled

    if not is_orchestrator_enabled():
        raise HTTPException(status_code=503, detail="ALFa AI orchestrator is not enabled.")
    facts = _gather_domain_facts()
    goal = _build_goal(job, facts)
    result = await create_run(goal)
    if result.get("error"):
        raise HTTPException(status_code=502, detail=f"Orchestrator error: {result['error']}")
    return {"status": "submitted", "job": job, "run_id": result.get("run_id")}


@router.post("/end-of-day-summary")
async def job_end_of_day_summary(_: dict = Depends(require_admin)) -> Dict[str, Any]:
    return await _submit("end-of-day-summary")


@router.post("/anomaly-digest")
async def job_anomaly_digest(_: dict = Depends(require_admin)) -> Dict[str, Any]:
    return await _submit("anomaly-digest")


@router.post("/sector-rotation")
async def job_sector_rotation(_: dict = Depends(require_admin)) -> Dict[str, Any]:
    return await _submit("sector-rotation")


@router.get("/runs/{run_id}")
async def job_run_status(run_id: str, _: dict = Depends(require_admin)) -> Dict[str, Any]:
    from api.services.alfa_orchestrator_client import get_run

    result = await get_run(run_id)
    if result.get("error"):
        raise HTTPException(status_code=502, detail=f"Orchestrator error: {result['error']}")
    return result
