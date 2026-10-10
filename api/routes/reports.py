"""
Reports Routes
Decision report: live candidates and per-symbol decisions from the bot loop
"""

from fastapi import APIRouter
from api.utils import get_bot_instance
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/decisions")
async def get_decision_report():
    """
    Live decision report: current candidate symbols and last evaluation per symbol.
    Updated by the bot loop; poll this when the bot is running to see filter/sort
    and understand the decision-making process.
    """
    bot = get_bot_instance()
    if not bot:
        return {
            "candidates": [],
            "decisions": [],
            "cycle_number": 0,
            "total_candidates": 0,
            "evaluated_count": 0,
            "cycle_in_progress_no_data": False,
            "last_cycle_timings": None,
        }

    candidates = getattr(bot, "current_symbols", []) or []
    candidate_decisions = getattr(bot, "candidate_decisions", {}) or {}
    cycle_number = getattr(bot, "current_cycle_number", 0) or 0
    evaluated_count = len(candidate_decisions)
    # Cycle in progress but no symbols evaluated yet = likely stuck on first symbol's data fetch (can take 1–2 min)
    cycle_in_progress_no_data = cycle_number >= 1 and evaluated_count == 0

    # Build one row per candidate (symbol) with latest decision
    decisions: List[Dict[str, Any]] = []
    for symbol in candidates:
        row = candidate_decisions.get(symbol)
        if row:
            decisions.append({
                "symbol": row.get("symbol", symbol),
                "signal": row.get("signal", "—"),
                "action": row.get("action", "—"),
                "price": row.get("price"),
                "volume": row.get("volume"),
                "reason": row.get("reason", ""),
                "cycle_number": row.get("cycle_number", 0),
                "updated_at": row.get("updated_at", ""),
            })
        else:
            decisions.append({
                "symbol": symbol,
                "signal": "—",
                "action": "—",
                "price": None,
                "volume": None,
                "reason": "Pending",
                "cycle_number": cycle_number,
                "updated_at": "",
            })

    last_cycle_timings = getattr(bot, "last_cycle_timings", None)

    return {
        "candidates": candidates,
        "decisions": decisions,
        "cycle_number": cycle_number,
        "total_candidates": len(candidates),
        "evaluated_count": evaluated_count,
        "cycle_in_progress_no_data": cycle_in_progress_no_data,
        "last_cycle_timings": last_cycle_timings,
    }
