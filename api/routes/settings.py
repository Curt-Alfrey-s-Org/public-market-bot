"""
Settings Routes
Handles bot configuration and settings
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import os
from pathlib import Path
from api.auth import require_admin  # settings writes: admin JWT only
from api.runtime_env import runtime_env_file, writable_runtime_env_file, not_persisted_reason

logger = logging.getLogger(__name__)

router = APIRouter()

class SettingsUpdate(BaseModel):
    """Settings update model"""
    settings: Dict[str, Any]

def _get_env_file_path():
    """Runtime env file settings are persisted to, or None when they must not be written
    (container without BOT_RUNTIME_ENV_FILE). Host installs: the project .env, as before.
    See api/runtime_env.py."""
    return runtime_env_file()

def _read_env_file():
    """Read the runtime env file and return it as a dictionary"""
    env_file = _get_env_file_path()
    env_vars = {}
    
    if env_file is not None and env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        env_vars[key] = value
        except Exception as e:
            logger.warning(f"Error reading .env file: {e}")
    
    return env_vars

# Keys that the Settings GUI is allowed to persist. Bot-managed keys (e.g. SCHWAB_API_ENABLED
# set by Dashboard mode, throttling defaults) are read from .env but not writable via Settings API.
USER_FACING_SETTING_KEYS = frozenset({
    "BOT_TOTAL_CAPITAL", "BOT_MIN_ALLOCATION", "BOT_MAX_ALLOCATION", "BOT_RISK_THRESHOLD",
    "BOT_POSITION_SIZE", "BOT_MAX_OPEN_POSITIONS", "BOT_STOP_LOSS_PERCENT", "BOT_TAKE_PROFIT_PERCENT",
    "MANUAL_TRADE_APPROVAL_MODE", "PAPER_TRADING_MODE", "DRY_RUN_MODE", "BACKTEST_MODE",
    "SCHWAB_SANDBOX_MODE", "USE_MARGIN",
    "TRADING_FREQUENCY", "LOG_LEVEL", "DEBUG", "EXIT_REFRESH_PRICE",
    "ALERT_EMAIL_ENABLED",
    # Discovery / today's best (screener, refresh)
    "SYMBOL_REFRESH_INTERVAL_CYCLES", "MAX_STOCK_PRICE", "MIN_STOCK_PRICE", "MAX_DISCOVERED_STOCKS",
    # Strategy / yfinance (ML filter, min bars for signals)
    "ENABLE_ML_SIGNAL_FILTER", "ML_SIGNAL_FILTER_MIN_CONFIDENCE", "ML_SIGNAL_FILTER_MIN_WIN_PROB", "STRATEGY_MIN_BARS",
})

# Third-party credentials are never returned by the API: any logged-in user can
# read GET /api/settings, so these are masked (security review 2026-09-25 follow-up).
# They are also not writable through the Settings API (not in USER_FACING_SETTING_KEYS).
SECRET_SETTING_KEYS = (
    "SCHWAB_APP_KEY", "SCHWAB_SECRET_KEY", "HUGGING_FACE_API_KEY",
    "ALPHA_VANTAGE_API_KEY", "NEWS_API_KEY", "FINNHUB_API_KEY",
)
MASKED_SECRET_VALUE = "change-me"


def _mask_secret(value: Any) -> str:
    """Return a fixed mask when a credential is configured, "" when it is not."""
    return MASKED_SECRET_VALUE if value else ""


def _update_env_file(updates: Dict[str, Any]):
    """Update .env file with new settings (only user-facing keys are persisted)."""
    if _get_env_file_path() is None:
        logger.warning(f"Settings not persisted: {not_persisted_reason()}")
        return False
    env_file = writable_runtime_env_file()
    if env_file is None:
        logger.warning(f"Runtime env file not found or not writable at {_get_env_file_path()}")
        return False
    
    # Only persist keys that are in the user-facing whitelist
    updates = {k: v for k, v in updates.items() if k in USER_FACING_SETTING_KEYS}
    # A value with a line break would write extra KEY=VALUE lines (any variable)
    # into the env file; refuse those values outright.
    bad = [k for k, v in updates.items() if any(c in str(v) for c in "\r\n\x00")]
    for k in bad:
        logger.warning(f"Refusing to persist {k}: value contains a line break")
        updates.pop(k)
    if not updates:
        return False

    try:
        # Read existing .env file
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated = False
        new_lines = []
        settings_found = {key: False for key in updates.keys()}
        
        # Map frontend setting names to .env variable names
        setting_to_env_map = {
            "BOT_TOTAL_CAPITAL": "BOT_TOTAL_CAPITAL",
            "BOT_MIN_ALLOCATION": "BOT_MIN_ALLOCATION",
            "BOT_MAX_ALLOCATION": "BOT_MAX_ALLOCATION",
            "BOT_RISK_THRESHOLD": "BOT_RISK_THRESHOLD",
            "BOT_POSITION_SIZE": "BOT_POSITION_SIZE",
            "BOT_MAX_OPEN_POSITIONS": "BOT_MAX_OPEN_POSITIONS",
            "BOT_STOP_LOSS_PERCENT": "BOT_STOP_LOSS_PERCENT",
            "BOT_TAKE_PROFIT_PERCENT": "BOT_TAKE_PROFIT_PERCENT",
            # Trading mode settings
            "MANUAL_TRADE_APPROVAL_MODE": "MANUAL_TRADE_APPROVAL_MODE",
            "PAPER_TRADING_MODE": "PAPER_TRADING_MODE",
            "DRY_RUN_MODE": "DRY_RUN_MODE",
            "BACKTEST_MODE": "BACKTEST_MODE",
            "SCHWAB_SANDBOX_MODE": "SCHWAB_SANDBOX_MODE",
            "SCHWAB_API_ENABLED": "SCHWAB_API_ENABLED",
            # Advanced settings
            "TRADING_FREQUENCY": "TRADING_FREQUENCY",
            "LOG_LEVEL": "LOG_LEVEL",
            "DEBUG": "DEBUG",
            "TOP_PERFORMERS_REFRESH_INTERVAL": "TOP_PERFORMERS_REFRESH_INTERVAL",
            "ASYNC_REQUEST_TIMEOUT": "ASYNC_REQUEST_TIMEOUT",
            "BOT_MAX_CPU_PERCENT": "BOT_MAX_CPU_PERCENT",
            "BOT_MAX_MEMORY_PERCENT": "BOT_MAX_MEMORY_PERCENT",
            "BOT_THROTTLE_DELAY": "BOT_THROTTLE_DELAY",
            "BOT_ENABLE_THROTTLING": "BOT_ENABLE_THROTTLING",
            "EXIT_REFRESH_PRICE": "EXIT_REFRESH_PRICE",
            # Email alert settings
            "ALERT_EMAIL_ENABLED": "ALERT_EMAIL_ENABLED",
            # Margin mode: use total capital vs settled-only
            "USE_MARGIN": "USE_MARGIN",
            # Strategy / yfinance
            "ENABLE_ML_SIGNAL_FILTER": "ENABLE_ML_SIGNAL_FILTER",
            "ML_SIGNAL_FILTER_MIN_CONFIDENCE": "ML_SIGNAL_FILTER_MIN_CONFIDENCE",
            "ML_SIGNAL_FILTER_MIN_WIN_PROB": "ML_SIGNAL_FILTER_MIN_WIN_PROB",
            "STRATEGY_MIN_BARS": "STRATEGY_MIN_BARS",
            # Discovery / today's best
            "SYMBOL_REFRESH_INTERVAL_CYCLES": "SYMBOL_REFRESH_INTERVAL_CYCLES",
            "MAX_STOCK_PRICE": "MAX_STOCK_PRICE",
            "MIN_STOCK_PRICE": "MIN_STOCK_PRICE",
            "MAX_DISCOVERED_STOCKS": "MAX_DISCOVERED_STOCKS",
        }
        
        # Process each line
        for line in lines:
            line_stripped = line.strip()
            updated_line = False
            
            # Check if this line contains a setting we want to update
            for setting_key, setting_value in updates.items():
                env_key = setting_to_env_map.get(setting_key, setting_key)
                if line_stripped.startswith(f'{env_key}='):
                    # Update the value
                    new_lines.append(f"{env_key}={setting_value}\n")
                    settings_found[setting_key] = True
                    updated = True
                    updated_line = True
                    break
            
            if not updated_line:
                new_lines.append(line)
        
        # Add missing variables if they weren't in the file
        for setting_key, setting_value in updates.items():
            if not settings_found[setting_key]:
                env_key = setting_to_env_map.get(setting_key, setting_key)
                new_lines.append(f"{env_key}={setting_value}\n")
                updated = True
        
        # Write back to file
        if updated:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            logger.info(f"Updated runtime env file with {len(updates)} settings")
            
            # Update environment variables in current process
            for setting_key, setting_value in updates.items():
                env_key = setting_to_env_map.get(setting_key, setting_key)
                os.environ[env_key] = str(setting_value)
        
        return updated
    except Exception as e:
        logger.error(f"Error updating .env file: {e}", exc_info=True)
        return False

@router.get("")
async def get_settings():
    """Get current bot settings from .env file"""
    # Read from .env file first, then fall back to environment variables
    env_vars = _read_env_file()
    
    def get_setting(key: str, default: str, type_func=float):
        """Get setting value with type conversion"""
        value = env_vars.get(key, os.getenv(key, default))
        try:
            return type_func(value)
        except (ValueError, TypeError):
            return type_func(default)
    
    def get_setting_bool(key: str, default: str):
        """Get boolean setting value"""
        value = env_vars.get(key, os.getenv(key, default))
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return False
    
    def get_setting_str(key: str, default: str):
        """Get string setting value"""
        return env_vars.get(key, os.getenv(key, default))
    
    settings = {
        "BOT_TOTAL_CAPITAL": get_setting("BOT_TOTAL_CAPITAL", "10000", float),
        "BOT_MIN_ALLOCATION": get_setting("BOT_MIN_ALLOCATION", "50", float),
        "BOT_MAX_ALLOCATION": get_setting("BOT_MAX_ALLOCATION", "500", float),
        "BOT_RISK_THRESHOLD": get_setting("BOT_RISK_THRESHOLD", "0.02", float),
        "BOT_POSITION_SIZE": get_setting("BOT_POSITION_SIZE", "0.01", float),
        "BOT_MAX_OPEN_POSITIONS": get_setting("BOT_MAX_OPEN_POSITIONS", "5", int),
        "BOT_STOP_LOSS_PERCENT": get_setting("BOT_STOP_LOSS_PERCENT", "0.05", float),
        "BOT_TAKE_PROFIT_PERCENT": get_setting("BOT_TAKE_PROFIT_PERCENT", "0.10", float),
        # Trading mode settings
        "MANUAL_TRADE_APPROVAL_MODE": get_setting_str("MANUAL_TRADE_APPROVAL_MODE", "false"),
        "PAPER_TRADING_MODE": get_setting_str("PAPER_TRADING_MODE", "true"),
        "DRY_RUN_MODE": get_setting_str("DRY_RUN_MODE", "false"),
        "BACKTEST_MODE": get_setting_str("BACKTEST_MODE", "false"),
        "SCHWAB_SANDBOX_MODE": get_setting_str("SCHWAB_SANDBOX_MODE", "false"),  # same default as main.py/bot_manager
        "SCHWAB_API_ENABLED": get_setting_str("SCHWAB_API_ENABLED", "on"),
        # Advanced settings
        "TRADING_FREQUENCY": get_setting("TRADING_FREQUENCY", "2", int),
        "LOG_LEVEL": get_setting_str("LOG_LEVEL", "INFO"),
        "DEBUG": get_setting_str("DEBUG", "false"),  # Return as string for consistency
        "TOP_PERFORMERS_REFRESH_INTERVAL": get_setting("TOP_PERFORMERS_REFRESH_INTERVAL", "60", int),
        "ASYNC_REQUEST_TIMEOUT": get_setting("ASYNC_REQUEST_TIMEOUT", "10", int),
        "BOT_MAX_CPU_PERCENT": get_setting("BOT_MAX_CPU_PERCENT", "75", int),
        "BOT_MAX_MEMORY_PERCENT": get_setting("BOT_MAX_MEMORY_PERCENT", "75", int),
        "BOT_THROTTLE_DELAY": get_setting("BOT_THROTTLE_DELAY", "5", int),
        "BOT_ENABLE_THROTTLING": get_setting_str("BOT_ENABLE_THROTTLING", "true"),  # Return as string for consistency
        "EXIT_REFRESH_PRICE": get_setting_str("EXIT_REFRESH_PRICE", "true"),  # Return as string for consistency
        # Email alert settings
        "ALERT_EMAIL_ENABLED": get_setting_bool("ALERT_EMAIL_ENABLED", "false"),  # Off by default (dev mode)
        # Margin mode: use total capital (true) vs settled-only (false)
        "USE_MARGIN": get_setting_bool("USE_MARGIN", "false"),
        # Strategy / yfinance (ML filter, min OHLCV bars for signal)
        "ENABLE_ML_SIGNAL_FILTER": get_setting_str("ENABLE_ML_SIGNAL_FILTER", "true"),
        "ML_SIGNAL_FILTER_MIN_CONFIDENCE": get_setting("ML_SIGNAL_FILTER_MIN_CONFIDENCE", "0.6", float),
        "ML_SIGNAL_FILTER_MIN_WIN_PROB": get_setting("ML_SIGNAL_FILTER_MIN_WIN_PROB", "0.55", float),
        "STRATEGY_MIN_BARS": get_setting("STRATEGY_MIN_BARS", "50", int),
        # API keys: masked ("********" when set, "" when not). The real values never leave the server.
        **{key: _mask_secret(get_setting_str(key, "")) for key in SECRET_SETTING_KEYS},
    }
    return settings

@router.put("", dependencies=[Depends(require_admin)])
async def update_settings(settings_update: SettingsUpdate):
    """Update bot settings and persist to .env file"""
    try:
        # Validate settings (basic validation)
        valid_settings = {}
        for key, value in settings_update.settings.items():
            # Convert to appropriate type
            if key in ["BOT_TOTAL_CAPITAL", "BOT_MIN_ALLOCATION", "BOT_MAX_ALLOCATION", 
                      "BOT_RISK_THRESHOLD", "BOT_POSITION_SIZE", "BOT_STOP_LOSS_PERCENT", 
                      "BOT_TAKE_PROFIT_PERCENT", "MAX_STOCK_PRICE", "MIN_STOCK_PRICE"]:
                try:
                    valid_settings[key] = float(value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {key}: {value}, skipping")
            elif key in ["BOT_MAX_OPEN_POSITIONS", "TRADING_FREQUENCY", "TOP_PERFORMERS_REFRESH_INTERVAL",
                        "ASYNC_REQUEST_TIMEOUT", "BOT_MAX_CPU_PERCENT", "BOT_MAX_MEMORY_PERCENT",
                        "BOT_THROTTLE_DELAY", "SYMBOL_REFRESH_INTERVAL_CYCLES", "MAX_DISCOVERED_STOCKS", "STRATEGY_MIN_BARS"]:
                try:
                    valid_settings[key] = int(value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {key}: {value}, skipping")
            elif key in ["ML_SIGNAL_FILTER_MIN_CONFIDENCE", "ML_SIGNAL_FILTER_MIN_WIN_PROB"]:
                try:
                    v = float(value)
                    valid_settings[key] = max(0.0, min(1.0, v))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {key}: {value}, skipping")
            elif key in ["DEBUG", "BOT_ENABLE_THROTTLING", "EXIT_REFRESH_PRICE", "MANUAL_TRADE_APPROVAL_MODE",
                        "ENABLE_ML_SIGNAL_FILTER", "PAPER_TRADING_MODE", "DRY_RUN_MODE", "BACKTEST_MODE",
                        "SCHWAB_SANDBOX_MODE", "ALERT_EMAIL_ENABLED", "USE_MARGIN"]:
                # Boolean settings
                if isinstance(value, bool):
                    valid_settings[key] = str(value).lower()
                elif isinstance(value, str):
                    valid_settings[key] = value.lower() if value.lower() in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off') else str(value)
                else:
                    valid_settings[key] = str(bool(value)).lower()
            elif key == "SCHWAB_API_ENABLED":
                # Special handling for SCHWAB_API_ENABLED (on/off)
                if isinstance(value, str):
                    valid_settings[key] = value.lower() if value.lower() in ('on', 'off', 'true', 'false', '1', '0') else value
                elif isinstance(value, bool):
                    valid_settings[key] = 'on' if value else 'off'
                else:
                    valid_settings[key] = 'on' if value else 'off'
            elif key == "LOG_LEVEL":
                # String setting with validation
                valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                if isinstance(value, str) and value.upper() in valid_levels:
                    valid_settings[key] = value.upper()
                else:
                    logger.warning(f"Invalid LOG_LEVEL: {value}, must be one of {valid_levels}, skipping")
            elif key in SECRET_SETTING_KEYS:
                # API keys are not writable via the Settings API (not in USER_FACING_SETTING_KEYS);
                # the GUI echoes back the mask from GET, so never treat it as a value.
                if value == MASKED_SECRET_VALUE:
                    continue
                valid_settings[key] = str(value) if value else ""
            else:
                # Unknown setting, but allow it
                valid_settings[key] = value
        
        # Persist to the runtime env file (see api/runtime_env.py)
        persisted = False
        if valid_settings:
            persisted = bool(_update_env_file(valid_settings))
            if not persisted:
                logger.warning("Settings were not persisted to the runtime env file")
        
        response_settings = {
            k: (_mask_secret(v) if k in SECRET_SETTING_KEYS else v) for k, v in valid_settings.items()
        }
        response = {
            "message": "Settings updated successfully" if persisted else "Settings were not saved",
            "settings": response_settings,
            "persisted": persisted,
        }
        if not persisted and _get_env_file_path() is None:
            response["detail"] = f"Not persisted: {not_persisted_reason()}"
        return response
    except Exception as e:
        logger.error(f"Error updating settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.get("/ml-filter")
async def get_ml_filter_settings():
    """Get current ML signal filter runtime settings"""
    try:
        from api.utils import get_bot_instance
        bot = get_bot_instance()
        
        if not bot:
            return {
                "enabled": False,
                "min_confidence": 0.6,
                "min_win_prob": 0.55,
                "filter_available": False,
                "message": "Bot not running"
            }
        
        return {
            "message": "ML filter settings",
            **bot.get_ml_filter_settings()
        }
    except Exception as e:
        logger.error(f"Error getting ML filter settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ML filter settings: {str(e)}")

@router.put("/ml-filter", dependencies=[Depends(require_admin)])
async def update_ml_filter_settings(settings: Dict[str, Any]):
    """
    Update ML signal filter runtime settings (does not require restart).
    
    Settings:
    - enabled: bool - Enable/disable ML filter
    - min_confidence: float (0-1) - Minimum model confidence
    - min_win_prob: float (0-1) - Minimum win probability
    """
    try:
        from api.utils import get_bot_instance
        bot = get_bot_instance()
        
        if not bot:
            raise HTTPException(status_code=400, detail="Bot is not running")
        
        # Extract valid settings
        enabled = settings.get('enabled')
        min_confidence = settings.get('min_confidence')
        min_win_prob = settings.get('min_win_prob')
        
        # Update settings on bot instance
        updated = bot.set_ml_filter_settings(
            enabled=enabled,
            min_confidence=min_confidence,
            min_win_prob=min_win_prob
        )
        
        # Also persist to .env file if settings provided
        env_updates = {}
        if enabled is not None:
            env_updates['ENABLE_ML_SIGNAL_FILTER'] = 'true' if enabled else 'false'
        if min_confidence is not None:
            env_updates['ML_SIGNAL_FILTER_MIN_CONFIDENCE'] = str(min_confidence)
        if min_win_prob is not None:
            env_updates['ML_SIGNAL_FILTER_MIN_WIN_PROB'] = str(min_win_prob)
        
        if env_updates:
            _update_env_file(env_updates)
        
        return {
            "message": "ML filter settings updated successfully",
            "settings": updated,
            "persisted_to_env": bool(env_updates)
        }
    except Exception as e:
        logger.error(f"Error updating ML filter settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update ML filter settings: {str(e)}")
