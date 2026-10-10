"""
Pending Trades Routes
Handles manual trade approval mode - pending trades awaiting user approval
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.utils import get_bot_instance
from api.auth import require_admin  # approving/rejecting trades: admin JWT only
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class PendingTradeResponse(BaseModel):
    """Pending trade response"""
    trade_id: str
    symbol: str
    action: str
    price: float
    quantity: float
    allocation: float
    volume: Optional[int]
    reasoning: Dict[str, Any]
    auto_mode_details: Dict[str, Any]
    timestamp: str
    expires_at: str
    status: str

class PendingTradesResponse(BaseModel):
    """List of pending trades"""
    pending_trades: List[PendingTradeResponse]
    total: int

class ApproveTradeRequest(BaseModel):
    """Request to approve a pending trade"""
    trade_id: str

class RejectTradeRequest(BaseModel):
    """Request to reject a pending trade"""
    trade_id: str
    reason: Optional[str] = None

@router.get("", response_model=PendingTradesResponse)
async def get_pending_trades():
    """Get all pending trades awaiting approval"""
    try:
        bot = get_bot_instance()
        if not bot:
            return PendingTradesResponse(pending_trades=[], total=0)
        
        # Get pending trades from bot
        pending_trades = bot.get_pending_trades()
        
        # Convert to response format
        trades = []
        for trade in pending_trades:
            try:
                trades.append(PendingTradeResponse(
                    trade_id=trade['trade_id'],
                    symbol=trade['symbol'],
                    action=trade['action'],
                    price=float(trade['price']),
                    quantity=float(trade['quantity']),
                    allocation=float(trade['allocation']),
                    volume=trade.get('volume'),
                    reasoning=trade.get('reasoning', {}),
                    auto_mode_details=trade.get('auto_mode_details', {}),
                    timestamp=trade.get('timestamp', ''),
                    expires_at=trade.get('expires_at', ''),
                    status=trade.get('status', 'pending')
                ))
            except Exception as e:
                logger.warning(f"Error converting pending trade to response: {e}")
                continue
        
        return PendingTradesResponse(
            pending_trades=trades,
            total=len(trades)
        )
    except Exception as e:
        logger.error(f"Error getting pending trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get pending trades: {str(e)}")

@router.post("/approve", dependencies=[Depends(require_admin)])
async def approve_pending_trade(request: ApproveTradeRequest):
    """Approve a pending trade and execute it"""
    try:
        bot = get_bot_instance()
        if not bot:
            raise HTTPException(status_code=503, detail="Bot not available")
        
        result = bot.approve_pending_trade(request.trade_id)
        
        if result.get('status') == 'error':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to approve trade'))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve trade: {str(e)}")

@router.post("/reject", dependencies=[Depends(require_admin)])
async def reject_pending_trade(request: RejectTradeRequest):
    """Reject a pending trade"""
    try:
        bot = get_bot_instance()
        if not bot:
            raise HTTPException(status_code=503, detail="Bot not available")
        
        result = bot.reject_pending_trade(request.trade_id, request.reason)
        
        if result.get('status') == 'error':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to reject trade'))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reject trade: {str(e)}")
