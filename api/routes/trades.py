"""
Trades Routes
Provides trade history and trade data
"""

import asyncio
from fastapi import APIRouter, HTTPException, Query, Depends
from api.utils import get_bot_instance
from api.auth import require_admin  # trade/state reset: admin JWT only
from api.models.responses import TradesResponse, TradeResponse
from typing import Optional, List
from datetime import datetime
import logging
from log_manager import LogManager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=TradesResponse)
async def get_trades(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    side: Optional[str] = Query(None, description="Filter by side (long/short)"),
    status: Optional[str] = Query(None, description="Filter by status (open/closed)"),
    limit: Optional[int] = Query(100, description="Limit number of results")
):
    """Get trade history"""
    try:
        # LogManager.get_trades() does blocking SQLite I/O - run in thread pool
        all_trades = await asyncio.to_thread(lambda: LogManager().get_trades())

        # Apply filters (fast, in event loop)
        filtered_trades = all_trades
        if symbol:
            filtered_trades = [t for t in filtered_trades if t.get('symbol') == symbol.upper()]
        if side:
            filtered_trades = [t for t in filtered_trades if t.get('side', 'long') == side.lower()]
        if status:
            filtered_trades = [t for t in filtered_trades if t.get('status') == status.lower()]
        
        # Limit results
        filtered_trades = filtered_trades[:limit] if limit else filtered_trades
        
        # Convert to response models
        trades = []
        for trade in filtered_trades:
            try:
                # Extract prices carefully - don't default None to 0
                entry_price_val = trade.get('entry_price')
                entry_price_float = float(entry_price_val) if (entry_price_val is not None and entry_price_val != '') else None
                
                exit_price_val = trade.get('exit_price')
                exit_price_float = float(exit_price_val) if (exit_price_val is not None and exit_price_val != '') else None
                
                pnl_val = trade.get('pnl')
                pnl_float = float(pnl_val) if (pnl_val is not None and pnl_val != '') else None
                
                trades.append(TradeResponse(
                    symbol=trade.get('symbol', ''),
                    side=trade.get('side', 'long'),
                    entry_price=entry_price_float,
                    exit_price=exit_price_float,
                    quantity=int(trade.get('quantity') or 0),
                    pnl=pnl_float,
                    status=trade.get('status', 'closed'),
                    entry_timestamp=datetime.fromisoformat(trade.get('entry_timestamp', datetime.now().isoformat())),
                    exit_timestamp=datetime.fromisoformat(trade.get('exit_timestamp')) if trade.get('exit_timestamp') else None,
                    strategy=trade.get('strategy')
                ))
            except Exception as e:
                logger.warning(f"Error converting trade to response: {e}", exc_info=True)
                continue
        
        return TradesResponse(
            trades=trades,
            total=len(trades)
        )
    except Exception as e:
        logger.error(f"Error getting trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get trades: {str(e)}")

@router.post("/reset", dependencies=[Depends(require_admin)])
async def reset_trades(session_only: Optional[bool] = Query(False, description="If true, clear only current session")):
    """Reset trades and bot stats/state in simulation/yfinance mode.
    - Clears in-memory trade history and positions
    - Resets decision report fields and cycle counters
    - Clears trades from SQLite via LogManager
    """
    try:
        bot = get_bot_instance()
        # Clear in-memory state (safe for yfinance/paper modes)
        if bot:
            try:
                bot.trade_history = []
                if hasattr(bot, 'positions'):
                    bot.positions = {}
                if hasattr(bot, 'candidate_decisions'):
                    bot.candidate_decisions = {}
                if hasattr(bot, 'current_symbols'):
                    bot.current_symbols = []
                if hasattr(bot, 'current_cycle_number'):
                    bot.current_cycle_number = 0
                if hasattr(bot, 'last_cycle_timings'):
                    bot.last_cycle_timings = None
                # Reset capital to starting_capital if available
                if hasattr(bot, 'starting_capital') and hasattr(bot, 'total_capital'):
                    bot.total_capital = bot.starting_capital
            except Exception as e:
                logger.warning(f"Bot state reset encountered an issue: {e}")

        # Clear persistent trades
        lm = LogManager()
        session_id = None
        # Try to use bot/log manager session_id when session_only requested
        if session_only:
            try:
                # Prefer bot.session_id if exposed, else use LogManager's current
                session_id = getattr(bot, 'session_id', None) if bot else None
            except Exception:
                session_id = None
        removed = lm.clear_trades(session_only=bool(session_only), session_id=session_id)

        return {
            "message": "Trades and state reset",
            "cleared_in_memory": bool(bot is not None),
            "db_rows_deleted": removed,
            "session_only": bool(session_only)
        }
    except Exception as e:
        logger.error(f"Error resetting trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reset trades: {str(e)}")
