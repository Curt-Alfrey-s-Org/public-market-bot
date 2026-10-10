"""
Response Models for API endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from collections import defaultdict
# Re-export error models from error.py
from api.models.error import ErrorResponse, ValidationError, UnauthorizedError, ForbiddenError, NotFoundError, RateLimitError, ServerError


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str

class StatsResponse(BaseModel):
    """Stats endpoint response"""
    capital: float
    capital_change: float
    capital_change_pct: float
    allocation: float
    win_rate: float
    total_trades: int
    open_positions: int
    total_pnl: float
    profit_factor: float  # Total Gross Profit / Total Gross Loss
    monthly_return_pct: float  # Dollar % change per month
    monthly_returns: List[Dict[str, Any]]  # List of monthly returns for chart

class StatusResponse(BaseModel):
    """Bot status response"""
    running: bool
    mode: str
    last_update: Optional[datetime] = None
    no_trade_reasons: Optional[List[str]] = None  # Why bot may not be trading (when running but no trades)

class TradeResponse(BaseModel):
    """Trade data response"""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: Optional[float] = None  # Allow None for legacy trades without entry prices
    exit_price: Optional[float] = None
    quantity: int
    pnl: Optional[float] = None
    status: str  # 'open' or 'closed'
    entry_timestamp: datetime
    exit_timestamp: Optional[datetime] = None
    strategy: Optional[str] = None

class TradesResponse(BaseModel):
    """Trades list response"""
    trades: List[TradeResponse]
    total: int
