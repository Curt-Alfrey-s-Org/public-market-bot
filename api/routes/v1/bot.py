"""
API V1 Bot Control Routes
Endpoints: /api/v1/bot/status, /api/v1/bot/start, /api/v1/bot/stop
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import logging

from api.dependencies.auth import get_current_user, get_admin_user
from api.models.user import User
from api.utils import get_bot_instance
from api.bot_manager import start_bot, stop_bot, is_bot_running, get_bot_status as get_manager_status, BrainUnavailableError
from api.middleware.rate_limit import limiter, BOT_CONTROL_RATE_LIMIT, GENERAL_RATE_LIMIT
from api.utils.timeutils import utcnow as _naive_utcnow

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS (V1 Mobile-Friendly)
# ============================================================================

class BotStatusResponse(BaseModel):
    """Bot status response."""
    running: bool = Field(..., description="Is bot currently running?")
    mode: str = Field(..., description="Bot mode: 'yfinance', 'sandbox', 'live', 'dryrun-live'")
    symbol: Optional[str] = Field(None, description="Current trading symbol (if trading)")
    trades_today: int = Field(default=0, description="Number of trades executed today")
    total_trades: int = Field(default=0, description="Total trades executed all time")
    uptime_seconds: int = Field(default=0, description="How long bot has been running (seconds)")
    last_trade_timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp of last trade")
    last_update: str = Field(..., description="ISO 8601 timestamp of this status update")


class BotControlResponse(BaseModel):
    """Bot start/stop response."""
    status: str = Field(..., description="'started' or 'stopped'")
    message: str = Field(..., description="Human-readable message")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


# ============================================================================
# GET /api/v1/bot/status
# ============================================================================

@router.get("/status", response_model=BotStatusResponse)
@limiter.limit(GENERAL_RATE_LIMIT)  # 60 requests/minute
async def get_bot_status(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get current bot status and stats.
    
    Returns:
        - running: Boolean if bot is active
        - mode: 'yfinance' | 'sandbox' | 'live' | 'dryrun-live'
        - trades_today: Integer count
        - total_trades: Integer count
        - uptime_seconds: Integer seconds
        - last_trade_timestamp: ISO 8601 or null
        - last_update: ISO 8601 current time
    
    Errors:
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        bot = get_bot_instance()
        is_running = is_bot_running()
        
        # Get mode from bot or environment
        mode = "yfinance"  # default
        if bot and hasattr(bot, 'mode'):
            mode = bot.mode
        
        # Get trade stats
        trades_today = 0
        total_trades = 0
        last_trade_ts = None
        
        if bot:
            if hasattr(bot, 'trades'):
                # Count trades
                all_trades = bot.trades if isinstance(bot.trades, list) else []
                total_trades = len(all_trades)
                
                # Count today's trades
                today = _naive_utcnow().date()
                trades_today = sum(1 for t in all_trades if hasattr(t, 'timestamp') and (
                    t.timestamp.date() == today if hasattr(t.timestamp, 'date') else False
                ))
                
                # Get last trade timestamp
                if all_trades:
                    last_trade = all_trades[-1]
                    if hasattr(last_trade, 'timestamp'):
                        last_trade_ts = last_trade.timestamp.isoformat() if hasattr(last_trade.timestamp, 'isoformat') else str(last_trade.timestamp)
        
        # Get uptime
        uptime_seconds = 0
        if bot and hasattr(bot, 'start_time') and bot.start_time:
            uptime_seconds = int((_naive_utcnow() - bot.start_time).total_seconds())
        
        return BotStatusResponse(
            running=is_running,
            mode=mode,
            symbol=None,  # Could be enhanced to return current symbol
            trades_today=trades_today,
            total_trades=total_trades,
            uptime_seconds=uptime_seconds,
            last_trade_timestamp=last_trade_ts,
            last_update=_naive_utcnow().isoformat() + "Z"
        )
    
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "server_error",
                "message": "Failed to get bot status"
            }
        )


# ============================================================================
# POST /api/v1/bot/start
# ============================================================================

@router.post("/start", response_model=BotControlResponse)
@limiter.limit(BOT_CONTROL_RATE_LIMIT)  # 30 requests/hour
async def start_bot_endpoint(
    request: Request,
    current_user: User = Depends(get_admin_user)  # control: admin only
):
    """
    Start the trading bot.
    
    Returns:
        - status: 'started'
        - message: 'Bot started successfully'
        - timestamp: ISO 8601
    
    Errors:
        - 401: Unauthorized
        - 400: Bot already running
        - 500: Failed to start
    """
    if is_bot_running():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_request",
                "message": "Bot is already running"
            }
        )
    
    try:
        start_bot()
        logger.info(f"Bot started by user: {current_user.username}")
        
        return BotControlResponse(
            status="started",
            message="Bot started successfully",
            timestamp=_naive_utcnow().isoformat() + "Z"
        )
    
    except BrainUnavailableError as e:
        logger.error(f"Start blocked — AI brain unavailable: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "brain_unavailable",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "server_error",
                "message": "Failed to start bot"
            }
        )


# ============================================================================
# POST /api/v1/bot/stop
# ============================================================================

@router.post("/stop", response_model=BotControlResponse)
@limiter.limit(BOT_CONTROL_RATE_LIMIT)  # 30 requests/hour
async def stop_bot_endpoint(
    request: Request,
    current_user: User = Depends(get_admin_user)  # control: admin only
):
    """
    Stop the trading bot.
    
    Returns:
        - status: 'stopped'
        - message: 'Bot stopped successfully'
        - timestamp: ISO 8601
    
    Errors:
        - 401: Unauthorized
        - 400: Bot not running
        - 500: Failed to stop
    """
    if not is_bot_running():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_request",
                "message": "Bot is not running"
            }
        )
    
    try:
        stop_bot()
        logger.info(f"Bot stopped by user: {current_user.username}")
        
        return BotControlResponse(
            status="stopped",
            message="Bot stopped successfully",
            timestamp=_naive_utcnow().isoformat() + "Z"
        )
    
    except Exception as e:
        logger.error(f"Failed to stop bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "server_error",
                "message": "Failed to stop bot"
            }
        )
