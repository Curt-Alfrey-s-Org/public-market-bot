"""
API V1 Trades Routes
Endpoints: /api/v1/trades, /api/v1/trades/{id}
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

# v1 dependency (api/dependencies/auth.py): validates tokens issued by the v1
# login (api/utils/jwt.py). The legacy api.auth dependency uses a different
# signing secret, so v1 tokens were rejected here with 401.
from api.dependencies.auth import get_current_user
from api.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TradeResponse(BaseModel):
    """Trade summary response."""
    id: str = Field(..., description="Unique trade ID")
    symbol: str = Field(..., description="Stock symbol (e.g., 'AAPL')")
    side: str = Field(..., description="'BUY' or 'SELL'")
    quantity: int = Field(..., description="Number of shares")
    price: float = Field(..., description="Execution price per share")
    executed_at: str = Field(..., description="ISO 8601 timestamp")
    status: str = Field(..., description="'completed', 'pending', 'failed'")
    pnl: Optional[float] = Field(None, description="Profit/loss in dollars")
    notes: Optional[str] = Field(None, description="Signal quality or notes")


class TradeDetailResponse(BaseModel):
    """Trade detail response."""
    id: str
    symbol: str
    side: str
    quantity: int
    entry_price: float
    exit_price: Optional[float] = None
    executed_at: str
    closed_at: Optional[str] = None
    status: str
    pnl: Optional[float] = None
    roi_pct: Optional[float] = None
    decision_notes: Optional[str] = None
    chart_image_url: Optional[str] = None


class TradesListResponse(BaseModel):
    """Paginated trades list."""
    trades: List[TradeResponse]
    total: int = Field(..., description="Total count of trades")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Starting position")
    has_more: bool = Field(..., description="Are there more trades?")


# ============================================================================
# GET /api/v1/trades - List trades with pagination
# ============================================================================

@router.get("", response_model=TradesListResponse)
async def list_trades(
    limit: int = Query(50, ge=1, le=1000, description="Items per page (1-1000)"),
    offset: int = Query(0, ge=0, description="Starting position (0-indexed)"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by status: 'completed', 'pending', 'failed'"),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of trades with pagination.
    
    Query Parameters:
        - limit: Number of trades per page (1-1000, default 50)
        - offset: Starting position (default 0)
        - symbol: Optional filter by symbol (e.g., 'AAPL')
        - status: Optional filter by status
    
    Returns:
        - trades: Array of trade summaries
        - total: Total count of trades
        - limit: Items per page
        - offset: Starting position
        - has_more: Boolean if more trades exist
    
    Errors:
        - 401: Unauthorized
        - 400: Invalid parameters
    """
    # TODO: Implement trades list from bot
    # For now, return empty list as placeholder
    
    return TradesListResponse(
        trades=[],
        total=0,
        limit=limit,
        offset=offset,
        has_more=False
    )


# ============================================================================
# GET /api/v1/trades/{id} - Get trade details
# ============================================================================

@router.get("/{trade_id}", response_model=TradeDetailResponse)
async def get_trade(
    trade_id: str = Path(..., description="Trade ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific trade.
    
    Path Parameters:
        - trade_id: Unique trade identifier
    
    Returns:
        - id, symbol, side, quantity
        - entry_price, exit_price, pnl, roi_pct
        - executed_at, closed_at, status
        - decision_notes, chart_image_url
    
    Errors:
        - 401: Unauthorized
        - 404: Trade not found
        - 500: Internal error
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Trade not found"
    )
