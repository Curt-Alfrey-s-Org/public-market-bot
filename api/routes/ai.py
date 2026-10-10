"""
AI Assistant Routes — insights and backtest-driven optimization (no LLM param tuning).

- Performance narrative and trade journal: LLM (factual, not financial advice).
- Parameter suggestions: backtest heuristics via MLParameterOptimizer (not the LLM).
"""

import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.utils import get_bot_instance

logger = logging.getLogger(__name__)

router = APIRouter()


class OptimizationExplainRequest(BaseModel):
    explain: bool = True


@router.get("/summary")
async def get_ai_summary():
    """Get performance summary for the AI page."""
    bot = get_bot_instance()
    if not bot:
        raise HTTPException(status_code=503, detail="Bot instance not available")

    try:
        trade_history = getattr(bot, "trade_history", []) or []
        total_trades = len(trade_history)

        if total_trades > 0:
            winning_trades = [t for t in trade_history if t.get("pnl", 0) > 0]
            win_rate = len(winning_trades) / total_trades * 100
            total_pnl = sum(t.get("pnl", 0) for t in trade_history)
        else:
            win_rate = 0.0
            total_pnl = 0.0

        return {
            "win_rate": win_rate,
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "min_trades_required": 10,
            "has_sufficient_data": total_trades >= 10,
            "parameter_optimization_method": "backtest_heuristic",
        }
    except Exception as e:
        logger.error("Error getting AI summary: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get AI summary: {str(e)}")


@router.post("/request")
async def request_ai_analysis():
    """
    Request a factual performance narrative (LLM). Does not change bot settings.
    Requires at least 10 trades.
    """
    bot = get_bot_instance()
    if not bot:
        raise HTTPException(status_code=503, detail="Bot instance not available")

    try:
        trade_history = getattr(bot, "trade_history", []) or []
        total = len(trade_history)
        if total < 10:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"At least 10 trades required for AI analysis. Current: {total} trades."
                ),
            )
        result = bot.send_track_record_to_ai()
        tr = getattr(bot, "track_record", {}) or {}
        if "error" in result:
            return {
                "message": "AI narrative unavailable",
                "status": "error",
                "error": result["error"],
                "total_trades": total,
                "win_rate": tr.get("win_rate", 0),
            }
        return {
            "message": "Performance narrative complete",
            "status": "success",
            "response": result.get("response", ""),
            "disclaimer": result.get("disclaimer"),
            "total_trades": total,
            "win_rate": tr.get("win_rate", 0),
            "note": "Narrative only — no settings applied. Use /api/ai/optimization-suggestions for parameters.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error requesting AI analysis: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to request AI analysis: {str(e)}")


@router.post("/journal")
async def request_trade_journal():
    """Summarize recent trades in plain English (LLM, factual)."""
    bot = get_bot_instance()
    if not bot:
        raise HTTPException(status_code=503, detail="Bot instance not available")

    try:
        from api.services.trading_insights_llm import generate_trade_journal

        history = getattr(bot, "trade_history", []) or []
        result = generate_trade_journal(history)
        if result.get("error"):
            return {"status": "error", "error": result["error"], "response": ""}
        return {
            "status": "success",
            "response": result.get("response", ""),
            "disclaimer": result.get("disclaimer"),
            "trade_count": len(history),
        }
    except Exception as e:
        logger.error("Trade journal failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimization-suggestions")
async def get_optimization_suggestions(
    explain: bool = Query(False, description="Optional LLM explanation of heuristic suggestions"),
):
    """
    Backtest-heuristic parameter suggestions (does not require LLM).
    Set explain=true for an optional human-readable summary via the brain.
    """
    bot = get_bot_instance()
    if not bot:
        raise HTTPException(status_code=503, detail="Bot instance not available")

    trade_history = getattr(bot, "trade_history", []) or []
    if len(trade_history) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"At least 10 trades required. Current: {len(trade_history)}",
        )

    optimized, predicted = bot.optimize_parameters_ml()
    if not optimized:
        return {
            "status": "no_suggestions",
            "method": "backtest_heuristic",
            "parameters": {},
            "predicted_win_rate": 0.0,
        }

    payload: Dict[str, Any] = {
        "status": "success",
        "method": "backtest_heuristic",
        "parameters": optimized,
        "predicted_win_rate": predicted,
        "message": "Review before applying. Not auto-applied unless BOT_ENABLE_AI_AUTO_TWEAK=true.",
    }

    if explain:
        try:
            from api.services.trading_insights_llm import explain_parameter_changes

            ml = getattr(bot, "ml_optimizer", None)
            if ml:
                backtest_results = [
                    {
                        "win_rate": bot.track_record.get("win_rate", 0),
                        "roi": (bot.total_capital - bot.starting_capital) / max(bot.starting_capital, 1),
                    }
                ]
                analysis = ml._analyze_backtest_results(backtest_results)
                current = {
                    "BOT_TRAILING_STOP_PERCENT": float(os.getenv("BOT_TRAILING_STOP_PERCENT", "0.03")),
                }
                narrative = explain_parameter_changes(
                    analysis, current, optimized, predicted, target_metric="win_rate"
                )
                payload["explanation"] = narrative.get("response", "")
                payload["explanation_error"] = narrative.get("error")
        except Exception as e:
            payload["explanation_error"] = str(e)

    return payload
