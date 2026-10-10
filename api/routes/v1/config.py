"""
API V1 Config Routes
Endpoints: /api/v1/config
Provides feature flags, version checks, and configuration for mobile apps.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LimitsConfig(BaseModel):
    """Trading limits configuration."""
    max_positions: int = Field(default=5, description="Maximum open positions allowed")
    max_trades_per_day: int = Field(default=20, description="Maximum trades per day")
    min_account_value: int = Field(default=1000, description="Minimum account value required (dollars)")


class ConfigResponse(BaseModel):
    """App configuration response."""
    apiVersion: str = Field(
        default="v1",
        description="Current API version"
    )
    minAppVersion: str = Field(
        default="1.0.0",
        description="Minimum required app version. App should prompt to update if installedVersion < minAppVersion"
    )
    maintenanceMode: bool = Field(
        default=False,
        description="If true, app should show maintenance message and disable most features"
    )
    maintenanceMessage: Optional[str] = Field(
        default=None,
        description="Custom maintenance message to display to users"
    )
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "live_trading": False,
            "advanced_orders": False,
            "ai_signals": True,
            "paper_trading": True
        },
        description="Feature flags for mobile app to enable/disable features"
    )
    limits: LimitsConfig = Field(
        default_factory=LimitsConfig,
        description="Trading limits for the app"
    )
    environment: str = Field(
        default="production",
        description="Environment: 'production' | 'staging' | 'development'"
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_maintenance_mode() -> tuple[bool, Optional[str]]:
    """
    Get maintenance mode status from environment.
    Returns: (is_maintenance, maintenance_message)
    """
    mode = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
    message = os.getenv("MAINTENANCE_MESSAGE", None)
    return mode, message


def _get_environment() -> str:
    """Get current environment (production, staging, development)."""
    env = os.getenv("ENVIRONMENT", "production").lower()
    if env not in ("production", "staging", "development"):
        env = "production"
    return env


def _get_min_app_version() -> str:
    """Get minimum required app version."""
    return os.getenv("MIN_APP_VERSION", "1.0.0")


def _get_feature_flags() -> Dict[str, bool]:
    """Get feature flags from environment or defaults."""
    return {
        "live_trading": os.getenv("FEATURE_LIVE_TRADING", "false").lower() == "true",
        "advanced_orders": os.getenv("FEATURE_ADVANCED_ORDERS", "false").lower() == "true",
        "ai_signals": os.getenv("FEATURE_AI_SIGNALS", "true").lower() == "true",
        "paper_trading": os.getenv("FEATURE_PAPER_TRADING", "true").lower() == "true"
    }


# ============================================================================
# GET /api/v1/config - Get app configuration
# ============================================================================

@router.get("", response_model=ConfigResponse)
async def get_config():
    """
    Get app configuration and feature flags.
    
    Mobile app should call this on launch to:
    1. Check if minimum version is met (and prompt update if needed)
    2. Check if maintenance mode is active
    3. Get feature flags to enable/disable UI elements
    4. Retrieve trading limits and restrictions
    
    **Response Example:**
    ```json
    {
      "apiVersion": "v1",
      "minAppVersion": "1.0.0",
      "maintenanceMode": false,
      "maintenanceMessage": null,
      "features": {
        "live_trading": false,
        "advanced_orders": false,
        "ai_signals": true,
        "paper_trading": true
      },
      "limits": {
        "max_positions": 5,
        "max_trades_per_day": 20,
        "min_account_value": 1000
      },
      "environment": "production"
    }
    ```
    
    **Mobile App Integration Example:**
    ```python
    # On app launch
    config = requests.get('https://api.example.com/api/v1/config').json()
    
    # Check maintenance
    if config['maintenanceMode']:
        show_message(f"Maintenance: {config['maintenanceMessage']}")
        disable_all_controls()
    
    # Check version
    if app_version < config['minAppVersion']:
        show_update_prompt("Please update the app")
    
    # Enable/disable features
    if config['features']['ai_signals']:
        enable_ai_signals_section()
    if not config['features']['live_trading']:
        show_badge('live_button', 'Coming Soon')
    
    # Show limits
    max_pos = config['limits']['max_positions']
    ```
    
    **Environment Variables:**
    - `MIN_APP_VERSION`: Minimum app version (default: "1.0.0")
    - `MAINTENANCE_MODE`: Set to "true" to enable maintenance (default: "false")
    - `MAINTENANCE_MESSAGE`: Custom message when maintenance is enabled
    - `FEATURE_LIVE_TRADING`: Enable live trading (default: "false")
    - `FEATURE_ADVANCED_ORDERS`: Enable advanced orders (default: "false")
    - `FEATURE_AI_SIGNALS`: Enable AI signals (default: "true")
    - `FEATURE_PAPER_TRADING`: Enable paper trading (default: "true")
    - `ENVIRONMENT`: Current environment: "production", "staging", "development" (default: "production")
    """
    maintenance_mode, maintenance_msg = _get_maintenance_mode()
    
    return ConfigResponse(
        apiVersion="v1",
        minAppVersion=_get_min_app_version(),
        maintenanceMode=maintenance_mode,
        maintenanceMessage=maintenance_msg,
        features=_get_feature_flags(),
        limits=LimitsConfig(
            max_positions=int(os.getenv("MAX_POSITIONS", "5")),
            max_trades_per_day=int(os.getenv("MAX_TRADES_PER_DAY", "20")),
            min_account_value=int(os.getenv("MIN_ACCOUNT_VALUE", "1000"))
        ),
        environment=_get_environment()
    )

