"""
Stats Routes
Provides bot statistics and performance metrics
"""

import asyncio
from fastapi import APIRouter, HTTPException
from api.utils import get_bot_instance
from api.models.responses import StatsResponse, ErrorResponse
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()

def _compute_stats_sync(bot):
    """Compute stats from bot - runs in thread pool to avoid blocking event loop."""
    if not bot:
        return None
    try:
        capital = getattr(bot, 'total_capital', None)
        if capital is None or (isinstance(capital, (int, float)) and capital == 0.0):
            try:
                capital = float(os.getenv('BOT_TOTAL_CAPITAL', '10000.0'))
            except Exception:
                capital = 10000.0
        starting_capital = getattr(bot, 'starting_capital', capital)
        capital_change = capital - starting_capital
        capital_change_pct = (capital_change / starting_capital * 100) if starting_capital > 0 else 0.0
        if hasattr(bot, 'get_settled_capital'):
            available_capital = bot.get_settled_capital()
        else:
            total_capital = getattr(bot, 'capital', 0.0) or getattr(bot, 'total_capital', 0.0)
            allocated_capital = getattr(bot, 'current_allocation', 0.0)
            unsettled_funds = getattr(bot, 'unsettled_funds', [])
            total_unsettled = sum(f.get('amount', 0) for f in unsettled_funds) if isinstance(unsettled_funds, list) else 0
            available_capital = max(0.0, total_capital - allocated_capital - total_unsettled)
        trade_history = getattr(bot, 'trade_history', []) or []
        total_trades = len(trade_history)
        win_rate = (len([t for t in trade_history if (t.get('pnl') or 0) > 0]) / total_trades * 100) if total_trades > 0 else 0.0
        positions = getattr(bot, 'positions', {}) or {}
        open_positions = len([p for p in positions.values() if p.get('status') == 'open'])
        total_pnl = sum((t.get('pnl') or 0) for t in trade_history)
        gross_profit = sum((t.get('pnl') or 0) for t in trade_history if (t.get('pnl') or 0) > 0)
        gross_loss = abs(sum((t.get('pnl') or 0) for t in trade_history if (t.get('pnl') or 0) < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)
        monthly_return_pct = 0.0
        if hasattr(bot, 'get_current_month_return_pct'):
            try:
                monthly_return_pct = bot.get_current_month_return_pct()
            except Exception:
                pass
        monthly_returns_data = []
        if trade_history and starting_capital > 0:
            monthly_pnl = defaultdict(float)
            monthly_capital = defaultdict(float)
            sorted_trades = sorted([t for t in trade_history if t.get('entry_timestamp')], key=lambda x: x.get('entry_timestamp', ''))
            current_capital = starting_capital
            current_month = None
            for trade in sorted_trades:
                entry_ts = trade.get('entry_timestamp')
                if not entry_ts:
                    continue
                try:
                    entry_date = datetime.fromisoformat(entry_ts.replace('Z', '+00:00')) if isinstance(entry_ts, str) else entry_ts
                except Exception:
                    continue
                month_key = entry_date.strftime('%Y-%m')
                pnl = trade.get('pnl', 0) or 0
                monthly_pnl[month_key] += pnl
                current_capital += pnl
                monthly_capital[month_key] = current_capital
                if current_month is None or month_key > current_month:
                    current_month = month_key
            prev_capital = starting_capital
            for month_key in sorted(monthly_capital.keys()):
                month_capital = monthly_capital[month_key]
                month_return_pct = ((month_capital - prev_capital) / prev_capital * 100) if prev_capital > 0 else 0.0
                monthly_returns_data.append({'month': month_key, 'return_pct': round(month_return_pct, 2), 'pnl': round(monthly_pnl[month_key], 2), 'capital': round(month_capital, 2)})
                prev_capital = month_capital
            if monthly_return_pct == 0.0 and monthly_returns_data:
                monthly_return_pct = monthly_returns_data[-1]['return_pct']
        return {
            'capital': float(capital), 'capital_change': float(capital_change), 'capital_change_pct': float(capital_change_pct),
            'allocation': float(available_capital), 'win_rate': float(win_rate), 'total_trades': total_trades,
            'open_positions': open_positions, 'total_pnl': float(total_pnl), 'profit_factor': float(profit_factor),
            'monthly_return_pct': float(monthly_return_pct), 'monthly_returns': monthly_returns_data
        }
    except Exception as e:
        logger.warning(f"Error computing stats: {e}")
        return None

@router.get("", response_model=StatsResponse)
async def get_stats():
    """Get bot statistics"""
    bot = get_bot_instance()
    if not bot:
        # Return default stats when bot is not available instead of 503
        # This allows the UI to show something even when bot isn't started
        return StatsResponse(
            capital=0.0,
            capital_change=0.0,
            capital_change_pct=0.0,
            allocation=0.0,
            win_rate=0.0,
            total_trades=0,
            open_positions=0,
            total_pnl=0.0,
            profit_factor=0.0,
            monthly_return_pct=0.0,
            monthly_returns=[]
        )
    
    try:
        # Heavy stats computation runs in thread pool to avoid blocking event loop
        data = await asyncio.to_thread(_compute_stats_sync, bot)
        if data is None:
            return StatsResponse(
                capital=0.0, capital_change=0.0, capital_change_pct=0.0,
                allocation=0.0, win_rate=0.0, total_trades=0, open_positions=0,
                total_pnl=0.0, profit_factor=0.0, monthly_return_pct=0.0, monthly_returns=[]
            )
        return StatsResponse(**data)
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
