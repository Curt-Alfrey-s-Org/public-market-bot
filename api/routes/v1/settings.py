"""
API V1 Settings Routes
Endpoints: /api/v1/settings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

# v1 dependency: validates tokens issued by the v1 login (api/utils/jwt.py)
from api.dependencies.auth import get_current_user, get_admin_user
from api.models.user import User
from api.utils.timeutils import utcnow as _naive_utcnow

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class BotSettings(BaseModel):
    """Bot configuration settings."""
    mode: str = Field(default="yfinance", description="'yfinance', 'sandbox', 'live', 'dryrun-live'")
    max_positions: int = Field(default=5, description="Maximum open positions")
    paper_trading_mode: bool = Field(default=True, description="Is paper trading enabled?")
    symbols: List[str] = Field(default_factory=list, description="Symbols to trade")
    risk_per_trade: float = Field(default=0.02, description="Risk per trade as percentage (e.g., 0.02 = 2%)")
    take_profit_pct: float = Field(default=2.5, description="Take profit target percentage")
    stop_loss_pct: float = Field(default=1.5, description="Stop loss percentage")


class SettingsResponse(BotSettings):
    """Settings response with metadata."""
    last_updated: str = Field(default_factory=lambda: _naive_utcnow().isoformat(), description="ISO 8601 timestamp")


# ============================================================================
# GET /api/v1/settings - Get current settings
# ============================================================================

@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get current bot settings and configuration.
    
    Returns:
        - mode: Current trading mode
        - max_positions, paper_trading_mode
        - symbols: List of symbols
        - risk_per_trade, take_profit_pct, stop_loss_pct
        - last_updated: ISO 8601 timestamp
    
    Errors:
        - 401: Unauthorized
        - 500: Internal error
    """
    return SettingsResponse()


# ============================================================================
# POST /api/v1/settings - Update settings (optional, may require admin)
# ============================================================================

@router.post("", response_model=SettingsResponse)
async def update_settings(
    settings: BotSettings,
    current_user: User = Depends(get_admin_user)  # settings writes: admin only
):
    """
    Update bot settings.
    
    Note: May require admin role depending on configuration.
    
    Request Body:
        - Any settings to update (mode, max_positions, etc.)
    
    Returns:
        - Updated settings
    
    Errors:
        - 401: Unauthorized
        - 403: Insufficient permissions
        - 500: Failed to update
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify settings"
        )
    
    # TODO: Implement settings update
    return SettingsResponse()
