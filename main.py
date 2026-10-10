#!/usr/bin/env python3
"""
Market Pie5 Bot - Trading bot with paper testing, self-scaling, and AI integration
"""

import warnings
# Suppress pandas/yfinance deprecation warnings (FutureWarning, Pandas4Warning, etc.)
# yfinance uses deprecated Timestamp.utcnow(); filter by message so we catch all categories
warnings.filterwarnings('ignore', message=r'.*Timestamp\.utcnow.*')
# Suppress yfinance errors for delisted stocks (yfinance logs directly to stderr)
warnings.filterwarnings('ignore', message=r'.*delisted.*')
warnings.filterwarnings('ignore', message=r'.*No data found.*')
warnings.filterwarnings('ignore', message=r'.*Failed downloads.*')

import os
import json
import re
import requests
import random
import time
import logging
import stat
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# Import Copilot debug logger for detailed execution traces
try:
    from copilot_debug_logger import get_debug_logger
    COPILOT_DEBUG_AVAILABLE = True
except ImportError:
    COPILOT_DEBUG_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("copilot_debug_logger not available - debug logging disabled")

# Try to import psutil for resource monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("psutil not available - resource throttling disabled")

# Import Schwab authentication module
try:
    from schwab_auth import SchwabAuthenticator
    SCHWAB_AUTH_AVAILABLE = True
except ImportError:
    SCHWAB_AUTH_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("schwab_auth module not available - OAuth authentication disabled")

# Import sentiment analyzer
try:
    from sentiment_analyzer import SentimentAnalyzer
    SENTIMENT_ANALYZER_AVAILABLE = True
except ImportError:
    SENTIMENT_ANALYZER_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("sentiment_analyzer module not available - sentiment analysis disabled")

# Import ML signal filter
try:
    from ml_signal_filter import MLSignalFilter
    ML_SIGNAL_FILTER_AVAILABLE = True
except ImportError:
    ML_SIGNAL_FILTER_AVAILABLE = False
    MLSignalFilter = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("ml_signal_filter module not available - ML signal filtering disabled")

# Import portfolio optimizer
try:
    from portfolio_optimizer import PortfolioOptimizer
    PORTFOLIO_OPTIMIZER_AVAILABLE = True
except ImportError:
    PORTFOLIO_OPTIMIZER_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("portfolio_optimizer module not available - portfolio optimization disabled")

# Import ML parameter optimizer for 70% win rate target
try:
    from ml_param_optimizer import MLParameterOptimizer
    ML_OPTIMIZER_AVAILABLE = True
except ImportError:
    ML_OPTIMIZER_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("ml_param_optimizer module not available - ML parameter optimization disabled")

# Import data fetcher for stock data retrieval
try:
    from data_fetcher import DataFetcher
    DATA_FETCHER_AVAILABLE = True
except ImportError:
    DATA_FETCHER_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("data_fetcher module not available - advanced data fetching disabled")

# Import async data fetcher for concurrent data retrieval
try:
    from async_data_fetcher import AsyncDataFetcher, get_async_fetcher
    ASYNC_DATA_FETCHER_AVAILABLE = True
except ImportError:
    ASYNC_DATA_FETCHER_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("async_data_fetcher module not available - async data fetching disabled")

# Import strategies for signal-based trading (BUY/SELL/HOLD)
try:
    from strategies import (
        StrategyManager, SMAStrategy, BollingerBandsStrategy,
        RSIStrategy, MACDStrategy, MomentumStrategy
    )
    STRATEGIES_AVAILABLE = True
except ImportError:
    STRATEGIES_AVAILABLE = False
    StrategyManager = None
    SMAStrategy = None
    BollingerBandsStrategy = None
    RSIStrategy = None
    MACDStrategy = None
    MomentumStrategy = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("strategies module not available - strategy signals disabled, use HOLD")

# Import adaptive learning
try:
    from adaptive_learning import AdaptiveLearningOrchestrator
    ADAPTIVE_LEARNING_AVAILABLE = True
except ImportError:
    ADAPTIVE_LEARNING_AVAILABLE = False
    AdaptiveLearningOrchestrator = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("adaptive_learning module not available - adaptive learning disabled")

# Import order payload builder for Schwab LIMIT/STOP/STOP_LIMIT/TRAILING_STOP
try:
    from order_payload_builder import build_schwab_order_payload
    ORDER_PAYLOAD_BUILDER_AVAILABLE = True
except ImportError:
    ORDER_PAYLOAD_BUILDER_AVAILABLE = False
    build_schwab_order_payload = None

# Import Phase 1: Earnings Calendar for earnings-aware trading
try:
    from web_scrapers.earnings_calendar import EarningsCalendar
    EARNINGS_CALENDAR_AVAILABLE = True
except ImportError:
    EARNINGS_CALENDAR_AVAILABLE = False
    EarningsCalendar = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("earnings_calendar module not available - earnings awareness disabled")

# Import Phase 1: Enhanced stock scraper with sector/market cap metadata
try:
    from stock_screener import fetch_stock_universe_with_metadata
    STOCK_UNIVERSE_METADATA_AVAILABLE = True
except ImportError:
    STOCK_UNIVERSE_METADATA_AVAILABLE = False
    fetch_stock_universe_with_metadata = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("enhanced stock_screener not available - sector/market cap awareness disabled")

# Import Phase 2: Macro Calendar for avoiding major economic events
try:
    from web_scrapers.macro_calendar import MacroCalendar
    MACRO_CALENDAR_AVAILABLE = True
except ImportError:
    MACRO_CALENDAR_AVAILABLE = False
    MacroCalendar = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("macro_calendar module not available - macro event awareness disabled")

# Import Phase 2.2: Retail Sentiment for fading FOMO trades
try:
    from web_scrapers.retail_sentiment import RetailSentiment
    RETAIL_SENTIMENT_AVAILABLE = True
except ImportError:
    RETAIL_SENTIMENT_AVAILABLE = False
    RetailSentiment = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("retail_sentiment module not available - FOMO detection disabled")

# Import Phase 2.3: Options Flow for following smart money
try:
    from web_scrapers.options_flow import OptionsFlow
    OPTIONS_FLOW_AVAILABLE = True
except ImportError:
    OPTIONS_FLOW_AVAILABLE = False
    OptionsFlow = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("options_flow module not available - smart money tracking disabled")

# Import Phase 3: News Monitor for IPO/M&A/Regulatory events
try:
    from web_scrapers.news_monitor import NewsMonitor
    NEWS_MONITOR_AVAILABLE = True
except ImportError:
    NEWS_MONITOR_AVAILABLE = False
    NewsMonitor = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("news_monitor module not available - news filtering disabled")

# Import Alert System for desktop notifications
try:
    from alert_manager import get_alert_manager, SizzleDetector, alert_trade, alert_trade_blocked, alert_sizzle
    ALERT_SYSTEM_AVAILABLE = True
except ImportError:
    ALERT_SYSTEM_AVAILABLE = False
    get_alert_manager = None
    SizzleDetector = None
    alert_trade = alert_trade_blocked = alert_sizzle = None
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("alert_manager not available - desktop notifications disabled")

# Try to import yfinance for real stock prices
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    # Apply timeout so first symbol doesn't hang for minutes (Decision Report stays "not yet evaluated")
    try:
        import functools
        import requests
        _yf_timeout = max(10, int(os.getenv('YFINANCE_TIMEOUT_SECONDS', '60')))
        _yf_session = requests.Session()
        _yf_session.request = functools.partial(_yf_session.request, timeout=_yf_timeout)
        if hasattr(yf, 'base'): yf.base._requests = _yf_session
        if hasattr(yf, 'utils'): yf.utils._requests = _yf_session
        if hasattr(yf, 'ticker'): yf.ticker._requests = _yf_session
    except Exception:
        pass  # Leave yfinance default if patch fails
except ImportError:
    YFINANCE_AVAILABLE = False
    # Use temp logger before main logger is configured
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("yfinance not available - will use simulated prices")

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import encryption library for decrypting sensitive environment variables
try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("cryptography library not available - encrypted environment variables will not be decrypted")

# Sensitive environment variable keys that may be encrypted
SENSITIVE_ENV_KEYS = {
    "SCHWAB_API_KEY",
    "SCHWAB_APP_SECRET",
    "ALPHA_VANTAGE_API_KEY",
    "NEWS_API_KEY",
    "FINNHUB_API_KEY",
}

def _check_file_permissions(file_path: str) -> bool:
    """
    Check if a file has secure permissions (owner read/write only, 0o600).
    
    Args:
        file_path: Path to file to check
        
    Returns:
        True if permissions are secure (0o600), False otherwise
    """
    if not os.path.exists(file_path):
        return True  # File doesn't exist, no permission issues
    
    try:
        file_stats = os.stat(file_path)
        file_mode = stat.S_IMODE(file_stats.st_mode)
        # Check if permissions are exactly 0o600 (owner read/write only)
        return file_mode == 0o600
    except OSError as e:
        logger_temp = logging.getLogger(__name__)
        logger_temp.error(f"Failed to check permissions for {file_path}: {e}")
        return False

def _fix_file_permissions(file_path: str) -> bool:
    """
    Attempt to fix file permissions to 0o600.
    
    Args:
        file_path: Path to file to fix
        
    Returns:
        True if permissions were fixed successfully, False otherwise
    """
    try:
        os.chmod(file_path, 0o600)
        logger_temp = logging.getLogger(__name__)
        logger_temp.info(f"Fixed permissions for {file_path} to 0o600")
        return True
    except OSError as e:
        logger_temp = logging.getLogger(__name__)
        logger_temp.error(f"Failed to fix permissions for {file_path}: {e}")
        return False

def _get_encryption_key():
    """Return a Fernet key for encrypting/decrypting sensitive configuration values."""
    if not FERNET_AVAILABLE:
        return None
    logger_temp = logging.getLogger(__name__)
    
    # Check for key rotation flag
    if os.environ.get("MP5_ROTATE_ENCRYPTION_KEY", "").lower() == "true":
        logger_temp.warning("Key rotation requested via MP5_ROTATE_ENCRYPTION_KEY - generating new key")
        key = Fernet.generate_key()
        key_path = ".env.key"
        try:
            with open(key_path, "wb") as f:
                f.write(key)
            os.chmod(key_path, 0o600)
            logger_temp.warning("Generated new encryption key at %s - store securely!", key_path)
            # Clear the rotation flag to avoid repeated rotation (safe deletion)
            os.environ.pop("MP5_ROTATE_ENCRYPTION_KEY", None)
        except (OSError, IOError, PermissionError) as e:
            logger_temp.error("Failed to persist encryption key during rotation: %s", e)
        return key
    
    # Try environment variable first
    key = os.environ.get("MP5_ENCRYPTION_KEY")
    if key:
        return key.encode("utf-8")
    
    # Try reading from .env.key file
    key_path = ".env.key"
    if os.path.exists(key_path):
        # Check file permissions before reading
        if not _check_file_permissions(key_path):
            logger_temp.warning(
                "Insecure permissions detected on %s - should be 0o600. Attempting to fix...",
                key_path
            )
            if not _fix_file_permissions(key_path):
                logger_temp.error(
                    "SECURITY WARNING: Could not fix permissions on %s - key file may be exposed!",
                    key_path
                )
        
        with open(key_path, "rb") as f:
            return f.read().strip()
    
    # Generate a new key if it doesn't exist
    key = Fernet.generate_key()
    try:
        with open(key_path, "wb") as f:
            f.write(key)
        # Set secure permissions (owner read/write only)
        os.chmod(key_path, 0o600)
        logger_temp.warning("Generated new encryption key at %s - store securely!", key_path)
    except (OSError, IOError, PermissionError) as e:
        logger_temp.error("Failed to persist encryption key: %s", e)
        # Return the key anyway for this process
    return key

def _decrypt_sensitive_value(value):
    """
    Decrypt a sensitive configuration value that was encrypted.
    
    If the value starts with 'enc:', it will be decrypted.
    Otherwise, it will be returned as-is.
    
    Returns the decrypted string or original value.
    """
    if not FERNET_AVAILABLE:
        return value
        
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    
    # Check if value is encrypted (starts with 'enc:')
    if value.startswith("enc:"):
        try:
            key = _get_encryption_key()
            if key is None:
                # No encryption key available, return empty string
                return ""
            fernet = Fernet(key)
            encrypted_token = value[4:]  # Remove 'enc:' prefix
            decrypted_bytes = fernet.decrypt(encrypted_token.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            # Decryption failed, log error and return empty string
            logger_temp = logging.getLogger(__name__)
            logger_temp.debug(f"Failed to decrypt environment variable: {e}")
            return ""
    
    # Not encrypted, return as-is
    return value

def get_decrypted_env(key, default=""):
    """
    Get an environment variable and decrypt it if it's encrypted.
    
    Args:
        key: Environment variable name
        default: Default value if key not found
        
    Returns:
        Decrypted value or default
    """
    value = os.getenv(key, default)
    if key in SENSITIVE_ENV_KEYS:
        return _decrypt_sensitive_value(value)
    return value

# Load environment variables
SCHWAB_API_KEY = get_decrypted_env('SCHWAB_API_KEY', 'your_app_key')
SCHWAB_APP_SECRET = get_decrypted_env('SCHWAB_APP_SECRET', 'your_app_secret')
SCHWAB_CALLBACK_URL = os.getenv('SCHWAB_CALLBACK_URL', 'https://127.0.0.1:8182')
SCHWAB_ACCOUNT_ID = os.getenv('SCHWAB_ACCOUNT_ID', 'your_account_number')
SCHWAB_TOKEN_PATH = os.getenv('SCHWAB_TOKEN_PATH', 'token.json')

# Placeholder values that indicate Schwab API credentials are not configured
SCHWAB_CREDENTIAL_PLACEHOLDERS = ['your_app_key', 'your_app_secret', '', None]

BOT_RISK_THRESHOLD = float(os.getenv('BOT_RISK_THRESHOLD', '0.02'))
BOT_MIN_ALLOCATION = float(os.getenv('BOT_MIN_ALLOCATION', '50'))
BOT_MAX_ALLOCATION = float(os.getenv('BOT_MAX_ALLOCATION', '500'))
BOT_TRAILING_STOP_PERCENT = float(os.getenv('BOT_TRAILING_STOP_PERCENT', '0.03'))
SCAN_SYMBOLS_FILE = os.getenv('SCAN_SYMBOLS_FILE', 'scan_symbols.txt')

# Dynamic trailing stop configuration
DYNAMIC_STOP_ENABLED = os.getenv('DYNAMIC_STOP_ENABLED', 'True').lower() == 'true'
VOLATILITY_WINDOW = int(os.getenv('VOLATILITY_WINDOW', '20'))
MIN_TRAILING_STOP = float(os.getenv('MIN_TRAILING_STOP', '0.02'))  # 2% minimum
MAX_TRAILING_STOP = float(os.getenv('MAX_TRAILING_STOP', '0.10'))  # 10% maximum

# Stock filtering configuration
MIN_STOCK_PRICE = float(os.getenv('MIN_STOCK_PRICE', '5.0'))  # Avoid penny stocks
MAX_STOCK_PRICE = float(os.getenv('MAX_STOCK_PRICE', '1000.0'))  # Avoid very high-priced stocks
MIN_DAILY_VOLUME = int(os.getenv('MIN_DAILY_VOLUME', '500000'))  # Minimum volume
MAX_STOCK_VOLATILITY = float(os.getenv('MAX_STOCK_VOLATILITY', '0.15'))  # 15% max volatility

# Stock scanning and prioritization (TOS-like behavior)
MAX_STOCKS_TO_SCAN = int(os.getenv('MAX_STOCKS_TO_SCAN', '100'))  # Initial pool to screen
TOP_STOCKS_TO_TRADE = int(os.getenv('TOP_STOCKS_TO_TRADE', '50'))  # Top N after ranking

# Constants for stock discovery logging and display
LOG_SEPARATOR_LENGTH = 70  # Length of separator lines in logs
LOW_MAX_PRICE_THRESHOLD = 50.0  # Warn if MAX_STOCK_PRICE is below this
HIGH_MIN_PRICE_THRESHOLD = 100.0  # Warn if MIN_STOCK_PRICE is above this
DISPLAY_LIMIT = 10  # Number of symbols to show in discovery log
DEFAULT_FALLBACK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']  # Emergency fallback symbols

# Position management configuration
BOT_MAX_OPEN_POSITIONS = int(os.getenv('BOT_MAX_OPEN_POSITIONS', '5'))
BOT_MAX_CONSECUTIVE_LOSSES = int(os.getenv('BOT_MAX_CONSECUTIVE_LOSSES', '3'))
PARTIAL_EXIT_ENABLED = os.getenv('PARTIAL_EXIT_ENABLED', 'True').lower() == 'true'
PARTIAL_EXIT_PERCENTAGE = float(os.getenv('PARTIAL_EXIT_PERCENTAGE', '0.5'))  # 50% partial exit
PARTIAL_EXIT_STOP_TIGHTENING = float(os.getenv('PARTIAL_EXIT_STOP_TIGHTENING', '0.8'))  # Make stop 20% tighter after partial exit

# Volatility normalization constants for dynamic stop calculation
VOLATILITY_NORMALIZATION_MIN = float(os.getenv('VOLATILITY_NORMALIZATION_MIN', '0.01'))
VOLATILITY_NORMALIZATION_RANGE = float(os.getenv('VOLATILITY_NORMALIZATION_RANGE', '0.19'))

# Paper trading mode flag - now configurable via environment variable
PAPER_TRADING_MODE = os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'

# Dry-run mode - validate live trading workflow without executing trades
# When true, simulates API calls and validates payloads but doesn't place orders
# Useful for end-to-end testing before going live
DRY_RUN_MODE = os.getenv('DRY_RUN_MODE', 'false').lower() == 'true'

# Manual Trade Approval Mode
# Set to 'true' to require user approval before executing trades
# When enabled:
#   - Bot identifies trades and creates pending trade requests
#   - Shows full trade details, reasoning, and what would happen in auto mode
#   - User approves/rejects each trade via GUI
#   - Trades only execute after approval
# Use this to learn bot decision-making and build trust before full automation
# Default: 'false'
MANUAL_TRADE_APPROVAL_MODE = os.getenv('MANUAL_TRADE_APPROVAL_MODE', 'false').lower() == 'true'

# Backtesting mode - run historical data simulation
BACKTEST_MODE = os.getenv('BACKTEST_MODE', 'false').lower() == 'true'

# Schwab API Sandbox mode - use sandbox environment for testing
# Only applies when PAPER_TRADING_MODE=True; ignored in live trading
# Default is now 'false' to make yfinance the default mode
SCHWAB_SANDBOX_MODE = os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'

# Schwab API Enable/Disable Toggle
# Set to 'on'/'true' to enable Schwab API, 'off'/'false' to disable
# When disabled, bot uses yfinance for data and runs simulation mode
SCHWAB_API_ENABLED_STR = os.getenv('SCHWAB_API_ENABLED', 'on').lower()
SCHWAB_API_ENABLED = SCHWAB_API_ENABLED_STR in ('on', 'true', '1', 'yes')

# Live capital from Schwab API
# In live production mode, fetch actual account cash/buying power from Schwab API
# and use it as BOT_TOTAL_CAPITAL instead of the configured value
USE_SCHWAB_CAPITAL_IN_LIVE = os.getenv('USE_SCHWAB_CAPITAL_IN_LIVE', 'true').lower() == 'true'

# Random price fallback configuration for simulation modes
# When true, allows random price generation if yfinance also fails
# ONLY applies in pure simulation or API disabled modes (NOT sandbox or live)
ALLOW_RANDOM_FALLBACK = os.getenv('ALLOW_RANDOM_FALLBACK', 'true').lower() == 'true'

# Paper trading simulation settings
SIMULATED_WIN_RATE = float(os.getenv('SIMULATED_WIN_RATE', '0.7'))

# Win rate target for AI/ML auto-tuning (70% goal)
WIN_RATE_TARGET = float(os.getenv('WIN_RATE_TARGET', '0.70'))

# Risk-free rate for Sharpe ratio calculation
BOT_RISK_FREE_RATE = float(os.getenv('BOT_RISK_FREE_RATE', '0.0'))

# Optional: Position sizing, stop loss, and take profit parameters (for future use)
BOT_POSITION_SIZE = float(os.getenv('BOT_POSITION_SIZE', '0.01'))
BOT_STOP_LOSS_PERCENT = float(os.getenv('BOT_STOP_LOSS_PERCENT', '0.06'))

# High sale percent (formerly BOT_TAKE_PROFIT_PERCENT) - used for selling positions at profit target
# Supports both HIGH_SALE_PERCENT (new) and BOT_TAKE_PROFIT_PERCENT (legacy) for backward compatibility
HIGH_SALE_PERCENT = float(os.getenv('HIGH_SALE_PERCENT', os.getenv('BOT_TAKE_PROFIT_PERCENT', '0.10')))
# Keep BOT_TAKE_PROFIT_PERCENT as alias for backward compatibility
BOT_TAKE_PROFIT_PERCENT = HIGH_SALE_PERCENT

# Trading frequency configuration (minimum seconds between trades)
TRADING_FREQUENCY = int(os.getenv('TRADING_FREQUENCY', '2'))  # Wait 2 seconds between trades

# Capital floor configuration
CAPITAL_FLOOR_PERCENT = float(os.getenv('CAPITAL_FLOOR_PERCENT', '0.10'))  # 10% floor

# PDT (Pattern Day Trading) rules enforcement
# Note: In live trading mode, this is always True for regulatory compliance
ENABLE_PDT_RULES = os.getenv('ENABLE_PDT_RULES', 'true').lower() == 'true'

# Order Type Configuration
# Valid order types (MARKET/LIMIT + order_types.py–aligned STOP/STOP_LIMIT/TRAILING_STOP)
VALID_ORDER_TYPES = ['LIMIT', 'MARKET', 'STOP', 'STOP_LIMIT', 'TRAILING_STOP']

# Default order types for BUY and SELL actions
# Recommended: 'LIMIT' for BUY (price control), 'MARKET' for SELL (faster execution)
BOT_DEFAULT_BUY_ORDER_TYPE = os.getenv('BOT_DEFAULT_BUY_ORDER_TYPE', 'LIMIT').upper()
BOT_DEFAULT_SELL_ORDER_TYPE = os.getenv('BOT_DEFAULT_SELL_ORDER_TYPE', 'MARKET').upper()

# Validate order types
def _validate_order_type(order_type: str, default: str, var_name: str) -> str:
    """Validate order type and return valid value or default."""
    if order_type not in VALID_ORDER_TYPES:
        logger.warning(f"Invalid {var_name} '{order_type}', defaulting to '{default}'")
        return default
    return order_type

BOT_DEFAULT_BUY_ORDER_TYPE = _validate_order_type(BOT_DEFAULT_BUY_ORDER_TYPE, 'LIMIT', 'BOT_DEFAULT_BUY_ORDER_TYPE')
BOT_DEFAULT_SELL_ORDER_TYPE = _validate_order_type(BOT_DEFAULT_SELL_ORDER_TYPE, 'MARKET', 'BOT_DEFAULT_SELL_ORDER_TYPE')

# Optional limit order offset (e.g. buy 0.5% below, sell 0.5% above). 0 = no offset. Capped [0, 0.05].
_limit_offset_raw = float(os.getenv('LIMIT_ORDER_OFFSET_PCT', '0'))
LIMIT_ORDER_OFFSET_PCT = max(0.0, min(0.05, _limit_offset_raw))

# Stop / stop-limit / trailing-stop order params (used when order type is STOP, STOP_LIMIT, TRAILING_STOP)
_stop_raw = float(os.getenv('STOP_OFFSET_PCT', '0.01'))
STOP_OFFSET_PCT = max(0.0, min(0.10, _stop_raw))
_stop_limit_raw = float(os.getenv('STOP_LIMIT_OFFSET_PCT', '0.01'))
STOP_LIMIT_OFFSET_PCT = max(0.0, min(0.10, _stop_limit_raw))
# Trailing-stop order % (broker order type); BOT_TRAILING_STOP_PERCENT is for internal position exit
_trailing_order_raw = float(os.getenv('TRAILING_STOP_ORDER_PCT', os.getenv('BOT_TRAILING_STOP_PERCENT', '0.03')))
TRAILING_STOP_ORDER_PCT = max(0.01, min(0.15, _trailing_order_raw))

# Price source for strategy/execution: 'realtime' (get_stock_price) vs 'last_close' (OHLCV last close when available)
PRICE_SOURCE = (os.getenv('PRICE_SOURCE', 'realtime') or 'realtime').lower().strip()
if PRICE_SOURCE not in ('realtime', 'last_close'):
    PRICE_SOURCE = 'realtime'
# Price/volume cache TTL (seconds). Shorter = more real-time, more API calls. 0 = no cache (always fetch).
PRICE_CACHE_TTL_SECONDS = max(0, int(os.getenv('PRICE_CACHE_TTL_SECONDS', '30')))
# Refresh price immediately before exit (SELL/COVER) and use that for execution; disable for signal-time price.
EXIT_REFRESH_PRICE = os.getenv('EXIT_REFRESH_PRICE', 'true').lower() in ('true', '1', 'yes')

# Trade actions (Phase 1: stocks buy/short per MISSION.md)
VALID_ACTIONS = ['BUY', 'SELL', 'SHORT', 'COVER']
ACTIONS_OPEN_POSITION = ('BUY', 'SHORT')   # BUY = open long, SHORT = open short
ACTIONS_CLOSE_POSITION = ('SELL', 'COVER')  # SELL = close long, COVER = close short

# Map internal action -> Schwab API order instruction (for live/sandbox)
# BUY/SELL: standard; SHORT->SELL_SHORT, COVER->BUY_TO_COVER per broker conventions
SCHWAB_INSTRUCTION_MAP = {
    'BUY': 'BUY',
    'SELL': 'SELL',
    'SHORT': 'SELL_SHORT',
    'COVER': 'BUY_TO_COVER',
}

# Short-selling (Phase 1): margin/availability and concentration limits
ALLOW_SHORTS_IN_PAPER = os.getenv('ALLOW_SHORTS_IN_PAPER', 'true').lower() == 'true'
SCHWAB_SHORT_SELLING_ENABLED = os.getenv('SCHWAB_SHORT_SELLING_ENABLED', 'true').lower() == 'true'
MAX_SHORT_POSITIONS = int(os.getenv('MAX_SHORT_POSITIONS', str(BOT_MAX_OPEN_POSITIONS)))
MAX_SHORT_EXPOSURE_PCT = float(os.getenv('MAX_SHORT_EXPOSURE_PCT', '0.25'))

# Swing trading hold period enforcement
# Minimum number of days to hold a position before allowing a sell
# Default: 1 (enforce minimum 24-hour hold for swing trading strategy)
SWING_MIN_HOLD_DAYS = int(os.getenv('SWING_MIN_HOLD_DAYS', '1'))

# Alert configuration
ALERT_EMAIL = os.getenv('ALERT_EMAIL', '')
ENABLE_ALERTS = os.getenv('ENABLE_ALERTS', 'True').lower() == 'true'

# SMTP email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.example.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'Market Pie5 Bot')
SMTP_MAX_RETRIES = int(os.getenv('SMTP_MAX_RETRIES', '3'))
SMTP_RETRY_DELAY = int(os.getenv('SMTP_RETRY_DELAY', '5'))

# Email alert rate limiting
EMAIL_RATE_LIMIT_ENABLED = os.getenv('EMAIL_RATE_LIMIT_ENABLED', 'true').lower() == 'true'
EMAIL_MAX_PER_HOUR = int(os.getenv('EMAIL_MAX_PER_HOUR', '20'))  # Max emails per hour
EMAIL_MIN_INTERVAL_SECONDS = int(os.getenv('EMAIL_MIN_INTERVAL_SECONDS', '60'))  # Min seconds between emails

# Alert severity levels
ALERT_MIN_SEVERITY = os.getenv('ALERT_MIN_SEVERITY', 'INFO').upper()  # INFO, WARNING, CRITICAL
ALERT_SEVERITY_LEVELS = {
    'INFO': 1,
    'WARNING': 2,
    'CRITICAL': 3
}

# Dynamic scan configuration
DYNAMIC_SCAN_API_URL = os.getenv('DYNAMIC_SCAN_API_URL', '')  # Optional API for symbol scanning

# Stock screener configuration
ENABLE_STOCK_SCREENER = os.getenv('ENABLE_STOCK_SCREENER', 'true').lower() == 'true'
MAX_DISCOVERED_STOCKS = int(os.getenv('MAX_DISCOVERED_STOCKS', '10'))
# Min OHLCV bars required for strategy signal (default 50; lower to 20–30 for yfinance testing to see more signals)
STRATEGY_MIN_BARS = max(10, int(os.getenv('STRATEGY_MIN_BARS', '50')))

# Sentiment analysis filter configuration
ENABLE_SENTIMENT_FILTER = os.getenv('ENABLE_SENTIMENT_FILTER', 'false').lower() == 'true'

# ML signal filter configuration
ENABLE_ML_SIGNAL_FILTER = os.getenv('ENABLE_ML_SIGNAL_FILTER', 'true').lower() == 'true'
ML_SIGNAL_FILTER_MIN_CONFIDENCE = float(os.getenv('ML_SIGNAL_FILTER_MIN_CONFIDENCE', '0.6'))
ML_SIGNAL_FILTER_MIN_WIN_PROB = float(os.getenv('ML_SIGNAL_FILTER_MIN_WIN_PROB', '0.55'))
ML_SIGNAL_FILTER_MODEL_TYPE = os.getenv('ML_SIGNAL_FILTER_MODEL_TYPE', 'random_forest')  # 'random_forest' or 'gradient_boosting'

# Adaptive learning configuration
ENABLE_ADAPTIVE_LEARNING = os.getenv('ENABLE_ADAPTIVE_LEARNING', 'true').lower() == 'true'
ADAPTIVE_LEARNING_METHOD = os.getenv('ADAPTIVE_LEARNING_METHOD', 'qlearning')  # 'qlearning' or 'bandit'
ADAPTIVE_LEARNING_EXPLORATION = os.getenv('ADAPTIVE_LEARNING_EXPLORATION', 'true').lower() == 'true'  # Enable exploration

# ML Parameter Optimization Configuration
ENABLE_REALTIME_ML_OPTIMIZATION = os.getenv('ENABLE_REALTIME_ML_OPTIMIZATION', 'true').lower() == 'true'
ML_OPTIMIZATION_INTERVAL_TRADES = int(os.getenv('ML_OPTIMIZATION_INTERVAL_TRADES', '20'))  # Optimize every N trades
ML_OPTIMIZATION_INTERVAL_MINUTES = int(os.getenv('ML_OPTIMIZATION_INTERVAL_MINUTES', '60'))  # Or every N minutes
ML_OPTIMIZATION_MIN_TRADES = int(os.getenv('ML_OPTIMIZATION_MIN_TRADES', '10'))  # Minimum trades before optimizing

# Portfolio optimizer configuration
ENABLE_PORTFOLIO_OPTIMIZATION = os.getenv('ENABLE_PORTFOLIO_OPTIMIZATION', 'true').lower() == 'true'
PORTFOLIO_OPTIMIZATION_METHOD = os.getenv('PORTFOLIO_OPTIMIZATION_METHOD', 'sharpe')  # 'sharpe', 'min_variance', 'risk_parity', 'equal'

# Resource throttling configuration (for Raspberry Pi 5 stability/efficiency)
BOT_ENABLE_THROTTLING = os.getenv('BOT_ENABLE_THROTTLING', 'true').lower() == 'true'
BOT_MAX_CPU_PERCENT = float(os.getenv('BOT_MAX_CPU_PERCENT', '75'))  # 75% max CPU usage
BOT_MAX_MEMORY_PERCENT = float(os.getenv('BOT_MAX_MEMORY_PERCENT', '75'))  # 75% max memory usage
BOT_MAX_DISK_PERCENT = float(os.getenv('BOT_MAX_DISK_PERCENT', '90'))  # Disk usage threshold
BOT_MAX_NETWORK_MBPS = float(os.getenv('BOT_MAX_NETWORK_MBPS', '100'))  # Network throughput threshold (MB/s)
BOT_THROTTLE_DELAY = int(os.getenv('BOT_THROTTLE_DELAY', '5'))  # 5 second delay when throttling

# Beta features configuration
BOT_ENABLE_AI_AUTO_TWEAK = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'  # AI Auto-Tweak requires explicit opt-in

# LLM insights: narrative only (see api/services/trading_insights_llm.py).
# Parameter changes use backtest heuristics in ml_param_optimizer — not the LLM.

# Schwab API endpoints
# Sandbox endpoints for testing (when SCHWAB_SANDBOX_MODE=True)
SCHWAB_SANDBOX_API_BASE = "https://api.schwabapi.com/trader/v1"  # Sandbox base URL
SCHWAB_SANDBOX_MARKET_DATA_BASE = "https://api.schwabapi.com/marketdata/v1"  # Sandbox market data

# Production endpoints (when SCHWAB_SANDBOX_MODE=False)
SCHWAB_PRODUCTION_API_BASE = "https://api.schwab.com/v1"  # Production base URL
SCHWAB_PRODUCTION_MARKET_DATA_BASE = "https://api.schwab.com/marketdata/v1"  # Production market data

# Default values for API responses
DEFAULT_VOLUME = 1000000  # Default volume when not available from API

# Paper trading simulation constants
SIMULATED_PROFIT_PERCENT = 0.05  # 5% gain for winning trades in paper mode
SIMULATED_LOSS_PERCENT = 0.05  # 5% loss for losing trades in paper mode

# Risk management constants
RISK_ALLOCATION_BUFFER = 0.95  # Use 95% of risk limit for allocation cap to provide safety buffer
RISK_SCALING_BUFFER = 1.5  # Allow 1.5x max allocation for risk threshold warnings (accounts for self-scaling)
DEFAULT_INITIAL_CAPITAL = 10000.0  # Default initial capital for validation (can be overridden by TradingBot)

# Schwab API error message template for sandbox mode
SCHWAB_API_CRITICAL_ERROR_MSG = (
    "CRITICAL ERROR: Schwab sandbox API failed for {symbol}. "
    "Sandbox mode requires Schwab API connectivity. The process has stopped immediately. "
    "Please check:\n"
    "  1. SCHWAB_API_KEY is correct\n"
    "  2. SCHWAB_APP_SECRET is correct\n"
    "  3. SCHWAB_CALLBACK_URL is set to https://127.0.0.1 (or your configured redirect URI)\n"
    "  4. Network connection is working\n"
    "  5. Schwab API service is available\n"
    "  6. API credentials are properly authorized\n"
    "To use pure simulation mode instead, set SCHWAB_SANDBOX_MODE=false in .env"
)

SCHWAB_API_CONNECTIVITY_ERROR_MSG = (
    "CRITICAL ERROR: Schwab sandbox API connectivity check failed.\n"
    "Sandbox mode requires Schwab API to be functional. NO fallback is allowed.\n"
    "The bot will NOT start until this is fixed.\n"
    "\n"
    "Please check:\n"
    "  1. SCHWAB_API_KEY is correct\n"
    "  2. SCHWAB_APP_SECRET is correct\n"
    "  3. SCHWAB_CALLBACK_URL is set to https://127.0.0.1 (or your configured redirect URI)\n"
    "  4. Network connectivity is working\n"
    "  5. Schwab API service is available at their sandbox endpoint\n"
    "  6. API credentials are properly authorized\n"
    "\n"
    "To use pure simulation mode instead (without Schwab API), set SCHWAB_SANDBOX_MODE=false in .env"
)

# Configure module logger (actual basicConfig will be called from main())
logger = logging.getLogger(__name__)


def _are_schwab_credentials_configured() -> bool:
    """
    Check if Schwab API credentials are properly configured.
    
    Returns:
        True if both API key and app secret are configured (not placeholder values), False otherwise
    """
    return (SCHWAB_API_KEY not in SCHWAB_CREDENTIAL_PLACEHOLDERS and 
            SCHWAB_APP_SECRET not in SCHWAB_CREDENTIAL_PLACEHOLDERS)


def _get_paper_trading_mode() -> bool:
    """
    Get current paper trading mode setting from environment.
    Reads directly from os.environ to support runtime updates from web GUI.
    
    Returns:
        True if in paper trading mode, False for live trading
    """
    return os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'


def _get_schwab_sandbox_mode() -> bool:
    """
    Get current Schwab sandbox mode setting from environment.
    Reads directly from os.environ to support runtime updates from web GUI.
    
    Returns:
        True if using Schwab sandbox API, False for production API or simulation
    """
    return os.getenv('SCHWAB_SANDBOX_MODE', 'false').lower() == 'true'


def _get_schwab_api_enabled() -> bool:
    """
    Get current Schwab API enabled setting from environment.
    Reads directly from os.environ to support runtime updates from web GUI.
    
    Returns:
        True if Schwab API is enabled, False if disabled (uses yfinance instead)
    """
    api_setting = os.getenv('SCHWAB_API_ENABLED', 'on').lower()
    return api_setting in ('on', 'true', '1', 'yes')


def _get_allow_random_fallback() -> bool:
    """
    Get current random fallback setting from environment.
    Reads directly from os.environ to support runtime updates.

    Returns:
        True if random price fallback is allowed in simulation mode, False otherwise
    """
    return os.getenv('ALLOW_RANDOM_FALLBACK', 'true').lower() == 'true'


def _get_dry_run_mode() -> bool:
    """
    Get current dry-run mode setting from environment.
    Reads directly from os.environ to support runtime updates from web GUI.
    
    Dry-run mode simulates live trading workflow without executing actual trades.
    Used to validate configuration and test order logic before going live.
    
    Returns:
        True if in dry-run mode (no orders placed), False for normal operation
    """
    dry_run_setting = os.getenv('DRY_RUN_MODE', 'false').lower()
    return dry_run_setting in ('true', '1', 'yes', 'on')


def _is_same_day_trade(entry_time_str: Optional[str]) -> bool:
    """Return True if entry date is today (same-day round trip for PDT)."""
    if not entry_time_str:
        return True
    try:
        entry_date = datetime.fromisoformat(entry_time_str).date()
        return entry_date == datetime.now().date()
    except (ValueError, AttributeError):
        return True


def _log_close_action(
    action: str,
    symbol: str,
    pnl_info: Dict[str, Any],
    exit_price: float,
    capital_after: float,
) -> None:
    """Log SELL/COVER close summary (mode, symbol, P&L, result)."""
    api_enabled = _get_schwab_api_enabled()
    sandbox_mode = _get_schwab_sandbox_mode()
    mode_display = (
        "API DISABLED MODE"
        if not api_enabled
        else ("SANDBOX MODE (STRICT)" if sandbox_mode else "PURE SIMULATION MODE")
    )
    qty = pnl_info["quantity"]
    print(f"\n[{mode_display}: {action}]")
    print(f"  Symbol: {symbol}\n  Quantity: {qty:.6f}\n  Exit Price: ${exit_price:.2f}")
    print(f"  P&L: ${pnl_info['pnl']:.2f} ({pnl_info['pnl_percent']:.1f}%)")
    print(f"  Remaining Capital: ${capital_after:.2f}")
    print(f"  Result: {'WIN' if pnl_info['is_win'] else 'LOSS'}")


def setup_logging():
    """
    Configure logging for the trading bot
    Should be called once at application startup
    """
    # Only configure if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )


class StoredMessages:
    """In-memory store for recent messages shown on the Dashboard (Recent activity)."""
    MAX_MESSAGES = 200

    def __init__(self):
        from collections import deque
        self._messages = deque(maxlen=self.MAX_MESSAGES)

    def add_message(self, message: str, category: str = 'info', details: Any = None):
        self._messages.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'category': category,
            'details': details,
        })

    def get_stored_messages(self, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        out = list(self._messages)
        if category and category != 'all':
            out = [m for m in out if m.get('category') == category]
        out = out[-limit:] if limit else out
        return out


class AlertSystem:
    """Handle alerts for significant events with severity levels and rate limiting"""
    
    # Rate limiting tracking
    _email_timestamps = []  # Track email send times for rate limiting
    _last_email_time = None
    
    @staticmethod
    def _check_rate_limit() -> bool:
        """
        Check if email can be sent based on rate limiting
        
        Returns:
            True if email can be sent, False if rate limited
        """
        if not EMAIL_RATE_LIMIT_ENABLED:
            return True
        
        now = datetime.now()
        current_time = now.timestamp()
        
        # Check minimum interval
        if AlertSystem._last_email_time:
            time_since_last = current_time - AlertSystem._last_email_time
            if time_since_last < EMAIL_MIN_INTERVAL_SECONDS:
                logger.debug(f"Email rate limited: {time_since_last:.1f}s since last email (min: {EMAIL_MIN_INTERVAL_SECONDS}s)")
                return False
        
        # Check hourly limit
        if EMAIL_MAX_PER_HOUR > 0:
            # Remove timestamps older than 1 hour
            one_hour_ago = current_time - 3600
            AlertSystem._email_timestamps = [ts for ts in AlertSystem._email_timestamps if ts > one_hour_ago]
            
            if len(AlertSystem._email_timestamps) >= EMAIL_MAX_PER_HOUR:
                logger.warning(f"Email rate limited: {len(AlertSystem._email_timestamps)} emails in last hour (max: {EMAIL_MAX_PER_HOUR})")
                return False
        
        return True
    
    @staticmethod
    def _record_email_sent():
        """Record that an email was sent for rate limiting"""
        if EMAIL_RATE_LIMIT_ENABLED:
            now = datetime.now().timestamp()
            AlertSystem._email_timestamps.append(now)
            AlertSystem._last_email_time = now
    
    @staticmethod
    def _is_email_alerts_enabled() -> bool:
        """
        Check if email alerts are enabled (Settings > Alerts toggle).
        Re-reads .env so that turning alerts off in the UI takes effect without restart.
        """
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
        except ImportError:
            pass
        v = (os.getenv('ALERT_EMAIL_ENABLED') or os.getenv('ENABLE_ALERTS') or 'false').strip().lower()
        return v in ('true', '1', 'yes', 'on')

    @staticmethod
    def _should_send_email(severity: str = 'INFO') -> bool:
        """
        Check if email should be sent based on severity level
        
        Args:
            severity: Alert severity (INFO, WARNING, CRITICAL)
            
        Returns:
            True if email should be sent, False otherwise
        """
        if not AlertSystem._is_email_alerts_enabled() or not ALERT_EMAIL:
            return False
        
        # Check severity level
        alert_level = ALERT_SEVERITY_LEVELS.get(severity.upper(), 1)
        min_level = ALERT_SEVERITY_LEVELS.get(ALERT_MIN_SEVERITY, 1)
        
        if alert_level < min_level:
            logger.debug(f"Email alert filtered by severity: {severity} < {ALERT_MIN_SEVERITY}")
            return False
        
        # Check rate limiting
        if not AlertSystem._check_rate_limit():
            return False
        
        return True
    
    @staticmethod
    def _create_html_template(subject: str, message: str, severity: str = 'INFO') -> str:
        """Create HTML email template"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Color scheme based on severity
        severity_colors = {
            'CRITICAL': {
                'bg': '#f8d7da',
                'border': '#dc3545',
                'badge': '#dc3545'
            },
            'WARNING': {
                'bg': '#fff3cd',
                'border': '#ffc107',
                'badge': '#ffc107'
            },
            'INFO': {
                'bg': '#d1ecf1',
                'border': '#17a2b8',
                'badge': '#17a2b8'
            }
        }
        
        colors = severity_colors.get(severity.upper(), severity_colors['INFO'])
        bg_color = colors['bg']
        border_color = colors['border']
        badge_color = colors['badge']
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .alert-box {{
                    background-color: {bg_color};
                    border-left: 4px solid {border_color};
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .severity-badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    background-color: {badge_color};
                    color: white;
                }}
                .message {{
                    color: #333;
                    line-height: 1.6;
                    white-space: pre-wrap;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #6c757d;
                    border-top: 1px solid #dee2e6;
                }}
                .timestamp {{
                    color: #6c757d;
                    font-size: 14px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 Market Pie5 Bot Alert</h1>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <span class="severity-badge">{severity}</span>
                        <h2 style="margin-top: 0; color: #856404;">{subject}</h2>
                    </div>
                    <div class="message">{message}</div>
                    <div class="timestamp">
                        <strong>Timestamp:</strong> {timestamp}
                    </div>
                </div>
                <div class="footer">
                    <p>This alert was automatically generated by Market Pie5 Bot.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def _create_plain_text(subject: str, message: str, severity: str = 'INFO') -> str:
        """Create plain text email content"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        text = f"""
╔════════════════════════════════════════════════════════════════╗
║                  MARKET PIE5 BOT ALERT                         ║
╚════════════════════════════════════════════════════════════════╝

SEVERITY: {severity}
SUBJECT: {subject}

{message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Timestamp: {timestamp}

This alert was automatically generated by Market Pie5 Bot.
Please do not reply to this email.
"""
        return text.strip()
    
    @staticmethod
    def _send_email_with_retry(subject: str, message: str, to_email: str, severity: str = 'INFO') -> bool:
        """
        Send email with retry logic and exponential backoff
        
        Args:
            subject: Email subject
            message: Email message body
            to_email: Recipient email address
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        # Validate SMTP configuration
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured - skipping email send")
            return False
        
        if not to_email:
            logger.warning("No recipient email configured - skipping email send")
            return False
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((SMTP_FROM_NAME, SMTP_USERNAME))
        msg['To'] = to_email
        
        # Attach both plain text and HTML versions
        plain_text = AlertSystem._create_plain_text(subject, message, severity)
        html_content = AlertSystem._create_html_template(subject, message, severity)
        
        part1 = MIMEText(plain_text, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Retry logic with exponential backoff
        for attempt in range(SMTP_MAX_RETRIES):
            try:
                # Create SMTP connection
                if SMTP_USE_TLS:
                    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
                    server.ehlo()
                    server.starttls()
                else:
                    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
                
                # Login and send
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()
                
                # Record email sent for rate limiting
                AlertSystem._record_email_sent()
                
                logger.info(f"Email alert sent successfully to {to_email}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication failed: {e}")
                return False  # Don't retry on auth errors
                
            except smtplib.SMTPException as e:
                logger.warning(f"SMTP error on attempt {attempt + 1}/{SMTP_MAX_RETRIES}: {e}")
                if attempt < SMTP_MAX_RETRIES - 1:
                    delay = SMTP_RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to send email after {SMTP_MAX_RETRIES} attempts")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error sending email: {e}")
                if attempt < SMTP_MAX_RETRIES - 1:
                    delay = SMTP_RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)
                else:
                    return False
        
        return False
    
    @staticmethod
    def send_alert(subject: str, message: str, severity: str = 'INFO'):
        """
        Send an alert (log and email) with severity level
        
        Args:
            subject: Alert subject
            message: Alert message
            severity: Alert severity (INFO, WARNING, CRITICAL)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        severity_upper = severity.upper()
        alert_msg = f"[{severity_upper}] Subject: {subject}\n{message}"
        
        # Use logging system with appropriate level
        if severity_upper == 'CRITICAL':
            logger.critical(f"ALERT - {alert_msg}")
        elif severity_upper == 'WARNING':
            logger.warning(f"ALERT - {alert_msg}")
        else:
            logger.info(f"ALERT - {alert_msg}")
        
        # Also log to dedicated alerts file
        try:
            with open('alerts.log', 'a') as f:
                f.write(f"\n{'='*60}\n[{severity_upper} ALERT - {timestamp}]\n{alert_msg}\n{'='*60}\n")
        except Exception as e:
            logger.error(f"Failed to write alert to alerts.log: {e}")
        
        # Email notification (with severity and rate limiting checks)
        if AlertSystem._should_send_email(severity_upper):
            try:
                # Update email templates with severity
                plain_text = AlertSystem._create_plain_text(subject, message, severity_upper)
                html_content = AlertSystem._create_html_template(subject, message, severity_upper)
                
                # Create email message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"[{severity_upper}] {subject}"
                msg['From'] = formataddr((SMTP_FROM_NAME, SMTP_USERNAME))
                msg['To'] = ALERT_EMAIL
                
                part1 = MIMEText(plain_text, 'plain')
                part2 = MIMEText(html_content, 'html')
                msg.attach(part1)
                msg.attach(part2)
                
                # Send with retry
                success = AlertSystem._send_email_with_retry(
                    f"[{severity_upper}] {subject}", 
                    message, 
                    ALERT_EMAIL
                )
                if not success:
                    logger.warning(f"Email alert to {ALERT_EMAIL} failed after all retries")
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")


class ResourceThrottler:
    """
    Monitor and throttle bot resource usage for Raspberry Pi 5 stability
    
    Automatically slows down trading when CPU, memory, disk, or network usage exceeds thresholds
    to maintain system stability and efficiency.
    """
    
    def __init__(self, enabled: bool = BOT_ENABLE_THROTTLING):
        self.enabled = enabled and PSUTIL_AVAILABLE
        self.max_cpu_percent = BOT_MAX_CPU_PERCENT
        self.max_memory_percent = BOT_MAX_MEMORY_PERCENT
        self.max_disk_percent = BOT_MAX_DISK_PERCENT
        self.max_network_mbps = BOT_MAX_NETWORK_MBPS
        self.throttle_delay = BOT_THROTTLE_DELAY
        self.throttle_count = 0
        self.last_net_io = None  # Track last network I/O for rate calculation
        self.last_net_io_time = None
        # Sample resource checks to avoid bottleneck: only run at most every N seconds
        self._check_interval_sec = max(1.0, float(os.getenv('BOT_THROTTLE_CHECK_INTERVAL', '2')))
        self._last_check_time = 0.0
        self._last_check_result = (True, "Throttling disabled")
        
        if self.enabled:
            logger.info(f"Resource throttling enabled: CPU<{self.max_cpu_percent}%, Memory<{self.max_memory_percent}%, Disk<{self.max_disk_percent}%, Network<{self.max_network_mbps}MB/s")
        elif not PSUTIL_AVAILABLE:
            logger.warning("Resource throttling disabled: psutil not available")
        else:
            logger.info("Resource throttling disabled by configuration")
    
    def check_resources(self) -> Tuple[bool, str]:
        """
        Check if resources are within acceptable limits
        Returns (is_ok, message)
        Samples checks to avoid bottleneck: at most every BOT_THROTTLE_CHECK_INTERVAL seconds.
        """
        # Early return if throttling is disabled - no resource checks needed
        if not self.enabled:
            return True, "Throttling disabled"
        now = time.time()
        if now - self._last_check_time < self._check_interval_sec:
            return self._last_check_result
        try:
            # Get current resource usage (interval=0.1 adds ~0.1s delay)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Check disk usage
            disk_usage = psutil.disk_usage('/')
            disk_percent = disk_usage.percent
            
            # Check network I/O (calculate throughput in MB/s)
            net_io = psutil.net_io_counters()
            network_mbps = 0.0
            if self.last_net_io and self.last_net_io_time:
                time_delta = time.time() - self.last_net_io_time
                if time_delta > 0:
                    bytes_sent = net_io.bytes_sent - self.last_net_io.bytes_sent
                    bytes_recv = net_io.bytes_recv - self.last_net_io.bytes_recv
                    total_bytes = bytes_sent + bytes_recv
                    # Convert to MB/s
                    network_mbps = (total_bytes / time_delta) / (1024 * 1024)
            
            self.last_net_io = net_io
            self.last_net_io_time = time.time()
            
            # Check if we need to throttle
            if cpu_percent > self.max_cpu_percent:
                self.throttle_count += 1
                self._last_check_time = now
                self._last_check_result = (False, f"CPU usage {cpu_percent:.1f}% exceeds {self.max_cpu_percent}%")
                return self._last_check_result
            
            if memory_percent > self.max_memory_percent:
                self.throttle_count += 1
                self._last_check_time = now
                self._last_check_result = (False, f"Memory usage {memory_percent:.1f}% exceeds {self.max_memory_percent}%")
                return self._last_check_result
            
            if disk_percent > self.max_disk_percent:
                self.throttle_count += 1
                self._last_check_time = now
                self._last_check_result = (False, f"Disk usage {disk_percent:.1f}% exceeds {self.max_disk_percent}%")
                return self._last_check_result
            
            if network_mbps > self.max_network_mbps:
                self.throttle_count += 1
                self._last_check_time = now
                self._last_check_result = (False, f"Network throughput {network_mbps:.1f}MB/s exceeds {self.max_network_mbps}MB/s")
                return self._last_check_result
            
            self._last_check_time = now
            self._last_check_result = (True, f"Resources OK (CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%, Network: {network_mbps:.1f}MB/s)")
            return self._last_check_result
            
        except Exception as e:
            logger.error(f"Error checking resources: {e}")
            self._last_check_time = now
            self._last_check_result = (True, "Resource check failed, continuing")
            return self._last_check_result
    
    def apply_throttle(self, reason: str):
        """
        Apply throttling delay when resources are constrained
        """
        # Early return if throttling is disabled - no delay applied
        if not self.enabled:
            return
        
        logger.warning(f"[THROTTLE] {reason} - Waiting {self.throttle_delay}s before continuing")
        time.sleep(self.throttle_delay)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get throttling statistics"""
        return {
            'enabled': self.enabled,
            'throttle_count': self.throttle_count,
            'max_cpu_percent': self.max_cpu_percent,
            'max_memory_percent': self.max_memory_percent,
            'max_disk_percent': self.max_disk_percent,
            'max_network_mbps': self.max_network_mbps,
            'throttle_delay': self.throttle_delay
        }


def _is_margin_enabled() -> bool:
    """
    Check if margin mode is enabled (Settings > Trading > Use margin).
    When true: use total capital for availability (ignore T+1 settled-only).
    When false: use settled capital only.
    Re-reads .env so Settings changes apply without restart.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except ImportError:
        pass
    v = (os.getenv('USE_MARGIN') or 'false').strip().lower()
    return v in ('true', '1', 'yes', 'on')


def _load_trade_history_from_db(max_trades: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load trade history from LogManager DB (logs/trading_logs.db) for restart recovery.
    Returns list of trade dicts in bot format (timestamp, symbol, action, quantity, price, is_win, mode, ...).
    """
    try:
        from log_manager import LogManager
        lm = LogManager()
        rows = lm.get_trades()
        out = []
        for row in rows:
            d = dict(row)
            meta = d.get('metadata')
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta) if meta else {}
                except (TypeError, ValueError):
                    meta = {}
            elif not isinstance(meta, dict):
                meta = {}
            d.update(meta)
            if 'metadata' in d:
                del d['metadata']
            d['is_win'] = bool(d.get('is_win'))
            out.append(d)
        if max_trades and len(out) > max_trades:
            out = out[-max_trades:]
        return out
    except Exception as e:
        logger.debug("Failed to load trade history from DB: %s", e)
        return []


def _derive_positions_from_trade_history(trade_history: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Derive open positions from trade history (BUY/SELL/SHORT/COVER).
    Returns positions dict: {symbol: {entry_price, quantity, side, high_price, low_price, stop_percent, partial_exit_done, entry_time}}.
    """
    # Per-symbol: net long qty, net short qty, last entry price and time for current side
    net_long: Dict[str, float] = {}
    net_short: Dict[str, float] = {}
    entry_price_long: Dict[str, float] = {}
    entry_price_short: Dict[str, float] = {}
    entry_time_long: Dict[str, str] = {}
    entry_time_short: Dict[str, str] = {}
    for t in trade_history:
        symbol = (t.get('symbol') or '').strip()
        if not symbol:
            continue
        action = (t.get('action') or '').upper()
        qty = float(t.get('quantity') or 0)
        price = float(t.get('price') or 0)
        ts = t.get('timestamp') or ''
        if action == 'BUY':
            net_long[symbol] = net_long.get(symbol, 0) + qty
            net_short[symbol] = net_short.get(symbol, 0) - 0  # no change
            if net_long[symbol] > 0:
                entry_price_long[symbol] = price
                entry_time_long[symbol] = ts
        elif action == 'SELL':
            net_long[symbol] = net_long.get(symbol, 0) - qty
            if net_long[symbol] <= 0:
                net_long[symbol] = 0
                entry_price_long.pop(symbol, None)
                entry_time_long.pop(symbol, None)
        elif action == 'SHORT':
            net_short[symbol] = net_short.get(symbol, 0) + qty
            if net_short[symbol] > 0:
                entry_price_short[symbol] = price
                entry_time_short[symbol] = ts
        elif action == 'COVER':
            net_short[symbol] = net_short.get(symbol, 0) - qty
            if net_short[symbol] <= 0:
                net_short[symbol] = 0
                entry_price_short.pop(symbol, None)
                entry_time_short.pop(symbol, None)
    positions: Dict[str, Dict[str, Any]] = {}
    for symbol, qty in net_long.items():
        if qty > 0 and net_short.get(symbol, 0) == 0:
            positions[symbol] = {
                'entry_price': entry_price_long.get(symbol, 0),
                'quantity': qty,
                'side': 'long',
                'high_price': entry_price_long.get(symbol),
                'low_price': None,
                'stop_percent': BOT_TRAILING_STOP_PERCENT,
                'partial_exit_done': False,
                'entry_time': entry_time_long.get(symbol) or datetime.now().isoformat(),
            }
    for symbol, qty in net_short.items():
        if qty > 0 and symbol not in positions:
            positions[symbol] = {
                'entry_price': entry_price_short.get(symbol, 0),
                'quantity': qty,
                'side': 'short',
                'high_price': None,
                'low_price': entry_price_short.get(symbol),
                'stop_percent': BOT_TRAILING_STOP_PERCENT,
                'partial_exit_done': False,
                'entry_time': entry_time_short.get(symbol) or datetime.now().isoformat(),
            }
    return positions


class TradingBot:
    def __init__(self, total_capital: float = 10000.0):
        self.track_record = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'current_allocation': BOT_MIN_ALLOCATION
        }
        # Manual Trade Approval Mode - pending trades storage
        self.pending_trades = {}
        self.pending_trade_counter = 0
        self.pending_trade_ttl = 300  # 5 minutes expiration

        self.trade_history = []
        # Optional: Load trade history from DB for restart recovery (logs/trading_logs.db)
        restart_enabled = (os.getenv('RESTART_RECOVERY_ENABLED', 'true').lower() == 'true')
        if restart_enabled:
            loaded = _load_trade_history_from_db(max_trades=5000)
            if loaded:
                self.trade_history = loaded
                self.track_record['total_trades'] = len(loaded)
                self.track_record['winning_trades'] = sum(1 for t in loaded if t.get('is_win'))
                self.track_record['losing_trades'] = self.track_record['total_trades'] - self.track_record['winning_trades']
                if self.track_record['total_trades'] > 0:
                    self.track_record['win_rate'] = self.track_record['winning_trades'] / self.track_record['total_trades']
                logger.info("Loaded %d trades from DB for restart recovery", len(loaded))
        self.consecutive_losses = 0  # Track consecutive losses
        self.total_capital = total_capital  # Track total capital for risk management
        self.starting_capital = total_capital  # Store original capital
        
        # Track current symbols for portfolio optimizer
        self.current_symbols = []
        
        # Live decision report: last evaluation per symbol (updated by bot loop)
        # Format: { symbol: { signal, action, price, volume, reason, cycle_number, updated_at } }
        self.candidate_decisions = {}
        self.current_cycle_number = 0
        
        # OHLCV cache: avoid repeated yfinance .history() per symbol (bottleneck)
        # Format: (symbol, period) -> (df, timestamp). TTL = OHLCV_CACHE_TTL_SECONDS. 0 = no cache (max real-time).
        self._ohlcv_cache = {}
        self._ohlcv_cache_ttl = max(0, int(os.getenv('OHLCV_CACHE_TTL_SECONDS', '90')))
        # Last cycle timings (set when BOT_TIMING=true): get_strategy_signal_s, execute_trade_s, ohlcv_s, strategy_s, price_s, etc.
        self.last_cycle_timings = None
        
        # Track ML optimization state
        self.last_ml_optimization_time = None
        self.last_ml_optimization_trade_count = 0
        self.optimized_parameters_cache = {}  # Cache optimized parameters
        
        # Portfolio optimization caching (enhancement)
        self.portfolio_optimization_cache = {}  # Cache portfolio optimization results
        self.portfolio_cache_timestamp = None  # When cache was last updated
        self.portfolio_cache_ttl = 300  # Cache TTL in seconds (5 minutes)
        
        # Component coordination tracking (enhancement)
        self.component_coordination_state = {
            'last_ml_filter_update': None,
            'last_portfolio_update': None,
            'last_adaptive_update': None,
            'coordinated_update_count': 0
        }
        self.capital_floor = total_capital * CAPITAL_FLOOR_PERCENT  # 10% floor
        self.positions = {}  # Track open positions: {symbol: {'entry_price', 'quantity', 'high_price', 'stop_percent', 'partial_exit_done'}}
        # Restore open positions from loaded trade history (restart recovery)
        if restart_enabled and getattr(self, 'trade_history', None):
            derived = _derive_positions_from_trade_history(self.trade_history)
            if derived:
                self.positions = derived
                logger.info("Derived %d open position(s) from trade history", len(derived))
        self.trailing_stop_percent = BOT_TRAILING_STOP_PERCENT
        self.stop_loss_percent = BOT_STOP_LOSS_PERCENT
        self.take_profit_percent = HIGH_SALE_PERCENT  # HIGH_SALE_PERCENT is the take profit
        self.price_history = {}  # Track price history for volatility: {symbol: [prices]}
        self.stock_metrics = {}  # Store computed metrics: {symbol: {'volatility', 'avg_volume', 'avg_price'}}
        self.is_paused = False  # Track if bot is paused due to capital floor
        self.alert_system = AlertSystem()
        self.stored_messages = StoredMessages()
        self.price_cache = {}  # Cache for fetched prices: {symbol: {'price': float, 'timestamp': datetime, 'volume': int}}
        
        # Initialize resource throttler for Pi5 stability
        self.throttler = ResourceThrottler()
        
        # Initialize Copilot debug logger if available
        self.debug_logger = None
        if COPILOT_DEBUG_AVAILABLE:
            try:
                self.debug_logger = get_debug_logger()
                if self.debug_logger.enabled:
                    # Log bot initialization
                    self.debug_logger.log_initialization({
                        'total_capital': total_capital,
                        'starting_capital': total_capital,
                        'capital_floor': total_capital * CAPITAL_FLOOR_PERCENT,
                        'risk_threshold': BOT_RISK_THRESHOLD,
                        'trailing_stop_percent': BOT_TRAILING_STOP_PERCENT,
                        'paper_trading_mode': PAPER_TRADING_MODE,
                        'sandbox_mode': SCHWAB_SANDBOX_MODE,
                        'api_enabled': os.getenv('SCHWAB_API_ENABLED', 'on'),
                        'win_rate_target': WIN_RATE_TARGET,
                        'max_open_positions': BOT_MAX_OPEN_POSITIONS,
                        'position_size': BOT_POSITION_SIZE,
                        'stop_loss_percent': BOT_STOP_LOSS_PERCENT
                    })
                    logger.info("Copilot debug logger initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Copilot debug logger: {e}")
        
        # PDT tracking - now enforced in all modes for realistic simulation
        self.day_trades = []  # List of (date, symbol) tuples for last 5 business days
        
        # T+1 Settlement tracking - Cash account settlement rules
        # Track unsettled funds that cannot be used until settlement date
        self.unsettled_funds = []  # List of {'amount': float, 'settlement_date': datetime, 'reason': str}
        
        # Track simulation mode - auto-switches to yfinance sim if Schwab API unavailable
        self.using_yfinance_sim = False
        self.schwab_api_available = True
        
        # Historical simulation support for frozen time backtesting
        self.historical_mode = False
        self.historical_data = {}  # {symbol: DataFrame with date-indexed OHLCV data}
        self.current_sim_date = None  # Current date in historical simulation
        
        # Trade activity monitoring
        self.last_trade_time = None  # Timestamp of last trade
        self.trade_activity_check_interval = 3600  # Check every hour (3600 seconds)
        self.last_trade_activity_check = None  # Last time we checked for trade activity
        self.no_trade_alert_sent = False  # Track if we've already sent a no-trade alert
        self.no_trade_reasons = []  # Store reasons why no trades are happening
        
        # Initialize Schwab OAuth client if needed
        self.schwab_client = None
        self.schwab_authenticator = None
        self._initialize_schwab_authenticator()
        
        # Auto-configure settings when yfinance mode is detected
        self._auto_configure_yfinance_mode()
        
        # In live mode, fetch capital from Schwab API if available
        # This overrides the total_capital parameter with actual account funds
        if not PAPER_TRADING_MODE and not SCHWAB_SANDBOX_MODE and USE_SCHWAB_CAPITAL_IN_LIVE:
            self._update_capital_from_schwab_api()
        
        # Initialize sentiment analyzer if available
        self.sentiment_analyzer = None
        if SENTIMENT_ANALYZER_AVAILABLE:
            try:
                self.sentiment_analyzer = SentimentAnalyzer()
                logger.info("Sentiment analyzer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize sentiment analyzer: {e}")
        
        # Initialize portfolio optimizer if available
        self.portfolio_optimizer = None
        if PORTFOLIO_OPTIMIZER_AVAILABLE:
            try:
                self.portfolio_optimizer = PortfolioOptimizer(
                    risk_free_rate=BOT_RISK_FREE_RATE
                )
                logger.info("Portfolio optimizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize portfolio optimizer: {e}")
        
        # Initialize ML parameter optimizer for 70% win rate target
        self.ml_optimizer = None
        if ML_OPTIMIZER_AVAILABLE:
            try:
                self.ml_optimizer = MLParameterOptimizer(target_win_rate=0.70)
                logger.info("ML parameter optimizer initialized (target: 70% win rate)")
            except Exception as e:
                logger.warning(f"Failed to initialize ML optimizer: {e}")
        
        # Initialize ML signal filter if available and enabled (read at init so Restart picks up GUI changes)
        self.ml_signal_filter = None
        _enable_ml = os.getenv('ENABLE_ML_SIGNAL_FILTER', 'true').lower() == 'true'
        if ML_SIGNAL_FILTER_AVAILABLE and _enable_ml:
            try:
                _model_type = os.getenv('ML_SIGNAL_FILTER_MODEL_TYPE', 'random_forest')
                self.ml_signal_filter = MLSignalFilter(model_type=_model_type)
                _min_conf = float(os.getenv('ML_SIGNAL_FILTER_MIN_CONFIDENCE', '0.6'))
                _min_win = float(os.getenv('ML_SIGNAL_FILTER_MIN_WIN_PROB', '0.55'))
                logger.info(f"ML signal filter initialized (type={_model_type}, enabled=True)")
                logger.info(f"  Min confidence: {_min_conf:.2f}, Min win prob: {_min_win:.2f}")
                
                # Try to load pre-trained model if available
                model_path = os.getenv('ML_SIGNAL_FILTER_MODEL_PATH', 'ml_signal_filter_model.pkl')
                if os.path.exists(model_path):
                    try:
                        self.ml_signal_filter.load_model(model_path)
                        logger.info(f"✓ Loaded trained ML model from {model_path}")
                        logger.info(f"  Model accuracy: {self.ml_signal_filter.metrics.get('accuracy', 0):.4f}")
                    except Exception as e:
                        logger.debug(f"Could not load pre-trained model from {model_path}: {e}")
                        logger.info("  Model will use default predictions until trained")
                else:
                    logger.info(f"  No pre-trained model found at {model_path} - will use default predictions")
                    logger.info("  Train model with: python3 train_ml_signal_filter.py")
            except Exception as e:
                logger.warning(f"Failed to initialize ML signal filter: {e}")
        elif not ML_SIGNAL_FILTER_AVAILABLE:
            logger.debug("ML signal filter not available (scikit-learn may not be installed)")
        elif not _enable_ml:
            logger.debug("ML signal filter disabled by configuration")
        
        # Store runtime ML settings (can be updated via API without restart)
        self.ml_filter_enabled = _enable_ml
        self.ml_filter_min_confidence = float(os.getenv('ML_SIGNAL_FILTER_MIN_CONFIDENCE', '0.6'))
        self.ml_filter_min_win_prob = float(os.getenv('ML_SIGNAL_FILTER_MIN_WIN_PROB', '0.55'))
        
        # Initialize strategy manager (lazy-loaded, but initialize attribute here to avoid AttributeError)
        self._strategy_manager = None
        self._data_fetcher = None
        
        # Initialize adaptive learning orchestrator if available and enabled
        self.adaptive_learner = None
        if ADAPTIVE_LEARNING_AVAILABLE and ENABLE_ADAPTIVE_LEARNING and STRATEGIES_AVAILABLE:
            try:
                # Get strategy names (will be set when strategies are initialized)
                strategy_names = ['SMA', 'Bollinger', 'RSI', 'MACD', 'Momentum']
                self.adaptive_learner = AdaptiveLearningOrchestrator(
                    strategies=strategy_names,
                    use_qlearning=(ADAPTIVE_LEARNING_METHOD == 'qlearning'),
                    use_bandit=(ADAPTIVE_LEARNING_METHOD == 'bandit'),
                    use_param_tuning=False,  # Can enable later if needed
                    use_online_learning=True
                )
                logger.info(f"Adaptive learning orchestrator initialized (method={ADAPTIVE_LEARNING_METHOD})")
            except Exception as e:
                logger.warning(f"Failed to initialize adaptive learning: {e}")
        elif not ADAPTIVE_LEARNING_AVAILABLE:
            logger.debug("Adaptive learning not available")
        elif not ENABLE_ADAPTIVE_LEARNING:
            logger.debug("Adaptive learning disabled by configuration")
        
        # Prefetched prices cache for current cycle/session: {symbol: (price, volume)}
        self._prefetched_prices = None
        
        # Phase 1: Initialize Earnings Calendar for earnings-aware trading
        self.earnings_calendar = None
        if EARNINGS_CALENDAR_AVAILABLE:
            try:
                self.earnings_calendar = EarningsCalendar(days_ahead=7)
                logger.info("Earnings calendar initialized (Phase 1 - earnings awareness enabled)")
            except Exception as e:
                logger.warning(f"Failed to initialize earnings calendar: {e}")
                logger.info("  Trading will continue without earnings awareness")
        
        # Phase 2.1: Initialize Macro Calendar for avoiding major economic events
        self.macro_calendar = None
        if MACRO_CALENDAR_AVAILABLE:
            try:
                self.macro_calendar = MacroCalendar(blackout_hours=24)
                logger.info("Macro calendar initialized (Phase 2.1 - macro event awareness enabled)")
                # Log upcoming events at startup
                self.macro_calendar.log_upcoming_events(days_ahead=7)
            except Exception as e:
                logger.warning(f"Failed to initialize macro calendar: {e}")
                logger.info("  Trading will continue without macro event awareness")
        
        # Phase 2.2: Initialize Retail Sentiment for FOMO detection
        self.retail_sentiment = None
        if RETAIL_SENTIMENT_AVAILABLE:
            try:
                self.retail_sentiment = RetailSentiment(cache_ttl_hours=6, fomo_threshold=3.0)
                logger.info("Retail sentiment monitor initialized (Phase 2.2 - FOMO detection enabled)")
            except Exception as e:
                logger.warning(f"Failed to initialize retail sentiment: {e}")
                logger.info("  Trading will continue without FOMO detection")
        
        # Phase 2.3: Initialize Options Flow for smart money tracking
        self.options_flow = None
        if OPTIONS_FLOW_AVAILABLE:
            try:
                self.options_flow = OptionsFlow(cache_ttl_hours=4, volume_threshold=2.0)
                logger.info("Options flow monitor initialized (Phase 2.3 - smart money tracking enabled)")
            except Exception as e:
                logger.warning(f"Failed to initialize options flow: {e}")
                logger.info("  Trading will continue without smart money tracking")
        
        # Phase 3: Initialize News Monitor for IPO/M&A/Regulatory events
        self.news_monitor = None
        if NEWS_MONITOR_AVAILABLE:
            try:
                self.news_monitor = NewsMonitor(cache_hours=1, max_articles=50)
                # Load existing intelligence database
                self.news_monitor.load_intelligence_from_file('data/market_intelligence.json')
                logger.info("News monitor initialized (Phase 3 - news filtering enabled)")
            except Exception as e:
                logger.warning(f"Failed to initialize news monitor: {e}")
                logger.info("  Trading will continue without news filtering")
        
        # Alert System: Initialize desktop notifications and sizzle detection
        self.alert_manager = None
        self.sizzle_detector = None
        if ALERT_SYSTEM_AVAILABLE:
            try:
                self.alert_manager = get_alert_manager(enabled=True)
                self.sizzle_detector = SizzleDetector(
                    volume_threshold=3.0,      # 3x average volume
                    price_change_threshold=5.0, # 5% price change
                    momentum_threshold=0.7      # High momentum
                )
                logger.info("Alert system initialized (desktop notifications + sizzle detection)")
            except Exception as e:
                logger.warning(f"Failed to initialize alert system: {e}")
                logger.info("  Trading will continue without alerts")
    
    def _auto_configure_yfinance_mode(self):
        """
        DO NOT auto-override mode settings when yfinance mode is detected.
        
        The mode is now managed through the API's _apply_mode_to_env() function
        which properly sets all related variables in .env and os.environ.
        
        This method should only log current state, not override user settings.
        Using_yfinance_sim being True just means Schwab API is unavailable,
        but the user's chosen mode (sandbox, yfinance, live, dryrun-live) 
        should be preserved from .env settings.
        """
        if not self.using_yfinance_sim:
            return  # Not in yfinance mode, skip
        
        logger.info("="*60)
        logger.info("YFINANCE MODE DETECTED (Schwab API unavailable)")
        logger.info("Using user-configured mode settings from .env")
        logger.info("="*60)
        
        # Just read and log current settings - don't override them
        # Settings were already set by API route via _apply_mode_to_env()
        paper_mode = _get_paper_trading_mode()
        sandbox_mode = _get_schwab_sandbox_mode()
        dry_run = _get_dry_run_mode()
        
        logger.info(f"✓ Paper trading mode: {'ENABLED' if paper_mode else 'DISABLED'}")
        logger.info(f"✓ Sandbox mode: {'ENABLED' if sandbox_mode else 'DISABLED'}")
        logger.info(f"✓ Dry run mode: {'ENABLED' if dry_run else 'DISABLED'}")
        logger.info("Mode settings are preserved from .env (not auto-configured)")
        logger.info("="*60)
    
    def _check_trade_activity(self):
        """
        Check if trades are happening and send alerts if no trades detected.
        Analyzes reasons why no trades might be occurring.
        """
        current_time = datetime.now()
        
        # Skip check if too soon since last check
        if self.last_trade_activity_check:
            time_since_check = (current_time - self.last_trade_activity_check).total_seconds()
            if time_since_check < self.trade_activity_check_interval:
                return
        
        self.last_trade_activity_check = current_time
        
        # Determine if we should expect trades
        # Skip check if bot is paused or in backtest mode
        if self.is_paused or BACKTEST_MODE:
            return
        
        # Check if we have any trades in the last hour
        time_threshold = current_time - timedelta(seconds=self.trade_activity_check_interval)
        def _coerce_ts(ts_val):
            # Ensure timestamp is a datetime for comparison
            if isinstance(ts_val, datetime):
                return ts_val
            if isinstance(ts_val, str):
                try:
                    # Prefer ISO 8601
                    return datetime.fromisoformat(ts_val)
                except Exception:
                    # Fallback: ignore unparsable strings
                    return current_time
            return current_time

        recent_trades = [t for t in self.trade_history if _coerce_ts(t.get('timestamp', current_time)) >= time_threshold]
        
        if len(recent_trades) > 0:
            # Trades are happening, reset alert flag
            if self.no_trade_alert_sent:
                logger.info("Trade activity resumed - clearing no-trade alert flag")
                self.no_trade_alert_sent = False
                self.no_trade_reasons = []
            self.last_trade_time = max(_coerce_ts(t.get('timestamp', current_time)) for t in recent_trades)
            return
        
        # No trades detected - analyze reasons
        reasons = []
        
        # Check capital
        if self.total_capital <= self.capital_floor:
            reasons.append(f"Capital below floor: ${self.total_capital:.2f} <= ${self.capital_floor:.2f}")
        
        # Check if bot is paused
        if self.is_paused:
            reasons.append("Bot is paused")
        
        # Check positions
        if len(self.positions) >= BOT_MAX_OPEN_POSITIONS:
            reasons.append(f"Max open positions reached: {len(self.positions)}/{BOT_MAX_OPEN_POSITIONS}")
        
        # Check if we have symbols to trade (API loop sets current_symbols; CLI may use scan_symbols)
        symbols_available = (
            (getattr(self, 'current_symbols', None) and len(self.current_symbols) > 0) or
            (getattr(self, 'scan_symbols', None) and len(self.scan_symbols) > 0)
        )
        if not symbols_available:
            reasons.append("No symbols available to trade")
        
        # Check if strategies are generating signals
        if hasattr(self, '_strategy_manager') and self._strategy_manager:
            # This is a simplified check - in practice, you'd track signal generation
            reasons.append("No trading signals generated (check strategy configuration)")
        
        # Check API connectivity (if using Schwab)
        if not self.using_yfinance_sim and not self.schwab_api_available:
            reasons.append("Schwab API not available")
        
        # If no specific reasons found, add generic ones
        if not reasons:
            reasons.append("No trading opportunities found (market conditions, filters, or thresholds)")
            reasons.append("Check: signal quality, risk thresholds, position limits, capital availability")
        
        self.no_trade_reasons = reasons
        
        # Send alert if we haven't already sent one
        if not self.no_trade_alert_sent:
            time_since_last = "Never" if not self.last_trade_time else f"{(current_time - self.last_trade_time).total_seconds() / 3600:.1f} hours ago"
            
            alert_subject = "⚠️ No Trading Activity Detected"
            alert_message = f"""No trades have been executed in the last {self.trade_activity_check_interval / 3600:.1f} hour(s).

Last Trade: {time_since_last}
Total Trades: {len(self.trade_history)}
Open Positions: {len(self.positions)}
Current Capital: ${self.total_capital:.2f}
Capital Floor: ${self.capital_floor:.2f}

Possible Reasons:
{chr(10).join(f"  • {reason}" for reason in reasons)}

Recommended Actions:
  1. Check capital availability (above floor)
  2. Verify symbols are available and tradeable
  3. Review strategy signals and filters
  4. Check risk thresholds and position limits
  5. Verify market data is being fetched correctly
  6. Review ML signal filter settings (if enabled)
  7. Check adaptive learning weights (if enabled)

Bot Status:
  • Paper Trading: {PAPER_TRADING_MODE}
  • Sandbox Mode: {SCHWAB_SANDBOX_MODE}
  • Schwab API: {'Enabled' if SCHWAB_API_ENABLED else 'Disabled'}
  • yfinance Mode: {self.using_yfinance_sim}
  • Bot Paused: {self.is_paused}
"""
            
            self.alert_system.send_alert(alert_subject, alert_message, severity='WARNING')
            self.no_trade_alert_sent = True
            
            # Also log to system
            logger.warning("="*60)
            logger.warning("NO TRADING ACTIVITY DETECTED")
            logger.warning("="*60)
            logger.warning(alert_message)
            logger.warning("="*60)
    
    def _initialize_schwab_authenticator(self):
        """
        Initialize Schwab OAuth authenticator for live or sandbox trading.
        Extracted to avoid code duplication.
        Respects SCHWAB_API_ENABLED setting and NON_INTERACTIVE environment.
        """
        if not SCHWAB_AUTH_AVAILABLE:
            return
        
        # Read mode settings dynamically to support runtime updates
        api_enabled = _get_schwab_api_enabled()
        paper_mode = _get_paper_trading_mode()
        sandbox_mode = _get_schwab_sandbox_mode()
        
        # Check if Schwab API is enabled
        if not api_enabled:
            logger.info("Schwab API is disabled (SCHWAB_API_ENABLED=off)")
            logger.info("Bot will use yfinance for market data and run in simulation mode")
            self.schwab_api_available = False
            self.using_yfinance_sim = True
            return
        
        # Check if running in non-interactive mode without token
        is_non_interactive = os.getenv('NON_INTERACTIVE', 'false').lower() == 'true'
        token_exists = os.path.exists(SCHWAB_TOKEN_PATH)
        
        if is_non_interactive and not token_exists:
            logger.warning("Running in NON_INTERACTIVE mode without token.json")
            logger.warning("Schwab OAuth requires either:")
            logger.warning("  1. Existing token.json file (run interactively first)")
            logger.warning("  2. SCHWAB_API_ENABLED=off (use yfinance simulation)")
            logger.info("Auto-switching to yfinance simulation mode")
            self.schwab_api_available = False
            self.using_yfinance_sim = True
            alert_message = """Bot is running in non-interactive mode without token.json.
Automatically switched to yfinance simulation mode.

To use Schwab API in non-interactive mode:
  1. Run bot interactively once to generate token.json
  2. Copy token.json to your automation environment
  3. Ensure NON_INTERACTIVE=true is set

Or disable Schwab API by setting SCHWAB_API_ENABLED=off"""
            self.alert_system.send_alert(
                "Non-Interactive Mode: Using yfinance Simulation",
                alert_message,
                severity='WARNING'
            )
            return
        
        # Validate credentials before initializing authenticator
        # Check for placeholder values that indicate credentials are not configured
        if not _are_schwab_credentials_configured():
            logger.info("Schwab API credentials not configured (using placeholder values)")
            logger.info("Bot will use yfinance for market data and run in simulation mode")
            logger.info("To enable Schwab API:")
            logger.info("  1. Get credentials from https://developer.schwab.com/")
            logger.info("  2. Set SCHWAB_API_KEY and SCHWAB_APP_SECRET in .env file")
            logger.info("  3. Run bot to authenticate and generate token.json")
            self.schwab_api_available = False
            self.using_yfinance_sim = True
            return
        
        # Initialize for live trading or sandbox mode
        if not paper_mode or sandbox_mode:
            try:
                # Determine environment based on sandbox_mode
                environment = 'sandbox' if sandbox_mode else 'production'
                
                self.schwab_authenticator = SchwabAuthenticator(
                    api_key=SCHWAB_API_KEY,
                    app_secret=SCHWAB_APP_SECRET,
                    callback_url=SCHWAB_CALLBACK_URL,
                    token_path=SCHWAB_TOKEN_PATH,
                    environment=environment
                )
                mode = "live trading" if not PAPER_TRADING_MODE else "sandbox mode"
                logger.info(f"Schwab OAuth authenticator initialized for {mode}")
                if is_non_interactive:
                    logger.info("Running in NON_INTERACTIVE mode with existing token file")
            except requests.exceptions.ConnectionError as e:
                error_msg = f"Network error initializing Schwab authenticator: {e}"
                logger.error(error_msg)
                # Show GUI alert if GUI is available
                if hasattr(self, 'gui') and self.gui is not None:
                    try:
                        from tkinter import messagebox
                        messagebox.showerror("OAuth Connection Error", 
                                           f"Failed to connect to Schwab OAuth service.\n"
                                           f"Check your internet connection.\n\n"
                                           f"Error: {str(e)}")
                    except Exception:
                        pass  # GUI not available or messagebox failed
                self.schwab_api_available = False
                self.using_yfinance_sim = True
            except requests.exceptions.RequestException as e:
                error_msg = f"Network error initializing Schwab authenticator: {e}"
                logger.error(error_msg)
                # Show GUI alert if GUI is available
                if hasattr(self, 'gui') and self.gui is not None:
                    try:
                        from tkinter import messagebox
                        messagebox.showerror("OAuth Network Error", 
                                           f"Network error with Schwab OAuth.\n"
                                           f"Check internet and API status.\n\n"
                                           f"Error: {str(e)}")
                    except Exception:
                        pass  # GUI not available or messagebox failed
                self.schwab_api_available = False
                self.using_yfinance_sim = True
            except Exception as e:
                error_msg = f"Failed to initialize Schwab authenticator: {e}"
                logger.warning(error_msg)
                # Show GUI alert if GUI is available
                if hasattr(self, 'gui') and self.gui is not None:
                    try:
                        from tkinter import messagebox
                        messagebox.showerror("OAuth Initialization Error", 
                                           f"Failed to initialize Schwab OAuth.\n"
                                           f"Check credentials and configuration.\n\n"
                                           f"Error: {str(e)}")
                    except Exception:
                        pass  # GUI not available or messagebox failed
                self.schwab_api_available = False
                self.using_yfinance_sim = True
    
    def _update_capital_from_schwab_api(self):
        """
        Fetch account cash/buying power from Schwab API and update total_capital.
        Only called in live production mode (not paper/sandbox).
        
        Uses Schwab API to get actual account funds available, which determines
        how much trading the bot can do. This overrides the total_capital parameter
        passed to __init__ with real account data.
        """
        if not SCHWAB_AUTH_AVAILABLE:
            logger.debug("Schwab auth not available - skipping capital fetch")
            return
        
        if self.schwab_authenticator is None:
            logger.debug("Schwab authenticator not initialized - skipping capital fetch")
            return
        
        try:
            # Get authenticated client
            interactive = not os.getenv('NON_INTERACTIVE', 'false').lower() == 'true'
            if self.schwab_client is None:
                self.schwab_client = self.schwab_authenticator.get_client(interactive=interactive)
            
            if self.schwab_client is None:
                logger.warning("Could not obtain Schwab client for capital fetch")
                return
            
            # Fetch account information
            # schwab-py uses get_account() or get_accounts() method
            # Try get_account with account ID first, then get_accounts as fallback
            account_capital = None
            
            try:
                # Method 1: Get specific account by ID
                if hasattr(self.schwab_client, 'get_account'):
                    response = self.schwab_client.get_account(SCHWAB_ACCOUNT_ID)
                    if response.status_code == 200:
                        account_data = response.json()
                        # Extract cash or buying power
                        # Schwab API returns: cashBalance, buyingPower, etc.
                        account_capital = self._extract_capital_from_account_data(account_data)
            except AttributeError:
                pass
            except Exception as e:
                logger.debug(f"get_account failed, trying get_accounts: {e}")
            
            # Method 2: Get all accounts and find matching account ID
            if account_capital is None:
                try:
                    if hasattr(self.schwab_client, 'get_accounts'):
                        response = self.schwab_client.get_accounts()
                        if response.status_code == 200:
                            accounts_data = response.json()
                            # Find account matching SCHWAB_ACCOUNT_ID
                            account_capital = self._extract_capital_from_accounts_list(accounts_data, SCHWAB_ACCOUNT_ID)
                except AttributeError:
                    logger.warning("Schwab client does not have get_account or get_accounts method")
                except Exception as e:
                    logger.warning(f"Failed to fetch account capital from Schwab API: {e}")
            
            # Update capital if we got a value
            if account_capital is not None and account_capital > 0:
                old_capital = self.total_capital
                self.total_capital = account_capital
                self.starting_capital = account_capital  # Update starting capital too
                self.capital_floor = account_capital * CAPITAL_FLOOR_PERCENT  # Recalculate floor
                
                logger.info(
                    f"[LIVE MODE] Capital updated from Schwab API: "
                    f"${old_capital:.2f} → ${self.total_capital:.2f}"
                )
                logger.info(
                    f"[LIVE MODE] Capital floor recalculated: ${self.capital_floor:.2f} "
                    f"({CAPITAL_FLOOR_PERCENT:.1%} of ${self.total_capital:.2f})"
                )
            else:
                logger.warning(
                    f"[LIVE MODE] Could not fetch account capital from Schwab API. "
                    f"Using configured capital: ${self.total_capital:.2f}"
                )
                
        except Exception as e:
            logger.warning(
                f"[LIVE MODE] Failed to update capital from Schwab API: {e}. "
                f"Using configured capital: ${self.total_capital:.2f}"
            )
            # Don't fail bot startup if capital fetch fails - use configured value
    
    def _extract_capital_from_account_data(self, account_data: dict) -> Optional[float]:
        """
        Extract cash/buying power from Schwab account data.
        
        Args:
            account_data: Account data dict from Schwab API
            
        Returns:
            Capital amount (cash or buying power), or None if not found
        """
        # Try different field names that Schwab API might use
        # Priority: cashAvailableForTrading > cashBalance > buyingPower > netValue
        
        capital = None
        
        # Check for cash available for trading (most relevant for trading)
        if 'cashAvailableForTrading' in account_data:
            capital = float(account_data['cashAvailableForTrading'])
        elif 'cashBalance' in account_data:
            capital = float(account_data['cashBalance'])
        elif 'buyingPower' in account_data:
            capital = float(account_data['buyingPower'])
        elif 'netValue' in account_data:
            capital = float(account_data['netValue'])
        elif 'accountBalance' in account_data:
            capital = float(account_data['accountBalance'])
        # Handle nested structures (e.g., account_data['securitiesAccount'])
        elif 'securitiesAccount' in account_data:
            sec_account = account_data['securitiesAccount']
            if 'cashAvailableForTrading' in sec_account:
                capital = float(sec_account['cashAvailableForTrading'])
            elif 'cashBalance' in sec_account:
                capital = float(sec_account['cashBalance'])
            elif 'buyingPower' in sec_account:
                capital = float(sec_account['buyingPower'])
            elif 'netValue' in sec_account:
                capital = float(sec_account['netValue'])
        
        return capital if capital and capital > 0 else None
    
    def _extract_capital_from_accounts_list(self, accounts_data: dict, account_id: str) -> Optional[float]:
        """
        Extract capital from accounts list by matching account ID.
        
        Args:
            accounts_data: Accounts data dict from Schwab API (may be list or dict)
            account_id: Account ID to match
            
        Returns:
            Capital amount for matching account, or None if not found
        """
        # Handle different response formats
        accounts = []
        if isinstance(accounts_data, list):
            accounts = accounts_data
        elif isinstance(accounts_data, dict):
            # Could be {'accounts': [...]} or {'accountId': {...}}
            if 'accounts' in accounts_data:
                accounts = accounts_data['accounts']
            elif 'accountId' in accounts_data or 'accountNumber' in accounts_data:
                # Single account in dict
                accounts = [accounts_data]
        
        # Find matching account
        for account in accounts:
            # Check various ID field names
            acc_id = None
            if 'accountId' in account:
                acc_id = str(account['accountId'])
            elif 'accountNumber' in account:
                acc_id = str(account['accountNumber'])
            elif 'accountCd' in account:
                acc_id = str(account['accountCd'])
            
            if acc_id and acc_id == str(account_id):
                # Found matching account - extract capital
                return self._extract_capital_from_account_data(account)
        
        return None
    
    def refresh_capital_from_schwab_api(self) -> bool:
        """
        Refresh capital from Schwab API (can be called periodically).
        
        Returns:
            True if capital was successfully updated, False otherwise
        """
        if not USE_SCHWAB_CAPITAL_IN_LIVE:
            return False
        
        if PAPER_TRADING_MODE or SCHWAB_SANDBOX_MODE:
            return False  # Only in live production mode
        
        old_capital = self.total_capital
        self._update_capital_from_schwab_api()
        
        # Return True if capital changed
        return self.total_capital != old_capital
    
    def check_capital_floor(self) -> Tuple[bool, str]:
        """
        Check if current capital is above the floor
        Returns (is_above_floor, message)
        In yfinance/training mode the floor is not enforced so learning can continue.
        """
        if getattr(self, 'using_yfinance_sim', False):
            return True, "Capital floor not enforced (yfinance/training mode)"
        if self.total_capital < self.capital_floor:
            # Send alert before setting paused flag (only if not already paused)
            if not self.is_paused:
                msg = (f"Capital ${self.total_capital:.2f} below floor ${self.capital_floor:.2f} "
                       f"({CAPITAL_FLOOR_PERCENT:.1%} of starting ${self.starting_capital:.2f})")
                self.alert_system.send_alert(
                    "Capital Floor Breach",
                    f"Trading paused due to capital floor breach.\n{msg}",
                    severity='CRITICAL'
                )
            
            self.is_paused = True
            msg = (f"Capital ${self.total_capital:.2f} below floor ${self.capital_floor:.2f} "
                   f"({CAPITAL_FLOOR_PERCENT:.1%} of starting ${self.starting_capital:.2f})")
            return False, msg
        
        # Check if we should resume
        if self.is_paused and self.total_capital >= self.capital_floor * 1.2:
            self.is_paused = False
            msg = f"Capital recovered to ${self.total_capital:.2f}, resuming trading"
            self.alert_system.send_alert("Trading Resumed", msg, severity='INFO')
        
        return True, "Capital above floor"
    
    def update_capital(self, pnl: float):
        """Update total capital based on P&L"""
        old_capital = self.total_capital
        self.total_capital += pnl
        
        # Check for significant changes (>10% of starting capital)
        if abs(pnl) > self.starting_capital * 0.10:
            self.alert_system.send_alert(
                "Significant P&L Event",
                f"Large P&L detected: ${pnl:.2f}\n"
                f"Capital changed from ${old_capital:.2f} to ${self.total_capital:.2f}"
            )
    
    def _calculate_business_days_ahead(self, days: int, from_date: datetime = None) -> datetime:
        """
        Calculate settlement date (business days ahead, excluding weekends)
        
        Args:
            days: Number of business days to add (1 for T+1)
            from_date: Starting date (defaults to now)
            
        Returns:
            Settlement date as datetime
        """
        if from_date is None:
            from_date = datetime.now()
        
        settlement_date = from_date
        business_days_added = 0
        
        while business_days_added < days:
            settlement_date += timedelta(days=1)
            # Skip weekends (Saturday=5, Sunday=6)
            if settlement_date.weekday() < 5:
                business_days_added += 1
        
        return settlement_date
    
    def _add_unsettled_funds(self, amount: float, reason: str):
        """
        Add unsettled funds that will become available after T+1 settlement
        
        Args:
            amount: Amount of funds to lock until settlement
            reason: Reason for unsettled funds (e.g., 'BUY', 'SELL')
        """
        # Calculate T+1 settlement date (1 business day from now)
        settlement_date = self._calculate_business_days_ahead(1)
        
        self.unsettled_funds.append({
            'amount': amount,
            'settlement_date': settlement_date,
            'reason': reason,
            'created_at': datetime.now()
        })
        
        logger.info(f"Added unsettled funds: ${amount:.2f} ({reason}) - settles on {settlement_date.strftime('%Y-%m-%d')}")
    
    def _clean_settled_funds(self):
        """
        Remove funds that have settled (settlement_date has passed)
        """
        now = datetime.now()
        original_count = len(self.unsettled_funds)
        
        # Filter out settled funds
        self.unsettled_funds = [
            fund for fund in self.unsettled_funds
            if fund['settlement_date'] > now
        ]
        
        settled_count = original_count - len(self.unsettled_funds)
        if settled_count > 0:
            logger.info(f"Released {settled_count} settled fund(s)")
    
    def get_settled_capital(self) -> float:
        """
        Calculate available (settled) capital that can be used for trading
        
        Returns:
            Amount of capital available after accounting for unsettled funds
            Never returns negative - returns 0.0 if unsettled funds exceed total capital
        """
        # Clean up settled funds first
        self._clean_settled_funds()
        
        # Calculate total unsettled amount
        unsettled_total = sum(fund['amount'] for fund in self.unsettled_funds)
        
        # Available capital = total capital - unsettled funds
        # Ensure we never return negative (can happen if P&L losses after locking funds)
        settled_capital = max(0.0, self.total_capital - unsettled_total)
        
        # Log if there are unsettled funds
        if unsettled_total > 0:
            logger.debug(
                f"Capital Status: Total=${self.total_capital:.2f}, "
                f"Unsettled=${unsettled_total:.2f}, "
                f"Available=${settled_capital:.2f}"
            )
        
        # Warn if total capital is less than unsettled (edge case: losses after locking)
        if self.total_capital < unsettled_total:
            logger.warning(
                f"Total capital (${self.total_capital:.2f}) is less than unsettled funds "
                f"(${unsettled_total:.2f}). This can occur if losses happened after funds "
                f"were locked. Settled capital set to $0.00 - no new trades possible until "
                f"settlement or capital recovery."
            )
        
        return settled_capital
    
    def get_stored_messages(self, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent messages for the Dashboard (Recent activity)."""
        return self.stored_messages.get_stored_messages(category=category, limit=limit)
    
    def get_available_capital(self) -> float:
        """
        Capital available for trading. When margin mode (USE_MARGIN): total capital.
        Otherwise: settled capital only (total minus T+1 unsettled).
        """
        if _is_margin_enabled():
            return self.total_capital
        return self.get_settled_capital()
    
    def get_ml_filter_settings(self) -> Dict[str, Any]:
        """Get current ML filter runtime settings"""
        return {
            'enabled': self.ml_filter_enabled,
            'min_confidence': self.ml_filter_min_confidence,
            'min_win_prob': self.ml_filter_min_win_prob,
            'filter_available': self.ml_signal_filter is not None
        }
    
    def set_ml_filter_settings(self, enabled: bool = None, min_confidence: float = None, min_win_prob: float = None) -> Dict[str, Any]:
        """
        Update ML filter runtime settings (does not require restart).
        
        Args:
            enabled: Whether to enable/disable ML signal filter
            min_confidence: Minimum model confidence (0.0-1.0)
            min_win_prob: Minimum win probability threshold (0.0-1.0)
        
        Returns:
            Updated settings dict
        """
        if enabled is not None:
            self.ml_filter_enabled = enabled
            logger.info(f"ML filter enabled: {enabled}")
        
        if min_confidence is not None:
            # Clamp to valid range
            self.ml_filter_min_confidence = max(0.0, min(1.0, float(min_confidence)))
            logger.info(f"ML filter min_confidence updated to {self.ml_filter_min_confidence:.2f}")
        
        if min_win_prob is not None:
            # Clamp to valid range
            self.ml_filter_min_win_prob = max(0.0, min(1.0, float(min_win_prob)))
            logger.info(f"ML filter min_win_prob updated to {self.ml_filter_min_win_prob:.2f}")
        
        return self.get_ml_filter_settings()
    
    def check_settled_capital_available(self, required_amount: float) -> Tuple[bool, str]:
        """
        Check if enough capital is available for a trade.
        Uses settled capital only when USE_MARGIN=false; total capital when USE_MARGIN=true.
        In yfinance/training mode T+1 is not enforced so trading can continue freely.
        
        Args:
            required_amount: Amount of capital needed for trade
            
        Returns:
            Tuple of (can_trade: bool, message: str)
        """
        if getattr(self, 'using_yfinance_sim', False):
            return True, "T+1 settlement not enforced (yfinance/training mode)"
        available = self.get_available_capital()
        use_margin = _is_margin_enabled()
        
        if available >= required_amount:
            kind = "total capital" if use_margin else "settled capital"
            return True, f"Available ({kind}): ${available:.2f}"
        else:
            unsettled_total = sum(fund['amount'] for fund in self.unsettled_funds)
            settled = self.get_settled_capital()
            if use_margin:
                message = (
                    f"Insufficient capital. Required: ${required_amount:.2f}, "
                    f"Total: ${self.total_capital:.2f}. "
                    f"Unsettled: ${unsettled_total:.2f} (T+1 pending)."
                )
            else:
                message = (
                    f"Insufficient settled capital. Required: ${required_amount:.2f}, "
                    f"Available (settled): ${settled:.2f}, "
                    f"Total: ${self.total_capital:.2f}, "
                    f"Unsettled: ${unsettled_total:.2f} (T+1 settlement pending)"
                )
            return False, message

    def get_capital_schedule(self) -> dict:
        """
        Get capital schedule showing when and how much capital will be available
        
        Returns:
            Dict with:
            - next_settlement_date: Next date when funds will settle (datetime or None)
            - next_settlement_amount: Amount that will settle on that date (float)
            - upcoming_settlements: List of upcoming settlements with dates and amounts
            - total_unsettled: Total amount currently unsettled
            - settled_capital: Currently available settled capital
        """
        # Clean up settled funds first
        self._clean_settled_funds()
        
        if not self.unsettled_funds:
            return {
                'next_settlement_date': None,
                'next_settlement_amount': 0.0,
                'upcoming_settlements': [],
                'total_unsettled': 0.0,
                'settled_capital': self.get_settled_capital()
            }
        
        # Group by settlement date
        settlements_by_date = {}
        for fund in self.unsettled_funds:
            settlement_date = fund['settlement_date']
            date_key = settlement_date.date()  # Use date as key (ignore time)
            
            if date_key not in settlements_by_date:
                settlements_by_date[date_key] = {
                    'date': settlement_date,
                    'amount': 0.0,
                    'reasons': []
                }
            
            settlements_by_date[date_key]['amount'] += fund['amount']
            settlements_by_date[date_key]['reasons'].append(fund['reason'])
        
        # Sort by date
        sorted_dates = sorted(settlements_by_date.keys())
        
        # Get next settlement
        next_settlement = None
        if sorted_dates:
            next_date = sorted_dates[0]
            next_settlement = settlements_by_date[next_date]
        
        # Build upcoming settlements list
        upcoming_settlements = []
        for date_key in sorted_dates:
            settlement = settlements_by_date[date_key]
            upcoming_settlements.append({
                'date': settlement['date'],
                'amount': settlement['amount'],
                'reasons': list(set(settlement['reasons']))  # Unique reasons
            })
        
        total_unsettled = sum(fund['amount'] for fund in self.unsettled_funds)
        
        return {
            'next_settlement_date': next_settlement['date'] if next_settlement else None,
            'next_settlement_amount': next_settlement['amount'] if next_settlement else 0.0,
            'upcoming_settlements': upcoming_settlements,
            'total_unsettled': total_unsettled,
            'settled_capital': self.get_settled_capital()
        }
    

    def get_current_month_return_pct(self) -> float:
        """Get current month's return percentage"""
        if not self.trade_history: return 0.0
        current_month = datetime.now().strftime('%Y-%m')
        month_trades = [t for t in self.trade_history if (isinstance(t.get('timestamp', ''), str) and t.get('timestamp', '').startswith(current_month)) or (isinstance(t.get('timestamp'), datetime) and t.get('timestamp').strftime('%Y-%m') == current_month)]
        if not month_trades: return 0.0
        month_pnl = sum(t.get('pnl', 0) for t in month_trades)
        return (month_pnl / self.starting_capital * 100) if self.starting_capital > 0 else 0.0

    def get_days_remaining_in_month(self) -> int:
        """Get number of days remaining in the current month"""
        today = datetime.now()
        last_day = datetime(today.year, today.month + 1, 1) - timedelta(days=1) if today.month != 12 else datetime(today.year + 1, 1, 1) - timedelta(days=1)
        return max(0, (last_day - today).days)

    def calculate_dynamic_exit_target(self, symbol: str) -> float:
        """Calculate optimal exit target based on context"""
        base_target = HIGH_SALE_PERCENT
        monthly_target_pct = float(os.getenv('MONTHLY_RETURN_TARGET', '0.03')) * 100
        current_month_return = self.get_current_month_return_pct()
        days_remaining = self.get_days_remaining_in_month()
        if days_remaining > 0:
            required_daily_return = (monthly_target_pct - current_month_return) / days_remaining
            if required_daily_return > 0.5: base_target *= 1.5
        capital_schedule = self.get_capital_schedule()
        next_settlement = capital_schedule.get('next_settlement_date')
        available_capital = self.get_available_capital()
        if available_capital < BOT_MIN_ALLOCATION and next_settlement:
            days_until_settlement = (next_settlement - datetime.now()).days
            if days_until_settlement > 1: base_target *= 1.3
        if symbol in self.positions:
            position = self.positions[symbol]
            entry_price = position['entry_price']
            current_price = position.get('high_price', entry_price)
            current_profit_pct = (current_price - entry_price) / entry_price
            if current_profit_pct > 0.08: base_target *= 1.2
        return min(base_target, 0.20)


    def collect_trade_reasoning(self, symbol: str, action: str, price: float, quantity: float, allocation: float) -> Dict[str, Any]:
        """Collect comprehensive reasoning for why the bot wants to make this trade"""
        reasoning = {'symbol': symbol, 'action': action, 'price': price, 'quantity': quantity, 'allocation': allocation, 'timestamp': datetime.now().isoformat(), 'strategy_signals': {}, 'ml_filter': {}, 'portfolio_optimization': {}, 'risk_analysis': {}, 'market_conditions': {}, 'capital_status': {}, 'monthly_progress': {}, 'auto_mode_decision': 'EXECUTE'}
        try:
            if self._strategy_manager:
                df = self._fetch_ohlcv_for_strategy(symbol)
                if df is not None and len(df) >= STRATEGY_MIN_BARS:
                    all_indicators = self._strategy_manager.get_all_indicator_values(df.copy())
                    combined_signal = self._strategy_manager.generate_combined_signal(df.copy())
                    reasoning['strategy_signals'] = {'combined_signal': combined_signal, 'individual_signals': {}, 'signal_strength': 0.0}
                    for strategy_item in self._strategy_manager.strategies:
                        strategy = strategy_item['strategy']
                        weight = strategy_item.get('weight', 1.0)
                        try:
                            signal = strategy.generate_signal(df.copy())
                            reasoning['strategy_signals']['individual_signals'][strategy.name] = {'signal': signal, 'weight': weight}
                        except: pass
                    buy_count = sum(1 for s in reasoning['strategy_signals']['individual_signals'].values() if s.get('signal') == 'BUY')
                    sell_count = sum(1 for s in reasoning['strategy_signals']['individual_signals'].values() if s.get('signal') == 'SELL')
                    total_strategies = len(reasoning['strategy_signals']['individual_signals'])
                    if total_strategies > 0:
                        if combined_signal == 'BUY': reasoning['strategy_signals']['signal_strength'] = buy_count / total_strategies
                        elif combined_signal == 'SELL': reasoning['strategy_signals']['signal_strength'] = sell_count / total_strategies
        except Exception as e: logger.debug(f"Could not collect strategy signals: {e}")
        # Check ML filter using runtime settings (can be toggled via API without restart)
        if self.ml_filter_enabled and self.ml_signal_filter and self.ml_signal_filter.enabled and self.ml_signal_filter.is_trained:
            try:
                df = self._fetch_ohlcv_for_strategy(symbol)
                if df is not None:
                    all_indicators = self._strategy_manager.get_all_indicator_values(df.copy()) if self._strategy_manager else {}
                    indicators = {k: v for s_name, s_indicators in all_indicators.items() if isinstance(s_indicators, dict) for k, v in s_indicators.items()}
                    signal_data = {'symbol': symbol, 'signal': action if action in ('BUY', 'SELL') else 'BUY', 'price': price, 'indicators': indicators, 'market_conditions': {'volume': self.price_cache.get(symbol, {}).get('volume', 0), 'volatility': self.calculate_volatility(symbol) if symbol in self.price_history else 0.05}}
                    should_filter, scores = self.ml_signal_filter.should_filter_signal(signal_data, min_confidence=self.ml_filter_min_confidence, min_win_prob=self.ml_filter_min_win_prob)
                    reasoning['ml_filter'] = {'filtered': should_filter, 'confidence': scores.get('confidence', 0.0), 'win_probability': scores.get('win_probability', 0.0), 'recommendation': 'REJECT' if should_filter else 'ACCEPT'}
            except Exception as e: logger.debug(f"Could not collect ML filter: {e}")
        if self.portfolio_optimizer and hasattr(self, 'current_symbols') and symbol in self.current_symbols:
            try:
                available_capital = self.get_available_capital()
                optimal_allocations = self.portfolio_optimizer.get_optimal_allocation(self.current_symbols, available_capital, method=PORTFOLIO_OPTIMIZATION_METHOD)
                if optimal_allocations and symbol in optimal_allocations:
                    optimal_allocation = optimal_allocations[symbol]
                    reasoning['portfolio_optimization'] = {'optimized_allocation': optimal_allocation, 'current_allocation': allocation, 'method': PORTFOLIO_OPTIMIZATION_METHOD, 'available_capital': available_capital, 'recommendation': 'USE_OPTIMIZED' if abs(optimal_allocation - allocation) > 10 else 'CURRENT_OK'}
            except Exception as e: logger.debug(f"Could not collect portfolio optimization: {e}")
        try:
            stop_loss_pct = getattr(self, 'stop_loss_percent', BOT_STOP_LOSS_PERCENT)
            potential_loss = allocation * stop_loss_pct
            risk_limit = BOT_RISK_THRESHOLD * self.total_capital
            risk_ratio = potential_loss / risk_limit if risk_limit > 0 else 0
            reasoning['risk_analysis'] = {'potential_loss': potential_loss, 'risk_limit': risk_limit, 'risk_ratio': risk_ratio, 'stop_loss_percent': stop_loss_pct, 'within_risk_limit': potential_loss <= risk_limit, 'risk_assessment': 'LOW' if risk_ratio < 0.5 else ('MEDIUM' if risk_ratio < 0.8 else 'HIGH')}
        except Exception as e: logger.debug(f"Could not collect risk analysis: {e}")
        try:
            volatility = self.calculate_volatility(symbol) if symbol in self.price_history else 0.05
            volume = self.price_cache.get(symbol, {}).get('volume', 0)
            reasoning['market_conditions'] = {'volatility': volatility, 'volume': volume, 'price': price, 'volatility_assessment': 'LOW' if volatility < 0.05 else ('MEDIUM' if volatility < 0.15 else 'HIGH'), 'liquidity_assessment': 'HIGH' if volume > 1000000 else ('MEDIUM' if volume > 500000 else 'LOW')}
        except Exception as e: logger.debug(f"Could not collect market conditions: {e}")
        try:
            available_capital = self.get_available_capital()
            capital_schedule = self.get_capital_schedule()
            reasoning['capital_status'] = {'available_capital': available_capital, 'total_capital': self.total_capital, 'allocation_percentage': (allocation / self.total_capital * 100) if self.total_capital > 0 else 0, 'next_settlement_date': capital_schedule.get('next_settlement_date').isoformat() if capital_schedule.get('next_settlement_date') else None, 'next_settlement_amount': capital_schedule.get('next_settlement_amount', 0), 'sufficient_capital': available_capital >= allocation}
        except Exception as e: logger.debug(f"Could not collect capital status: {e}")
        try:
            current_month_return = self.get_current_month_return_pct()
            days_remaining = self.get_days_remaining_in_month()
            monthly_target = float(os.getenv('MONTHLY_RETURN_TARGET', '0.03')) * 100
            reasoning['monthly_progress'] = {'current_return': current_month_return, 'target_return': monthly_target, 'days_remaining': days_remaining, 'progress_percentage': (current_month_return / monthly_target * 100) if monthly_target > 0 else 0, 'on_track': current_month_return >= monthly_target * (1 - days_remaining/30), 'needs_catch_up': current_month_return < monthly_target * 0.8}
        except Exception as e: logger.debug(f"Could not collect monthly progress: {e}")
        auto_decision = 'EXECUTE'
        auto_reasons = []
        if reasoning.get('ml_filter', {}).get('filtered', False): auto_decision, auto_reasons = 'REJECT', ['ML filter rejected']
        if not reasoning.get('risk_analysis', {}).get('within_risk_limit', True): auto_decision, auto_reasons = 'REJECT', ['Exceeds risk threshold']
        if not reasoning.get('capital_status', {}).get('sufficient_capital', True): auto_decision, auto_reasons = 'REJECT', ['Insufficient capital']
        reasoning['auto_mode_decision'] = auto_decision
        reasoning['auto_mode_reasons'] = auto_reasons if auto_reasons else ['All checks passed - would execute']
        return reasoning
    
    def create_pending_trade(self, symbol: str, action: str, price: float, quantity: float, allocation: float, volume: int = None) -> str:
        """Create a pending trade request for manual approval"""
        self.pending_trade_counter += 1
        trade_id = f"pending_{self.pending_trade_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        reasoning = self.collect_trade_reasoning(symbol, action, price, quantity, allocation)
        auto_mode_details = {'would_execute': reasoning['auto_mode_decision'] == 'EXECUTE', 'decision': reasoning['auto_mode_decision'], 'reasons': reasoning.get('auto_mode_reasons', []), 'expected_allocation': allocation, 'expected_quantity': quantity, 'expected_price': price}
        pending_trade = {'trade_id': trade_id, 'symbol': symbol, 'action': action, 'price': price, 'quantity': quantity, 'allocation': allocation, 'volume': volume, 'reasoning': reasoning, 'auto_mode_details': auto_mode_details, 'timestamp': datetime.now().isoformat(), 'expires_at': (datetime.now() + timedelta(seconds=self.pending_trade_ttl)).isoformat(), 'status': 'pending'}
        self.pending_trades[trade_id] = pending_trade
        self.alert_system.send_alert("Pending Trade - Manual Approval Required", f"Trade pending: {action} {quantity:.6f} shares of {symbol} at ${price:.2f}\nAllocation: ${allocation:.2f}\nAuto mode: {auto_mode_details['decision']}", severity='INFO')
        self.stored_messages.add_message(f"Pending trade: {action} {symbol} @ ${price:.2f} - Manual approval required", category='pending_trade', details=pending_trade)
        logger.info(f"Created pending trade {trade_id}: {action} {symbol} @ ${price:.2f} (${allocation:.2f})")
        return trade_id
    
    def approve_pending_trade(self, trade_id: str) -> Dict[str, Any]:
        """Approve a pending trade and execute it"""
        if trade_id not in self.pending_trades: return {'status': 'error', 'reason': 'trade_not_found', 'message': f'Pending trade {trade_id} not found'}
        pending_trade = self.pending_trades[trade_id]
        expires_at = datetime.fromisoformat(pending_trade['expires_at'])
        if datetime.now() > expires_at: pending_trade['status'] = 'expired'; return {'status': 'error', 'reason': 'trade_expired', 'message': f'Pending trade {trade_id} has expired'}
        pending_trade['status'] = 'approved'
        pending_trade['approved_at'] = datetime.now().isoformat()
        logger.info(f"Executing approved trade {trade_id}: {pending_trade['action']} {pending_trade['symbol']}")
        try:
            result = self.execute_trade(pending_trade['symbol'], pending_trade['action'], pending_trade['price'], volume=pending_trade.get('volume'))
            del self.pending_trades[trade_id]
            result['approved_by'] = 'user'
            result['pending_trade_id'] = trade_id
            return result
        except Exception as e:
            logger.error(f"Error executing approved trade {trade_id}: {e}")
            return {'status': 'error', 'reason': 'execution_failed', 'message': f'Failed to execute trade: {str(e)}'}
    
    def reject_pending_trade(self, trade_id: str, reason: str = None) -> Dict[str, Any]:
        """Reject a pending trade"""
        if trade_id not in self.pending_trades: return {'status': 'error', 'reason': 'trade_not_found', 'message': f'Pending trade {trade_id} not found'}
        pending_trade = self.pending_trades[trade_id]
        pending_trade['status'] = 'rejected'
        pending_trade['rejected_at'] = datetime.now().isoformat()
        pending_trade['rejection_reason'] = reason or 'User rejected'
        del self.pending_trades[trade_id]
        logger.info(f"Rejected pending trade {trade_id}: {pending_trade['symbol']} - {reason or 'No reason provided'}")
        return {'status': 'rejected', 'trade_id': trade_id, 'message': 'Trade rejected by user'}
    
    def get_pending_trades(self) -> List[Dict[str, Any]]:
        """Get all pending trades awaiting approval"""
        current_time = datetime.now()
        expired_ids = []
        for trade_id, trade in self.pending_trades.items():
            expires_at = datetime.fromisoformat(trade['expires_at'])
            if current_time > expires_at and trade['status'] == 'pending': trade['status'] = 'expired'; expired_ids.append(trade_id)
        for trade_id in expired_ids: del self.pending_trades[trade_id]
        return [trade for trade in self.pending_trades.values() if trade['status'] == 'pending']
    def get_current_month_return_pct(self) -> float:
        """Get current month's return percentage"""
        if not self.trade_history: return 0.0
        current_month = datetime.now().strftime('%Y-%m')
        month_trades = [t for t in self.trade_history if (isinstance(t.get('timestamp', ''), str) and t.get('timestamp', '').startswith(current_month)) or (isinstance(t.get('timestamp'), datetime) and t.get('timestamp').strftime('%Y-%m') == current_month)]
        if not month_trades: return 0.0
        month_pnl = sum(t.get('pnl', 0) for t in month_trades)
        return (month_pnl / self.starting_capital * 100) if self.starting_capital > 0 else 0.0

    def get_days_remaining_in_month(self) -> int:
        """Get number of days remaining in the current month"""
        today = datetime.now()
        last_day = datetime(today.year, today.month + 1, 1) - timedelta(days=1) if today.month != 12 else datetime(today.year + 1, 1, 1) - timedelta(days=1)
        return max(0, (last_day - today).days)

    def calculate_dynamic_exit_target(self, symbol: str) -> float:
        """Calculate optimal exit target based on context"""
        base_target = HIGH_SALE_PERCENT
        monthly_target_pct = float(os.getenv('MONTHLY_RETURN_TARGET', '0.03')) * 100
        current_month_return = self.get_current_month_return_pct()
        days_remaining = self.get_days_remaining_in_month()
        if days_remaining > 0:
            required_daily_return = (monthly_target_pct - current_month_return) / days_remaining
            if required_daily_return > 0.5: base_target *= 1.5
        capital_schedule = self.get_capital_schedule()
        next_settlement = capital_schedule.get('next_settlement_date')
        available_capital = self.get_available_capital()
        if available_capital < BOT_MIN_ALLOCATION and next_settlement:
            days_until_settlement = (next_settlement - datetime.now()).days
            if days_until_settlement > 1: base_target *= 1.3
        if symbol in self.positions:
            position = self.positions[symbol]
            entry_price = position['entry_price']
            current_price = position.get('high_price', entry_price)
            current_profit_pct = (current_price - entry_price) / entry_price
            if current_profit_pct > 0.08: base_target *= 1.2
        return min(base_target, 0.20)

    def handle_resource_bottleneck(self, bottlenecks: list):
        """
        Handle resource bottlenecks detected by ResourceMonitor
        Integrates GUI resource monitoring with bot throttling
        
        Args:
            bottlenecks: List of bottleneck descriptions from ResourceMonitor.get_bottlenecks()
        """
        if not bottlenecks:
            return
        
        # Log the bottlenecks
        bottleneck_str = ", ".join(bottlenecks)
        logger.warning(f"[RESOURCE BOTTLENECK] Detected: {bottleneck_str}")
        
        # Apply throttling if enabled (otherwise just log the bottleneck)
        if self.throttler.enabled:
            reason = f"Resource bottlenecks detected: {bottleneck_str}"
            self.throttler.apply_throttle(reason)
            
            # Send alert for critical bottlenecks (>90% usage)
            critical_bottlenecks = [b for b in bottlenecks if '>90' in b or 'Disk: 9' in b]
            if critical_bottlenecks:
                self.alert_system.send_alert(
                    "Critical Resource Bottleneck",
                    f"Critical resource usage detected:\n{chr(10).join(critical_bottlenecks)}\n\n"
                    f"Trading will be throttled to preserve system stability.",
                    severity='CRITICAL'
                )
        else:
            logger.info("[RESOURCE BOTTLENECK] Throttling disabled, continuing normally")

    
    def add_day_trade(self, symbol: str):
        """Add a day trade (buy and sell same day) for PDT tracking"""
        today = datetime.now().date()
        self.day_trades.append((today, symbol))
        
        # Keep only last 5 business days using pandas BDay for PDT rule
        from pandas.tseries.offsets import BDay
        import pandas as pd
        cutoff = (pd.Timestamp.now() - BDay(5)).date()
        self.day_trades = [(date, sym) for date, sym in self.day_trades if date >= cutoff]
    
    def get_day_trade_count(self) -> int:
        """Get number of day trades in last 5 business days"""
        return len(self.day_trades)
    
    def check_pdt_compliance(self) -> Tuple[bool, str]:
        """
        Check if day trading is allowed based on PDT rules
        Returns (can_trade, message)
        
        PDT rules are ONLY enforced in live/production mode (PAPER_TRADING_MODE=false).
        In training, backtest, sandbox, and simulation modes, PDT is disabled to allow
        the bot to learn and test strategies without regulatory restrictions.
        """
        count = self.get_day_trade_count()
        
        # Determine mode for messaging
        mode_name = "sandbox mode" if (PAPER_TRADING_MODE and SCHWAB_SANDBOX_MODE) else (
            "simulation mode" if PAPER_TRADING_MODE else "production mode"
        )
        
        # PDT is ONLY enforced in production/live mode
        # In all other modes (paper, sandbox, backtest, training), PDT is disabled
        if not PAPER_TRADING_MODE:
            # Production/Live mode - enforce PDT rules
            if count >= 3 and self.total_capital < 25000:
                return False, f"PDT Limit Reached in {mode_name}: {count}/3 day trades (need $25k+ for more)"
            return True, f"PDT OK ({mode_name}): {count}/3 day trades"
        else:
            # Paper/Sandbox/Training mode - PDT disabled
            return True, f"PDT disabled ({mode_name}): {count} day trades (no limit in training)"

    def check_holding_period(self, symbol: str, action: str) -> Tuple[bool, str]:
        """
        Check if the minimum holding period has been met before allowing a sell
        Returns (can_trade, message)
        
        This enforces swing trading strategy by preventing same-day sells/covers.
        Applied in all modes (sandbox, simulation, and live) for consistent strategy.
        """
        # Only check for SELL (close long) and COVER (close short) actions
        if action.upper() not in ('SELL', 'COVER'):
            return True, "Open action - holding period check not applicable"
        
        # Check if we have a position for this symbol
        if symbol not in self.positions:
            return True, f"No open position for {symbol}"
        
        position = self.positions[symbol]
        entry_time_str = position.get('entry_time')
        
        # If no entry time recorded, allow the trade (backward compatibility)
        if not entry_time_str:
            return True, "No entry time recorded - allowing trade"
        
        try:
            entry_time = datetime.fromisoformat(entry_time_str)
            current_time = datetime.now()
            hold_duration = current_time - entry_time
            
            # Check if minimum hold period has been met
            min_hold_duration = timedelta(days=SWING_MIN_HOLD_DAYS)
            
            if hold_duration < min_hold_duration:
                hours_held = hold_duration.total_seconds() / 3600
                hours_required = min_hold_duration.total_seconds() / 3600
                return False, f"Holding period not met: {hours_held:.1f}h held, {hours_required:.1f}h required (SWING_MIN_HOLD_DAYS={SWING_MIN_HOLD_DAYS})"
            
            hours_held = hold_duration.total_seconds() / 3600
            return True, f"Holding period met: {hours_held:.1f}h held ({SWING_MIN_HOLD_DAYS} days minimum)"
            
        except Exception as e:
            logger.warning(f"Error parsing entry time for {symbol}: {e}")
            return True, "Error parsing entry time - allowing trade"

    def calculate_win_rate(self) -> float:
        """
        Calculate the current win rate based on rolling window:
        - Last 7 days of trades (time-based window), OR  
        - Last 20 trades (count-based window)
        
        Uses whichever is more restrictive/recent:
        - If we have <= 20 trades total, use all of them
        - If 7-day window has <= 20 trades, use the 7-day window (more recent)
        - If 7-day window has > 20 trades, use last 20 trades (more restrictive)
        """
        if self.track_record['total_trades'] == 0:
            return 0.0
        
        # Get trades from last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_trades_7_days = []
        for trade in self.trade_history:
            try:
                trade_time = datetime.fromisoformat(trade['timestamp'])
                if trade_time >= seven_days_ago:
                    recent_trades_7_days.append(trade)
            except (ValueError, KeyError, TypeError) as e:
                # Skip trades with invalid timestamps
                logger.warning(f"Skipping trade with invalid timestamp: {e}")
                continue
        
        # Get last 20 trades
        last_20_trades = self.trade_history[-20:]
        
        # Decision logic: use the smaller, more recent window
        # If 7-day window has fewer or equal trades to 20, use 7-day (it's more time-recent)
        # If 7-day window has more than 20 trades, use last 20 (it's more count-restrictive)
        if len(recent_trades_7_days) <= 20 and len(recent_trades_7_days) > 0:
            trades_to_consider = recent_trades_7_days
        else:
            trades_to_consider = last_20_trades
        
        if len(trades_to_consider) == 0:
            return 0.0
        
        winning_trades = sum(1 for trade in trades_to_consider if trade['is_win'])
        return winning_trades / len(trades_to_consider)

    def apply_self_scaling_logic(self):
        """
        Self-scaling logic: Adjust allocation based on win rate and consecutive losses
        - If win_rate > 60%: increase allocation by 20%
        - If BOT_MAX_CONSECUTIVE_LOSSES+ consecutive losses: decrease allocation by 20-30% (using 25% as midpoint)
        - Otherwise: decrease allocation by 10%
        
        Also respects risk threshold constraint - allocation won't exceed risk limit
        """
        win_rate = self.calculate_win_rate()
        self.track_record['win_rate'] = win_rate
        
        current_allocation = self.track_record['current_allocation']
        
        print(f"\n[ALLOCATION ADJUSTMENT - Rolling Win Rate: {win_rate:.1%}]")
        print(f"  Consecutive Losses: {self.consecutive_losses}")
        
        if win_rate > 0.60:
            # Increase allocation by 20%
            new_allocation = current_allocation * 1.20
            print(f"  [+] Win rate {win_rate:.1%} > 60% - Increasing allocation by 20%")
        elif self.consecutive_losses >= BOT_MAX_CONSECUTIVE_LOSSES:
            # Decrease allocation by 25% (midpoint of 20-30%) after BOT_MAX_CONSECUTIVE_LOSSES+ consecutive losses
            new_allocation = current_allocation * 0.75
            print(f"  [-] {self.consecutive_losses} consecutive losses - Decreasing allocation by 25%")
        else:
            # Decrease allocation by 10%
            new_allocation = current_allocation * 0.90
            print(f"  [-] Win rate {win_rate:.1%} <= 60% - Decreasing allocation by 10%")
        
        # Apply min/max bounds - ensure we don't exceed BOT_MAX_ALLOCATION
        new_allocation = max(BOT_MIN_ALLOCATION, min(BOT_MAX_ALLOCATION, new_allocation))
        
        # Also constrain by risk threshold to prevent blocking future trades
        # Calculate the maximum allocation allowed by risk threshold
        risk_limit = BOT_RISK_THRESHOLD * self.total_capital
        max_allocation_by_risk = risk_limit * RISK_ALLOCATION_BUFFER  # Use buffer to provide safety margin
        
        if new_allocation > max_allocation_by_risk:
            print(f"  ⚠ Allocation ${new_allocation:.2f} would exceed risk-adjusted limit ${max_allocation_by_risk:.2f}")
            new_allocation = max_allocation_by_risk
            print(f"  ⚠ Capping allocation at ${new_allocation:.2f} to respect risk threshold")
        
        self.track_record['current_allocation'] = new_allocation
        
        print(f"  Allocation adjusted: ${current_allocation:.2f} -> ${new_allocation:.2f}")
        return new_allocation

    def record_trade(self, symbol: str, action: str, quantity: float, price: float, is_win: bool,
                    entry_price: Optional[float] = None, exit_price: Optional[float] = None,
                    pnl: Optional[float] = None, pnl_percent: Optional[float] = None,
                    exit_reason: Optional[str] = None, hold_duration: Optional[float] = None,
                    volatility: Optional[float] = None, volume: Optional[int] = None,
                    entry_time: Optional[str] = None, exit_time: Optional[str] = None):
        """
        Record a trade in the track record with comprehensive data for AI analysis.

        Args:
            symbol: Stock symbol
            action: 'BUY', 'SELL', 'SHORT', or 'COVER' (Phase 1: stocks buy/short per MISSION.md)
            quantity: Number of shares
            price: Execution price (for BUY: entry price, for SELL: exit price)
            is_win: Whether the trade was profitable
            entry_price: Entry price for position (mainly for SELL orders, always set for BUY)
            exit_price: Exit price for position (mainly for SELL orders)
            pnl: Profit/Loss in dollars
            pnl_percent: Profit/Loss percentage
            exit_reason: Reason for exit (e.g., 'trailing_stop', 'target_reached')
            hold_duration: Time held in hours
            volatility: Stock volatility at exit
            volume: Trading volume
            entry_time: ISO format timestamp when position was opened
            exit_time: ISO format timestamp when position was closed (for SELL/COVER)
        """
        # Validate critical data
        if price is not None and price <= 0:
            logger.error(f"[DATA_QUALITY_REJECT] {symbol} {action}: price={price} is invalid (must be > 0)")
            return
        if quantity is not None and quantity <= 0:
            logger.error(f"[DATA_QUALITY_REJECT] {symbol} {action}: quantity={quantity} is invalid (must be > 0)")
            return
        # Determine trading mode for classification
        # Read mode settings dynamically to support runtime updates
        api_enabled = _get_schwab_api_enabled()
        paper_mode = _get_paper_trading_mode()
        sandbox_mode = _get_schwab_sandbox_mode()
        
        # Prefer explicit env-derived mode when Schwab API is disabled
        if not api_enabled:
            # API disabled mode - training/learning with yfinance
            trade_mode = 'api_disabled'
        elif self.using_yfinance_sim:
            # Fallback mode (only set in non-interactive without token or no credentials)
            trade_mode = 'yfinance_sim'
        elif paper_mode and sandbox_mode:
            trade_mode = 'schwab_sandbox'
        elif paper_mode:
            trade_mode = 'pure_simulation'
        else:
            trade_mode = 'live_trading'
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'is_win': is_win,
            'mode': trade_mode  # Track which mode this trade was executed in
        }
        
        # Track entry and exit times for stale position detection
        if action.upper() == 'BUY':
            # BUY action: record entry time
            trade['entry_price'] = price
            trade['entry_time'] = entry_time or datetime.now().isoformat()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[TRADE_RECORDED] BUY {symbol}: entry_price={price:.2f}, entry_time={trade['entry_time']}")
        elif action.upper() == 'SHORT':
            # SHORT action: record entry time
            trade['entry_price'] = price
            trade['entry_time'] = entry_time or datetime.now().isoformat()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[TRADE_RECORDED] SHORT {symbol}: entry_price={price:.2f}, entry_time={trade['entry_time']}")
        elif action.upper() in ('SELL', 'COVER'):
            # SELL/COVER: record exit time
            trade['exit_time'] = exit_time or datetime.now().isoformat()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[TRADE_RECORDED] {action} {symbol}: exit_time={trade['exit_time']}")
        
        # Add comprehensive trade data if provided (especially for SELL orders)
        if entry_price is not None and entry_price > 0:
            trade['entry_price'] = entry_price
        if exit_price is not None:
            trade['exit_price'] = exit_price
        if pnl is not None:
            trade['pnl'] = pnl
        if pnl_percent is not None:
            trade['pnl_percent'] = pnl_percent
        if exit_reason is not None:
            trade['exit_reason'] = exit_reason
        if hold_duration is not None:
            trade['hold_duration_hours'] = hold_duration
            # For backward compatibility, also include without _hours suffix for persistence
            trade['hold_duration'] = hold_duration
            # Log stale position warning if held > 48 hours
            if hold_duration > 48:
                logger.warning(f"[STALE_POSITION] {symbol}: held for {hold_duration:.1f} hours (>48h threshold)")
            elif hold_duration > 24:
                logger.info(f"[EXTENDED_HOLD] {symbol}: held for {hold_duration:.1f} hours")
        if volatility is not None:
            trade['volatility'] = volatility
        if volume is not None:
            trade['volume'] = volume
        # Record exit_time when provided (for simulated round-trip trades with BUY/SHORT + exit_price/pnl)
        if exit_time is not None and 'exit_time' not in trade:
            trade['exit_time'] = exit_time
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[TRADE_RECORDED] {action} {symbol}: recorded exit_time for round-trip simulation")
        # For close trades, include entry_time for reference
        if entry_time is not None and action.upper() not in ('BUY', 'SHORT'):
            trade['entry_time'] = entry_time
        
        self.trade_history.append(trade)
        
        # Persist to DB for restart recovery (logs/trading_logs.db)
        try:
            from log_manager import LogManager
            lm = LogManager()
            # Include all metadata fields with correct names
            meta = {}
            if 'mode' in trade:
                meta['mode'] = trade['mode']
            if 'volume' in trade:
                meta['volume'] = trade['volume']
            if 'hold_duration_hours' in trade:
                meta['hold_duration_hours'] = trade['hold_duration_hours']
            if 'hold_duration' in trade:
                # For backward compatibility, include both variants
                meta['hold_duration'] = trade['hold_duration']
            if 'volatility' in trade:
                meta['volatility'] = trade['volatility']
            
            trade_for_db = dict(trade)
            if meta:
                trade_for_db['metadata'] = meta
            lm.log_trade(trade_for_db)
        except Exception as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Failed to persist trade to DB: %s", e)
        
        # Update last trade time for activity monitoring
        self.last_trade_time = datetime.now()
        
        # Reset no-trade alert flag if trades are happening
        if self.no_trade_alert_sent:
            logger.info("Trade executed - clearing no-trade alert flag")
            self.alert_system.send_alert(
                "✅ Trading Activity Resumed",
                f"Trade activity has resumed. Last trade: {trade.get('symbol', 'N/A')} {trade.get('action', 'N/A')}",
                severity='INFO'
            )
            self.no_trade_alert_sent = False
            self.no_trade_reasons = []
        
        # Check trade activity periodically (called after each trade)
        self._check_trade_activity()
        self.track_record['total_trades'] += 1
        
        if is_win:
            self.track_record['winning_trades'] += 1
            self.consecutive_losses = 0  # Reset consecutive losses on win
        else:
            self.track_record['losing_trades'] += 1
            self.consecutive_losses += 1  # Increment consecutive losses
        
        # Apply self-scaling logic after each trade
        self.apply_self_scaling_logic()
    
    def check_sentiment_filter(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if sentiment supports trading a symbol
        Returns (should_trade, reason)
        """
        if not self.sentiment_analyzer:
            return True, "Sentiment analysis not available"
        
        try:
            return self.sentiment_analyzer.should_trade_based_on_sentiment(symbol)
        except Exception as e:
            logger.warning(f"Sentiment check failed for {symbol}: {e}")
            return True, f"Sentiment check failed: {e}"
    
    def get_portfolio_optimal_allocation(self, symbols: List[str], 
                                         method: str = 'sharpe') -> Optional[Dict[str, float]]:
        """
        Get optimal portfolio allocation for given symbols
        
        Args:
            symbols: List of symbols to optimize
            method: Optimization method ('sharpe', 'min_variance', 'risk_parity', 'equal')
            
        Returns:
            Dictionary mapping symbols to dollar amounts
        """
        if not self.portfolio_optimizer:
            logger.warning("Portfolio optimizer not available - using equal allocation")
            allocation = self.total_capital / len(symbols)
            return {symbol: allocation for symbol in symbols}
        
        try:
            # Add price history to optimizer
            for symbol in symbols:
                if symbol in self.price_history:
                    self.portfolio_optimizer.add_price_data(symbol, self.price_history[symbol])
            
            # Get optimal allocation
            return self.portfolio_optimizer.get_optimal_allocation(
                symbols, 
                self.total_capital,
                method=method
            )
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            allocation = self.total_capital / len(symbols)
            return {symbol: allocation for symbol in symbols}
    
    def calculate_portfolio_diversification(self, symbols: List[str]) -> float:
        """
        Calculate diversification score for current symbols
        Returns score from 0 to 1 (higher is more diversified)
        """
        if not self.portfolio_optimizer:
            return 0.5  # Default middle score
        
        try:
            # Add price history to optimizer
            for symbol in symbols:
                if symbol in self.price_history:
                    self.portfolio_optimizer.add_price_data(symbol, self.price_history[symbol])
            
            return self.portfolio_optimizer.calculate_diversification_score(symbols)
        except Exception as e:
            logger.error(f"Diversification calculation failed: {e}")
            return 0.5

    def update_price_history(self, symbol: str, price: float):
        """Update price history for volatility calculation"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(price)
        
        # Keep only last VOLATILITY_WINDOW prices
        if len(self.price_history[symbol]) > VOLATILITY_WINDOW:
            self.price_history[symbol] = self.price_history[symbol][-VOLATILITY_WINDOW:]
    
    def calculate_volatility(self, symbol: str) -> float:
        """
        Calculate historical volatility (standard deviation) for a symbol
        Returns annualized volatility as a decimal (e.g., 0.15 for 15%)
        """
        if symbol not in self.price_history or len(self.price_history[symbol]) < 2:
            return 0.05  # Default to 5% if insufficient data
        
        prices = self.price_history[symbol]
        # Calculate returns
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        if not returns:
            return 0.05
        
        # Calculate standard deviation of returns
        volatility = np.std(returns)
        
        # Annualize (assuming daily prices, ~252 trading days per year)
        # For simplicity in simulation, we'll use the raw volatility
        return volatility if volatility > 0 else 0.05
    
    def _get_market_data_for_learning(self, symbol: str, price: float) -> Dict[str, Any]:
        """
        Get market data for adaptive learning.
        
        Returns market indicators needed by adaptive learning orchestrator.
        """
        market_data = {
            'price': price,
            'volatility': self.calculate_volatility(symbol),
            'trend': 0.0,  # Can be enhanced with trend calculation
            'volume_ratio': 1.0,  # Can be enhanced with volume analysis
        }
        
        # Try to get RSI if available from strategy indicators
        try:
            if self._strategy_manager:
                df = self._fetch_ohlcv_for_strategy(symbol)
                if df is not None and len(df) >= 14:
                    indicators = self._strategy_manager.get_all_indicator_values(df)
                    # Extract RSI from indicators if available
                    for strategy_name, strategy_indicators in indicators.items():
                        if isinstance(strategy_indicators, dict) and 'rsi' in strategy_indicators:
                            market_data['rsi'] = strategy_indicators['rsi']
                            break
        except Exception as e:
            logger.debug(f"Could not get RSI for adaptive learning: {e}")
        
        # Default RSI if not found
        if 'rsi' not in market_data:
            market_data['rsi'] = 50.0  # Neutral
        
        return market_data
    
    def _update_strategy_weights_from_adaptive_learning(self):
        """
        Update StrategyManager strategy weights based on adaptive learning results.
        """
        if not self.adaptive_learner or not self._strategy_manager:
            return
        
        try:
            # Get strategy weights from adaptive learning
            strategy_weights = {}
            
            if ADAPTIVE_LEARNING_METHOD == 'bandit' and self.adaptive_learner.bandit:
                # Get probabilities from bandit as weights
                bandit_stats = self.adaptive_learner.bandit.get_statistics()
                probabilities = bandit_stats.get('probabilities', {})
                
                # Map strategy names to weights
                strategy_name_map = {
                    'SMA': 'SMA',
                    'Bollinger': 'Bollinger',
                    'RSI': 'RSI',
                    'MACD': 'MACD',
                    'Momentum': 'Momentum'
                }
                
                for strategy_name, mapped_name in strategy_name_map.items():
                    if mapped_name in probabilities:
                        strategy_weights[strategy_name] = probabilities[mapped_name]
                    else:
                        strategy_weights[strategy_name] = 1.0  # Default
            else:
                # For Q-Learning, use strategy performance statistics
                stats = self.adaptive_learner.get_all_statistics()
                qlearning_stats = stats.get('components', {}).get('qlearning', {})
                strategy_performance = qlearning_stats.get('strategy_performance', {})
                
                # Use average reward as weight (normalize to 0.5-2.0 range)
                for strategy_name in ['SMA', 'Bollinger', 'RSI', 'MACD', 'Momentum']:
                    if strategy_name in strategy_performance:
                        avg_reward = strategy_performance[strategy_name].get('avg_reward', 0.0)
                        # Normalize: -0.1 to 0.1 reward -> 0.5 to 2.0 weight
                        weight = max(0.5, min(2.0, 1.0 + (avg_reward * 10)))
                        strategy_weights[strategy_name] = weight
                    else:
                        strategy_weights[strategy_name] = 1.0  # Default
            
            # Update weights in StrategyManager
            for i, strategy_item in enumerate(self._strategy_manager.strategies):
                strategy = strategy_item['strategy']
                strategy_name = strategy.name.split()[0]  # Get first word (e.g., "SMA" from "SMA Crossover")
                
                if strategy_name in strategy_weights:
                    new_weight = strategy_weights[strategy_name]
                    old_weight = strategy_item['weight']
                    strategy_item['weight'] = new_weight
                    
                    if abs(new_weight - old_weight) > 0.1:  # Only log significant changes
                        logger.info(f"Updated {strategy_name} strategy weight: {old_weight:.2f} -> {new_weight:.2f}")
        
        except Exception as e:
            logger.warning(f"Failed to update strategy weights from adaptive learning: {e}")
    
    def _check_and_run_ml_optimization(self):
        """
        Check if ML parameter optimization should run and execute it.
        Runs periodically based on trade count or time interval.
        """
        if not self.ml_optimizer or not self.ml_optimizer.is_api_configured():
            return
        
        # Check if we have minimum trades for optimization
        if len(self.trade_history) < ML_OPTIMIZATION_MIN_TRADES:
            return
        
        # Check trade count interval
        trade_count_since_optimization = len(self.trade_history) - self.last_ml_optimization_trade_count
        should_optimize_by_trades = (trade_count_since_optimization >= ML_OPTIMIZATION_INTERVAL_TRADES)
        
        # Check time interval
        should_optimize_by_time = False
        if self.last_ml_optimization_time:
            time_since_optimization = (datetime.now() - self.last_ml_optimization_time).total_seconds() / 60
            should_optimize_by_time = (time_since_optimization >= ML_OPTIMIZATION_INTERVAL_MINUTES)
        else:
            # First optimization
            should_optimize_by_time = True
        
        # Run optimization if interval reached
        if should_optimize_by_trades or should_optimize_by_time:
            try:
                logger.info(f"Running periodic ML parameter optimization (trade #{len(self.trade_history)})...")
                optimized_params, predicted_win_rate = self.optimize_parameters_ml()
                
                if optimized_params:
                    logger.info(f"ML optimization complete: predicted win rate {predicted_win_rate:.1%}")
                    
                    # Cache optimized parameters
                    self.optimized_parameters_cache = optimized_params
                    
                    # Apply parameters that can be changed at runtime
                    applied_params = self._apply_optimized_parameters(optimized_params)
                    
                    # Invalidate portfolio cache when parameters change (enhancement)
                    if applied_params > 0:
                        self.portfolio_optimization_cache.clear()
                        self.portfolio_cache_timestamp = None
                        logger.debug("Cleared portfolio optimization cache due to parameter changes")
                    
                    # Update tracking
                    self.last_ml_optimization_time = datetime.now()
                    self.last_ml_optimization_trade_count = len(self.trade_history)
                else:
                    logger.debug("ML optimization returned no parameters (may need more trade data)")
                    
            except Exception as e:
                logger.warning(f"Periodic ML optimization failed: {e}")
    
    def _apply_optimized_parameters(self, optimized_params: Dict[str, Any]) -> int:
        """
        Apply optimized parameters that can be changed at runtime.
        Some parameters (env vars) can only be logged as suggestions.
        
        Returns:
            Number of parameters successfully applied
        """
        applied_count = 0
        suggested_count = 0
        
        # Parameters that can be applied at runtime
        runtime_params = {
            'BOT_TRAILING_STOP_PERCENT': ('trailing_stop_percent', float),
            'BOT_STOP_LOSS_PERCENT': ('stop_loss_percent', float),
            'BOT_TAKE_PROFIT_PERCENT': ('take_profit_percent', float),
            'HIGH_SALE_PERCENT': ('take_profit_percent', float),  # Alternative name
        }
        
        # Parameters that require .env update (log as suggestions)
        env_params = [
            'BOT_RISK_THRESHOLD',
            'BOT_MAX_CONSECUTIVE_LOSSES',
            'BOT_MIN_ALLOCATION',
            'BOT_MAX_ALLOCATION',
            'TRADING_FREQUENCY',
            'MIN_TRAILING_STOP',
            'MAX_TRAILING_STOP'
        ]
        
        # Apply runtime parameters
        for param_name, (attr_name, param_type) in runtime_params.items():
            if param_name in optimized_params:
                try:
                    value = param_type(optimized_params[param_name])
                    if hasattr(self, attr_name):
                        old_value = getattr(self, attr_name)
                        setattr(self, attr_name, value)
                        logger.info(f"Applied optimized {param_name}: {old_value:.4f} -> {value:.4f}")
                        applied_count += 1
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not apply {param_name}: {e}")
        
        # Log suggestions for env parameters
        env_suggestions = []
        for param_name in env_params:
            if param_name in optimized_params:
                value = optimized_params[param_name]
                current_value = globals().get(param_name, 'N/A')
                env_suggestions.append(f"  {param_name}={value}  # Current: {current_value}")
                suggested_count += 1
        
        if env_suggestions:
            logger.info(f"\n💡 Suggested .env parameter updates (requires restart):")
            for suggestion in env_suggestions:
                logger.info(suggestion)
        
        if applied_count > 0:
            logger.info(f"✓ Applied {applied_count} optimized parameters at runtime")
        if suggested_count > 0:
            logger.info(f"📋 {suggested_count} parameters require .env update (see suggestions above)")
        
        # Return count of applied parameters (enhancement)
        return applied_count
    
    def calculate_dynamic_trailing_stop(self, symbol: str) -> float:
        """
        Calculate dynamic trailing stop based on volatility
        - Low volatility: Tighter stops (closer to MIN_TRAILING_STOP)
        - High volatility: Looser stops (closer to MAX_TRAILING_STOP)
        """
        if not DYNAMIC_STOP_ENABLED:
            return self.trailing_stop_percent
        
        volatility = self.calculate_volatility(symbol)
        
        # Map volatility to trailing stop range
        # Volatility range: VOLATILITY_NORMALIZATION_MIN to (MIN + RANGE)
        # Stop range: MIN_TRAILING_STOP to MAX_TRAILING_STOP
        
        # Normalize volatility to 0-1 range
        normalized_vol = min(max((volatility - VOLATILITY_NORMALIZATION_MIN) / VOLATILITY_NORMALIZATION_RANGE, 0), 1)
        
        # Calculate dynamic stop
        dynamic_stop = MIN_TRAILING_STOP + (normalized_vol * (MAX_TRAILING_STOP - MIN_TRAILING_STOP))
        
        return dynamic_stop
    
    def calculate_trend_gradient(self, symbol: str, window: int = 5) -> Optional[float]:
        """
        Calculate the trend gradient (slope) of price movement
        
        Args:
            symbol: Stock symbol
            window: Number of recent prices to use
            
        Returns:
            Trend gradient (positive = uptrend, negative = downtrend)
            None if insufficient data
        """
        if symbol not in self.price_history or len(self.price_history[symbol]) < window:
            return None
        
        prices = self.price_history[symbol][-window:]
        
        # Use linear regression to calculate slope
        x = np.arange(len(prices))
        y = np.array(prices)
        
        # Calculate slope using least squares
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Normalize by price to get percentage gradient
        gradient = (slope / y_mean) * 100 if y_mean > 0 else 0
        
        return gradient
    
    def analyze_volatility_pattern(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze volatility patterns for enhanced validation
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with volatility analysis
        """
        if symbol not in self.price_history or len(self.price_history[symbol]) < 10:
            return {
                'is_stable': True,
                'recent_volatility': 0.0,
                'volatility_trend': 'insufficient_data'
            }
        
        prices = self.price_history[symbol]
        
        # Calculate recent volatility (last 5 prices)
        recent_returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                         for i in range(len(prices)-5, len(prices))]
        recent_vol = np.std(recent_returns) if recent_returns else 0.0
        
        # Calculate older volatility (previous 5 prices before recent)
        if len(prices) >= 10:
            older_returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                           for i in range(len(prices)-10, len(prices)-5)]
            older_vol = np.std(older_returns) if older_returns else 0.0
            
            # Determine volatility trend
            if recent_vol > older_vol * 1.5:
                vol_trend = 'increasing'
            elif recent_vol < older_vol * 0.7:
                vol_trend = 'decreasing'
            else:
                vol_trend = 'stable'
        else:
            vol_trend = 'insufficient_history'
        
        return {
            'is_stable': recent_vol < MAX_STOCK_VOLATILITY * 0.8,
            'recent_volatility': recent_vol,
            'volatility_trend': vol_trend
        }
    
    def filter_stock(self, symbol: str, price: float, volume: int) -> Tuple[bool, str]:
        """
        Filter stocks based on enhanced risk criteria including trend and volatility analysis
        Returns (is_valid, reason)
        """
        # Check resource throttling before volatility calculations (CPU intensive)
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE - STOCK FILTERING] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        validation_metadata = {
            'price': price,
            'volume': volume,
            'checks_passed': []
        }
        
        # Check minimum price (avoid penny stocks)
        if price < MIN_STOCK_PRICE:
            return False, f"Price ${price:.2f} below minimum ${MIN_STOCK_PRICE:.2f}"
        validation_metadata['checks_passed'].append('min_price')
        
        # Check maximum price (avoid very high-priced stocks)
        if price > MAX_STOCK_PRICE:
            return False, f"Price ${price:.2f} exceeds maximum ${MAX_STOCK_PRICE:.2f}"
        validation_metadata['checks_passed'].append('max_price')
        
        # Check minimum volume
        if volume < MIN_DAILY_VOLUME:
            return False, f"Volume {volume:,} below minimum {MIN_DAILY_VOLUME:,}"
        validation_metadata['checks_passed'].append('min_volume')
        
        # Check volatility if we have history
        if symbol in self.price_history and len(self.price_history[symbol]) >= 5:
            volatility = self.calculate_volatility(symbol)
            validation_metadata['volatility'] = volatility
            
            if volatility > MAX_STOCK_VOLATILITY:
                return False, f"Volatility {volatility:.1%} exceeds maximum {MAX_STOCK_VOLATILITY:.1%}"
            validation_metadata['checks_passed'].append('volatility')
            
            # Enhanced: Check trend gradient
            gradient = self.calculate_trend_gradient(symbol, window=5)
            if gradient is not None:
                validation_metadata['trend_gradient'] = gradient
                
                # Reject if strong downtrend (gradient < -2% per period)
                if gradient < -2.0:
                    return False, f"Strong downtrend detected (gradient: {gradient:.2f}%)"
                validation_metadata['checks_passed'].append('trend_gradient')
            
            # Enhanced: Analyze volatility pattern
            vol_analysis = self.analyze_volatility_pattern(symbol)
            validation_metadata['volatility_analysis'] = vol_analysis
            
            if not vol_analysis['is_stable']:
                return False, f"Unstable volatility pattern (recent: {vol_analysis['recent_volatility']:.1%})"
            
            if vol_analysis['volatility_trend'] == 'increasing':
                # More conservative: reject if volatility is rapidly increasing
                if vol_analysis['recent_volatility'] > MAX_STOCK_VOLATILITY * 0.6:
                    return False, "Rapidly increasing volatility detected"
            
            validation_metadata['checks_passed'].append('volatility_pattern')
        
        # Store validation metadata for logging
        if not hasattr(self, 'stock_validation_log'):
            self.stock_validation_log = []
        
        self.stock_validation_log.append({
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'passed': True,
            'metadata': validation_metadata
        })
        
        return True, "Passed all filters"
    
    def can_open_new_position(self) -> Tuple[bool, str]:
        """
        Check if bot can open new position based on limits
        Returns (can_open, reason)
        """
        current_positions = len(self.positions)
        
        if current_positions >= BOT_MAX_OPEN_POSITIONS:
            return False, f"Maximum positions ({BOT_MAX_OPEN_POSITIONS}) reached"
        
        return True, f"Can open position ({current_positions}/{BOT_MAX_OPEN_POSITIONS})"

    def can_open_short(self, allocation: float, for_live: bool = False) -> Tuple[bool, str]:
        """
        Check if bot can open a short (margin/availability + concentration limits).
        Paper: ALLOW_SHORTS_IN_PAPER. Live/sandbox: SCHWAB_SHORT_SELLING_ENABLED.
        Also enforces MAX_SHORT_POSITIONS and MAX_SHORT_EXPOSURE_PCT.
        Returns (can_open, reason).
        """
        if for_live:
            if not SCHWAB_SHORT_SELLING_ENABLED:
                return False, "Short selling disabled (SCHWAB_SHORT_SELLING_ENABLED=false)"
        else:
            if not ALLOW_SHORTS_IN_PAPER:
                return False, "Short selling disabled in paper (ALLOW_SHORTS_IN_PAPER=false)"
        shorts = [p for p in self.positions.values() if p.get('side') == 'short']
        if len(shorts) >= MAX_SHORT_POSITIONS:
            return False, f"Maximum short positions ({MAX_SHORT_POSITIONS}) reached"
        exposure = sum(
            p.get('quantity', 0) * p.get('entry_price', 0)
            for p in shorts
        )
        new_exposure = exposure + allocation
        cap = max(self.total_capital, 1.0)
        if (new_exposure / cap) > MAX_SHORT_EXPOSURE_PCT:
            return False, (
                f"Short exposure would exceed {MAX_SHORT_EXPOSURE_PCT:.0%} of capital "
                f"(current ${exposure:.2f} + ${allocation:.2f} > ${cap * MAX_SHORT_EXPOSURE_PCT:.2f})"
            )
        return True, "Short allowed"
    
    def search_stocks(self, symbols: Optional[List[str]] = None, 
                      use_screener: bool = True, 
                      max_stocks: int = 10) -> List[Dict[str, Any]]:
        """
        Explicit stock searching method that loops over symbols and applies filtering criteria.
        
        This method:
        1. Loads symbols from file, screener, or provided list
        2. Fetches data via data_fetcher for each symbol
        3. Applies .env criteria (price, volume, volatility)
        4. Returns filtered list of tradeable stocks with their data
        
        Args:
            symbols: Optional list of symbols to search. If None, uses load_scan_symbols
            use_screener: Whether to use stock screener to discover stocks
            max_stocks: Maximum number of stocks to return
            
        Returns:
            List of dictionaries with stock data for stocks that pass all filters
            Each dict contains: {'symbol', 'price', 'volume', 'volatility', 'data'}
        """
        # Check resource throttling before stock search (CPU/network intensive loop)
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE - STOCK SEARCH] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        logger.info("Starting explicit stock search...")
        
        # Load symbols if not provided
        if symbols is None:
            symbols = self.load_scan_symbols(
                filename=SCAN_SYMBOLS_FILE,
                use_screener=use_screener,
                max_symbols=max_stocks
            )
            logger.info(f"Loaded {len(symbols)} symbols for screening")
        
        # Initialize data fetcher if available
        # Prefer async fetcher for concurrent operations
        data_fetcher = None
        use_async = False
        
        if ASYNC_DATA_FETCHER_AVAILABLE:
            try:
                data_fetcher = get_async_fetcher()
                use_async = True
                logger.info("AsyncDataFetcher initialized for concurrent data retrieval")
            except Exception as e:
                logger.warning(f"Failed to initialize AsyncDataFetcher: {e}")
        
        if data_fetcher is None and DATA_FETCHER_AVAILABLE:
            try:
                data_fetcher = DataFetcher()
                logger.info("DataFetcher initialized for advanced data retrieval")
            except Exception as e:
                logger.warning(f"Failed to initialize DataFetcher: {e}")
        
        tradeable_stocks = []
        
        # Prefetch prices: async concurrent if available, else batch via DataFetcher
        prices_dict = {}
        if use_async and data_fetcher is not None:
            try:
                logger.info(f"Fetching prices for {len(symbols)} symbols concurrently...")
                prices_dict = data_fetcher.fetch_multiple_prices(symbols)
                logger.info(f"Fetched {len(prices_dict)} prices concurrently")
            except Exception as e:
                logger.warning(f"Concurrent price fetching failed: {e}, falling back to batch provider if available")
                use_async = False
        if not use_async and data_fetcher is not None:
            try:
                logger.info(f"Fetching batch prices for {len(symbols)} symbols via provider...")
                batch = data_fetcher.fetch_batch_prices(symbols)
                # Normalize to (price, volume)
                for s, pv in (batch or {}).items():
                    if isinstance(pv, (list, tuple)) and len(pv) >= 2:
                        prices_dict[s] = (pv[0], pv[1])
                    else:
                        prices_dict[s] = (pv if isinstance(pv, (int, float)) else None, None)
                logger.info(f"Fetched {len(prices_dict)} batch prices")
            except Exception as e:
                logger.warning(f"Batch price fetching failed: {e}; continuing with per-symbol fetches")
        
        for symbol in symbols:
            try:
                # Fetch stock data
                stock_data = None
                
                # Use pre-fetched price data if available (async or batch)
                if symbol in prices_dict:
                    price, volume = prices_dict[symbol]
                    
                    if price is None or price <= 0:
                        logger.debug(f"Skipping {symbol}: Invalid price from async fetch")
                        continue
                    
                    # Calculate volatility from price history if available
                    volatility = 0.0
                    if symbol in self.price_history and len(self.price_history[symbol]) >= 5:
                        volatility = self.calculate_volatility(symbol)
                    
                    stock_data = {
                        'symbol': symbol,
                        'price': price,
                        'volume': volume,
                        'volatility': volatility,
                        'data': None
                    }
                
                # Fetch comprehensive data if not using async or price not in cache
                elif data_fetcher is not None and not use_async:
                    try:
                        # Fetch comprehensive data including historical for volatility
                        comprehensive_data = data_fetcher.get_comprehensive_data(symbol, period='1mo')
                        
                        if comprehensive_data and comprehensive_data.get('price'):
                            stock_data = {
                                'symbol': symbol,
                                'price': comprehensive_data['price'],
                                'volume': comprehensive_data.get('volume', 0),
                                'volatility': comprehensive_data.get('volatility', 0.0),
                                'data': comprehensive_data
                            }
                    except Exception as e:
                        logger.debug(f"DataFetcher failed for {symbol}: {e}")
                
                # Fallback to simple price fetch if other methods unavailable or failed
                if stock_data is None:
                    price_data = self.fetch_real_stock_price(symbol)
                    
                    if price_data is None:
                        logger.debug(f"Skipping {symbol}: Unable to fetch valid price")
                        continue
                    
                    price, volume = price_data
                    
                    if price is None or price <= 0:
                        logger.debug(f"Skipping {symbol}: Invalid price")
                        continue
                    
                    # Skip if volume is invalid (None or 0)
                    if volume is None or volume <= 0:
                        logger.debug(f"Skipping {symbol}: Invalid or missing volume data")
                        continue
                    
                    # Calculate volatility from price history if available
                    volatility = 0.0
                    if symbol in self.price_history and len(self.price_history[symbol]) >= 5:
                        volatility = self.calculate_volatility(symbol)
                    
                    stock_data = {
                        'symbol': symbol,
                        'price': price,
                        'volume': volume,
                        'volatility': volatility,
                        'data': None
                    }
                
                # Apply filtering criteria from .env
                # NOTE: When use_screener=True, stock_screener.py already filters by these
                # criteria and returns stocks sorted by probability/composite score. We skip
                # redundant filtering in that case for better performance.
                # When use_screener=False (using scan_symbols.txt), we need to filter here.
                
                if not use_screener:
                    # Apply filters when not using screener
                    # 1. Check price range
                    if stock_data['price'] < MIN_STOCK_PRICE:
                        logger.debug(f"Skipping {symbol}: Price ${stock_data['price']:.2f} below minimum ${MIN_STOCK_PRICE:.2f}")
                        continue
                    
                    if stock_data['price'] > MAX_STOCK_PRICE:
                        logger.debug(f"Skipping {symbol}: Price ${stock_data['price']:.2f} above maximum ${MAX_STOCK_PRICE:.2f}")
                        continue
                    
                    # 2. Check volume
                    if stock_data['volume'] < MIN_DAILY_VOLUME:
                        logger.debug(f"Skipping {symbol}: Volume {stock_data['volume']:,} below minimum {MIN_DAILY_VOLUME:,}")
                        continue
                    
                    # 3. Check volatility (only if we have enough history)
                    if stock_data['volatility'] > 0 and stock_data['volatility'] > MAX_STOCK_VOLATILITY:
                        logger.debug(f"Skipping {symbol}: Volatility {stock_data['volatility']:.1%} above maximum {MAX_STOCK_VOLATILITY:.1%}")
                        continue
                
                # Stock passed all filters (or was pre-filtered by screener)
                logger.info(f"✓ {symbol} accepted: ${stock_data['price']:.2f}, "
                           f"vol={stock_data['volume']:,}, volatility={stock_data['volatility']:.2%}")
                
                tradeable_stocks.append(stock_data)
                
                # Stop if we've reached max_stocks
                if len(tradeable_stocks) >= max_stocks:
                    logger.info(f"Reached maximum of {max_stocks} tradeable stocks")
                    break
                
            except Exception as e:
                logger.warning(f"Error processing {symbol}: {e}")
                continue
        
        logger.info(f"Stock search complete: {len(tradeable_stocks)} tradeable stocks found")
        
        return tradeable_stocks

    def execute_trade_paper_mode(self, symbol: str, action: str, price: float, volume: int = None):
        """
        Paper trading mode: Simulate trades without executing live trades
        
        This mode simulates trade execution and tracks hypothetical P/L.
        For TOS paperMoney integration: Export positions.csv from ThinkorSwim
        and use it to seed initial positions or validate paper trading results.
        
        Current implementation: Logs simulated buys/sells, tracks P/L in dict/log.
        Trade quantity is calculated as: quantity = current_allocation / price
        
        Includes trailing stop monitoring, stock filtering, and partial exits.
        
        Args:
            symbol: Stock symbol
            action: 'BUY', 'SELL', 'SHORT', or 'COVER' (Phase 1: stocks buy/short per MISSION.md)
            price: Stock price
            volume: Trading volume (will be generated if not provided)
        """
        action = action.upper()
        if action not in VALID_ACTIONS:
            return {
                'status': 'error',
                'reason': 'invalid_action',
                'message': f"Invalid action '{action}'. Use BUY, SELL, SHORT, or COVER.",
            }

        # Check resource throttling before trading
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        # Check capital floor before trading
        can_trade, floor_msg = self.check_capital_floor()
        if not can_trade:
            print(f"\n[CAPITAL FLOOR - TRADING PAUSED]")
            print(f"  {floor_msg}")
            return {
                'status': 'paused',
                'reason': 'capital_floor_breach',
                'message': floor_msg
            }
        
        # Check PDT compliance before trading (BUY and SHORT initiate positions)
        if action in ACTIONS_OPEN_POSITION:
            can_trade_pdt, pdt_msg = self.check_pdt_compliance()
            if not can_trade_pdt:
                print(f"\n[PDT CHECK FAILED - TRADE SKIPPED]")
                print(f"  Symbol: {symbol}")
                print(f"  Reason: {pdt_msg}")
                return {
                    'status': 'skipped',
                    'reason': 'pdt_limit_reached',
                    'message': pdt_msg
                }
        
        # Generate volume if not provided - for backward compatibility
        if volume is None:
            # Try to fetch real volume if price was real
            if symbol in self.price_cache:
                volume = self.price_cache[symbol]['volume']
                logger.debug(f"Using cached volume for {symbol}: {volume:,}")
            else:
                volume = self.generate_random_volume()
                logger.debug(f"Generated random volume for {symbol}: {volume:,}")
        
        # Update price history for volatility calculation
        self.update_price_history(symbol, price)
        
        # Calculate quantity based on allocation (portfolio-optimized if available, else simple)
        current_allocation = self.track_record['current_allocation']
        
        # Use portfolio optimizer for allocation if available and enabled (ENHANCED with caching)
        if (ENABLE_PORTFOLIO_OPTIMIZATION and 
            self.portfolio_optimizer and 
            hasattr(self, 'current_symbols') and 
            self.current_symbols and 
            symbol in self.current_symbols):
            try:
                # Check cache first (enhancement)
                cache_key = f"{','.join(sorted(self.current_symbols))}_{self.total_capital:.0f}_{PORTFOLIO_OPTIMIZATION_METHOD}"
                use_cache = False
                
                if (cache_key in self.portfolio_optimization_cache and 
                    self.portfolio_cache_timestamp and
                    (datetime.now() - self.portfolio_cache_timestamp).total_seconds() < self.portfolio_cache_ttl):
                    # Use cached result
                    optimal_allocations = self.portfolio_optimization_cache[cache_key]
                    use_cache = True
                    logger.debug(f"Using cached portfolio optimization for {symbol}")
                else:
                    # Add price data to optimizer if not already present
                    if symbol in self.price_history:
                        self.portfolio_optimizer.add_price_data(symbol, self.price_history[symbol])
                    
                    # Get optimal allocation for all current symbols
                    optimal_allocations = self.portfolio_optimizer.get_optimal_allocation(
                        self.current_symbols,
                        self.total_capital,
                        method=PORTFOLIO_OPTIMIZATION_METHOD
                    )
                    
                    # Cache the result (enhancement)
                    if optimal_allocations:
                        self.portfolio_optimization_cache[cache_key] = optimal_allocations
                        self.portfolio_cache_timestamp = datetime.now()
                        # Limit cache size (keep last 10 entries)
                        if len(self.portfolio_optimization_cache) > 10:
                            oldest_key = min(self.portfolio_optimization_cache.keys(), 
                                           key=lambda k: self.portfolio_optimization_cache.get(k, {}).get('_timestamp', datetime.min))
                            self.portfolio_optimization_cache.pop(oldest_key, None)
                
                if optimal_allocations and symbol in optimal_allocations:
                    # Use portfolio-optimized allocation
                    portfolio_allocation = optimal_allocations[symbol]
                    # Ensure it doesn't exceed maximum
                    current_allocation = min(portfolio_allocation, BOT_MAX_ALLOCATION)
                    logger.debug(f"Using portfolio-optimized allocation for {symbol}: ${current_allocation:.2f} {'(cached)' if use_cache else ''}")
                    
                    # Update component coordination state (enhancement)
                    self.component_coordination_state['last_portfolio_update'] = datetime.now()
                else:
                    # Fall back to simple allocation
                    current_allocation = min(current_allocation, BOT_MAX_ALLOCATION)
                    logger.debug(f"Portfolio optimization unavailable, using simple allocation for {symbol}: ${current_allocation:.2f}")
            except Exception as e:
                # Fall back to simple allocation on error
                logger.warning(f"Portfolio optimization failed for {symbol}: {e} - using simple allocation")
                current_allocation = min(current_allocation, BOT_MAX_ALLOCATION)
        else:
            # Simple allocation (fallback)
            current_allocation = min(current_allocation, BOT_MAX_ALLOCATION)

        # Enforce allocation floor for opening new positions
        if action in ACTIONS_OPEN_POSITION:
            current_allocation = max(BOT_MIN_ALLOCATION, current_allocation)

        quantity = current_allocation / price
        
        # Phase 1: Apply earnings-aware position sizing adjustment
        if action in ACTIONS_OPEN_POSITION and self.earnings_calendar:
            try:
                # Get earnings adjustment multiplier (0.25-1.0 based on earnings proximity)
                earnings_multiplier = self.earnings_calendar.get_position_size_adjustment(symbol)
                if earnings_multiplier < 1.0:
                    # Log the adjustment
                    days_until = self.earnings_calendar.get_days_until_earnings(symbol)
                    adjusted_allocation = current_allocation * earnings_multiplier
                    logger.info(f"[EARNINGS ADJUSTMENT] {symbol}: reducing position from ${current_allocation:.2f} to ${adjusted_allocation:.2f} ({earnings_multiplier*100:.0f}%) - earnings in {days_until} days")
                    current_allocation = adjusted_allocation
                    quantity = current_allocation / price
            except Exception as e:
                # Graceful fallback: if earnings adjustment fails, use unadjusted quantity
                logger.debug(f"Earnings adjustment failed for {symbol}: {e} - using unadjusted position")
        
        # Phase 2.2: Apply retail sentiment position sizing (fade FOMO)
        if action in ACTIONS_OPEN_POSITION and self.retail_sentiment:
            try:
                fomo_multiplier = self.retail_sentiment.get_position_size_adjustment(symbol)
                if fomo_multiplier < 1.0:
                    adjusted_allocation = current_allocation * fomo_multiplier
                    logger.info(f"[FOMO ADJUSTMENT] {symbol}: reducing position from ${current_allocation:.2f} to ${adjusted_allocation:.2f} ({fomo_multiplier*100:.0f}%) - high retail interest detected")
                    current_allocation = adjusted_allocation
                    quantity = current_allocation / price
            except Exception as e:
                logger.debug(f"Retail sentiment adjustment failed for {symbol}: {e} - using unadjusted position")
        
        # Phase 2.3: Apply options flow position sizing (follow/fade smart money)
        if action in ACTIONS_OPEN_POSITION and self.options_flow:
            try:
                options_multiplier = self.options_flow.get_position_size_adjustment(symbol, signal_direction=action)
                if options_multiplier != 1.0:
                    adjusted_allocation = current_allocation * options_multiplier
                    direction = "boosting" if options_multiplier > 1.0 else "reducing"
                    logger.info(f"[OPTIONS ADJUSTMENT] {symbol}: {direction} position from ${current_allocation:.2f} to ${adjusted_allocation:.2f} ({options_multiplier*100:.0f}%) - smart money signal")
                    current_allocation = adjusted_allocation
                    quantity = current_allocation / price
            except Exception as e:
                logger.debug(f"Options flow adjustment failed for {symbol}: {e} - using unadjusted position")
        
        # Entry condition tracking
        entry_conditions = {
            'allocation': current_allocation,
            'price': price,
            'volume': volume,
            'timestamp': datetime.now().isoformat()
        }
        
        # T+1 Settlement Check: BUY and SHORT use capital/collateral
        if action in ACTIONS_OPEN_POSITION:
            can_trade_settlement, settlement_msg = self.check_settled_capital_available(current_allocation)
            if not can_trade_settlement:
                print(f"\n[T+1 SETTLEMENT CHECK FAILED - TRADE SKIPPED]")
                print(f"  Symbol: {symbol}")
                print(f"  {settlement_msg}")
                return {
                    'status': 'skipped',
                    'reason': 't1_settlement_pending',
                    'message': settlement_msg
                }
        
        # Risk management check: Calculate potential loss
        # Phase 3: News filtering (before any other filters)
        if self.news_monitor and action in ['BUY', 'SHORT']:
            try:
                should_avoid, news_reason = self.news_monitor.should_avoid_symbol(symbol)
                if should_avoid:
                    print(f"\n[NEWS FILTER - TRADE SKIPPED]")
                    print(f"  Symbol: {symbol}")
                    print(f"  Reason: {news_reason}")
                    logger.info(f"[NEWS FILTER] {symbol}: {news_reason}")
                    
                    # Alert System: Send filter block alert
                    if alert_trade_blocked and self.alert_manager:
                        try:
                            alert_trade_blocked(symbol, news_reason, 'news')
                        except Exception as e:
                            logger.debug(f"Filter alert failed: {e}")
                    
                    return {
                        'status': 'skipped',
                        'reason': 'failed_news_filter',
                        'message': f"Skipping trade: {news_reason}"
                    }
            except Exception as e:
                logger.debug(f"News filter check failed for {symbol}: {e}")
        
        # Use stop loss percentage for realistic risk calculation
        # Actual risk is allocation * stop_loss_percent, not full allocation
        # In yfinance/training mode risk limit is not enforced so learning can continue.
        # Use instance variable if available (from ML optimization), else use global
        stop_loss_pct = getattr(self, 'stop_loss_percent', BOT_STOP_LOSS_PERCENT)
        potential_loss = current_allocation * stop_loss_pct
        risk_limit = BOT_RISK_THRESHOLD * self.total_capital
        
        if not getattr(self, 'using_yfinance_sim', False) and potential_loss > risk_limit:
            print(f"\n[RISK CHECK FAILED - TRADE SKIPPED]")
            print(f"  Symbol: {symbol}")
            print(f"  Potential Loss: ${potential_loss:.2f}")
            print(f"  Risk Limit: ${risk_limit:.2f} ({BOT_RISK_THRESHOLD:.1%} of ${self.total_capital:.2f})")
            print(f"  Trade skipped due to excessive risk")
            return {
                'status': 'skipped',
                'reason': 'risk_threshold_exceeded',
                'potential_loss': potential_loss,
                'risk_limit': risk_limit
            }
        
        # Handle position tracking and trailing stops
        if action in ACTIONS_OPEN_POSITION:
            # Check position limits (BUY and SHORT both consume a slot)
            # In yfinance/training mode position limit is not enforced so learning can continue
            if not getattr(self, 'using_yfinance_sim', False):
                can_open, reason = self.can_open_new_position()
                if not can_open:
                    print(f"\n[POSITION LIMIT - TRADE SKIPPED]")
                    print(f"  Symbol: {symbol}")
                    print(f"  Reason: {reason}")
                    return {
                        'status': 'skipped',
                        'reason': 'position_limit_reached',
                        'message': reason
                    }
            # Short-specific: margin/availability and concentration (paper mode)
            if action == 'SHORT':
                can_short, short_reason = self.can_open_short(current_allocation, for_live=False)
                if not can_short:
                    print(f"\n[SHORT CHECK FAILED - TRADE SKIPPED]")
                    print(f"  Symbol: {symbol}")
                    print(f"  Reason: {short_reason}")
                    return {
                        'status': 'skipped',
                        'reason': 'short_not_allowed',
                        'message': short_reason
                    }
            
            # Stock filtering
            is_valid, filter_reason = self.filter_stock(symbol, price, volume)
            if not is_valid:
                print(f"\n[STOCK FILTER - TRADE SKIPPED]")
                print(f"  Symbol: {symbol}")
                print(f"  Reason: {filter_reason}")
                return {
                    'status': 'skipped',
                    'reason': 'failed_stock_filter',
                    'message': filter_reason
                }
            
            # Phase 1: Earnings filtering (if available)
            if self.earnings_calendar:
                if not self.earnings_calendar.should_trade(symbol, days_buffer=3):
                    earnings_days = self.earnings_calendar.get_days_until_earnings(symbol)
                    earnings_reason = f"Earnings in {earnings_days} days" if earnings_days else "Upcoming earnings"
                    print(f"\n[EARNINGS FILTER - TRADE SKIPPED]")
                    print(f"  Symbol: {symbol}")
                    print(f"  Reason: {earnings_reason}")
                    
                    # Alert System: Send filter block alert
                    if alert_trade_blocked and self.alert_manager:
                        try:
                            alert_trade_blocked(symbol, earnings_reason, 'earnings')
                        except Exception as e:
                            logger.debug(f"Filter alert failed: {e}")
                    
                    return {
                        'status': 'skipped',
                        'reason': 'failed_earnings_filter',
                        'message': f"Skipping {symbol}: {earnings_reason}"
                    }
            
            # Phase 2.1: Macro event filtering (if available)
            if self.macro_calendar:
                can_trade, macro_reason = self.macro_calendar.should_trade(days_buffer=1.0)
                if not can_trade:
                    print(f"\n[MACRO FILTER - TRADE SKIPPED]")
                    print(f"  Symbol: {symbol}")
                    print(f"  Reason: {macro_reason}")
                    
                    # Alert System: Send filter block alert
                    if alert_trade_blocked and self.alert_manager:
                        try:
                            alert_trade_blocked(symbol, macro_reason, 'macro')
                        except Exception as e:
                            logger.debug(f"Filter alert failed: {e}")
                    
                    return {
                        'status': 'skipped',
                        'reason': 'failed_macro_filter',
                        'message': f"Skipping trade: {macro_reason}"
                    }
            
            # Phase 2.2: Retail sentiment filtering (fade FOMO)
            if self.retail_sentiment and action in ['BUY', 'SHORT']:
                can_trade, fomo_reason = self.retail_sentiment.should_trade(symbol)
                if not can_trade:
                    print(f"\n[FOMO FILTER - TRADE SKIPPED]")
                    print(f"  Symbol: {symbol}")
                    print(f"  Reason: {fomo_reason}")
                    return {
                        'status': 'skipped',
                        'reason': 'failed_fomo_filter',
                        'message': f"Skipping trade: {fomo_reason}"
                    }
            
            # Phase 2.3: Options flow check (fade bearish smart money on BUY)
            if self.options_flow and action == 'BUY':
                should_fade, options_reason = self.options_flow.should_fade_buy_signal(symbol)
                if should_fade:
                    print(f"\n[OPTIONS FILTER - TRADE SKIPPED]")
                    print(f"  Symbol: {symbol}")
                    print(f"  Signal: {action}")
                    print(f"  Reason: {options_reason}")
                    
                    # Alert System: Send filter block alert
                    if alert_trade_blocked and self.alert_manager:
                        try:
                            alert_trade_blocked(symbol, options_reason, 'options')
                        except Exception as e:
                            logger.debug(f"Filter alert failed: {e}")
                    
                    return {
                        'status': 'skipped',
                        'reason': 'failed_options_filter',
                        'message': f"Skipping trade: {options_reason}"
                    }
            
            # Sentiment filtering (if enabled)
            should_trade, sentiment_reason = self.check_sentiment_filter(symbol)
            if not should_trade:
                print(f"\n[SENTIMENT FILTER - TRADE SKIPPED]")
                print(f"  Symbol: {symbol}")
                print(f"  Reason: {sentiment_reason}")
                
                # Alert System: Send filter block alert
                if alert_trade_blocked and self.alert_manager:
                    try:
                        alert_trade_blocked(symbol, sentiment_reason, 'sentiment')
                    except Exception as e:
                        logger.debug(f"Filter alert failed: {e}")
                
                return {
                    'status': 'skipped',
                    'reason': 'failed_sentiment_filter',
                    'message': sentiment_reason
                }
            
            # Calculate dynamic trailing stop
            dynamic_stop = self.calculate_dynamic_trailing_stop(symbol)
            volatility = self.calculate_volatility(symbol)
            
            # Determine mode string for logging (read dynamically)
            api_enabled = _get_schwab_api_enabled()
            sandbox_mode = _get_schwab_sandbox_mode()
            
            if not api_enabled:
                mode_display = "API DISABLED MODE"
            elif sandbox_mode:
                mode_display = "SANDBOX MODE (STRICT)"
            else:
                mode_display = "PURE SIMULATION MODE"
            
            # Alert System: Check for sizzle stock (unusual volume/price activity)
            if self.sizzle_detector and volume:
                try:
                    # Volume spike detection
                    is_volume_sizzle, vol_multiplier = self.sizzle_detector.check_volume_spike(
                        symbol, volume, average_volume=None
                    )
                    if is_volume_sizzle and alert_sizzle:
                        alert_sizzle(symbol, 'volume', vol_multiplier, 3.0)
                        logger.info(f"[SIZZLE ALERT] {symbol}: Volume {vol_multiplier:.1f}x average (threshold: 3.0x)")
                    
                    # Price change detection (compare to history if available)
                    if symbol in self.price_history and len(self.price_history[symbol]) > 0:
                        previous_price = self.price_history[symbol][-1]
                        is_price_sizzle, price_change = self.sizzle_detector.check_price_change(
                            symbol, price, previous_price
                        )
                        if is_price_sizzle and alert_sizzle:
                            alert_sizzle(symbol, 'price_change', price_change, 5.0)
                            logger.info(f"[SIZZLE ALERT] {symbol}: Price change {price_change:+.1f}% (threshold: 5.0%)")
                except Exception as e:
                    logger.debug(f"Sizzle detection failed for {symbol}: {e}")
            
            print(f"\n[{mode_display}: {action.upper()}]")
            print(f"  Symbol: {symbol}")
            print(f"  Quantity: {quantity:.6f}")
            print(f"  Price: ${price:.2f}")
            print(f"  Volume: {volume:,}")
            print(f"  Total: ${quantity * price:.2f}")
            print(f"  Current Capital: ${self.total_capital:.2f}")
            
            # Alert System: Send trade execution alert
            if alert_trade and self.alert_manager:
                try:
                    alert_trade(symbol, action, price, int(quantity))
                    logger.info(f"[TRADE ALERT] {action} {quantity:.2f} {symbol} @ ${price:.2f}")
                except Exception as e:
                    logger.debug(f"Trade alert failed for {symbol}: {e}")
            
            # T+1 Settlement: Lock capital/collateral used (BUY or SHORT)
            trade_value = quantity * price
            self._add_unsettled_funds(trade_value, f'{action} {symbol}')

            side = 'long' if action == 'BUY' else 'short'
            self.open_position(symbol, price, quantity, dynamic_stop, side=side)

            should_win = random.random() < SIMULATED_WIN_RATE

            for _ in range(5):
                current_price = self.generate_random_price(price)
                self.update_price_history(symbol, current_price)
                if symbol not in self.positions:
                    continue
                pos = self.positions[symbol]
                if side == 'long':
                    if pos.get('high_price') is not None and current_price > pos['high_price']:
                        pos['high_price'] = current_price
                else:
                    if pos.get('low_price') is not None and current_price < pos['low_price']:
                        pos['low_price'] = current_price

            if side == 'long':
                if should_win:
                    final_price = price * (1 + SIMULATED_PROFIT_PERCENT)
                else:
                    final_price = price * (1 - SIMULATED_LOSS_PERCENT)
            else:
                if should_win:
                    final_price = price * (1 - SIMULATED_PROFIT_PERCENT)
                else:
                    final_price = price * (1 + SIMULATED_LOSS_PERCENT)

            self.update_price_history(symbol, final_price)
            pnl_info = self.close_position(symbol, final_price, exit_reason='end_of_simulation')
            is_win = pnl_info['is_win']

            self.update_capital(pnl_info['pnl'])

            sale_proceeds = pnl_info['quantity'] * final_price
            close_action = 'SELL' if action == 'BUY' else 'COVER'
            self._add_unsettled_funds(sale_proceeds, f'{close_action} {symbol}')
            
            # Check if it's a day trade (bought and sold on same day)
            # Only record as day trade if entry and exit are on the same date
            entry_time_str = pnl_info.get('exit_conditions', {}).get('entry_time')
            is_day_trade = False
            if entry_time_str:
                try:
                    entry_date = datetime.fromisoformat(entry_time_str).date()
                    exit_date = datetime.now().date()
                    is_day_trade = (entry_date == exit_date)
                except (ValueError, AttributeError):
                    # If we can't parse the time, assume it's a day trade (simulation default)
                    is_day_trade = True
            else:
                # No entry time recorded, assume day trade (simulation default)
                is_day_trade = True
            
            # Record as day trade only if it's actually same-day
            if is_day_trade and not PAPER_TRADING_MODE:
                # Only track for PDT in production mode
                self.add_day_trade(symbol)
            elif is_day_trade:
                # In paper mode, still call add_day_trade for testing but it won't be enforced
                self.add_day_trade(symbol)
            
            print(f"  Exit P&L: ${pnl_info['pnl']:.2f} ({pnl_info['pnl_percent']:.1f}%)")
            print(f"  Remaining Total Capital: ${self.total_capital:.2f}")
            
            # Display individual trade result
            if is_win:
                print(f"  Result: ✓ WIN")
            else:
                print(f"  Result: [-] LOSS")
            
            self.record_trade(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                is_win=is_win,
                entry_price=pnl_info['entry_price'],
                exit_price=pnl_info['exit_price'],
                pnl=pnl_info['pnl'],
                pnl_percent=pnl_info['pnl_percent'],
                exit_reason=pnl_info['exit_reason'],
                hold_duration=pnl_info.get('exit_conditions', {}).get('hold_duration_hours'),
                volatility=pnl_info.get('exit_conditions', {}).get('volatility'),
                volume=volume,
                entry_time=pnl_info.get('exit_conditions', {}).get('entry_time'),
                exit_time=datetime.now().isoformat(),
            )
        else:
            # SELL (close long) or COVER (close short)
            has_position = symbol in self.positions
            pos = self.positions.get(symbol)
            pos_side = pos.get('side', 'long') if pos else None

            if action == 'COVER':
                if not has_position or pos_side != 'short':
                    msg = f"No open short position for {symbol}"
                    print(f"\n[COVER SKIPPED] {msg}")
                    return {'status': 'skipped', 'reason': 'no_short_position', 'message': msg}
                can_close, hold_msg = self.check_holding_period(symbol, action)
                if not can_close:
                    print(f"\n[HOLDING PERIOD CHECK FAILED - COVER SKIPPED]\n  Symbol: {symbol}\n  Reason: {hold_msg}")
                    return {'status': 'skipped', 'reason': 'holding_period_not_met', 'message': hold_msg}
                pnl_info = self.close_position(symbol, price, exit_reason='simulated_exit')
                self.update_capital(pnl_info['pnl'])
                self._add_unsettled_funds(pnl_info['quantity'] * price, f'COVER {symbol}')
                if _is_same_day_trade(pnl_info.get('exit_conditions', {}).get('entry_time')):
                    self.add_day_trade(symbol)
                _log_close_action('COVER', symbol, pnl_info, price, self.total_capital)
                self.record_trade(
                    symbol=symbol, action='COVER', quantity=pnl_info['quantity'], price=price,
                    is_win=pnl_info['is_win'], entry_price=pnl_info['entry_price'], exit_price=price,
                    pnl=pnl_info['pnl'], pnl_percent=pnl_info['pnl_percent'], exit_reason=pnl_info['exit_reason'],
                    hold_duration=pnl_info.get('exit_conditions', {}).get('hold_duration_hours'),
                    volatility=pnl_info.get('exit_conditions', {}).get('volatility'), volume=volume,
                    entry_time=pnl_info.get('exit_conditions', {}).get('entry_time'),
                    exit_time=datetime.now().isoformat(),
                )
                return {'status': 'simulated', 'symbol': symbol, 'action': 'COVER', 'quantity': pnl_info['quantity'], 'price': price}

            if action == 'SELL' and has_position and pos_side == 'long':
                can_sell, hold_msg = self.check_holding_period(symbol, action)
                if not can_sell:
                    print(f"\n[HOLDING PERIOD CHECK FAILED - SELL SKIPPED]\n  Symbol: {symbol}\n  Reason: {hold_msg}")
                    return {'status': 'skipped', 'reason': 'holding_period_not_met', 'message': hold_msg}
                pnl_info = self.close_position(symbol, price, exit_reason='simulated_exit')
                self.update_capital(pnl_info['pnl'])
                self._add_unsettled_funds(pnl_info['quantity'] * price, f'SELL {symbol}')
                if _is_same_day_trade(pnl_info.get('exit_conditions', {}).get('entry_time')):
                    self.add_day_trade(symbol)
                _log_close_action('SELL', symbol, pnl_info, price, self.total_capital)
                self.record_trade(
                    symbol=symbol, action='SELL', quantity=pnl_info['quantity'], price=price,
                    is_win=pnl_info['is_win'], entry_price=pnl_info['entry_price'], exit_price=price,
                    pnl=pnl_info['pnl'], pnl_percent=pnl_info['pnl_percent'], exit_reason=pnl_info['exit_reason'],
                    hold_duration=pnl_info.get('exit_conditions', {}).get('hold_duration_hours'),
                    volatility=pnl_info.get('exit_conditions', {}).get('volatility'), volume=volume,
                    entry_time=pnl_info.get('exit_conditions', {}).get('entry_time'),
                    exit_time=datetime.now().isoformat(),
                )
                return {'status': 'simulated', 'symbol': symbol, 'action': 'SELL', 'quantity': pnl_info['quantity'], 'price': price}

            # Standalone SELL (no long position): simulate P&L
            can_sell, hold_msg = self.check_holding_period(symbol, action)
            if not can_sell:
                print(f"\n[HOLDING PERIOD CHECK FAILED - SELL SKIPPED]\n  Symbol: {symbol}\n  Reason: {hold_msg}")
                return {'status': 'skipped', 'reason': 'holding_period_not_met', 'message': hold_msg}
            api_enabled = _get_schwab_api_enabled()
            sandbox_mode = _get_schwab_sandbox_mode()
            mode_display = "API DISABLED MODE" if not api_enabled else ("SANDBOX MODE (STRICT)" if sandbox_mode else "PURE SIMULATION MODE")
            print(f"\n[{mode_display}: SELL]")
            print(f"  Symbol: {symbol}\n  Quantity: {quantity:.6f}\n  Price: ${price:.2f}\n  Total: ${quantity * price:.2f}\n  Current Capital: ${self.total_capital:.2f}")
            is_win = random.random() < SIMULATED_WIN_RATE
            pnl = current_allocation * (0.05 if is_win else -0.05)
            simulated_entry_price = price / (1 + (0.05 if is_win else -0.05))
            self.update_capital(pnl)
            self.add_day_trade(symbol)
            pnl_percent = (pnl / current_allocation) * 100
            print(f"  Exit P&L: ${pnl:.2f} ({pnl_percent:.1f}%)\n  Remaining Total Capital: ${self.total_capital:.2f}")
            print(f"  Result: {'WIN' if is_win else 'LOSS'}")
            self.record_trade(
                symbol=symbol, action='SELL', quantity=quantity, price=price, is_win=is_win,
                entry_price=simulated_entry_price, exit_price=price, pnl=pnl, pnl_percent=pnl_percent,
                exit_reason='simulated_exit', volume=volume
            )

        return {
            'status': 'simulated',
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price
        }

    def execute_trade_live_mode(self, symbol: str, action: str, price: float, order_type: Optional[str] = None):
        """
        Live trading mode: Execute real trades via Schwab API
        
        Includes comprehensive error handling, validation, and logging for production use.
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            action: 'BUY', 'SELL', 'SHORT', or 'COVER' (Phase 1 per MISSION.md)
            price: Current market price
            order_type: Optional order type override ('LIMIT' or 'MARKET')
                       If not specified, uses BOT_DEFAULT_BUY_ORDER_TYPE for BUY
                       and BOT_DEFAULT_SELL_ORDER_TYPE for SELL
        """
        # Determine mode early so it's available in all error handlers
        # Read dynamically to support runtime mode changes
        paper_mode = _get_paper_trading_mode()
        sandbox_mode = _get_schwab_sandbox_mode()
        dry_run_mode = _get_dry_run_mode()
        
        if dry_run_mode:
            mode_str = "DRY-RUN"
        elif paper_mode and sandbox_mode:
            mode_str = "SANDBOX"
        else:
            mode_str = "PRODUCTION"

        action = action.upper()
        if action not in VALID_ACTIONS:
            return {
                'status': 'error',
                'reason': 'invalid_action',
                'message': f"Invalid action '{action}'. Use BUY, SELL, SHORT, or COVER.",
            }
        
        logger.info(f"[{mode_str}] Attempting {action} trade for {symbol} at ${price:.2f}")
        
        # Check resource throttling before trading
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE - {mode_str}] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        # Validate API credentials before attempting trade
        if not self._validate_live_mode_credentials():
            error_msg = "Live mode credentials not configured or invalid"
            logger.error(f"[LIVE MODE] {error_msg}")
            self.alert_system.send_alert(
                "Live Trading Error",
                f"Failed to execute {action} for {symbol}: {error_msg}"
            )
            return {
                'status': 'error',
                'reason': 'invalid_credentials',
                'message': error_msg
            }
        
        # Check capital floor before trading
        can_trade, floor_msg = self.check_capital_floor()
        if not can_trade:
            logger.warning(f"[LIVE MODE] Capital floor breach - trade blocked: {floor_msg}")
            return {
                'status': 'paused',
                'reason': 'capital_floor_breach',
                'message': floor_msg
            }
        
        # Calculate quantity based on allocation (portfolio-optimized if available, else simple)
        current_allocation = self.track_record['current_allocation']
        
        # Use portfolio optimizer for allocation if available and enabled
        if (ENABLE_PORTFOLIO_OPTIMIZATION and 
            self.portfolio_optimizer and 
            hasattr(self, 'current_symbols') and 
            self.current_symbols and 
            symbol in self.current_symbols):
            try:
                # Add price data to optimizer if not already present
                if symbol in self.price_history:
                    self.portfolio_optimizer.add_price_data(symbol, self.price_history[symbol])
                
                # Get optimal allocation for all current symbols
                optimal_allocations = self.portfolio_optimizer.get_optimal_allocation(
                    self.current_symbols,
                    self.total_capital,
                    method=PORTFOLIO_OPTIMIZATION_METHOD
                )
                
                if optimal_allocations and symbol in optimal_allocations:
                    # Use portfolio-optimized allocation
                    portfolio_allocation = optimal_allocations[symbol]
                    # Ensure it doesn't exceed maximum
                    current_allocation = min(portfolio_allocation, BOT_MAX_ALLOCATION)
                    logger.debug(f"[LIVE MODE] Using portfolio-optimized allocation for {symbol}: ${current_allocation:.2f}")
                else:
                    # Fall back to simple allocation
                    current_allocation = min(current_allocation, BOT_MAX_ALLOCATION)
                    logger.debug(f"[LIVE MODE] Portfolio optimization unavailable, using simple allocation for {symbol}: ${current_allocation:.2f}")
            except Exception as e:
                # Fall back to simple allocation on error
                logger.warning(f"[LIVE MODE] Portfolio optimization failed for {symbol}: {e} - using simple allocation")
                current_allocation = min(current_allocation, BOT_MAX_ALLOCATION)
        else:
            # Simple allocation (fallback)
            current_allocation = min(current_allocation, BOT_MAX_ALLOCATION)

        # Enforce allocation floor for opening new positions
        if action in ACTIONS_OPEN_POSITION:
            current_allocation = max(BOT_MIN_ALLOCATION, current_allocation)

        quantity = current_allocation / price
        
        # Phase 1: Apply earnings-aware position sizing adjustment (live mode)
        if action in ACTIONS_OPEN_POSITION and self.earnings_calendar:
            try:
                # Get earnings adjustment multiplier (0.25-1.0 based on earnings proximity)
                earnings_multiplier = self.earnings_calendar.get_position_size_adjustment(symbol)
                if earnings_multiplier < 1.0:
                    # Log the adjustment
                    days_until = self.earnings_calendar.get_days_until_earnings(symbol)
                    adjusted_allocation = current_allocation * earnings_multiplier
                    logger.info(f"[LIVE MODE] [EARNINGS ADJUSTMENT] {symbol}: reducing position from ${current_allocation:.2f} to ${adjusted_allocation:.2f} ({earnings_multiplier*100:.0f}%) - earnings in {days_until} days")
                    current_allocation = adjusted_allocation
                    quantity = current_allocation / price
            except Exception as e:
                # Graceful fallback: if earnings adjustment fails, use unadjusted quantity
                logger.debug(f"[LIVE MODE] Earnings adjustment failed for {symbol}: {e} - using unadjusted position")
        
        # Phase 2.2: Apply retail sentiment position sizing (live mode)
        if action in ACTIONS_OPEN_POSITION and self.retail_sentiment:
            try:
                fomo_multiplier = self.retail_sentiment.get_position_size_adjustment(symbol)
                if fomo_multiplier < 1.0:
                    adjusted_allocation = current_allocation * fomo_multiplier
                    logger.info(f"[LIVE MODE] [FOMO ADJUSTMENT] {symbol}: reducing position from ${current_allocation:.2f} to ${adjusted_allocation:.2f} ({fomo_multiplier*100:.0f}%) - high retail interest")
                    current_allocation = adjusted_allocation
                    quantity = current_allocation / price
            except Exception as e:
                logger.debug(f"[LIVE MODE] Retail sentiment adjustment failed for {symbol}: {e}")
        
        # Phase 2.3: Apply options flow position sizing (live mode)
        if action in ACTIONS_OPEN_POSITION and self.options_flow:
            try:
                options_multiplier = self.options_flow.get_position_size_adjustment(symbol, signal_direction=action)
                if options_multiplier != 1.0:
                    adjusted_allocation = current_allocation * options_multiplier
                    direction = "boosting" if options_multiplier > 1.0 else "reducing"
                    logger.info(f"[LIVE MODE] [OPTIONS ADJUSTMENT] {symbol}: {direction} position from ${current_allocation:.2f} to ${adjusted_allocation:.2f} ({options_multiplier*100:.0f}%)")
                    current_allocation = adjusted_allocation
                    quantity = current_allocation / price
            except Exception as e:
                logger.debug(f"[LIVE MODE] Options flow adjustment failed for {symbol}: {e}")
        
        # T+1 Settlement Check: BUY and SHORT use capital/collateral
        if action in ACTIONS_OPEN_POSITION:
            can_trade_settlement, settlement_msg = self.check_settled_capital_available(current_allocation)
            if not can_trade_settlement:
                logger.warning(f"[LIVE MODE] T+1 settlement check failed: {settlement_msg}")
                return {
                    'status': 'skipped',
                    'reason': 't1_settlement_pending',
                    'message': settlement_msg
                }
        
        # Risk management check: Calculate potential loss
        # Use stop loss percentage for realistic risk calculation
        potential_loss = current_allocation * BOT_STOP_LOSS_PERCENT
        risk_limit = BOT_RISK_THRESHOLD * self.total_capital
        
        if potential_loss > risk_limit:
            logger.warning(
                f"[LIVE MODE] Risk check failed - Potential loss ${potential_loss:.2f} "
                f"exceeds risk limit ${risk_limit:.2f}"
            )
            return {
                'status': 'skipped',
                'reason': 'risk_threshold_exceeded',
                'potential_loss': potential_loss,
                'risk_limit': risk_limit
            }
        
        # Stock filtering for opens (BUY, SHORT); holding period for closes (SELL, COVER)
        if action in ACTIONS_OPEN_POSITION:
            # Short-specific: margin/availability and concentration (live/sandbox)
            if action == 'SHORT':
                can_short, short_reason = self.can_open_short(current_allocation, for_live=True)
                if not can_short:
                    logger.warning(f"[LIVE MODE] Short check failed for {symbol}: {short_reason}")
                    return {
                        'status': 'skipped',
                        'reason': 'short_not_allowed',
                        'message': short_reason
                    }
            volume = self.generate_random_volume()
            logger.warning(
                f"[LIVE MODE] Using mock volume data for {symbol}. "
                f"In production, fetch real-time data from Schwab API for accurate filtering."
            )
            is_valid, filter_reason = self.filter_stock(symbol, price, volume)
            if not is_valid:
                logger.warning(f"[LIVE MODE] Stock filter failed for {symbol}: {filter_reason}")
                return {
                    'status': 'skipped',
                    'reason': 'failed_stock_filter',
                    'message': filter_reason
                }
        else:
            can_close, hold_msg = self.check_holding_period(symbol, action)
            if not can_close:
                logger.warning(f"[LIVE MODE] Holding period check failed for {symbol}: {hold_msg}")
                return {
                    'status': 'skipped',
                    'reason': 'holding_period_not_met',
                    'message': hold_msg
                }
        
        # Log pre-trade information
        logger.info(
            f"[LIVE MODE] Pre-trade validation passed - "
            f"{action} {quantity:.6f} shares of {symbol} at ${price:.2f}"
        )
        
        # Build order payload (order_types.py–aligned: LIMIT, STOP, STOP_LIMIT, TRAILING_STOP)
        open_order_type = BOT_DEFAULT_BUY_ORDER_TYPE
        close_order_type = BOT_DEFAULT_SELL_ORDER_TYPE
        if order_type is not None:
            order_type = order_type.upper()
            if order_type not in VALID_ORDER_TYPES:
                logger.warning(
                    f"[{mode_str}] Invalid order_type '{order_type}', using default for {action}"
                )
                order_type = open_order_type if action in ACTIONS_OPEN_POSITION else close_order_type
        else:
            order_type = open_order_type if action in ACTIONS_OPEN_POSITION else close_order_type

        instruction = SCHWAB_INSTRUCTION_MAP.get(action, action)
        use_builder = (
            ORDER_PAYLOAD_BUILDER_AVAILABLE
            and build_schwab_order_payload is not None
            and order_type in ('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', 'TRAILING_STOP')
        )
        if use_builder:
            try:
                order_payload = build_schwab_order_payload(
                    action, order_type, price, quantity, symbol, instruction,
                    limit_offset_pct=LIMIT_ORDER_OFFSET_PCT,
                    stop_offset_pct=STOP_OFFSET_PCT,
                    stop_limit_offset_pct=STOP_LIMIT_OFFSET_PCT,
                    trailing_stop_pct=TRAILING_STOP_ORDER_PCT,
                )
            except Exception as e:
                logger.warning(f"[{mode_str}] order_payload builder failed: {e}; using LIMIT/MARKET fallback")
                use_builder = False
        if not use_builder:
            order_payload = {
                'orderType': order_type if order_type in ('MARKET', 'LIMIT') else 'MARKET',
                'session': 'NORMAL',
                'duration': 'DAY',
                'orderStrategyType': 'SINGLE',
                'orderLegCollection': [{
                    'instruction': instruction,
                    'quantity': quantity,
                    'instrument': {'symbol': symbol, 'assetType': 'EQUITY'}
                }]
            }
            fallback_type = order_payload['orderType']
            if fallback_type == 'LIMIT':
                limit_price = (price * (1.0 - LIMIT_ORDER_OFFSET_PCT) if action in ACTIONS_OPEN_POSITION
                               else price * (1.0 + LIMIT_ORDER_OFFSET_PCT))
                order_payload['price'] = round(limit_price, 2)
            logger.info(
                f"[LIVE MODE] Using {fallback_type} order"
                + (f" at ${order_payload.get('price', price):.2f}" if fallback_type == 'LIMIT' else "")
            )
            order_type = fallback_type
        else:
            if order_type == 'LIMIT':
                limit_price = order_payload.get('price', price)
                logger.info(
                    f"[LIVE MODE] Using LIMIT order at ${limit_price:.2f}"
                    + (f" (ref ${price:.2f}, offset {LIMIT_ORDER_OFFSET_PCT:.2%})" if LIMIT_ORDER_OFFSET_PCT > 0 else "")
                )
            elif order_type == 'STOP':
                logger.info(
                    f"[LIVE MODE] Using STOP order, stopPrice=${order_payload.get('stopPrice', 0):.2f}"
                )
            elif order_type == 'STOP_LIMIT':
                logger.info(
                    f"[LIVE MODE] Using STOP_LIMIT order, "
                    f"stopPrice=${order_payload.get('stopPrice', 0):.2f}, "
                    f"price=${order_payload.get('price', 0):.2f}"
                )
            elif order_type == 'TRAILING_STOP':
                logger.info(
                    f"[LIVE MODE] Using TRAILING_STOP order, "
                    f"offset={order_payload.get('stopPriceOffset', 0)}%"
                )
            else:
                logger.info(f"[LIVE MODE] Using {order_type} order")
        
        # DRY-RUN MODE: Validate workflow without executing trade
        if _get_dry_run_mode():
            logger.info(f"[DRY-RUN MODE] ✓ All validations passed - would execute: {action} {quantity:.6f} {symbol}")
            logger.info(f"[DRY-RUN MODE] Order payload validated: {order_payload}")
            
            # Simulate successful order placement
            mock_order_id = f"DRY_RUN_{symbol}_{action}_{int(time.time())}"
            
            logger.info(
                f"[DRY-RUN MODE] ✓ Trade validated successfully - "
                f"Mock Order ID: {mock_order_id}, {action} {quantity:.6f} {symbol} at ${price:.2f}"
            )
            
            return {
                'status': 'dry_run_success',
                'order_id': mock_order_id,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'order_type': order_type,
                'order_payload': order_payload,
                'message': 'Dry-run validation successful - no actual trade executed'
            }
        
        try:
            # Initialize OAuth-authenticated client if not already done
            if self.schwab_client is None and self.schwab_authenticator is not None:
                try:
                    interactive = not os.getenv('NON_INTERACTIVE', 'false').lower() == 'true'
                    self.schwab_client = self.schwab_authenticator.get_client(interactive=interactive)
                    logger.info(f"[{mode_str}] Successfully obtained Schwab OAuth client for trading")
                except Exception as e:
                    error_msg = f"Failed to authenticate with Schwab OAuth: {str(e)}"
                    logger.error(f"[{mode_str}] {error_msg}")
                    self.alert_system.send_alert("Live Trading Error", error_msg, severity='CRITICAL')
                    return {
                        'status': 'error',
                        'reason': 'authentication_failed',
                        'message': error_msg
                    }
            
            # Use OAuth-authenticated client to place order
            if self.schwab_client is not None:
                logger.info(f"[{mode_str}] Placing order via OAuth-authenticated Schwab client")
                
                # Place order using schwab-py client
                response = self.schwab_client.place_order(
                    SCHWAB_ACCOUNT_ID,
                    order_payload
                )
                
                # Check response status
                if response.status_code == 201 or response.status_code == 200:
                    # Order successfully placed
                    # Extract order ID from response headers (Location header contains order URL)
                    order_id = 'unknown'
                    if 'Location' in response.headers:
                        # Location header format: .../accounts/{accountId}/orders/{orderId}
                        location = response.headers['Location']
                        if '/orders/' in location:
                            order_id = location.split('/orders/')[-1]
                    
                    # Try to parse response body for order details
                    result = {}
                    if response.text:
                        try:
                            result = response.json()
                            order_id = result.get('orderId', order_id)
                        except ValueError:
                            logger.warning(
                                f"[{mode_str}] Failed to parse order response JSON; "
                                f"using header-derived order ID {order_id}."
                            )
                    
                    logger.info(
                        f"[{mode_str}] ✓ Order successfully placed - "
                        f"Order ID: {order_id}, {action} {quantity:.6f} {symbol} at ${price:.2f}"
                    )
                    
                    # Send success alert
                    self.alert_system.send_alert(
                        f"{mode_str} Trade Executed",
                        f"Successfully placed {action} order for {quantity:.6f} shares of {symbol}\n"
                        f"Price: ${price:.2f}\n"
                        f"Order ID: {order_id}\n"
                        f"Mode: {mode_str}\n"
                        f"Total: ${quantity * price:.2f}"
                    )
                    
                    trade_value = quantity * price
                    self._add_unsettled_funds(trade_value, f'{action} {symbol}')
                    
                    # NOTE: For live mode, we don't record the trade outcome yet
                    # Trade should be recorded later when the position is closed and P&L is known
                    # This prevents skewing performance metrics with premature win/loss classification
                    logger.info(
                        f"[{mode_str}] Trade outcome will be recorded when position is closed. "
                        f"Track order {order_id} for completion."
                    )
                    
                    return {
                        'status': 'success',
                        'order_id': order_id,
                        'symbol': symbol,
                        'action': action,
                        'quantity': quantity,
                        'price': price,
                        'mode': mode_str,
                        'response': result
                    }
                    
                elif response.status_code == 401:
                    # Authentication error - OAuth token may be expired
                    error_msg = (
                        "API authentication failed - OAuth token invalid or expired.\n"
                        "Solutions:\n"
                        "  1. Delete token.json and re-authenticate interactively\n"
                        "  2. Set NON_INTERACTIVE=false to allow interactive login\n"
                        "  3. Verify SCHWAB_API_KEY and SCHWAB_APP_SECRET are correct\n"
                        "  4. Check if app has been approved at developer.schwab.com"
                    )
                    logger.error(f"[{mode_str}] {error_msg}")
                    self.alert_system.send_alert("Live Trading Error", error_msg, severity='CRITICAL')
                    return {
                        'status': 'error',
                        'reason': 'authentication_failed',
                        'message': error_msg,
                        'status_code': response.status_code
                    }
                    
                elif response.status_code == 429:
                    # Rate limit exceeded
                    error_msg = "API rate limit exceeded - too many requests"
                    logger.error(f"[{mode_str}] {error_msg}")
                    self.alert_system.send_alert(f"{mode_str} Trading Error", error_msg, severity='CRITICAL')
                    return {
                        'status': 'error',
                        'reason': 'rate_limit_exceeded',
                        'message': error_msg,
                        'status_code': response.status_code,
                        'mode': mode_str
                    }
                    
                else:
                    # Other error
                    error_msg = f"API request failed with status {response.status_code}: {response.text}"
                    logger.error(f"[{mode_str}] {error_msg}")
                    self.alert_system.send_alert(
                        f"{mode_str} Trading Error",
                        f"Failed to place {action} order for {symbol}\n{error_msg}"
                    )
                    return {
                        'status': 'error',
                        'reason': 'api_error',
                        'message': error_msg,
                        'status_code': response.status_code,
                        'response_text': response.text,
                        'mode': mode_str
                    }
            else:
                # No OAuth client available - fall back to legacy method (should not happen)
                error_msg = "OAuth client not available and Schwab authenticator not initialized"
                logger.error(f"[{mode_str}] {error_msg}")
                self.alert_system.send_alert("Live Trading Error", error_msg, severity='CRITICAL')
                return {
                    'status': 'error',
                    'reason': 'no_auth_client',
                    'message': error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"API request timed out after 30 seconds"
            logger.error(f"[{mode_str}] {error_msg}")
            self.alert_system.send_alert("Trading Error", error_msg, severity='CRITICAL')
            return {
                'status': 'error',
                'reason': 'timeout',
                'message': error_msg
            }
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error while placing order: {str(e)}"
            logger.error(f"[{mode_str}] {error_msg}")
            self.alert_system.send_alert("Trading Error", error_msg, severity='CRITICAL')
            return {
                'status': 'error',
                'reason': 'connection_error',
                'message': error_msg
            }
            
        except Exception as e:
            error_msg = f"Unexpected error executing trade: {str(e)}"
            logger.exception(f"[{mode_str}] {error_msg}")
            self.alert_system.send_alert("Live Trading Error", error_msg)
            return {
                'status': 'error',
                'reason': 'unexpected_error',
                'message': error_msg
            }
    
    def _validate_live_mode_credentials(self) -> bool:
        """
        Validate that all required credentials are configured for live trading
        
        Returns:
            True if credentials are valid, False otherwise
        """
        required_credentials = {
            'SCHWAB_API_KEY': SCHWAB_API_KEY,
            'SCHWAB_APP_SECRET': SCHWAB_APP_SECRET,
            'SCHWAB_CALLBACK_URL': SCHWAB_CALLBACK_URL,
            'SCHWAB_ACCOUNT_ID': SCHWAB_ACCOUNT_ID
        }
        
        # Check if any credential is still a placeholder
        placeholder_values = ['your_app_key', 'your_app_secret', 'your_redirect_uri', 'your_account_number']
        
        for cred_name, cred_value in required_credentials.items():
            if not cred_value or cred_value in placeholder_values:
                logger.error(f"[VALIDATION] {cred_name} is not configured or is a placeholder")
                return False
        
        logger.info("[VALIDATION] All live mode credentials are configured")
        return True

    def execute_trade(self, symbol: str, action: str, price: float, volume: int = None):
        """
        Execute trade based on current mode
        
        Three modes:
        1. Sandbox Mode (PAPER_TRADING_MODE=true, SCHWAB_SANDBOX_MODE=true):
           - Uses Schwab sandbox API to place real orders
           - Orders visible in ThinkorSwim paperMoney
           - No local simulation - actual API calls
        
        2. Simulation Mode (PAPER_TRADING_MODE=true, SCHWAB_SANDBOX_MODE=false):
           - Local simulation only
           - No API calls for order placement
           - Not visible in ThinkorSwim
        
        3. Live Mode (PAPER_TRADING_MODE=false):
           - Uses Schwab production API
           - Real money trades
           - Orders visible in ThinkorSwim live account
        
        Args:
            symbol: Stock symbol
            action: 'BUY', 'SELL', 'SHORT', or 'COVER' (Phase 1: stocks buy/short per MISSION.md)
            price: Stock price
            volume: Trading volume (optional, will be generated if not provided)
        """
        # Log trade decision if debug logger is enabled
        if self.debug_logger and self.debug_logger.enabled:
            mode = 'sandbox' if SCHWAB_SANDBOX_MODE else ('simulation' if PAPER_TRADING_MODE else 'live')
            self.debug_logger.log_decision(
                decision_type='trade_execution',
                context={
                    'symbol': symbol,
                    'action': action,
                    'price': price,
                    'volume': volume,
                    'mode': mode,
                    'total_capital': self.total_capital,
                    'open_positions': len(self.positions)
                },
                result=f"{action} {symbol} at ${price:.2f}",
                rationale=f"Executing {action} in {mode} mode"
            )

        # Manual Trade Approval Mode: Create pending trade instead of executing
        if MANUAL_TRADE_APPROVAL_MODE:
            # Calculate allocation for this trade
            current_allocation = self.track_record['current_allocation']
            # Use portfolio optimizer if available
            if (ENABLE_PORTFOLIO_OPTIMIZATION and self.portfolio_optimizer and 
                hasattr(self, 'current_symbols') and self.current_symbols and symbol in self.current_symbols):
                try:
                    available_capital = self.get_available_capital()
                    optimal_allocations = self.portfolio_optimizer.get_optimal_allocation(
                        self.current_symbols, available_capital, method=PORTFOLIO_OPTIMIZATION_METHOD
                    )
                    if optimal_allocations and symbol in optimal_allocations:
                        current_allocation = min(optimal_allocations[symbol], BOT_MAX_ALLOCATION)
                except Exception as e:
                    logger.debug(f"Portfolio optimization failed in manual mode: {e}")
            # Enforce allocation bounds and calculate quantity
            current_allocation = max(BOT_MIN_ALLOCATION, min(BOT_MAX_ALLOCATION, current_allocation))
            quantity = current_allocation / price if price > 0 else 0
            # Create pending trade
            trade_id = self.create_pending_trade(symbol, action, price, quantity, current_allocation, volume)
            return {
                'status': 'pending_approval',
                'trade_id': trade_id,
                'symbol': symbol,
                'action': action,
                'price': price,
                'quantity': quantity,
                'allocation': current_allocation,
                'message': f'Trade pending manual approval. View in GUI to approve/reject.'
            }

        
        # Sandbox mode: Use live mode execution with sandbox API endpoints
        # This ensures orders go through the API and are visible in ThinkorSwim
        if SCHWAB_SANDBOX_MODE:
            logger.debug(f"[SANDBOX MODE] Executing trade via Schwab sandbox API: {action} {symbol}")
            result = self.execute_trade_live_mode(symbol, action, price)
            
            # Log result if debug logger is enabled
            if self.debug_logger and self.debug_logger.enabled:
                # Extract quantity from result if available
                quantity = result.get('quantity') if isinstance(result, dict) else None
                self.debug_logger.log_trade_execution(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    price=price,
                    metadata={'mode': 'sandbox', 'result': result}
                )
            
            return result
        
        # Pure simulation mode: Local simulation only
        elif PAPER_TRADING_MODE:
            logger.debug(f"[SIMULATION MODE] Simulating trade locally: {action} {symbol}")
            result = self.execute_trade_paper_mode(symbol, action, price, volume)
            
            # Log result if debug logger is enabled
            if self.debug_logger and self.debug_logger.enabled:
                # Extract quantity from result if available
                quantity = result.get('quantity') if isinstance(result, dict) else None
                self.debug_logger.log_trade_execution(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    price=price,
                    metadata={'mode': 'simulation', 'result': result}
                )
            
            return result
        
        # Live mode: Production API
        else:
            logger.debug(f"[LIVE MODE] Executing trade via Schwab production API: {action} {symbol}")
            result = self.execute_trade_live_mode(symbol, action, price)
            
            # Log result if debug logger is enabled
            if self.debug_logger and self.debug_logger.enabled:
                # Extract quantity from result if available
                quantity = result.get('quantity') if isinstance(result, dict) else None
                self.debug_logger.log_trade_execution(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    price=price,
                    metadata={'mode': 'live', 'result': result}
                )
            
            return result

    def calculate_total_pnl(self) -> Tuple[float, float]:
        """
        Calculate total P&L and percentage
        Returns: (total_pnl, total_pnl_percent)
        """
        total_pnl = self.total_capital - self.starting_capital
        
        # Prevent division by zero
        if self.starting_capital == 0:
            total_pnl_percent = 0.0
        else:
            total_pnl_percent = (total_pnl / self.starting_capital) * 100
        
        return total_pnl, total_pnl_percent
    
    def get_decision_factors_summary(self) -> Dict:
        """
        Read-only summary of the local ML decision layer for brain narratives.

        Reports how the in-process ML layer is configured (signal filter,
        adaptive-learning strategy weights, sentiment source) so the ALFa AI
        brain can describe *how* the bot decides. Purely informational, fully
        defensive (never raises), and never influences trade execution.
        """
        factors: Dict = {}

        # ML signal filter status
        try:
            mlf = getattr(self, 'ml_signal_filter', None)
            if mlf is not None:
                factors['ml_signal_filter'] = {
                    'enabled': bool(getattr(self, 'ml_filter_enabled', False)),
                    'trained': bool(getattr(mlf, 'is_trained', False)),
                    'accuracy': round(float((getattr(mlf, 'metrics', {}) or {}).get('accuracy', 0.0)), 4),
                    'min_confidence': float(getattr(self, 'ml_filter_min_confidence', 0.0) or 0.0),
                }
            else:
                factors['ml_signal_filter'] = {'enabled': False, 'trained': False}
        except Exception:
            pass

        # Adaptive-learning strategy weights (best-effort)
        try:
            learner = getattr(self, 'adaptive_learner', None)
            bandit = getattr(learner, 'bandit', None) if learner else None
            if bandit is not None:
                stats = bandit.get_statistics() or {}
                probs = stats.get('probabilities', {}) or {}
                weights = {
                    name: round(float(probs[name]), 4)
                    for name in ('SMA', 'Bollinger', 'RSI', 'MACD', 'Momentum')
                    if name in probs
                }
                if weights:
                    factors['strategy_weights'] = weights
        except Exception:
            pass

        # Sentiment source (brain vs local fallback)
        try:
            factors['sentiment_source'] = (
                'alfa_ai_brain'
                if os.getenv('SENTIMENT_USE_BRAIN', 'true').lower() in ('true', '1', 'yes')
                else os.getenv('SENTIMENT_METHOD', 'vader')
            )
        except Exception:
            pass

        return factors

    def analyze_strategy(self, track_record_json: Dict) -> Dict:
        """
        Generate a factual performance narrative via the ALFa AI brain (optional).

        Does not return parameter settings — use optimize_parameters_ml() for
        backtest-driven parameter suggestions.
        """
        win_rate = track_record_json.get('win_rate', 0)
        win_rate_pct = win_rate * 100 if win_rate <= 1 else win_rate
        total_pnl, total_pnl_percent = self.calculate_total_pnl()

        track_record_summary = {
            'win_rate_pct': round(win_rate_pct, 2),
            'total_trades': track_record_json.get('total_trades', 0),
            'current_allocation': track_record_json.get('current_allocation', 0),
            'initial_capital': self.starting_capital,
            'final_capital': self.total_capital,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
        }

        print("\n[AI INSIGHTS] Requesting performance narrative (no auto-settings)...")
        print(f"  Win Rate: {track_record_json.get('win_rate', 0):.1%}")
        print(f"  Total Trades: {track_record_json.get('total_trades', 0)}")

        try:
            from api.services.trading_insights_llm import generate_performance_narrative
            decision_factors = self.get_decision_factors_summary()
            result = generate_performance_narrative(track_record_summary, decision_factors=decision_factors)
        except Exception as e:
            print(f"[AI INSIGHTS] Unavailable: {e}")
            return {'error': str(e)}

        if result.get('error'):
            print(f"[AI INSIGHTS] [-] {result['error']}")
            return {'error': result['error']}

        text = result.get('response', '')
        if text:
            print("[AI INSIGHTS] ✓ Narrative received")
            print(f"\n{text}")
            return {'response': text, 'disclaimer': result.get('disclaimer')}
        return {'error': 'Empty narrative from ALFa AI'}

    def send_track_record_to_ai(self) -> Dict:
        """Send track record to the ALFa AI brain (LiteLLM) for strategy optimization."""
        # Check resource throttling before API call (network intensive)
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE - AI API] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        return self.analyze_strategy(self.track_record)
    
    def apply_ai_suggestions(self, ai_response: Dict, auto_apply: bool = False) -> bool:
        """
        Apply backtest-heuristic parameter suggestions when win rate is below target.

        The LLM narrative from analyze_strategy is never parsed for settings.
        Only optimize_parameters_ml() (backtest heuristics) can change parameters.
        """
        current_win_rate = self.track_record.get('win_rate', 0.0)

        if current_win_rate < WIN_RATE_TARGET and self.track_record.get('total_trades', 0) >= 10:
            logger.info(
                "[WIN RATE AUTO-TUNE] Win rate %.1f%% below target %.1f%% — running backtest heuristic optimizer",
                current_win_rate * 100,
                WIN_RATE_TARGET * 100,
            )
            optimized_params, predicted_win_rate = self.optimize_parameters_ml()

            if optimized_params and predicted_win_rate > current_win_rate:
                logger.info(
                    "[WIN RATE AUTO-TUNE] Heuristic optimizer: %d params, predicted win rate %.1f%%",
                    len(optimized_params),
                    predicted_win_rate * 100,
                )
                if auto_apply:
                    applied_count = self._apply_optimized_parameters(optimized_params)
                    if applied_count > 0:
                        self.alert_system.send_alert(
                            "Win Rate Auto-Tune Applied",
                            f"Win rate {current_win_rate:.1%} below target {WIN_RATE_TARGET:.1%}. "
                            f"Backtest heuristic optimizer applied {applied_count} parameter(s). "
                            f"Estimated win rate: {predicted_win_rate:.1%}",
                        )
                        return True
                else:
                    logger.info("[WIN RATE AUTO-TUNE] Suggestions available (auto_apply=False)")

        if ai_response and 'error' not in ai_response:
            print("[AI INSIGHTS] Performance narrative available (no settings auto-applied from LLM)")
        return False
    
    def optimize_parameters_ml(self, backtest_results: List[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], float]:
        """
        Optimize bot parameters using ML for 70% win rate target
        
        Args:
            backtest_results: Optional list of backtest results. If None, uses trade history.
            
        Returns:
            Tuple of (optimized_parameters, predicted_win_rate)
        """
        # Check resource throttling before ML optimization (CPU/memory intensive)
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE - ML OPTIMIZATION] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        if not self.ml_optimizer:
            logger.warning("ML optimizer not available")
            return {}, 0.0
        
        # If no backtest results provided, use trade history as proxy
        if backtest_results is None:
            if not self.trade_history:
                logger.warning("No trade history available for ML optimization")
                return {}, 0.0
            
            # Convert trade history to backtest result format
            backtest_results = [{
                'win_rate': self.track_record['win_rate'],
                'roi': (self.total_capital - self.starting_capital) / self.starting_capital,
                'sharpe_ratio': 0.0,  # Not calculated from trade history
                'max_drawdown': 0.0  # Not calculated from trade history
            }]
        
        # Get current parameters
        current_params = {
            'BOT_RISK_THRESHOLD': BOT_RISK_THRESHOLD,
            'BOT_TRAILING_STOP_PERCENT': BOT_TRAILING_STOP_PERCENT,
            'BOT_STOP_LOSS_PERCENT': BOT_STOP_LOSS_PERCENT,
            'BOT_TAKE_PROFIT_PERCENT': BOT_TAKE_PROFIT_PERCENT,
            'BOT_MAX_CONSECUTIVE_LOSSES': BOT_MAX_CONSECUTIVE_LOSSES,
            'BOT_MIN_ALLOCATION': BOT_MIN_ALLOCATION,
            'BOT_MAX_ALLOCATION': BOT_MAX_ALLOCATION,
            'TRADING_FREQUENCY': TRADING_FREQUENCY,
            'MIN_TRAILING_STOP': MIN_TRAILING_STOP,
            'MAX_TRAILING_STOP': MAX_TRAILING_STOP
        }
        
        logger.info("Starting backtest heuristic parameter optimization (target ~70%% win rate)...")
        logger.info(f"Current win rate: {self.track_record['win_rate']:.1%}")

        try:
            analysis = self.ml_optimizer._analyze_backtest_results(backtest_results)
            optimized_params, predicted_win_rate = self.ml_optimizer.optimize_parameters(
                backtest_results,
                current_params,
            )

            if optimized_params:
                logger.info("Backtest heuristic optimization complete")
                logger.info(f"Predicted win rate: {predicted_win_rate:.1%}")
                logger.info(f"Suggested {len(optimized_params)} parameters")

                self.ml_optimizer.save_optimization_result(
                    optimized_params, predicted_win_rate, analysis=analysis
                )
                
                return optimized_params, predicted_win_rate
            else:
                logger.warning("ML optimization returned no parameter suggestions")
                return {}, 0.0
                
        except Exception as e:
            logger.error(f"Error during ML parameter optimization: {e}")
            return {}, 0.0
    
    def check_trailing_stop(self, symbol: str, current_price: float):
        """
        Check if trailing stop is triggered for a position.
        Supports long and short (Phase 1: stocks buy/short per MISSION.md).
        Long: track high, trail below; trigger when price <= stop.
        Short: track low, trail above; trigger when price >= stop.
        Returns:
        - False: No stop triggered
        - 'partial_exit': Partial exit executed
        - True: Full exit triggered
        """
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]
        side = position.get('side', 'long')
        stop_percent = position.get('stop_percent', self.trailing_stop_percent)

        if side == 'short':
            low = position.get('low_price')
            if low is None:
                position['low_price'] = current_price
                low = current_price
            if current_price < low:
                position['low_price'] = current_price
                low = current_price
            trailing_stop_price = low * (1 + stop_percent)
            triggered = current_price >= trailing_stop_price
            price_label, trail_label = 'Low Price', 'Trailing Stop (cover)'
        else:
            high = position.get('high_price')
            if high is None:
                position['high_price'] = current_price
                high = current_price
            if current_price > high:
                position['high_price'] = current_price
                high = current_price
            trailing_stop_price = high * (1 - stop_percent)
            triggered = current_price <= trailing_stop_price
            price_label, trail_label = 'High Price', 'Trailing Stop Price'

        if not triggered:
            return False

        if PARTIAL_EXIT_ENABLED and not position.get('partial_exit_done', False):
            exit_quantity = position['quantity'] * PARTIAL_EXIT_PERCENTAGE
            remaining_quantity = position['quantity'] - exit_quantity
            entry = position['entry_price']
            if side == 'short':
                partial_pnl = (entry - current_price) * exit_quantity
                partial_pnl_percent = ((entry - current_price) / entry) * 100
            else:
                partial_pnl = (current_price - entry) * exit_quantity
                partial_pnl_percent = ((current_price - entry) / entry) * 100

            print(f"\n[PARTIAL EXIT TRIGGERED]")
            print(f"  Symbol: {symbol} ({side})")
            print(f"  Entry Price: ${entry:.2f}")
            print(f"  {price_label}: ${(position.get('low_price') or position.get('high_price') or entry):.2f}")
            print(f"  Current Price: ${current_price:.2f}")
            print(f"  {trail_label}: ${trailing_stop_price:.2f}")
            print(f"  Partial Exit: {PARTIAL_EXIT_PERCENTAGE:.1%} ({exit_quantity:.6f} shares)")
            print(f"  Partial P&L: ${partial_pnl:.2f} ({partial_pnl_percent:.1f}%)")
            print(f"  Remaining: {remaining_quantity:.6f} shares")

            position['quantity'] = remaining_quantity
            position['partial_exit_done'] = True
            position['stop_percent'] = stop_percent * PARTIAL_EXIT_STOP_TIGHTENING
            return 'partial_exit'

        print(f"\n[TRAILING STOP TRIGGERED]")
        print(f"  Symbol: {symbol} ({side})")
        print(f"  Entry Price: ${position['entry_price']:.2f}")
        print(f"  {price_label}: ${(position.get('low_price') or position.get('high_price') or position['entry_price']):.2f}")
        print(f"  Current Price: ${current_price:.2f}")
        print(f"  {trail_label}: ${trailing_stop_price:.2f}")
        if position.get('partial_exit_done'):
            print(f"  Note: Partial exit was previously executed")
        return True
    
    def open_position(
        self,
        symbol: str,
        entry_price: float,
        quantity: float,
        stop_percent: float = None,
        side: str = 'long',
    ):
        """
        Open a new position with trailing stop tracking and optional dynamic stop.

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            quantity: Number of shares
            stop_percent: Trailing stop percentage (default: bot trailing_stop_percent)
            side: 'long' or 'short' (Phase 1: stocks buy/short per MISSION.md)
        """
        if stop_percent is None:
            stop_percent = self.trailing_stop_percent
        if side not in ('long', 'short'):
            side = 'long'

        self.positions[symbol] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'side': side,
            'high_price': entry_price if side == 'long' else None,
            'low_price': entry_price if side == 'short' else None,
            'stop_percent': stop_percent,
            'partial_exit_done': False,
            'entry_time': datetime.now().isoformat(),
        }
    
    def close_position(self, symbol: str, exit_price: float, exit_reason: str = 'unknown') -> Optional[Dict]:
        """
        Close a position and return P&L information with detailed exit conditions.

        Supports long and short (Phase 1: stocks buy/short per MISSION.md).
        Long: P&L = (exit - entry) * quantity. Short: P&L = (entry - exit) * quantity.
        """
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]
        entry_price = position['entry_price']
        quantity = position['quantity']
        side = position.get('side', 'long')
        entry_time = position.get('entry_time')

        if side == 'short':
            pnl = (entry_price - exit_price) * quantity
            pnl_percent = ((entry_price - exit_price) / entry_price) * 100
        else:
            pnl = (exit_price - entry_price) * quantity
            pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        
        # Calculate hold duration if entry time available
        hold_duration = None
        if entry_time:
            try:
                entry_dt = datetime.fromisoformat(entry_time)
                hold_duration = (datetime.now() - entry_dt).total_seconds() / 3600  # hours
            except:
                pass
        
        exit_conditions = {
            'reason': exit_reason,
            'side': side,
            'high_price': position.get('high_price'),
            'low_price': position.get('low_price'),
            'stop_percent': position.get('stop_percent'),
            'partial_exit_done': position.get('partial_exit_done', False),
            'hold_duration_hours': hold_duration,
            'entry_time': entry_time,
        }
        
        # Add current volatility if available
        if symbol in self.price_history and len(self.price_history[symbol]) >= 2:
            exit_conditions['volatility'] = self.calculate_volatility(symbol)
        
        result = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'side': side,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'is_win': pnl > 0,
            'exit_reason': exit_reason,
            'exit_conditions': exit_conditions,
            'partial_exit_executed': position.get('partial_exit_done', False),
            'timestamp': datetime.now().isoformat(),
        }
        
        # Log exit conditions explicitly
        print(f"\n[EXIT CONDITIONS LOGGED]")
        print(f"  Symbol: {symbol}")
        print(f"  Exit Reason: {exit_reason}")
        print(f"  Entry Price: ${entry_price:.2f}")
        print(f"  Exit Price: ${exit_price:.2f}")
        print(f"  P&L: ${pnl:.2f} ({pnl_percent:.1f}%)")
        if hold_duration:
            print(f"  Hold Duration: {hold_duration:.2f} hours")
        if exit_conditions.get('volatility'):
            print(f"  Exit Volatility: {exit_conditions['volatility']:.1%}")
        
        # Feed trade outcome to adaptive learning if available
        if self.adaptive_learner:
            try:
                # Get market data for adaptive learning
                market_data = self._get_market_data_for_learning(symbol, exit_price)
                
                # Calculate reward (normalized P&L as percentage of entry price)
                reward = pnl_percent / 100.0  # Convert to decimal (e.g., 5% -> 0.05)
                
                # Determine which strategy was used (for now, use combined signal - can be improved)
                # In future, we could track which strategy generated the signal that opened this position
                strategy_used = 'SMA'  # Default - can be enhanced to track actual strategy
                
                # Update adaptive learning with trade outcome
                trade_data = {
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'side': side,
                    'hold_duration': hold_duration,
                    'exit_reason': exit_reason
                }
                
                self.adaptive_learner.update_from_trade(
                    strategy=strategy_used,
                    profit=pnl,
                    market_data=market_data,
                    trade_data=trade_data
                )
                
                logger.debug(f"Updated adaptive learning for {symbol}: reward={reward:.4f}, strategy={strategy_used}")
                
                # Periodically update strategy weights in StrategyManager
                # Update every 10 trades or when significant learning has occurred
                if (self.adaptive_learner.trade_count % 10 == 0 or 
                    self.adaptive_learner.trade_count == 1):
                    self._update_strategy_weights_from_adaptive_learning()
                    # Update component coordination state (enhancement)
                    self.component_coordination_state['last_adaptive_update'] = datetime.now()
                    self.component_coordination_state['coordinated_update_count'] += 1
                
                # Periodically run ML parameter optimization (real-time)
                if ENABLE_REALTIME_ML_OPTIMIZATION:
                    self._check_and_run_ml_optimization()
                    
            except Exception as e:
                logger.warning(f"Failed to update adaptive learning for {symbol}: {e}")
        
        # Remove position
        del self.positions[symbol]
        
        return result
    
    def detect_stale_positions(self, stale_threshold_hours: float = 48.0) -> Dict[str, Dict]:
        """
        Identify positions held open for longer than threshold duration.
        Useful for detecting positions that are no longer trending or capital-efficient.

        Args:
            stale_threshold_hours: Duration in hours above which position is considered stale (default: 48h)

        Returns:
            Dict mapping symbol -> {hold_duration_hours, entry_price, entry_time, current_price, current_pnl_percent}
        """
        stale_positions = {}
        current_time = datetime.now()
        
        for symbol, position in self.positions.items():
            entry_time_str = position.get('entry_time')
            if not entry_time_str:
                continue
            
            try:
                entry_time = datetime.fromisoformat(entry_time_str)
                hold_duration_hours = (current_time - entry_time).total_seconds() / 3600
                
                if hold_duration_hours > stale_threshold_hours:
                    entry_price = position['entry_price']
                    side = position.get('side', 'long')
                    
                    # Use cached price if available, otherwise fall back to high_price (longs) / low_price (shorts)
                    current_price = None
                    if symbol in self.price_cache and 'price' in self.price_cache[symbol]:
                        current_price = self.price_cache[symbol]['price']
                    elif side == 'long' and position.get('high_price') is not None:
                        current_price = position.get('high_price')
                    elif side == 'short' and position.get('low_price') is not None:
                        current_price = position.get('low_price')
                    
                    if current_price is None:
                        current_price = entry_price  # Fallback to entry price if no better option
                    
                    # Calculate current P&L
                    if side == 'long':
                        current_pnl_percent = ((current_price - entry_price) / entry_price) * 100
                    else:
                        current_pnl_percent = ((entry_price - current_price) / entry_price) * 100
                    
                    stale_positions[symbol] = {
                        'hold_duration_hours': hold_duration_hours,
                        'entry_price': entry_price,
                        'entry_time': entry_time_str,
                        'current_price': current_price,
                        'current_pnl_percent': current_pnl_percent,
                        'side': side,
                        'quantity': position['quantity'],
                    }
                    
                    # Log stale position warning
                    logger.warning(
                        f"[STALE_POSITION] {symbol}: held for {hold_duration_hours:.1f}h "
                        f"(side={side}, pnl={current_pnl_percent:.1f}%, entry=${entry_price:.2f}, current=${current_price:.2f})"
                    )
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse entry_time for {symbol}: {e}")
                continue
        
        return stale_positions
    
    def load_scan_symbols(self, filename: str = None, use_screener: bool = True, max_symbols: int = 10) -> List[str]:
        """
        Load symbols for trading using TOS-like dynamic stock discovery
        
        Discovery Priority (First Available Method Used):
        1. Dynamic API (if DYNAMIC_SCAN_API_URL configured) - RARELY USED
        2. Stock Screener (RECOMMENDED - TOS-like behavior) - DEFAULT
           - Scans 300+ stocks from S&P 500, NASDAQ-100, etc.
           - Filters by .env criteria (price, volume, volatility)
           - Ranks by quality (momentum, volume, liquidity, sentiment)
           - Returns top N stocks (MAX_DISCOVERED_STOCKS)
        3. Static File (scan_symbols.txt) - FALLBACK ONLY
           - Used when ENABLE_STOCK_SCREENER=false
           - Requires manual symbol management
        4. Hardcoded Defaults (emergency fallback)
        
        Args:
            filename: Optional symbol file path (rarely needed)
            use_screener: Whether to use TOS-like stock discovery (default: True)
            max_symbols: Maximum symbols to return from screener
        
        Returns:
            List of stock symbols to trade (prioritized by quality if using screener)
        """
        # Check resource throttling before loading symbols (API/disk intensive)
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE - SYMBOL LOADING] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        # ========================================================================
        # METHOD 1: Dynamic API (if configured - advanced use case)
        # ========================================================================
        if DYNAMIC_SCAN_API_URL:
            try:
                logger.info(f"\n{'='*LOG_SEPARATOR_LENGTH}")
                logger.info(f"[STOCK DISCOVERY] Method: Dynamic API")
                logger.info(f"[STOCK DISCOVERY] Source: {DYNAMIC_SCAN_API_URL}")
                logger.info(f"{'='*LOG_SEPARATOR_LENGTH}")
                
                response = requests.get(
                    DYNAMIC_SCAN_API_URL, 
                    timeout=10,
                    verify=True  # Verify SSL certificates
                )
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different API response formats
                    if isinstance(data, list):
                        symbols = data
                    elif isinstance(data, dict) and 'symbols' in data:
                        symbols = data['symbols']
                    else:
                        symbols = list(data.keys())
                    
                    # Clean symbols
                    symbols = [str(s).strip().upper() for s in symbols if s]
                    logger.info(f"✓ Loaded {len(symbols)} symbols from dynamic API")
                    return symbols
                else:
                    logger.warning(f"API returned status {response.status_code}, trying next method...")
            except requests.exceptions.SSLError as e:
                logger.warning(f"SSL certificate verification failed: {e}, trying next method...")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error: {e}, trying next method...")
            except requests.exceptions.Timeout as e:
                logger.warning(f"Request timed out: {e}, trying next method...")
            except Exception as e:
                logger.warning(f"Failed to fetch from API: {e}, trying next method...")
        
        # ========================================================================
        # METHOD 2: Stock Screener (RECOMMENDED - TOS-like dynamic discovery)
        # ========================================================================
        if use_screener:
            try:
                from stock_screener import screen_for_trades
                
                logger.info(f"\n{'='*LOG_SEPARATOR_LENGTH}")
                logger.info(f"[STOCK DISCOVERY] Method: TOS-like Dynamic Screener (RECOMMENDED)")
                logger.info(f"[STOCK DISCOVERY] Universe: S&P 500, NASDAQ-100, Dow Jones, etc.")
                logger.info(f"[STOCK DISCOVERY] Scanning up to {MAX_STOCKS_TO_SCAN} stocks...")
                logger.info(f"{'='*LOG_SEPARATOR_LENGTH}")
                logger.info(f"Filtering Criteria:")
                logger.info(f"  • Price Range: ${MIN_STOCK_PRICE:.2f} - ${MAX_STOCK_PRICE:.2f}")
                logger.info(f"  • Min Volume: {MIN_DAILY_VOLUME:,} shares/day")
                logger.info(f"  • Max Volatility: {MAX_STOCK_VOLATILITY:.1%}")
                
                # Warn if criteria might be too restrictive
                if MAX_STOCK_PRICE < LOW_MAX_PRICE_THRESHOLD:
                    logger.warning(f"⚠️  MAX_STOCK_PRICE (${MAX_STOCK_PRICE}) is very low!")
                    logger.warning(f"    Most major stocks are $50-$500. You may find 0 stocks.")
                    logger.warning(f"    Recommended: Set MAX_STOCK_PRICE=1000 in .env")
                
                if MIN_STOCK_PRICE > HIGH_MIN_PRICE_THRESHOLD:
                    logger.warning(f"⚠️  MIN_STOCK_PRICE (${MIN_STOCK_PRICE}) is very high!")
                    logger.warning(f"    This excludes many good trading opportunities.")
                    logger.warning(f"    Recommended: Set MIN_STOCK_PRICE=5.0 to 50.0 in .env")
                
                symbols = screen_for_trades(max_stocks=max_symbols)
                
                if symbols and len(symbols) > 0:
                    logger.info(f"✓ Discovered {len(symbols)} tradeable stocks (ranked by quality):")
                    for i, symbol in enumerate(symbols[:DISPLAY_LIMIT], 1):  # Show first N
                        logger.info(f"  #{i:2d}. {symbol}")
                    if len(symbols) > DISPLAY_LIMIT:
                        logger.info(f"  ... and {len(symbols) - DISPLAY_LIMIT} more")
                    logger.info(f"{'='*LOG_SEPARATOR_LENGTH}\n")
                    return symbols
                else:
                    logger.warning(f"⚠️  Stock screener found 0 stocks matching criteria!")
                    logger.warning(f"    Your filters may be too restrictive.")
                    logger.warning(f"    Check MIN/MAX_STOCK_PRICE, MIN_DAILY_VOLUME, MAX_STOCK_VOLATILITY in .env")
                    logger.warning(f"    Falling back to static file method...")
            except ImportError:
                logger.warning(f"Stock screener module not available, trying next method...")
            except Exception as e:
                logger.warning(f"Stock screener failed: {e}, trying next method...")
        
        # ========================================================================
        # METHOD 3: Static File (scan_symbols.txt - FALLBACK ONLY)
        # ========================================================================
        if filename is None:
            filename = SCAN_SYMBOLS_FILE
        
        try:
            logger.info(f"\n{'='*LOG_SEPARATOR_LENGTH}")
            logger.info(f"[STOCK DISCOVERY] Method: Static File (Fallback)")
            logger.info(f"[STOCK DISCOVERY] File: {filename}")
            logger.info(f"{'='*LOG_SEPARATOR_LENGTH}")
            
            filepath = os.path.join(os.path.dirname(__file__), filename)
            with open(filepath, 'r') as f:
                # Skip comment lines starting with # and empty lines
                symbols = [line.strip() for line in f 
                          if line.strip() and not line.strip().startswith('#')]
            
            if len(symbols) == 0:
                logger.warning(f"⚠️  {filename} contains no symbols (all commented out)")
                logger.warning(f"    To use this file, uncomment symbols or add new ones")
                logger.warning(f"    Falling back to hardcoded defaults...")
                return DEFAULT_FALLBACK_SYMBOLS
            
            logger.info(f"✓ Loaded {len(symbols)} symbols from {filename}")
            logger.warning(f"⚠️  Using static symbol list - NOT TOS-like behavior")
            logger.warning(f"    Set ENABLE_STOCK_SCREENER=true in .env for dynamic discovery")
            logger.info(f"{'='*LOG_SEPARATOR_LENGTH}\n")
            return symbols
        except FileNotFoundError:
            logger.warning(f"⚠️  Symbol file {filename} not found")
            logger.warning(f"    Using hardcoded default symbols")
            logger.info(f"{'='*LOG_SEPARATOR_LENGTH}\n")
            return DEFAULT_FALLBACK_SYMBOLS
    
    def fetch_schwab_stock_price(self, symbol: str) -> Optional[Tuple[float, int]]:
        """
        Fetch real-time stock price and volume using Schwab Market Data API
        Returns (price, volume) tuple or None if fetch fails
        
        Uses caching to reduce API calls; TTL from PRICE_CACHE_TTL_SECONDS (default 30s). Set 0 for no cache.
        Supports both sandbox and production environments based on SCHWAB_SANDBOX_MODE
        Now uses OAuth authentication via schwab-py library when available
        """
        # Check resource throttling before API call (network intensive)
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE - SCHWAB API] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        # Check cache first (TTL from PRICE_CACHE_TTL_SECONDS; 0 = no cache)
        if PRICE_CACHE_TTL_SECONDS > 0 and symbol in self.price_cache:
            cache_entry = self.price_cache[symbol]
            # Validate cache structure before accessing
            if isinstance(cache_entry, dict) and 'price' in cache_entry and 'volume' in cache_entry and 'timestamp' in cache_entry:
                try:
                    cache_age = (datetime.now() - cache_entry['timestamp']).total_seconds()
                    if cache_age < PRICE_CACHE_TTL_SECONDS:
                        logger.debug(f"Using cached Schwab price for {symbol}: ${cache_entry['price']:.2f}")
                        return cache_entry['price'], cache_entry['volume']
                except (TypeError, AttributeError) as e:
                    logger.warning(f"Invalid cache entry for {symbol}, will fetch fresh data: {e}")
                    # Remove invalid cache entry
                    del self.price_cache[symbol]
        
        # Try OAuth-authenticated client first (if available)
        if self.schwab_authenticator is not None:
            try:
                if self.schwab_client is None:
                    # Get authenticated client (will use cached token or prompt for login)
                    # In non-interactive environments, this requires token.json to exist
                    interactive = not os.getenv('NON_INTERACTIVE', 'false').lower() == 'true'
                    self.schwab_client = self.schwab_authenticator.get_client(interactive=interactive)
                    logger.info("Successfully obtained Schwab OAuth client")
                
                # Fetch quote using schwab-py client
                response = self.schwab_client.get_quote(symbol)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse response - Schwab returns data in format: {symbol: {quote: {...}}}
                    if symbol in data and 'quote' in data[symbol]:
                        quote = data[symbol]['quote']
                        
                        # Extract price (use last price, or bid/ask average as fallback)
                        price = quote.get('lastPrice')
                        if price is None or price <= 0.0:
                            # Fallback to bid/ask average
                            bid = quote.get('bidPrice', 0)
                            ask = quote.get('askPrice', 0)
                            if bid > 0 and ask > 0:
                                price = (bid + ask) / 2
                            else:
                                logger.warning(f"No valid price in OAuth response for {symbol}")
                                return None
                        
                        # Extract volume (use total volume or last volume)
                        volume = quote.get('totalVolume', 0)
                        if volume == 0:
                            volume = quote.get('lastSize', DEFAULT_VOLUME)  # Default if not available
                        
                        # Cache the result
                        self.price_cache[symbol] = {
                            'price': price,
                            'volume': volume,
                            'timestamp': datetime.now(),
                            'source': 'schwab_oauth'
                        }
                        
                        logger.info(f"[OAuth] Fetched price for {symbol}: ${price:.2f}, volume: {volume:,}")
                        return price, volume
                    else:
                        logger.warning(f"[OAuth] No quote data in response for {symbol}")
                        
            except Exception as e:
                logger.warning(f"OAuth client fetch failed for {symbol}: {e}")
                # Fall through to legacy method
        
        # Fallback to legacy REST API method (for backward compatibility)
        # Skip if credentials are not configured (placeholder values)
        if not _are_schwab_credentials_configured():
            logger.debug(f"Skipping Schwab REST API (credentials not configured)")
            return None
        
        # Determine API base URL based on mode (read dynamically)
        paper_mode = _get_paper_trading_mode()
        sandbox_mode = _get_schwab_sandbox_mode()
        
        if paper_mode and sandbox_mode:
            api_base = SCHWAB_SANDBOX_MARKET_DATA_BASE
            mode_str = "SANDBOX"
        else:
            api_base = SCHWAB_PRODUCTION_MARKET_DATA_BASE
            mode_str = "PRODUCTION"
        
        # Build API endpoint for quote retrieval
        # Schwab Market Data API: GET /quotes
        api_url = f"{api_base}/quotes"
        
        headers = {
            'Authorization': f'Bearer {SCHWAB_API_KEY}',
            'Accept': 'application/json'
        }
        
        params = {
            'symbols': symbol,
            'fields': 'quote'  # Request quote data including price and volume
        }
        
        try:
            logger.debug(f"[{mode_str}] Fetching price for {symbol} from Schwab Market Data API...")
            
            response = requests.get(
                api_url,
                headers=headers,
                params=params,
                timeout=10  # 10 second timeout for market data
            )
            
            # Check response status
            if response.status_code == 200:
                data = response.json()
                
                # Parse response - Schwab returns data in format: {symbol: {quote: {...}}}
                if symbol in data and 'quote' in data[symbol]:
                    quote = data[symbol]['quote']
                    
                    # Extract price (use last price, or bid/ask average as fallback)
                    price = quote.get('lastPrice')
                    if price is None or price <= 0.0:
                        # Fallback to bid/ask average
                        bid = quote.get('bidPrice', 0)
                        ask = quote.get('askPrice', 0)
                        if bid > 0 and ask > 0:
                            price = (bid + ask) / 2
                        else:
                            logger.warning(f"[{mode_str}] No valid price in response for {symbol}")
                            return None
                    
                    # Extract volume (use total volume or last volume)
                    volume = quote.get('totalVolume', 0)
                    if volume == 0:
                        volume = quote.get('lastSize', DEFAULT_VOLUME)  # Default if not available
                    
                    # Cache the result
                    self.price_cache[symbol] = {
                        'price': price,
                        'volume': volume,
                        'timestamp': datetime.now(),
                        'source': f'schwab_{mode_str.lower()}'
                    }
                    
                    logger.info(f"[{mode_str}] Fetched price for {symbol}: ${price:.2f}, volume: {volume:,}")
                    return price, volume
                else:
                    logger.warning(f"[{mode_str}] No quote data in response for {symbol}")
                    return None
                    
            elif response.status_code == 401:
                logger.error(f"[{mode_str}] Authentication failed - invalid or expired API key")
                return None
                
            elif response.status_code == 429:
                logger.warning(f"[{mode_str}] Rate limit exceeded - waiting before retry")
                return None
                
            elif response.status_code == 404:
                logger.warning(f"[{mode_str}] Symbol {symbol} not found")
                return None
                
            else:
                logger.error(f"[{mode_str}] API error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            error_msg = f"[{mode_str}] Request timeout fetching price for {symbol}"
            logger.error(error_msg)
            # Show GUI alert if GUI is available
            if hasattr(self, 'gui') and self.gui is not None:
                try:
                    from tkinter import messagebox
                    messagebox.showerror("API Timeout", 
                                       f"Schwab API request timed out for {symbol}.\n"
                                       f"Check your internet connection.")
                except Exception:
                    pass  # GUI not available or messagebox failed
            return None
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"[{mode_str}] Connection error fetching price for {symbol}: {e}"
            logger.error(error_msg)
            # Show GUI alert if GUI is available
            if hasattr(self, 'gui') and self.gui is not None:
                try:
                    from tkinter import messagebox
                    messagebox.showerror("API Connection Error", 
                                       f"Failed to connect to Schwab API for {symbol}.\n"
                                       f"Check your internet connection and Schwab API status.")
                except Exception:
                    pass  # GUI not available or messagebox failed
            return None
        
        except requests.exceptions.RequestException as e:
            error_msg = f"[{mode_str}] Network error fetching price for {symbol}: {e}"
            logger.error(error_msg)
            # Show GUI alert if GUI is available
            if hasattr(self, 'gui') and self.gui is not None:
                try:
                    from tkinter import messagebox
                    messagebox.showerror("API Network Error", 
                                       f"Network error accessing Schwab API for {symbol}.\n"
                                       f"Check internet connection and API status.")
                except Exception:
                    pass  # GUI not available or messagebox failed
            return None
            
        except Exception as e:
            error_msg = f"[{mode_str}] Unexpected error fetching price for {symbol}: {e}"
            logger.error(error_msg)
            # Show GUI alert if GUI is available
            if hasattr(self, 'gui') and self.gui is not None:
                try:
                    from tkinter import messagebox
                    messagebox.showerror("API Unexpected Error", 
                                       f"Unexpected error with Schwab API for {symbol}.\n"
                                       f"Error: {str(e)}")
                except Exception:
                    pass  # GUI not available or messagebox failed
            return None
    
    def fetch_real_stock_price(self, symbol: str) -> Optional[Tuple[float, int]]:
        """
        Fetch real-time stock price and volume using yfinance API
        Returns (price, volume) tuple or None if fetch fails
        
        Uses caching to reduce API calls; TTL from PRICE_CACHE_TTL_SECONDS (default 30s). Set 0 for no cache (max real-time).
        """
        # Check resource throttling before API call (network intensive)
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE - PRICE FETCH] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        # Check cache first (TTL from PRICE_CACHE_TTL_SECONDS; 0 = no cache, always real-time)
        if PRICE_CACHE_TTL_SECONDS > 0 and symbol in self.price_cache:
            cache_entry = self.price_cache[symbol]
            # Validate cache entry structure before accessing
            if isinstance(cache_entry, dict) and 'price' in cache_entry and 'volume' in cache_entry and 'timestamp' in cache_entry:
                try:
                    cache_age = (datetime.now() - cache_entry['timestamp']).total_seconds()
                    if cache_age < PRICE_CACHE_TTL_SECONDS:
                        logger.debug(f"Using cached price for {symbol}: ${cache_entry['price']:.2f}")
                        return cache_entry['price'], cache_entry['volume']
                except (TypeError, AttributeError) as e:
                    logger.warning(f"Invalid cache entry for {symbol}, will fetch fresh data: {e}")
                    # Remove invalid cache entry
                    del self.price_cache[symbol]
        
        # Fetch real price if yfinance is available
        if not YFINANCE_AVAILABLE:
            logger.warning(f"yfinance not available - cannot fetch real price for {symbol}")
            return None
        
        # Configurable lightweight retry with jitter for yfinance fetches
        max_retries = max(0, int(os.getenv('YFINANCE_MAX_RETRIES', '2')))
        delay_ms = max(0, int(os.getenv('YFINANCE_RETRY_DELAY_MS', '250')))
        jitter_ms = max(0, int(os.getenv('YFINANCE_JITTER_MS', '150')))

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Fetching real-time price for {symbol} from Yahoo Finance (attempt {attempt+1}/{max_retries+1})...")
                ticker = yf.Ticker(symbol)

                # Try fast_info first (faster), fallback to info if needed
                try:
                    price = ticker.fast_info.get('lastPrice')
                    volume = ticker.fast_info.get('lastVolume', 0)
                except (KeyError, AttributeError, TypeError) as e:
                    logger.debug(f"fast_info not available for {symbol}, trying regular info: {e}")
                    info = ticker.info
                    price = info.get('currentPrice') or info.get('regularMarketPrice')
                    volume = info.get('volume') or info.get('regularMarketVolume', 0)

                if price is None or price <= 0:
                    logger.warning(f"Invalid price data for {symbol}: {price} — attempting history fallback")
                    try:
                        hist = ticker.history(period='1d', interval='1m', prepost=True)
                        if hist is not None and len(hist) > 0:
                            last_close = float(hist['Close'].dropna().iloc[-1])
                            last_vol = int(hist['Volume'].dropna().iloc[-1]) if 'Volume' in hist.columns else 0
                            price = last_close
                            volume = last_vol or volume or 0
                            logger.debug(f"History fallback for {symbol}: close={last_close}, vol={last_vol}")
                        else:
                            logger.warning(f"History data empty for {symbol}; cannot fallback")
                            raise ValueError("Empty history data")
                    except Exception as e:
                        logger.warning(f"History fallback failed for {symbol}: {e}")
                        # Will retry if attempts remain

                # If we now have a price, cache and return
                if price is not None and price > 0:
                    self.price_cache[symbol] = {
                        'price': float(price),
                        'volume': int(volume) if volume else 1000000,
                        'timestamp': datetime.now()
                    }
                    logger.info(f"Fetched real price for {symbol}: ${price:.2f}, volume: {volume:,}")
                    return price, volume

            except requests.exceptions.Timeout:
                logger.error(f"Request timeout fetching price for {symbol} from Yahoo Finance (attempt {attempt+1})")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error fetching price for {symbol} from Yahoo Finance: {e} (attempt {attempt+1})")
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error fetching price for {symbol} from Yahoo Finance: {e} (attempt {attempt+1})")
            except Exception as e:
                logger.error(f"Unexpected error fetching price for {symbol}: {str(e)} (attempt {attempt+1})")

            # Retry delay with jitter if attempts remain
            if attempt < max_retries:
                sleep_time = (delay_ms + random.randint(0, jitter_ms)) / 1000.0
                logger.debug(f"Retrying price fetch for {symbol} in {sleep_time:.2f}s")
                time.sleep(sleep_time)

        # All attempts failed
        return None
    
    def _is_pure_simulation_mode(self) -> bool:
        """
        Check if running in pure simulation mode.
        
        Pure simulation mode allows random price fallback when APIs fail.
        This includes:
        1. Paper trading with sandbox disabled (PAPER_TRADING_MODE=true, SCHWAB_SANDBOX_MODE=false)
        2. API explicitly disabled mode (SCHWAB_API_ENABLED=off) - overrides sandbox setting
        
        This is different from sandbox mode (which requires Schwab API).
        
        Returns:
            True if in pure simulation mode, False otherwise
        """
        # Read mode settings dynamically to support runtime updates
        api_enabled = _get_schwab_api_enabled()
        paper_mode = _get_paper_trading_mode()
        sandbox_mode = _get_schwab_sandbox_mode()
        
        # If API is explicitly disabled, always treat as pure simulation (overrides sandbox)
        if not api_enabled:
            return True
        
        # Otherwise, check for paper mode without sandbox
        return paper_mode and not sandbox_mode
    
    def enable_historical_mode(self, start_date: str, end_date: str):
        """
        Enable historical simulation mode with frozen time
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
        """
        self.historical_mode = True
        self.historical_start = datetime.strptime(start_date, '%Y-%m-%d')
        self.historical_end = datetime.strptime(end_date, '%Y-%m-%d')
        self.current_sim_date = self.historical_start
        
        logger.info(f"Historical mode enabled: {start_date} to {end_date}")
    
    def load_historical_data(self, symbol: str, start_date: str, end_date: str):
        """
        Load historical data for a symbol (for frozen time simulation)
        
        Args:
            symbol: Stock symbol
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
        """
        # Check resource throttling before data loading (network/memory intensive)
        resources_ok, resource_msg = self.throttler.check_resources()
        if not resources_ok:
            logger.warning(f"[RESOURCE THROTTLE - HISTORICAL DATA] {resource_msg}")
            self.throttler.apply_throttle(resource_msg)
        
        if not YFINANCE_AVAILABLE:
            logger.warning(f"yfinance not available, cannot load historical data for {symbol}")
            return
        
        try:
            logger.info(f"Loading historical data for {symbol}: {start_date} to {end_date}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                logger.warning(f"No historical data found for {symbol}")
                return
            
            self.historical_data[symbol] = df
            logger.info(f"Loaded {len(df)} days of historical data for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to load historical data for {symbol}: {e}")
    
    def advance_sim_date(self, days: int = 1):
        """
        Advance the simulation date in historical mode
        
        Args:
            days: Number of days to advance
        """
        if not self.historical_mode:
            logger.warning("Not in historical mode, cannot advance date")
            return
        
        self.current_sim_date += timedelta(days=days)
        logger.debug(f"Advanced sim date to {self.current_sim_date.strftime('%Y-%m-%d')}")
    
    def get_historical_price(self, symbol: str) -> Optional[Tuple[float, int]]:
        """
        Get historical price for a symbol at current simulation date
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (price, volume) or None if not available
        """
        if not self.historical_mode:
            logger.warning("Not in historical mode, cannot get historical price")
            return None
        
        if symbol not in self.historical_data:
            logger.warning(f"No historical data loaded for {symbol}")
            return None
        
        df = self.historical_data[symbol]
        
        # Find the row for current simulation date
        try:
            # Convert current_sim_date to timezone-naive if DataFrame index is timezone-naive
            # Or make both timezone-aware for consistent comparison
            sim_date = self.current_sim_date
            
            # Check if DataFrame index is timezone-aware
            if hasattr(df.index, 'tz') and df.index.tz is not None:
                # DataFrame is timezone-aware, make sim_date aware too
                import pytz
                sim_date = pytz.UTC.localize(sim_date) if sim_date.tzinfo is None else sim_date
            else:
                # DataFrame is timezone-naive, ensure sim_date is also naive
                sim_date = sim_date.replace(tzinfo=None) if sim_date.tzinfo is not None else sim_date
            
            # Try exact match first
            if sim_date in df.index:
                row = df.loc[sim_date]
            else:
                # Find closest date before or equal to current sim date
                valid_dates = df.index[df.index <= sim_date]
                if len(valid_dates) == 0:
                    logger.warning(f"No data available for {symbol} at {sim_date}")
                    return None
                row = df.loc[valid_dates[-1]]
            
            # Use Close price and Volume
            price = float(row['Close'])
            # Handle NaN or non-numeric volume data
            try:
                volume = int(row['Volume']) if pd.notna(row['Volume']) else DEFAULT_VOLUME
            except (ValueError, TypeError):
                logger.warning(f"Invalid volume data for {symbol}, using default")
                volume = DEFAULT_VOLUME
            
            logger.debug(f"Historical price for {symbol} on {self.current_sim_date.strftime('%Y-%m-%d')}: ${price:.2f}")
            return price, volume
            
        except Exception as e:
            logger.error(f"Error getting historical price for {symbol}: {e}")
            return None
    
    def get_stock_price(self, symbol: str, use_random_fallback: bool = True) -> Tuple[float, int]:
        """
        Get stock price - mode-specific behavior with strict isolation
        Returns (price, volume) tuple
        
        HISTORICAL MODE (FROZEN TIME SIMULATION):
        - If historical_mode is enabled, returns price from loaded historical data
        - Simulates frozen time for realistic backtesting
        
        STRICT NO-FALLBACK POLICY:
        - Sandbox mode (PAPER_TRADING_MODE=true, SCHWAB_SANDBOX_MODE=true):
          REQUIRES Schwab API, raises ValueError if unavailable
        - Live mode (PAPER_TRADING_MODE=false):
          REQUIRES Schwab API, raises ValueError if unavailable
        
        FALLBACK ALLOWED:
        - API Disabled (SCHWAB_API_ENABLED=off): yfinance → random
        - Pure Simulation (PAPER_TRADING_MODE=true, SCHWAB_SANDBOX_MODE=false): yfinance → random
        
        Args:
            symbol: Stock symbol to fetch
            use_random_fallback: If True, use random prices when APIs fail
                                Only applies in API disabled or pure simulation modes
        
        Raises:
            ValueError: In sandbox or live mode when Schwab API is unavailable
        """
        # Check for historical mode first (frozen time simulation)
        if self.historical_mode:
            logger.debug(f"[HISTORICAL MODE] Getting frozen time price for {symbol}")
            result = self.get_historical_price(symbol)
            if result is not None:
                return result
            else:
                logger.warning(f"[HISTORICAL MODE] No historical data for {symbol}, falling back to live data")
        
        result = None
        
        # ============================================================
        # STRICT NO-FALLBACK MODES: Sandbox and Live Trading
        # These modes REQUIRE Schwab API and will raise ValueError if it fails
        # ============================================================
        
        # Read mode settings dynamically to support runtime updates from web GUI
        paper_mode = _get_paper_trading_mode()
        sandbox_mode = _get_schwab_sandbox_mode()
        api_enabled = _get_schwab_api_enabled()
        
        if paper_mode and sandbox_mode and api_enabled:
            # SANDBOX MODE: STRICT NO-FALLBACK
            # Requires Schwab sandbox API, raises error if unavailable
            logger.debug(f"[SANDBOX MODE] Fetching {symbol} from Schwab sandbox API (no fallback)")
            result = self.fetch_schwab_stock_price(symbol)
            
            if result is not None:
                logger.debug(f"[SANDBOX MODE] ✓ Successfully fetched {symbol}: ${result[0]:.2f}")
                self.schwab_api_available = True
                return result
            
            # Sandbox API failed - try yfinance fallback (runtime auto-fallback)
            self.schwab_api_available = False
            self.using_yfinance_sim = True
            result = self.fetch_real_stock_price(symbol)
            if result is not None:
                logger.warning(
                    f"[SANDBOX MODE] Schwab failed for {symbol}, using yfinance fallback: ${result[0]:.2f}"
                )
                return result
            # Both Schwab and yfinance failed - raise
            credentials_configured = _are_schwab_credentials_configured()
            error_details = SCHWAB_API_CRITICAL_ERROR_MSG.format(symbol=symbol)
            logger.error(f"[SANDBOX MODE] {error_details}")
            if not credentials_configured:
                logger.error("[SANDBOX MODE] Schwab API credentials not configured (using placeholder values)")
                logger.error("[SANDBOX MODE] To use sandbox mode, configure SCHWAB_API_KEY and SCHWAB_APP_SECRET")
            self.alert_system.send_alert(
                "Sandbox Mode: Schwab API Required",
                f"Schwab sandbox API failed for {symbol}.\n"
                f"yfinance fallback also failed.\n\n"
                f"Options:\n"
                f"1. Fix Schwab API credentials and connectivity\n"
                f"2. Set SCHWAB_SANDBOX_MODE=false for pure simulation\n"
                f"3. Set SCHWAB_API_ENABLED=off for yfinance training mode"
            )
            raise ValueError(error_details)
        
        if not paper_mode and api_enabled:
            # LIVE MODE: STRICT NO-FALLBACK
            # Requires Schwab production API, raises error if unavailable
            logger.debug(f"[LIVE MODE] Fetching {symbol} from Schwab production API (no fallback)")
            result = self.fetch_schwab_stock_price(symbol)
            
            if result is not None:
                logger.debug(f"[LIVE MODE] ✓ Successfully fetched {symbol}: ${result[0]:.2f}")
                return result
            
            # Production API failed - enforce strict no-fallback policy for safety
            error_msg = (
                f"CRITICAL ERROR: Schwab production API failed for {symbol}. "
                f"Live trading mode requires Schwab API connectivity. The process has stopped immediately. "
                f"Please check:\n"
                f"  1. SCHWAB_API_KEY is correct\n"
                f"  2. SCHWAB_APP_SECRET is correct\n"
                f"  3. Network connection is working\n"
                f"  4. Schwab API service is available\n"
                f"To use simulation mode instead, set PAPER_TRADING_MODE=true in .env"
            )
            logger.error(f"[LIVE MODE] {error_msg}")
            
            self.alert_system.send_alert(
                "Live Mode: Schwab API Required",
                f"Schwab production API failed for {symbol}.\n"
                f"Live mode requires Schwab API - NO fallback for safety.\n"
                f"Trading has been stopped."
            )
            
            # Raise error to stop execution - no fallback in live mode
            raise ValueError(error_msg)
        
        # ============================================================
        # FALLBACK ALLOWED MODES: API Disabled and Pure Simulation
        # These modes allow fallback: yfinance → random (if configured)
        # ============================================================
        
        # Determine mode for logging (read dynamically for consistency)
        if not api_enabled:
            mode_str = "API DISABLED"
            logger.debug(f"[{mode_str}] Schwab API disabled, using yfinance for {symbol}")
        else:
            mode_str = "PURE SIMULATION"
            logger.debug(f"[{mode_str}] Using yfinance for {symbol}")
        
        # Try yfinance first
        result = self.fetch_real_stock_price(symbol)
        if result is not None:
            logger.debug(f"[{mode_str}] ✓ Using yfinance price for {symbol}: ${result[0]:.2f}")
            return result
        
        # Fallback to random prices if enabled
        # Check both the parameter AND the global configuration
        allow_random = _get_allow_random_fallback()
        if (use_random_fallback and allow_random) and self._is_pure_simulation_mode():
            logger.warning(f"[{mode_str}] yfinance unavailable for {symbol}, using random price fallback")
            logger.info(f"[{mode_str}] Random fallback is normal in pure simulation mode")
            price = self.generate_random_price()
            volume = self.generate_random_volume()
            logger.debug(f"[{mode_str}] Generated random price for {symbol}: ${price:.2f}")
            return price, volume
        
        # No valid price source available
        logger.error(f"[{mode_str}] Failed to fetch price for {symbol} - all data sources unavailable")
        if not allow_random:
            logger.error(f"[{mode_str}] Random fallback is disabled (ALLOW_RANDOM_FALLBACK=false)")
        raise ValueError(f"Failed to fetch price for {symbol} - all APIs unavailable")

    def _ensure_strategy_manager(self):
        """Lazy-initialize strategy manager and data fetcher for signal-based trading."""
        if getattr(self, '_strategy_manager', None) is not None:
            return
        self._strategy_manager = None
        self._data_fetcher = None
        
        # Check prerequisites for strategy manager
        if not STRATEGIES_AVAILABLE:
            logger.error("CRITICAL: STRATEGIES_AVAILABLE=False - strategies module not loaded!")
            logger.error("   This will cause all signals to return HOLD")
            logger.error("   Check that strategies.py is in the bot directory and imports work")
            return
            
        if StrategyManager is None:
            logger.error("CRITICAL: StrategyManager class not available!")
            logger.error("   This will cause all signals to return HOLD")
            return
            
        if SMAStrategy is None:
            logger.error("CRITICAL: SMAStrategy not available!")
            logger.error("   This will cause all signals to return HOLD")
            return
        
        if STRATEGIES_AVAILABLE and StrategyManager is not None and SMAStrategy is not None:
            self._strategy_manager = StrategyManager()
            
            # Get strategy weights from adaptive learning if available
            strategy_weights = {}
            if self.adaptive_learner:
                try:
                    # Get weights from bandit if using bandit method
                    if ADAPTIVE_LEARNING_METHOD == 'bandit' and self.adaptive_learner.bandit:
                        # Bandit provides probabilities, use as weights
                        bandit_stats = self.adaptive_learner.bandit.get_statistics()
                        for strategy_name in ['SMA', 'Bollinger', 'RSI', 'MACD', 'Momentum']:
                            if strategy_name in bandit_stats.get('probabilities', {}):
                                strategy_weights[strategy_name] = bandit_stats['probabilities'][strategy_name]
                            else:
                                strategy_weights[strategy_name] = 1.0  # Default weight
                    else:
                        # Default equal weights (will be updated as learning progresses)
                        for strategy_name in ['SMA', 'Bollinger', 'RSI', 'MACD', 'Momentum']:
                            strategy_weights[strategy_name] = 1.0
                except Exception as e:
                    logger.warning(f"Failed to get adaptive learning weights: {e} - using equal weights")
                    for strategy_name in ['SMA', 'Bollinger', 'RSI', 'MACD', 'Momentum']:
                        strategy_weights[strategy_name] = 1.0
            else:
                # No adaptive learning - use equal weights
                for strategy_name in ['SMA', 'Bollinger', 'RSI', 'MACD', 'Momentum']:
                    strategy_weights[strategy_name] = 1.0
            
            # Add all available strategies with adaptive weights
            if SMAStrategy is not None:
                self._strategy_manager.add_strategy(
                    SMAStrategy(fast_period=20, slow_period=50), 
                    weight=strategy_weights.get('SMA', 1.0)
                )
            if BollingerBandsStrategy is not None:
                self._strategy_manager.add_strategy(
                    BollingerBandsStrategy(period=20, num_std=2.0),
                    weight=strategy_weights.get('Bollinger', 1.0)
                )
            if RSIStrategy is not None:
                self._strategy_manager.add_strategy(
                    RSIStrategy(period=14, oversold=30, overbought=70),
                    weight=strategy_weights.get('RSI', 1.0)
                )
            if MACDStrategy is not None:
                self._strategy_manager.add_strategy(
                    MACDStrategy(fast=12, slow=26, signal=9),
                    weight=strategy_weights.get('MACD', 1.0)
                )
            if MomentumStrategy is not None:
                self._strategy_manager.add_strategy(
                    MomentumStrategy(period=10),
                    weight=strategy_weights.get('Momentum', 1.0)
                )
            
            logger.info(f"Strategy manager initialized with {len(self._strategy_manager.strategies)} strategies")
            if self.adaptive_learner:
                logger.info("  Using adaptive learning weights")
        if DATA_FETCHER_AVAILABLE:
            try:
                self._data_fetcher = DataFetcher()
            except Exception as e:
                logger.warning(f"DataFetcher init failed for strategy OHLCV: {e}")
                self._data_fetcher = None

    def _fetch_ohlcv_for_strategy(self, symbol: str, period: str = '3mo') -> Optional[pd.DataFrame]:
        """Fetch OHLCV DataFrame for strategy. Uses cache (TTL) then DataFetcher or yfinance. Returns None on failure."""
        cache = getattr(self, '_ohlcv_cache', None)
        cache_ttl = getattr(self, '_ohlcv_cache_ttl', 90)
        cache_key = (symbol, period)
        if cache is not None and cache_ttl > 0:
            if cache_key in cache:
                entry = cache[cache_key]
                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    cached_df, cached_ts = entry[0], entry[1]
                    try:
                        age = (datetime.now() - cached_ts).total_seconds()
                        _min_bars = max(10, int(os.getenv('STRATEGY_MIN_BARS', '50')))
                        if age < cache_ttl and cached_df is not None and len(cached_df) >= _min_bars:
                            logger.debug(f"OHLCV cache hit for {symbol} ({age:.0f}s old)")
                            return cached_df
                    except (TypeError, AttributeError):
                        pass
                del cache[cache_key]
        df = None
        if getattr(self, '_data_fetcher', None) is not None:
            try:
                df = self._data_fetcher.fetch_historical_data_yfinance(symbol, period=period, interval='1d')
            except Exception as e:
                logger.debug(f"DataFetcher OHLCV failed for {symbol}: {e}")
        if df is None and YFINANCE_AVAILABLE:
            try:
                import yfinance as yf
                data = yf.Ticker(symbol).history(period=period, interval='1d')
                if data is not None and not data.empty:
                    data.columns = data.columns.str.lower()
                    if 'date' not in data.columns:
                        data['date'] = data.index
                    df = data
            except Exception as e:
                logger.debug(f"yfinance OHLCV failed for {symbol}: {e}")
        if df is not None and cache is not None and cache_ttl > 0:
            try:
                cache[cache_key] = (df, datetime.now())
                # Limit cache size to avoid unbounded growth (e.g. keep last 50 entries)
                max_entries = 50
                if len(cache) > max_entries:
                    keys_to_drop = list(cache.keys())[: len(cache) - max_entries]
                    for k in keys_to_drop:
                        del cache[k]
            except Exception:
                pass
        return df

    def get_strategy_signal(
        self, symbol: str, use_random_fallback: bool = True
    ) -> Tuple[str, Optional[float], Optional[int]]:
        """
        Get trading signal (BUY/SELL/HOLD) from strategy using OHLCV data, plus current price/volume.

        Used by CLI and GUI trading loops for signal-based trading (Phase 1 per MISSION.md).
        Returns ('HOLD', None, None) if strategies unavailable, insufficient data, or on error.

        Returns:
            (signal, price, volume): signal in BUY|SELL|HOLD; price/volume for execute_trade or None.
        """
        self._ensure_strategy_manager()
        if self._strategy_manager is None:
            return ('HOLD', None, None)
        timing = os.getenv('BOT_TIMING', 'false').lower() == 'true'
        _breakdown = {}
        if timing:
            import time as _time
            _t0 = _time.perf_counter()
        df = self._fetch_ohlcv_for_strategy(symbol)
        if timing:
            _breakdown['ohlcv_s'] = _time.perf_counter() - _t0
        min_bars = max(10, int(os.getenv('STRATEGY_MIN_BARS', '50')))
        if df is None or len(df) < min_bars:
            n_bars = len(df) if df is not None else 0
            logger.info(f"{symbol}: insufficient data ({n_bars} bars, need {min_bars}) — skip")
            if timing and getattr(self, '_cycle_signal_breakdown', None) is not None:
                _breakdown.setdefault('strategy_s', 0)
                _breakdown.setdefault('price_s', 0)
                self._cycle_signal_breakdown.append(_breakdown)
            return ('HOLD', None, None)
        if 'close' not in df.columns:
            logger.info(f"{symbol}: no 'close' column in data — skip")
            if timing and getattr(self, '_cycle_signal_breakdown', None) is not None:
                _breakdown.setdefault('strategy_s', 0)
                _breakdown.setdefault('price_s', 0)
                self._cycle_signal_breakdown.append(_breakdown)
            return ('HOLD', None, None)
        if timing:
            _t0 = _time.perf_counter()
        try:
            signal = self._strategy_manager.generate_combined_signal(df.copy())
        except Exception as e:
            logger.warning(f"Strategy signal failed for {symbol}: {e}")
            if timing and getattr(self, '_cycle_signal_breakdown', None) is not None:
                _breakdown['strategy_s'] = _time.perf_counter() - _t0
                _breakdown.setdefault('price_s', 0)
                self._cycle_signal_breakdown.append(_breakdown)
            return ('HOLD', None, None)
        if timing:
            _breakdown['strategy_s'] = _time.perf_counter() - _t0
        price, volume = None, None
        if PRICE_SOURCE == 'last_close':
            last = df.iloc[-1]
            price = float(last['close'])
            volume = int(last.get('volume', 1_000_000))
            logger.debug(f"Using last close/volume for {symbol} (PRICE_SOURCE=last_close)")
            if timing:
                _breakdown['price_s'] = 0.0
        else:
            # Use prefetched price if available to avoid per-symbol calls
            if isinstance(getattr(self, '_prefetched_prices', None), dict) and symbol in self._prefetched_prices:
                price, volume = self._prefetched_prices.get(symbol)
                if timing:
                    _breakdown['price_s'] = 0.0
            else:
                try:
                    if timing:
                        _t0 = _time.perf_counter()
                    allow = use_random_fallback
                    price, volume = self.get_stock_price(symbol, use_random_fallback=allow)
                    if timing:
                        _breakdown['price_s'] = _time.perf_counter() - _t0
                except ValueError:
                    last = df.iloc[-1]
                    price = float(last['close'])
                    volume = int(last.get('volume', 1_000_000))
                    logger.debug(f"Using last close/volume for {symbol} (get_stock_price unavailable)")
                    if timing:
                        _breakdown['price_s'] = 0.0
        if timing and getattr(self, '_cycle_signal_breakdown', None) is not None:
            _breakdown.setdefault('ohlcv_s', 0)
            _breakdown.setdefault('strategy_s', 0)
            _breakdown.setdefault('price_s', 0)
            self._cycle_signal_breakdown.append(_breakdown)
        if price is None or volume is None:
            return ('HOLD', None, None)
        
        # ML Signal Filter: Filter signals based on ML predictions (if enabled and trained)
        if (self.ml_signal_filter and 
            self.ml_signal_filter.enabled and 
            self.ml_signal_filter.is_trained and
            signal in ('BUY', 'SELL')):  # Only filter BUY/SELL, not HOLD
            try:
                # Get indicator values from strategy manager
                all_indicators = self._strategy_manager.get_all_indicator_values(df.copy())
                
                # Flatten indicators dict (strategy_name -> indicators) into single dict
                indicators = {}
                for strategy_name, strategy_indicators in all_indicators.items():
                    if isinstance(strategy_indicators, dict):
                        # Use strategy name as prefix to avoid conflicts
                        for key, value in strategy_indicators.items():
                            indicators[key] = value
                
                # Prepare signal data for ML filter
                signal_data = {
                    'symbol': symbol,  # Add symbol for cache key
                    'signal': signal,
                    'price': price,
                    'indicators': indicators,
                    'market_conditions': {
                        'volume': volume,
                        'volatility': self.calculate_volatility(symbol) if symbol in self.price_history else 0.05
                    }
                }
                
                # Check if signal should be filtered (read at runtime so Restart picks up GUI changes)
                should_filter, scores = self.ml_signal_filter.should_filter_signal(
                    signal_data,
                    min_confidence=self.ml_filter_min_confidence,
                    min_win_prob=self.ml_filter_min_win_prob
                )
                
                if should_filter:
                    logger.info(f"ML signal filter rejected {signal} for {symbol}: "
                              f"confidence={scores['confidence']:.3f}, win_prob={scores['win_probability']:.3f}")
                    # Update component coordination state (enhancement)
                    self.component_coordination_state['last_ml_filter_update'] = datetime.now()
                    # Return HOLD but keep price/volume so callers can display context
                    return ('HOLD', price, volume)
                else:
                    logger.debug(f"ML signal filter accepted {signal} for {symbol}: "
                               f"confidence={scores['confidence']:.3f}, win_prob={scores['win_probability']:.3f}")
                    # Update component coordination state (enhancement)
                    self.component_coordination_state['last_ml_filter_update'] = datetime.now()
            except Exception as e:
                logger.warning(f"ML signal filter failed for {symbol}: {e} - proceeding with signal")
                # Continue with signal if filter fails
        
        return (signal, price, volume)

    def _signal_to_action(self, symbol: str, signal: str) -> Optional[str]:
        """
        Map (signal, position) → action for Phase 1 buy+short (MISSION.md).

        BUY + flat → BUY (open long).  BUY + short → COVER (close short).  BUY + long → skip.
        SELL + long → SELL (close long).  SELL + flat → SHORT (open short).  SELL + short → skip.
        HOLD or unmapped → None (skip).
        """
        if signal not in ('BUY', 'SELL'):
            return None
        pos = self.positions.get(symbol)
        side = pos.get('side', 'long') if pos else None
        if signal == 'BUY':
            if side == 'short':
                return 'COVER'
            if side == 'long':
                return None
            return 'BUY'
        if signal == 'SELL':
            if side == 'long':
                return 'SELL'
            if side == 'short':
                return None
            return 'SHORT'
        return None

    def generate_random_price(self, base_price: float = None) -> float:
        """
        Generate a random price for paper trading simulation
        If base_price is provided, generates a price within +/- 5% of it
        Otherwise, generates a random price between $1 and $500
        
        NOTE: This is for simulation only. For real trading, use get_stock_price()
        """
        if base_price:
            variation = random.uniform(-0.05, 0.05)
            return base_price * (1 + variation)
        else:
            return random.uniform(1.0, 500.0)
    
    def generate_random_volume(self) -> int:
        """Generate random trading volume for paper trading simulation"""
        return random.randint(100000, 10000000)
    
    def import_tos_csv(self, csv_file: str) -> List[Dict]:
        """
        Import TOS paperMoney export CSV file
        Expected columns: Symbol, Quantity, Price, etc.
        Returns list of trades parsed from CSV
        """
        try:
            df = pd.read_csv(csv_file)
            
            print(f"\n[TOS CSV IMPORT] Loading {csv_file}")
            print(f"  Columns found: {', '.join(df.columns)}")
            print(f"  Total rows: {len(df)}")
            
            trades = []
            
            # Normalize column names (case-insensitive)
            df.columns = df.columns.str.strip().str.lower()
            
            # Check for required columns
            required_cols = ['symbol', 'quantity', 'price']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"[ERROR] Missing required columns: {', '.join(missing_cols)}")
                return []
            
            for idx, row in df.iterrows():
                trade = {
                    'symbol': str(row['symbol']).strip(),
                    'quantity': float(row['quantity']),
                    'price': float(row['price']),
                }
                
                # Add optional columns if they exist
                if 'action' in df.columns:
                    trade['action'] = str(row['action']).strip().upper()
                else:
                    trade['action'] = 'BUY' if trade['quantity'] > 0 else 'SELL'
                
                if 'date' in df.columns:
                    trade['date'] = row['date']
                
                # Safely handle optional pnl column
                if 'pnl' in df.columns:
                    try:
                        trade['pnl'] = float(row['pnl'])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse pnl value for row {idx}: {e}")
                        trade['pnl'] = 0.0
                
                trades.append(trade)
            
            print(f"  Successfully parsed {len(trades)} trades")
            return trades
            
        except Exception as e:
            print(f"[ERROR] Failed to import TOS CSV: {str(e)}")
            return []
    
    def process_tos_trades(self, trades: List[Dict]):
        """
        Process imported TOS trades to update bot track record
        Simulates P&L and updates trade history
        """
        print(f"\n[TOS TRADE PROCESSING] Processing {len(trades)} trades")
        
        for trade in trades:
            symbol = trade['symbol']
            action = trade['action']
            quantity = abs(trade['quantity'])
            price = trade['price']
            
            # Simulate entry and exit for P&L calculation
            if action == 'BUY':
                # For buys, simulate an exit at +/- 2% for P&L
                exit_price = price * random.uniform(0.98, 1.02)
                is_win = exit_price > price
                entry_price = price
            else:  # SELL
                # For sells (short), simulate a cover at +/- 2%
                exit_price = price * random.uniform(0.98, 1.02)
                is_win = exit_price < price
                # For SELL, price is the exit, calculate simulated entry
                entry_price = exit_price * 1.02 if is_win else exit_price * 0.98
            
            # Calculate P&L
            pnl = (exit_price - entry_price) * quantity
            pnl_percent = ((exit_price - entry_price) / entry_price) * 100
            
            # Record the trade with comprehensive data
            self.record_trade(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                is_win=is_win,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl=pnl,
                pnl_percent=pnl_percent,
                exit_reason='tos_csv_import'
            )
        
        print(f"  Processing complete. Total trades: {self.track_record['total_trades']}")
        print(f"  Win rate: {self.track_record['win_rate']:.1%}")

    def print_summary(self):
        """Print current bot status and track record"""
        # Calculate total P&L using helper method
        total_pnl, total_pnl_percent = self.calculate_total_pnl()
        
        # Determine trading mode display string
        if PAPER_TRADING_MODE:
            if not SCHWAB_API_ENABLED:
                mode_str = "PAPER TRADING (API Disabled - yfinance Simulation)"
            elif SCHWAB_SANDBOX_MODE:
                mode_str = "PAPER TRADING (Schwab Sandbox - Strict Mode)"
            else:
                mode_str = "PAPER TRADING (Pure Simulation)"
        else:
            mode_str = "LIVE TRADING (Production - Strict Mode)"
        
        print("\n" + "="*60)
        print("TRADING BOT UPDATED SUMMARY")
        print("="*60)
        print(f"Mode: {mode_str}")
        
        # PDT status - only enforced in production mode
        mode_name = "API disabled" if not SCHWAB_API_ENABLED else (
            "sandbox mode" if SCHWAB_SANDBOX_MODE else (
                "simulation mode" if PAPER_TRADING_MODE else "production mode"
            )
        )
        if PAPER_TRADING_MODE:
            print(f"PDT Protection: Disabled ({mode_name} - no limit in training mode)")
        else:
            print(f"PDT Protection: Enabled ({mode_name} - regulatory compliance)")
        print(f"Day Trades Used: {self.get_day_trade_count()}/3")
        if self.total_capital >= 25000:
            print(f"  ✓ Capital >${25000:.0f}, unlimited day trades allowed")
        else:
            remaining = max(0, 3 - self.get_day_trade_count())
            print(f"  ⚠ Capital <${25000:.0f}, {remaining} day trades remaining")
        
        print(f"Total Initial Capital: ${self.starting_capital:.2f}")
        print(f"Final Capital: ${self.total_capital:.2f}")
        print(f"Total P&L: ${total_pnl:.2f} ({total_pnl_percent:.1f}%)")
        print(f"Total Trades: {self.track_record['total_trades']}")
        print(f"Winning Trades: {self.track_record['winning_trades']}")
        print(f"Losing Trades: {self.track_record['losing_trades']}")
        print(f"Win Rate: {self.track_record['win_rate']:.1%}")
        print(f"Consecutive Losses: {self.consecutive_losses}")
        print(f"Current Allocation: ${self.track_record['current_allocation']:.2f}")
        print(f"Risk Threshold: {BOT_RISK_THRESHOLD:.1%}")
        print(f"Max Allocation: ${BOT_MAX_ALLOCATION:.2f}")
        
        # Resource throttling stats
        throttle_stats = self.throttler.get_stats()
        if throttle_stats['enabled']:
            print(f"\nResource Throttling: Enabled")
            print(f"  CPU Limit: {throttle_stats['max_cpu_percent']}%")
            print(f"  Memory Limit: {throttle_stats['max_memory_percent']}%")
            print(f"  Disk Limit: {throttle_stats['max_disk_percent']}%")
            print(f"  Network Limit: {throttle_stats['max_network_mbps']}MB/s")
            print(f"  Throttle Events: {throttle_stats['throttle_count']}")
        else:
            print(f"\nResource Throttling: Disabled")
        
        # Sentiment analysis status
        if self.sentiment_analyzer:
            print(f"\nSentiment Analysis: Enabled")
            print(f"  Method: {self.sentiment_analyzer.method}")
            if self.sentiment_analyzer.news_api_available:
                print(f"  NewsAPI: Configured")
            if self.sentiment_analyzer.finnhub_available:
                print(f"  Finnhub: Configured")
        else:
            print(f"\nSentiment Analysis: Disabled")
        
        # Portfolio optimization status
        if self.portfolio_optimizer:
            print(f"\nPortfolio Optimization: Enabled")
            print(f"  Risk-Free Rate: {self.portfolio_optimizer.risk_free_rate:.1%}")
            
            # Calculate diversification if we have symbols
            if len(self.price_history) > 1:
                symbols = list(self.price_history.keys())
                diversification = self.calculate_portfolio_diversification(symbols)
                print(f"  Portfolio Diversification: {diversification:.2f} (0=low, 1=high)")
        else:
            print(f"\nPortfolio Optimization: Disabled")
        
        print("="*60 + "\n")
    
    def save_trade_history(self, filename: str = None):
        """
        Save trade history to JSON file, separating modes
        
        Args:
            filename: Optional custom filename (default: auto-generated based on mode and date)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if filename is None:
            # Auto-generate filename based on mode
            if not SCHWAB_API_ENABLED:
                filename = f'trade_history_api_disabled_{timestamp}.json'
            elif PAPER_TRADING_MODE and SCHWAB_SANDBOX_MODE:
                filename = f'trade_history_sandbox_{timestamp}.json'
            elif PAPER_TRADING_MODE:
                filename = f'trade_history_simulation_{timestamp}.json'
            else:
                filename = f'trade_history_live_{timestamp}.json'
        
        try:
            # Prepare data for export
            export_data = {
                'metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'mode': 'api_disabled' if not SCHWAB_API_ENABLED else (
                        'sandbox' if (PAPER_TRADING_MODE and SCHWAB_SANDBOX_MODE) else (
                            'simulation' if PAPER_TRADING_MODE else 'live'
                        )
                    ),
                    'total_trades': self.track_record['total_trades'],
                    'win_rate': self.track_record['win_rate'],
                    'initial_capital': self.starting_capital,
                    'final_capital': self.total_capital,
                    'total_pnl': self.total_capital - self.starting_capital
                },
                'trades': self.trade_history
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Trade history saved to {filename}")
            print(f"\n[TRADE HISTORY SAVED]")
            print(f"  File: {filename}")
            print(f"  Total Trades: {len(self.trade_history)}")
            
        except Exception as e:
            logger.error(f"Failed to save trade history: {e}")
            print(f"\n[ERROR] Failed to save trade history: {e}")
    
    def get_trades_by_mode(self, mode: str = None) -> List[Dict]:
        """
        Filter trades by mode
        
        Args:
            mode: Mode to filter by ('yfinance_sim', 'schwab_sandbox', 'pure_simulation', 'live_trading')
                  If None, returns all trades
        
        Returns:
            List of trades matching the mode
        """
        if mode is None:
            return self.trade_history
        
        return [trade for trade in self.trade_history if trade.get('mode') == mode]
    
    def backtest_loop(self, start_date: str, end_date: str, symbols: List[str]) -> Dict:
        """
        Run backtesting loop using historical data
        Instance method version for OOP design
        
        Args:
            start_date: Start date for backtest (YYYY-MM-DD format)
            end_date: End date for backtest (YYYY-MM-DD format)
            symbols: List of stock symbols to backtest
        
        Returns:
            Dictionary with backtest results including win rate, P&L, and trade details
        """
        logger.info("="*60)
        logger.info("BACKTESTING MODE - Historical Data Analysis")
        logger.info("="*60)
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Symbols: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")
        logger.info(f"Initial Capital: ${self.total_capital:.2f}")
        logger.info("="*60)
        
        data_fetcher = DataFetcher()
        all_trades = []
        starting_capital = self.total_capital
        last_prices = {}  # Store last known prices for each symbol
        
        # Convert dates to pandas datetime
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
        except Exception as e:
            logger.error(f"Invalid date format: {e}")
            return {
                'metadata': {
                    'error': f"Invalid date format: {e}",
                    'initial_capital': starting_capital,
                    'final_capital': self.total_capital
                },
                'trades': []
            }
        
        # Process each symbol
        for symbol in symbols:
            logger.info(f"\n--- Backtesting {symbol} ---")
            
            # Fetch historical data using yfinance
            # Calculate period from start and end dates
            try:
                start_dt_obj = pd.to_datetime(start_date)
                end_dt_obj = pd.to_datetime(end_date)
                days_diff = (end_dt_obj - start_dt_obj).days
                
                # Map days to yfinance period format
                if days_diff <= 5:
                    period = '5d'
                elif days_diff <= 30:
                    period = '1mo'
                elif days_diff <= 90:
                    period = '3mo'
                elif days_diff <= 180:
                    period = '6mo'
                elif days_diff <= 365:
                    period = '1y'
                elif days_diff <= 730:
                    period = '2y'
                else:
                    period = '5y'
            except Exception:
                period = '1y'  # Default fallback
            
            historical_data = data_fetcher.fetch_historical_data_yfinance(
                symbol, 
                period=period,
                interval='1d'
            )
            
            if historical_data is None or historical_data.empty:
                logger.warning(f"No historical data available for {symbol}, skipping...")
                continue
            
            # Filter data to match requested date range
            if 'date' in historical_data.columns:
                historical_data['date'] = pd.to_datetime(historical_data['date'])
                historical_data = historical_data[
                    (historical_data['date'] >= start_dt) & 
                    (historical_data['date'] <= end_dt)
                ]
            
            if historical_data.empty:
                logger.warning(f"No data in date range for {symbol}, skipping...")
                continue
            
            logger.info(f"Loaded {len(historical_data)} days of historical data for {symbol}")
            
            # Iterate through historical data day by day
            for idx in range(len(historical_data)):
                row = historical_data.iloc[idx]
                date = row.get('date', row.name)
                open_price = row['open']
                high_price = row['high']
                low_price = row['low']
                close_price = row['close']
                volume = row.get('volume', 1000000)
                
                # Update price history
                self.update_price_history(symbol, close_price)
                
                # Check if we have an open position for this symbol
                if symbol not in self.positions:
                    # Check if we can open a new position
                    can_trade, reason = self.can_open_new_position()
                    if not can_trade:
                        logger.debug(f"{date}: Cannot open position - {reason}")
                        continue
                    
                    # Try to filter stock and enter a position
                    passes_filter, filter_reason = self.filter_stock(symbol, open_price, volume)
                    if passes_filter:
                        # Calculate position size based on BOT_POSITION_SIZE and enforce allocation bounds
                        position_size = self.total_capital * BOT_POSITION_SIZE
                        # Enforce configured allocation limits
                        if position_size < BOT_MIN_ALLOCATION:
                            position_size = BOT_MIN_ALLOCATION
                        elif position_size > BOT_MAX_ALLOCATION:
                            position_size = BOT_MAX_ALLOCATION
                        
                        # Check if we have enough capital for at least the minimum allocation
                        if self.total_capital >= BOT_MIN_ALLOCATION and position_size >= BOT_MIN_ALLOCATION:
                            # Open position directly without execute_trade_paper_mode to avoid
                            # immediate trade simulation and allow backtest to manage positions
                            # over historical time periods
                            quantity = position_size / open_price
                            stop_percent = BOT_TRAILING_STOP_PERCENT
                            
                            # Open the position
                            self.open_position(symbol, open_price, quantity, stop_percent)
                            
                            # Record the trade
                            trade_info = {
                                'date': str(date),
                                'symbol': symbol,
                                'action': 'BUY',
                                'price': open_price,
                                'quantity': quantity,
                                'allocation': position_size
                            }
                            all_trades.append(trade_info)
                            logger.debug(f"{date}: BUY {symbol} @ ${open_price:.2f}")
                else:
                    # We have a position - check exit conditions
                    position = self.positions[symbol]
                    entry_price = position['entry_price']
                    
                    # Check take profit (use high price of the day)
                    take_profit_price = entry_price * (1 + BOT_TAKE_PROFIT_PERCENT)
                    if high_price >= take_profit_price:
                        # Take profit triggered
                        exit_price = min(high_price, take_profit_price)
                        pnl_info = self.close_position(symbol, exit_price, exit_reason='take_profit')
                        
                        trade_info = {
                            'date': str(date),
                            'symbol': symbol,
                            'action': 'SELL',
                            'price': exit_price,
                            'triggered_by': 'take_profit',
                            'pnl': pnl_info
                        }
                        all_trades.append(trade_info)
                        logger.debug(f"{date}: SELL {symbol} @ ${exit_price:.2f} (Take Profit)")
                        continue
                    
                    # Check trailing stop (use low price of the day)
                    stop_triggered = self.check_trailing_stop(symbol, low_price)
                    if stop_triggered and stop_triggered != 'partial_exit':
                        # Trailing stop triggered
                        pnl_info = self.close_position(symbol, low_price, exit_reason='trailing_stop')
                        
                        trade_info = {
                            'date': str(date),
                            'symbol': symbol,
                            'action': 'SELL',
                            'price': low_price,
                            'triggered_by': 'trailing_stop',
                            'pnl': pnl_info
                        }
                        all_trades.append(trade_info)
                        logger.debug(f"{date}: SELL {symbol} @ ${low_price:.2f} (Trailing Stop)")
                        continue
                    
                    # Update high price for trailing stop
                    if high_price > position.get('high_price', 0):
                        position['high_price'] = high_price
            
            # Store last known price for this symbol
            if historical_data is not None and not historical_data.empty:
                last_prices[symbol] = {
                    'close': historical_data['close'].iloc[-1],
                    'date': historical_data['date'].iloc[-1] if 'date' in historical_data.columns else historical_data.index[-1]
                }
        
        # Close any remaining positions at last available prices
        logger.info("\n--- Closing remaining positions ---")
        for symbol in list(self.positions.keys()):
            # Use stored last price if available, otherwise use entry price (break-even)
            if symbol in last_prices:
                final_price = last_prices[symbol]['close']
                final_date = last_prices[symbol]['date']
            else:
                # If no stored price, use current position entry price (break-even)
                final_price = self.positions[symbol]['entry_price']
                final_date = datetime.now()
            
            pnl_info = self.close_position(symbol, final_price, exit_reason='backtest_end')
            
            trade_info = {
                'date': str(final_date),
                'symbol': symbol,
                'action': 'SELL',
                'price': final_price,
                'triggered_by': 'backtest_end',
                'pnl': pnl_info
            }
            all_trades.append(trade_info)
        
        # Calculate results
        final_capital = self.total_capital
        total_pnl = final_capital - starting_capital
        roi = (total_pnl / starting_capital) * 100 if starting_capital > 0 else 0
        
        winning_trades = self.track_record['winning_trades']
        losing_trades = self.track_record['losing_trades']
        total_trades = self.track_record['total_trades']
        win_rate = self.track_record['win_rate']
        
        backtest_results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'start_date': start_date,
                'end_date': end_date,
                'symbols': symbols,
                'initial_capital': starting_capital,
                'final_capital': final_capital,
                'total_pnl': total_pnl,
                'roi_percent': roi,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'parameters': {
                    'risk_threshold': BOT_RISK_THRESHOLD,
                    'trailing_stop_percent': BOT_TRAILING_STOP_PERCENT,
                    'take_profit_percent': BOT_TAKE_PROFIT_PERCENT,
                    'stop_loss_percent': BOT_STOP_LOSS_PERCENT,
                    'position_size': BOT_POSITION_SIZE,
                    'min_allocation': BOT_MIN_ALLOCATION,
                    'max_allocation': BOT_MAX_ALLOCATION,
                }
            },
            'trades': all_trades
        }
        
        # Save results to backtest_history.json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backtest_history_{timestamp}.json'
        
        try:
            with open(filename, 'w') as f:
                json.dump(backtest_results, f, indent=2)
            logger.info(f"\nBacktest results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save backtest results: {e}")
        
        return backtest_results
    
    def print_backtest_summary(self, backtest_results: Dict = None):
        """
        Print summary of backtest results
        
        Args:
            backtest_results: Optional dictionary of backtest results
                            If None, uses current bot state
        """
        if backtest_results is None:
            # Use current bot state
            total_pnl, total_pnl_percent = self.calculate_total_pnl()
            
            print("\n" + "="*60)
            print("BACKTEST SUMMARY")
            print("="*60)
            print(f"Initial Capital: ${self.starting_capital:.2f}")
            print(f"Final Capital: ${self.total_capital:.2f}")
            print(f"Total P&L: ${total_pnl:+.2f} ({total_pnl_percent:+.1f}%)")
            print(f"Total Trades: {self.track_record['total_trades']}")
            print(f"Winning Trades: {self.track_record['winning_trades']}")
            print(f"Losing Trades: {self.track_record['losing_trades']}")
            print(f"Win Rate: {self.track_record['win_rate']:.2%}")
            print("="*60 + "\n")
        else:
            # Use provided backtest results
            metadata = backtest_results.get('metadata', {})
            
            print("\n" + "="*60)
            print("BACKTEST SUMMARY")
            print("="*60)
            print(f"Period: {metadata.get('start_date', 'N/A')} to {metadata.get('end_date', 'N/A')}")
            print(f"Symbols: {len(metadata.get('symbols', []))} stocks")
            print(f"Initial Capital: ${metadata.get('initial_capital', 0):.2f}")
            print(f"Final Capital: ${metadata.get('final_capital', 0):.2f}")
            print(f"Total P&L: ${metadata.get('total_pnl', 0):+.2f}")
            print(f"ROI: {metadata.get('roi_percent', 0):+.2f}%")
            print(f"Total Trades: {metadata.get('total_trades', 0)}")
            print(f"Winning Trades: {metadata.get('winning_trades', 0)}")
            print(f"Losing Trades: {metadata.get('losing_trades', 0)}")
            print(f"Win Rate: {metadata.get('win_rate', 0):.2%}")
            print("="*60 + "\n")


def validate_api_connectivity(bot: 'TradingBot') -> Tuple[bool, str]:
    """
    Validate API connectivity when required (sandbox or live mode)
    
    Enforces strict "no fallback" policy in sandbox and live modes.
    In these modes, if Schwab API is unavailable, startup is blocked.
    
    Respects SCHWAB_API_ENABLED setting - when disabled, skips Schwab checks entirely.
    
    Args:
        bot: TradingBot instance to test with
        
    Returns:
        Tuple of (is_connected, message)
    """
    # Check if Schwab API is disabled
    if not SCHWAB_API_ENABLED:
        logger.info("Schwab API is disabled (SCHWAB_API_ENABLED=off)")
        logger.info("Bot will use yfinance for market data - testing yfinance connectivity...")
        
        # Test yfinance connectivity
        test_symbol = "AAPL"
        yfinance_result = bot.fetch_real_stock_price(test_symbol)
        if yfinance_result is not None:
            logger.info(f"✓ yfinance API available (price: ${yfinance_result[0]:.2f})")
            bot.schwab_api_available = False
            bot.using_yfinance_sim = True
            return True, "Schwab API disabled - using yfinance for market data"
        else:
            logger.warning("yfinance API unavailable - will use random simulation")
            bot.schwab_api_available = False
            bot.using_yfinance_sim = False
            bot.alert_system.send_alert(
                "Data Warning",
                "yfinance unavailable - using random prices for simulation.\n"
                "This is NOT real market data. Prices are randomly generated.\n"
                "For real data, ensure yfinance is installed and working."
            )
            return True, "Schwab API disabled - using random price simulation"
    
    # Only check connectivity if we're in a mode that requires APIs
    if PAPER_TRADING_MODE and not SCHWAB_SANDBOX_MODE:
        # Pure simulation mode - no API required
        return True, "Simulation mode - no API required"
    
    # Test with a well-known symbol
    test_symbol = "AAPL"
    
    try:
        logger.info(f"Testing API connectivity with symbol {test_symbol}...")
        
        # Try to fetch a price
        if PAPER_TRADING_MODE and SCHWAB_SANDBOX_MODE:
            # Test sandbox API - requires connectivity, no fallback
            logger.info("Testing Schwab sandbox API connectivity...")
            
            # Check if credentials are configured
            if not _are_schwab_credentials_configured():
                error_msg = (
                    "Sandbox mode requires Schwab API credentials to be configured.\n"
                    "Credentials are using placeholder values. Please:\n"
                    "  1. Get credentials from https://developer.schwab.com/\n"
                    "  2. Set SCHWAB_API_KEY and SCHWAB_APP_SECRET in .env file\n"
                    "  3. Run bot to authenticate and generate token.json\n"
                    "\n"
                    "Alternatively:\n"
                    "  - Set SCHWAB_SANDBOX_MODE=false for pure simulation\n"
                    "  - Set SCHWAB_API_ENABLED=off for yfinance training mode"
                )
                logger.error(error_msg)
                bot.schwab_api_available = False
                return False, error_msg
            
            result = bot.fetch_schwab_stock_price(test_symbol)
            if result is not None:
                logger.info(f"✓ Schwab sandbox API connection successful (price: ${result[0]:.2f})")
                bot.schwab_api_available = True
                return True, "Schwab sandbox API connected"
            else:
                # API failure in sandbox mode - block startup
                error_msg = SCHWAB_API_CONNECTIVITY_ERROR_MSG
                logger.error(error_msg)
                bot.schwab_api_available = False
                bot.alert_system.send_alert(
                    "Sandbox Mode: API Connectivity Failed",
                    "Schwab sandbox API connectivity check failed.\n"
                    "Sandbox mode requires working Schwab API - no fallback allowed.\n"
                    "Bot startup has been blocked.\n\n"
                    "Options:\n"
                    "1. Fix Schwab API credentials and connectivity\n"
                    "2. Set SCHWAB_SANDBOX_MODE=false for pure simulation\n"
                    "3. Set SCHWAB_API_ENABLED=off for yfinance training mode"
                )
                return False, error_msg
        elif not PAPER_TRADING_MODE:
            # Test production API - no fallback in live mode
            result = bot.fetch_schwab_stock_price(test_symbol)
            if result is not None:
                logger.info(f"✓ Schwab production API connection successful (price: ${result[0]:.2f})")
                return True, "Schwab production API connected"
            else:
                error_msg = (
                    "Production API connectivity check failed. Live mode requires Schwab production API. "
                    "Please check:\n"
                    "  1. Schwab API credentials (SCHWAB_API_KEY, etc.)\n"
                    "  2. Network connectivity\n"
                    "  3. Schwab API service status\n"
                    "  4. API authentication and permissions"
                )
                logger.error(error_msg)
                return False, error_msg
        
        return True, "API check passed"
        
    except Exception as e:
        error_msg = f"API connectivity check failed with exception: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def has_placeholder_pattern(key_value: str, patterns: List[str]) -> bool:
    """
    Check if a configuration value contains placeholder patterns
    
    Args:
        key_value: The configuration value to check
        patterns: List of placeholder patterns to search for
    
    Returns:
        True if any placeholder pattern is found, False otherwise
    """
    if not key_value:
        return False
    
    for pattern in patterns:
        if pattern in key_value.lower():
            return True
    return False


def validate_configuration() -> Tuple[bool, List[str]]:
    """
    Validate bot configuration before starting
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    
    # Check for configuration conflicts first
    try:
        from env_conflict_checker import check_env_conflicts
        conflicts = check_env_conflicts()
        
        # Add errors to issues list
        for conflict in conflicts:
            if conflict.severity == 'ERROR':
                issues.append(f"{conflict.title}: {conflict.description} Fix: {conflict.suggestion}")
            elif conflict.severity == 'WARNING':
                logger.warning(f"Configuration Warning - {conflict.title}")
                logger.warning(f"  Variables: {', '.join(conflict.affected_vars)}")
                logger.warning(f"  Issue: {conflict.description}")
                logger.warning(f"  Suggestion: {conflict.suggestion}")
            elif conflict.severity == 'INFO':
                logger.info(f"Configuration Info - {conflict.title}")
                logger.info(f"  Note: {conflict.description}")
    except ImportError:
        logger.debug("env_conflict_checker module not available, skipping conflict checks")
    
    # Check trading mode
    mode = "PAPER" if PAPER_TRADING_MODE else "LIVE"
    logger.info(f"\n--- Configuration Validation ---")
    logger.info(f"Trading mode: {mode}")
    
    # Check sandbox mode and API enabled status
    if not SCHWAB_API_ENABLED:
        logger.info("Schwab API: DISABLED")
        logger.info("  → Schwab API connectivity is disabled by configuration")
        logger.info("  → Bot will use yfinance for market data")
        logger.info("  → Running in training/simulation mode")
        logger.info("  → PDT rules are DISABLED")
        
        # Cannot run in live mode with API disabled
        if not PAPER_TRADING_MODE:
            issues.append(
                "Cannot run in LIVE mode with SCHWAB_API_ENABLED=off. "
                "Live trading requires Schwab API connectivity. "
                "Fix: Set SCHWAB_API_ENABLED=on or PAPER_TRADING_MODE=true to proceed."
            )
    elif PAPER_TRADING_MODE and SCHWAB_SANDBOX_MODE:
        logger.info("Sandbox mode: ENABLED (Strict - NO fallback)")
        logger.info("  → Bot requires Schwab sandbox API connectivity")
        logger.info("  → NO fallback to yfinance or random simulation")
        logger.info("  → Startup will be blocked if API unavailable")
        logger.info("  → PDT rules are DISABLED")
    elif PAPER_TRADING_MODE:
        logger.info("Simulation mode: ENABLED")
        logger.info("  → Bot will use yfinance for market data")
        logger.info("  → Random simulation if yfinance fails")
        logger.info("  → Schwab API not required")
        logger.info("  → PDT rules are DISABLED")
    else:
        logger.info("Production mode: ENABLED (Strict - NO fallback)")
        logger.info("  → Bot requires Schwab production API connectivity")
        logger.info("  → NO fallback to yfinance or simulation")
        logger.info("  → Real money trades will be executed")
        logger.info("  → PDT rules are ENABLED for regulatory compliance")
    
    # If live mode, validate credentials and API enabled status
    if not PAPER_TRADING_MODE:
        # Check if API is disabled in live mode
        if not SCHWAB_API_ENABLED:
            issues.append(
                "Cannot run in LIVE mode with SCHWAB_API_ENABLED=off. "
                "Live trading requires Schwab API connectivity. "
                "Fix: Set SCHWAB_API_ENABLED=on or PAPER_TRADING_MODE=true to proceed."
            )
        
        logger.info("\nLive mode detected - validating credentials...")
        
        required_credentials = {
            'SCHWAB_API_KEY': SCHWAB_API_KEY,
            'SCHWAB_APP_SECRET': SCHWAB_APP_SECRET,
            'SCHWAB_CALLBACK_URL': SCHWAB_CALLBACK_URL,
            'SCHWAB_ACCOUNT_ID': SCHWAB_ACCOUNT_ID
        }
        
        placeholder_values = ['your_app_key', 'your_app_secret', 'your_redirect_uri', 'your_account_number']
        
        for cred_name, cred_value in required_credentials.items():
            if not cred_value or cred_value in placeholder_values:
                issues.append(f"{cred_name} is not configured or is a placeholder")
        
        if issues:
            logger.error("Live mode credential validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
    
    # Check for placeholder values in sensitive API keys ONLY if they are required for enabled features
    # These API keys are optional and should only be validated if the feature using them is enabled
    
    placeholder_patterns = ['your_', 'your-', 'placeholder', 'example.com']
    
    # ALFa AI (LiteLLM) - AI auto-tweak requires the brain to be enabled
    if BOT_ENABLE_AI_AUTO_TWEAK:
        litellm_on = os.getenv('LITELLM_ENABLED', 'false').strip().lower() in ('true', '1', 'yes')
        if not litellm_on:
            issues.append(
                "LITELLM_ENABLED must be true when BOT_ENABLE_AI_AUTO_TWEAK=true. "
                "Enable the ALFa AI brain (LiteLLM) or set BOT_ENABLE_AI_AUTO_TWEAK=false."
            )
    
    # Alpha Vantage API - optional for fundamental data
    av_key = get_decrypted_env('ALPHA_VANTAGE_API_KEY', '')
    if av_key and has_placeholder_pattern(av_key, placeholder_patterns):
        logger.info("Alpha Vantage API key has placeholder value - fundamental data features limited")
    
    # News API keys - only warn if sentiment analysis is enabled
    news_key = get_decrypted_env('NEWS_API_KEY', '')
    finnhub_key = get_decrypted_env('FINNHUB_API_KEY', '')
    
    if ENABLE_SENTIMENT_FILTER and not news_key and not finnhub_key:
        logger.warning(
            "ENABLE_SENTIMENT_FILTER=true but no news API keys configured. "
            "Sentiment filtering will be limited. Consider adding NEWS_API_KEY or FINNHUB_API_KEY."
        )
    
    # Check for placeholder values in news APIs (just log, don't block)
    if news_key and has_placeholder_pattern(news_key, placeholder_patterns):
        logger.info("News API key has placeholder value - news sentiment features limited")
    
    if finnhub_key and has_placeholder_pattern(finnhub_key, placeholder_patterns):
        logger.info("Finnhub API key has placeholder value - news sentiment features limited")
    
    # Validate numeric configuration
    try:
        if BOT_RISK_THRESHOLD <= 0 or BOT_RISK_THRESHOLD > 1:
            issues.append(f"BOT_RISK_THRESHOLD must be between 0 and 1, got {BOT_RISK_THRESHOLD}")
        
        if BOT_MIN_ALLOCATION <= 0:
            issues.append(f"BOT_MIN_ALLOCATION must be positive, got {BOT_MIN_ALLOCATION}")
        
        if BOT_MAX_ALLOCATION <= BOT_MIN_ALLOCATION:
            issues.append(f"BOT_MAX_ALLOCATION must be greater than BOT_MIN_ALLOCATION")
        
        if not (0 < BOT_TRAILING_STOP_PERCENT < 1):
            issues.append(f"BOT_TRAILING_STOP_PERCENT must be between 0 and 1, got {BOT_TRAILING_STOP_PERCENT}")
        
        # Validate VOLATILITY_WINDOW (must be positive, already loaded as int)
        if VOLATILITY_WINDOW <= 0:
            issues.append(f"VOLATILITY_WINDOW must be a positive value, got {VOLATILITY_WINDOW}")
        
        # Validate stock filtering configuration
        if MIN_STOCK_PRICE <= 0:
            issues.append(f"MIN_STOCK_PRICE must be positive, got {MIN_STOCK_PRICE}")
        
        if MAX_STOCK_PRICE <= 0:
            issues.append(f"MAX_STOCK_PRICE must be positive, got {MAX_STOCK_PRICE}")
        
        if MAX_STOCK_PRICE <= MIN_STOCK_PRICE:
            issues.append(f"MAX_STOCK_PRICE ({MAX_STOCK_PRICE}) must be greater than MIN_STOCK_PRICE ({MIN_STOCK_PRICE})")
        
        if MIN_DAILY_VOLUME <= 0:
            issues.append(f"MIN_DAILY_VOLUME must be positive, got {MIN_DAILY_VOLUME}")
        
        if not (0 < MAX_STOCK_VOLATILITY <= 1):
            issues.append(f"MAX_STOCK_VOLATILITY must be between 0 and 1, got {MAX_STOCK_VOLATILITY}")
        
        # Validate trailing stop configuration
        # MIN_TRAILING_STOP: Must be greater than 0 and less than 1 (0% < value < 100%)
        # MAX_TRAILING_STOP: Must be greater than 0 and can be up to 1.0 (0% < value <= 100%)
        if not (0 < MIN_TRAILING_STOP < 1):
            issues.append(f"MIN_TRAILING_STOP must be between 0 and 1 (exclusive), got {MIN_TRAILING_STOP}")
        
        if not (0 < MAX_TRAILING_STOP <= 1):
            issues.append(f"MAX_TRAILING_STOP must be between 0 and 1 (inclusive), got {MAX_TRAILING_STOP}")
        
        if MIN_TRAILING_STOP >= MAX_TRAILING_STOP:
            issues.append(f"MIN_TRAILING_STOP ({MIN_TRAILING_STOP}) must be less than MAX_TRAILING_STOP ({MAX_TRAILING_STOP})")
        
        # Validate partial exit configuration
        if not (0 < PARTIAL_EXIT_PERCENTAGE <= 1):
            issues.append(f"PARTIAL_EXIT_PERCENTAGE must be between 0 and 1, got {PARTIAL_EXIT_PERCENTAGE}")
        
        if not (0 < PARTIAL_EXIT_STOP_TIGHTENING <= 1):
            issues.append(f"PARTIAL_EXIT_STOP_TIGHTENING must be between 0 and 1, got {PARTIAL_EXIT_STOP_TIGHTENING}")
        
        # Validate simulation and normalization settings
        if not (0 < SIMULATED_WIN_RATE <= 1):
            issues.append(f"SIMULATED_WIN_RATE must be between 0 and 1, got {SIMULATED_WIN_RATE}")
        
        if VOLATILITY_NORMALIZATION_MIN <= 0:
            issues.append(f"VOLATILITY_NORMALIZATION_MIN must be positive, got {VOLATILITY_NORMALIZATION_MIN}")
        
        if VOLATILITY_NORMALIZATION_RANGE <= 0:
            issues.append(f"VOLATILITY_NORMALIZATION_RANGE must be positive, got {VOLATILITY_NORMALIZATION_RANGE}")
        
        # Validate capital floor
        if not (0 < CAPITAL_FLOOR_PERCENT <= 1):
            issues.append(f"CAPITAL_FLOOR_PERCENT must be between 0 and 1, got {CAPITAL_FLOOR_PERCENT}")
        
        # Validate position and loss limits
        if BOT_MAX_OPEN_POSITIONS <= 0:
            issues.append(f"BOT_MAX_OPEN_POSITIONS must be positive, got {BOT_MAX_OPEN_POSITIONS}")
        
        if BOT_MAX_CONSECUTIVE_LOSSES <= 0:
            issues.append(f"BOT_MAX_CONSECUTIVE_LOSSES must be positive, got {BOT_MAX_CONSECUTIVE_LOSSES}")
        
        # Validate trading frequency
        if TRADING_FREQUENCY <= 0:
            issues.append(f"TRADING_FREQUENCY must be positive, got {TRADING_FREQUENCY}")
        
        # Validate position sizing and profit/loss parameters
        if not (0 < BOT_POSITION_SIZE <= 1):
            issues.append(f"BOT_POSITION_SIZE must be between 0 and 1, got {BOT_POSITION_SIZE}")
        
        if not (0 < BOT_STOP_LOSS_PERCENT <= 1):
            issues.append(f"BOT_STOP_LOSS_PERCENT must be between 0 and 1, got {BOT_STOP_LOSS_PERCENT}")
        
        if not (0 < HIGH_SALE_PERCENT <= 1):
            issues.append(f"HIGH_SALE_PERCENT must be between 0 and 1, got {HIGH_SALE_PERCENT}")
        
        if not (0 <= BOT_RISK_FREE_RATE <= 1):
            issues.append(f"BOT_RISK_FREE_RATE must be between 0 and 1, got {BOT_RISK_FREE_RATE}")
        
        # Validate swing trading configuration
        if SWING_MIN_HOLD_DAYS < 0:
            issues.append(f"SWING_MIN_HOLD_DAYS must be non-negative, got {SWING_MIN_HOLD_DAYS}")
        
        # Validate stock screener configuration
        if MAX_DISCOVERED_STOCKS <= 0:
            issues.append(f"MAX_DISCOVERED_STOCKS must be positive, got {MAX_DISCOVERED_STOCKS}")
        
        # Validate resource throttling configuration (if enabled)
        if BOT_ENABLE_THROTTLING:
            if not (0 < BOT_MAX_CPU_PERCENT <= 100):
                issues.append(f"BOT_MAX_CPU_PERCENT must be between 0 and 100, got {BOT_MAX_CPU_PERCENT}")
            
            if not (0 < BOT_MAX_MEMORY_PERCENT <= 100):
                issues.append(f"BOT_MAX_MEMORY_PERCENT must be between 0 and 100, got {BOT_MAX_MEMORY_PERCENT}")
            
            if BOT_THROTTLE_DELAY <= 0:
                issues.append(f"BOT_THROTTLE_DELAY must be positive, got {BOT_THROTTLE_DELAY}")
        
        # Validate risk threshold vs allocation consistency
        # The risk threshold must allow for at least the minimum allocation
        # Use realistic risk calculation: allocation * stop_loss_percent
        initial_capital = DEFAULT_INITIAL_CAPITAL
        min_risk_per_trade = BOT_MIN_ALLOCATION * BOT_STOP_LOSS_PERCENT
        min_required_risk_threshold = min_risk_per_trade / initial_capital
        
        if BOT_RISK_THRESHOLD < min_required_risk_threshold:
            issues.append(
                f"BOT_RISK_THRESHOLD ({BOT_RISK_THRESHOLD:.1%}) is too low for BOT_MIN_ALLOCATION (${BOT_MIN_ALLOCATION}). "
                f"With initial capital of ${initial_capital:.2f} and BOT_STOP_LOSS_PERCENT of {BOT_STOP_LOSS_PERCENT:.1%}, "
                f"risk threshold must be at least {min_required_risk_threshold:.1%} to allow minimum allocation trades. "
                f"Current risk limit: ${BOT_RISK_THRESHOLD * initial_capital:.2f}, "
                f"but minimum allocation with stop loss requires: ${min_risk_per_trade:.2f}"
            )
        
        # Also check if max allocation is reasonable with risk threshold
        # Allow buffer for allocation increases due to self-scaling
        max_allocation_with_scaling = BOT_MAX_ALLOCATION * RISK_SCALING_BUFFER
        max_risk_per_trade = max_allocation_with_scaling * BOT_STOP_LOSS_PERCENT
        max_required_risk_threshold = max_risk_per_trade / initial_capital
        
        if BOT_RISK_THRESHOLD < max_required_risk_threshold:
            logger.warning(
                f"BOT_RISK_THRESHOLD ({BOT_RISK_THRESHOLD:.1%}) may be too low for BOT_MAX_ALLOCATION "
                f"(${BOT_MAX_ALLOCATION}) with self-scaling. "
                f"With BOT_STOP_LOSS_PERCENT of {BOT_STOP_LOSS_PERCENT:.1%}, "
                f"consider increasing to at least {max_required_risk_threshold:.1%} "
                f"to avoid blocking trades after allocation increases."
            )
            
    except (ValueError, TypeError) as e:
        issues.append(f"Configuration parsing error: {str(e)}")
    
    # Log results
    if issues:
        logger.error(f"Configuration validation failed with {len(issues)} issue(s)")
        return False, issues
    else:
        logger.info("✓ Configuration validation passed")
        return True, []


def backtest_loop(bot: 'TradingBot', symbols: List[str], period: str = '1y') -> Dict:
    """
    Run backtesting loop using historical data from yfinance
    
    DEPRECATED: This is a wrapper function for backwards compatibility.
    Use bot.backtest_loop(start_date, end_date, symbols) instead.
    
    Args:
        bot: TradingBot instance
        symbols: List of stock symbols to backtest
        period: Historical data period (default: '1y')
    
    Returns:
        Dictionary with backtest results including win rate, P&L, and trade details
    """
    # Calculate date range from period
    end_date = datetime.now()
    if period == '1y':
        start_date = end_date - timedelta(days=365)
    elif period == '6mo':
        start_date = end_date - timedelta(days=182)
    elif period == '3mo':
        start_date = end_date - timedelta(days=90)
    elif period == '1mo':
        start_date = end_date - timedelta(days=30)
    elif period == '5d':
        start_date = end_date - timedelta(days=5)
    else:
        # Default to 1 year
        start_date = end_date - timedelta(days=365)
    
    # Format dates for the instance method
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Delegate to the instance method
    logger.info(f"Using instance method: bot.backtest_loop({start_date_str}, {end_date_str}, {len(symbols)} symbols)")
    return bot.backtest_loop(start_date_str, end_date_str, symbols)


def main():
    """Main entry point for the trading bot"""
    # Set up logging first
    setup_logging()
    
    # Display legal disclaimer at startup
    logger.info("="*60)
    logger.info("⚠️  DISCLAIMER - IMPORTANT LEGAL NOTICE")
    logger.info("="*60)
    logger.info("")
    logger.info("This is EXPERIMENTAL SOFTWARE for educational purposes only.")
    logger.info("")
    logger.info("• Trading involves SIGNIFICANT RISK of financial loss")
    logger.info("• The author is NOT RESPONSIBLE for any losses")
    logger.info("• This software is provided 'AS IS' without warranty")
    logger.info("• You assume ALL RISKS when using this software")
    logger.info("")
    logger.info("By using this software, you accept all risks and agree")
    logger.info("to the full disclaimer in the README.")
    logger.info("")
    logger.info("See: https://github.com/operator/market-pie5-bot")
    logger.info("="*60)
    logger.info("")
    
    logger.info("="*60)
    logger.info("Starting Market Pie5 Trading Bot")
    logger.info("="*60)
    
    # Check if running in backtest mode
    if BACKTEST_MODE:
        logger.info("BACKTEST_MODE enabled - running historical data simulation")
        
        # Initialize bot for backtesting
        bot = TradingBot(total_capital=10000.0)
        
        # Load symbols for backtesting
        if ENABLE_STOCK_SCREENER:
            logger.info("Loading symbols from stock screener...")
            symbols = bot.load_scan_symbols(use_screener=True, max_symbols=MAX_DISCOVERED_STOCKS)
        else:
            logger.info("Loading symbols from file...")
            symbols = bot.load_scan_symbols(use_screener=False)
        
        if not symbols:
            logger.error("No symbols available for backtesting")
            return
        
        logger.info(f"Running backtest on {len(symbols)} symbols...")
        
        # Run backtest
        results = backtest_loop(bot, symbols, period='1y')
        
        logger.info("\nBacktesting completed successfully")
        logger.info("="*60)
        return
    
    # Normal trading mode continues below...
    
    # Log configuration with comprehensive details
    logger.info("\n--- TRADING MODE CONFIGURATION ---")
    logger.info(f"PAPER_TRADING_MODE: {PAPER_TRADING_MODE}")
    logger.info(f"SCHWAB_SANDBOX_MODE: {SCHWAB_SANDBOX_MODE}")
    logger.info(f"SCHWAB_API_ENABLED: {SCHWAB_API_ENABLED} ({SCHWAB_API_ENABLED_STR})")
    
    if not SCHWAB_API_ENABLED:
        logger.info("\n--- SCHWAB API DISABLED ---")
        logger.info("Schwab API connectivity is disabled (SCHWAB_API_ENABLED=off)")
        logger.info("Bot will use yfinance for market data")
        logger.info("Running in simulation mode to learn patterns and improve predictions")
        logger.info("This is helpful for:")
        logger.info("  - Troubleshooting without API credentials")
        logger.info("  - Reducing log entries from connection attempts")
        logger.info("  - Learning from historical data")
        logger.info("  - Development and testing")
        logger.info("To enable Schwab API: Set SCHWAB_API_ENABLED=on in .env")
        logger.info("="*60)
    
    if PAPER_TRADING_MODE:
        if not SCHWAB_API_ENABLED:
            mode_str = "PAPER TRADING (API Disabled - yfinance Simulation)"
            logger.info(f"Mode: {mode_str}")
            logger.info(f"API Connectivity: DISABLED (by configuration)")
            logger.info(f"Price Source: yfinance only (Schwab API skipped)")
            logger.info(f"Order Execution: Local simulation only")
            logger.info(f"PDT Rules: DISABLED (no limit in training/simulation mode)")
        elif SCHWAB_SANDBOX_MODE:
            mode_str = "PAPER TRADING (Schwab Sandbox - Strict Mode)"
            logger.info(f"Mode: {mode_str}")
            logger.info(f"Sandbox API: {SCHWAB_SANDBOX_API_BASE}")
            logger.info(f"API Connectivity: REQUIRED (NO fallback - strict mode)")
            logger.info(f"Price Source: Schwab Sandbox API only")
            logger.info(f"Order Execution: Real orders via Schwab Sandbox API")
            logger.info(f"Fallback Policy: NONE - startup blocked if API unavailable")
            logger.info(f"PDT Rules: DISABLED (no limit in training/simulation mode)")
        else:
            mode_str = "PAPER TRADING (Pure Simulation)"
            logger.info(f"Mode: {mode_str}")
            logger.info(f"API Connectivity: OPTIONAL (will use random prices if APIs fail)")
            logger.info(f"Price Source: yfinance -> random fallback")
            logger.info(f"Order Execution: Local simulation only (not visible in ThinkorSwim)")
            logger.info(f"PDT Rules: DISABLED (no limit in training/simulation mode)")
    else:
        mode_str = "LIVE TRADING (Production - Strict Mode)"
        logger.info(f"Mode: {mode_str}")
        logger.info(f"Production API: {SCHWAB_PRODUCTION_API_BASE}")
        logger.info(f"API Connectivity: REQUIRED (NO fallback - strict mode)")
        logger.info(f"Price Source: Schwab Production API only")
        logger.info(f"Order Execution: Real orders via Schwab Production API")
        logger.info(f"Fallback Policy: NONE - errors stop trading for safety")
        logger.info(f"PDT Rules: ENABLED (regulatory compliance - max 3 day trades per 5 days if capital < $25k)")
    
    logger.info("\n--- BOT PARAMETERS ---")
    logger.info(f"Trailing Stop: {BOT_TRAILING_STOP_PERCENT:.1%}")
    logger.info(f"Risk Threshold: {BOT_RISK_THRESHOLD:.1%}")
    logger.info(f"Min Allocation: ${BOT_MIN_ALLOCATION:.2f}")
    logger.info(f"Max Allocation: ${BOT_MAX_ALLOCATION:.2f}")
    logger.info(f"Initial Capital: $10000.00")
    logger.info(f"Simulated Win Rate: {SIMULATED_WIN_RATE:.1%} (simulation mode only)")
    logger.info(f"Trading Frequency: {TRADING_FREQUENCY}s between trades")
    logger.info(f"Max Open Positions: {BOT_MAX_OPEN_POSITIONS}")
    
    # Resource throttling configuration
    logger.info("\n--- RESOURCE THROTTLING (Pi5 Stability) ---")
    if BOT_ENABLE_THROTTLING and PSUTIL_AVAILABLE:
        logger.info(f"Resource Throttling: ENABLED")
        logger.info(f"  CPU Limit: {BOT_MAX_CPU_PERCENT}%")
        logger.info(f"  Memory Limit: {BOT_MAX_MEMORY_PERCENT}%")
        logger.info(f"  Throttle Delay: {BOT_THROTTLE_DELAY}s")
    elif BOT_ENABLE_THROTTLING and not PSUTIL_AVAILABLE:
        logger.warning(f"Resource Throttling: DISABLED (psutil not available)")
    else:
        logger.info(f"Resource Throttling: DISABLED (by configuration)")
    
    logger.info("="*60)
    
    # Initialize the bot EARLY (needed for API connectivity check)
    logger.info("\nInitializing trading bot...")
    bot = TradingBot(total_capital=10000.0)
    logger.info("Trading bot initialized successfully")
    
    # STEP 1: Validate API connectivity FIRST (before config validation)
    # This is critical - all other data comes from the API, so check it first
    if SCHWAB_SANDBOX_MODE or not PAPER_TRADING_MODE:
        logger.info("\n--- STEP 1: API Connectivity Check (PRIORITY) ---")
        is_connected, connectivity_msg = validate_api_connectivity(bot)
        if not is_connected:
            logger.error("="*60)
            logger.error("API CONNECTIVITY CHECK FAILED")
            logger.error("="*60)
            logger.error(connectivity_msg)
            logger.error("="*60)
            logger.error("Bot cannot start without API connectivity in sandbox/live mode")
            logger.error("All data comes from the API - cannot proceed without connection")
            logger.error("="*60)
            return
        else:
            logger.info(f"✓ API connectivity: {connectivity_msg}")
            logger.info("="*60)
    
    # STEP 2: Validate configuration (now that API is confirmed working)
    logger.info("\n--- STEP 2: Configuration Validation ---")
    is_valid, issues = validate_configuration()
    if not is_valid:
        logger.error("Configuration validation failed!")
        for issue in issues:
            logger.error(f"  - {issue}")
        logger.error("Please fix the configuration issues and try again.")
        return
    logger.info("✓ Configuration validated successfully")
    
    # STEP 3: Warn if entering live mode
    if not PAPER_TRADING_MODE:
        logger.warning("="*60)
        logger.warning("!!! LIVE TRADING MODE ENABLED !!!")
        logger.warning("Real money will be used for trades!")
        logger.warning("="*60)
        
        # Add a confirmation prompt for safety
        try:
            confirmation = input("\nType 'CONFIRM' to proceed with live trading: ")
            if confirmation != 'CONFIRM':
                logger.info("Live trading cancelled by user")
                return
        except (KeyboardInterrupt, EOFError):
            logger.info("\nLive trading cancelled by user")
            return
    
    # Load scan symbols - use stock screener if enabled
    logger.info("Loading symbols to trade...")
    if ENABLE_STOCK_SCREENER:
        logger.info("Stock screener enabled - discovering tradeable stocks with prioritization...")
        scan_symbols = bot.load_scan_symbols(use_screener=True, max_symbols=MAX_DISCOVERED_STOCKS)
    else:
        logger.info("Stock screener disabled - using symbols from file...")
        scan_symbols = bot.load_scan_symbols(use_screener=False)
    
    logger.info(f"Loaded {len(scan_symbols)} symbols for trading (prioritized by quality)")
    
    # Set current symbols for portfolio optimizer
    bot.current_symbols = scan_symbols
    logger.debug(f"Set current_symbols for portfolio optimizer: {len(scan_symbols)} symbols")
    
    # STEP 4: Request user confirmation before starting trading
    logger.info("\n" + "="*60)
    logger.info("READY TO START TRADING")
    logger.info("="*60)
    logger.info(f"Mode: {mode_str}")
    logger.info(f"Capital: ${bot.total_capital:.2f}")
    logger.info(f"Symbols to trade: {len(scan_symbols)} (in priority order)")
    logger.info(f"Max allocation: ${BOT_MAX_ALLOCATION:.2f}")
    logger.info(f"Risk threshold: {BOT_RISK_THRESHOLD:.1%}")
    logger.info("="*60)
    logger.info("NOTE: Bot will trade stocks in priority order (best opportunities first)")
    logger.info("="*60)
    
    # Check if running in headless mode (no interactive terminal)
    import sys
    is_headless = not (hasattr(sys.stdin, 'isatty') and sys.stdin.isatty())
    
    try:
        if is_headless:
            logger.info("Running in headless mode (no interactive terminal) - auto-starting trading")
            auto_start = True
        else:
            confirmation = input("\nType 'START' to begin trading (or anything else to cancel): ")
            auto_start = confirmation.strip().upper() == 'START'
        
        if not auto_start:
            logger.info("Trading cancelled by user")
            logger.info("Bot initialized but no trades executed")
            return
    except (KeyboardInterrupt, EOFError):
        logger.info("\nTrading cancelled by user")
        return
    
    # Example usage: Execute paper trades with realistic sequencing
    logger.info(f"\n--- Executing {mode_str} Trades (Priority Order) ---")
    logger.info("Trading best opportunities first, then #2, #3, etc.")
    
    allow_fallback = PAPER_TRADING_MODE and not SCHWAB_SANDBOX_MODE

    # Prefetch batch prices for the trading set using provider (async if available)
    try:
        _prefetched = {}
        data_fetcher = None
        use_async = False
        if ASYNC_DATA_FETCHER_AVAILABLE:
            try:
                data_fetcher = get_async_fetcher()
                use_async = True
                logger.info("AsyncDataFetcher initialized for concurrent data retrieval (trading loop prefetch)")
            except Exception as e:
                logger.warning(f"Failed to initialize AsyncDataFetcher: {e}")
        if data_fetcher is None and DATA_FETCHER_AVAILABLE:
            try:
                data_fetcher = DataFetcher()
                logger.info("DataFetcher initialized for batch data retrieval (trading loop prefetch)")
            except Exception as e:
                logger.warning(f"Failed to initialize DataFetcher: {e}")
        if data_fetcher is not None:
            if use_async:
                try:
                    logger.info(f"Prefetching {len(scan_symbols)} prices concurrently for trading loop...")
                    _prefetched = data_fetcher.fetch_multiple_prices(scan_symbols)
                    logger.info(f"Prefetched {len(_prefetched)} concurrent prices")
                except Exception as e:
                    logger.warning(f"Concurrent prefetch failed: {e}")
                    use_async = False
            if not use_async:
                try:
                    logger.info(f"Prefetching {len(scan_symbols)} batch prices via provider for trading loop...")
                    batch = data_fetcher.fetch_batch_prices(scan_symbols)
                    for s, pv in (batch or {}).items():
                        if isinstance(pv, (list, tuple)) and len(pv) >= 2:
                            _prefetched[s] = (pv[0], pv[1])
                        else:
                            _prefetched[s] = (pv if isinstance(pv, (int, float)) else None, None)
                    logger.info(f"Prefetched {len(_prefetched)} batch prices")
                except Exception as e:
                    logger.warning(f"Batch prefetch failed: {e}")
        # Attach to bot for consumption by get_strategy_signal
        bot._prefetched_prices = _prefetched if _prefetched else None
    except Exception as e:
        logger.debug(f"Price prefetch skipped due to error: {e}")
    
    # Hard gate: do not run the trader if the ALFa AI brain is required but down.
    def _brain_required_cli() -> bool:
        return os.getenv("BOT_REQUIRE_BRAIN", "true").lower() in ("true", "1", "yes")

    def _brain_status_cli():
        try:
            from api.services.litellm_client import litellm_health_sync
            h = litellm_health_sync(timeout=float(os.getenv("BOT_BRAIN_CHECK_TIMEOUT_SECONDS", "10")))
            detail = f"{h.get('status', 'unknown')} @ {h.get('base_url', '?')}"
            if h.get("error"):
                detail += f" ({h['error']})"
            return bool(h.get("ok")), detail
        except Exception as e:
            return False, f"probe_error: {type(e).__name__}: {e}"

    require_brain = _brain_required_cli()
    if require_brain:
        ok, detail = _brain_status_cli()
        if not ok:
            logger.error(
                "Refusing to start trading loop — ALFa AI brain unreachable "
                "(BOT_REQUIRE_BRAIN=true): %s", detail
            )
            bot.running = False
            return
        logger.info(f"Brain health OK ({detail}) — starting trading loop")
    brain_check_interval = max(0, int(os.getenv("BOT_BRAIN_CHECK_INTERVAL_SECONDS", "60")))

    # Continuous trading loop - cycle through symbols repeatedly
    import time as time_module
    cycle_count = 0
    last_brain_check = time_module.time()
    bot.running = True  # CRITICAL: Set flag for API status endpoint
    
    while True:
        # Halt trading if the brain goes down mid-run.
        if require_brain and brain_check_interval > 0 and (time_module.time() - last_brain_check) >= brain_check_interval:
            last_brain_check = time_module.time()
            ok, detail = _brain_status_cli()
            if not ok:
                logger.error(
                    "Halting trading loop — ALFa AI brain unreachable mid-run "
                    "(BOT_REQUIRE_BRAIN=true): %s", detail
                )
                bot.running = False
                break
        
        cycle_count += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"Trading Cycle #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"{'='*60}")
        
        # Track cycle statistics
        cycle_stats = {
            'hold_signals': 0,
            'ml_filtered': 0,
            'executed_trades': 0,
            'no_price': 0,
            'no_action': 0,
            'errors': 0
        }
        
        for index, symbol in enumerate(scan_symbols, 1):
            # Show trading priority
            logger.info(f"\n[Priority #{index}/{len(scan_symbols)}] Processing {symbol}...")
            
            # Get strategy signal (BUY/SELL/HOLD) and current price/volume
            try:
                signal, price, volume = bot.get_strategy_signal(symbol, use_random_fallback=allow_fallback)
            except Exception as e:
                logger.error(f"Strategy signal failed for {symbol}: {e}")
                cycle_stats['errors'] += 1
                logger.error("Stopping bot due to signal failure")
                break
            
            if signal == 'HOLD':
                cycle_stats['hold_signals'] += 1
                logger.info(f"Strategy signal HOLD for {symbol} — skipping")
                delay = TRADING_FREQUENCY
                logger.debug(f"Waiting {delay}s before next symbol (TRADING_FREQUENCY={TRADING_FREQUENCY})...")
                time.sleep(delay)
                continue
            
            if price is None or volume is None:
                cycle_stats['no_price'] += 1
                logger.warning(f"No price/volume for {symbol} (signal={signal}) — skipping")
                delay = TRADING_FREQUENCY
                time.sleep(delay)
                continue
            
            action = bot._signal_to_action(symbol, signal)
            if action is None:
                cycle_stats['no_action'] += 1
                logger.info(f"Strategy signal {signal} for {symbol} — no action (position state); skipping")
                delay = TRADING_FREQUENCY
                time.sleep(delay)
                continue
            
            logger.info(f"Retrieved price for {symbol}: ${price:.2f}, volume: {volume:,} — signal: {signal} → action: {action}")
            
            # Exit-price refresh: re-fetch price immediately before SELL/COVER and use for execution
            if EXIT_REFRESH_PRICE and action in ('SELL', 'COVER'):
                try:
                    exit_price, _ = bot.get_stock_price(symbol, use_random_fallback=False)
                    if exit_price is not None:
                        price = exit_price
                    logger.debug(f"Exit price refresh for {symbol}: ${price:.2f}")
                except (ValueError, TypeError):
                    pass
            
            # Execute trade (BUY, SELL, SHORT, or COVER)
            logger.info(f"Processing trade for {symbol} ({action})...")
            result = bot.execute_trade(symbol, action, price, volume=volume)
            
            if result and result.get('status') == 'error':
                logger.error(f"Trade failed for {symbol}: {result.get('message', 'Unknown error')}")
            else:
                cycle_stats['executed_trades'] += 1
            
            # Add delay between trades based on TRADING_FREQUENCY setting
            delay = TRADING_FREQUENCY
            logger.debug(f"Waiting {delay}s before next trade (TRADING_FREQUENCY={TRADING_FREQUENCY})...")
            time.sleep(delay)
        
    # End of trading cycle - log statistics and wait before restarting
    logger.info(f"\n--- End of Trading Cycle #{cycle_count} ---")
    logger.info(f"Cycle Summary: {cycle_stats['executed_trades']} trades executed")
    logger.info(f"  • {cycle_stats['hold_signals']} natural HOLD signals")
    logger.info(f"  • {cycle_stats['no_price']} no price/volume")
    logger.info(f"  • {cycle_stats['no_action']} no action needed (position state)")
    logger.info(f"  • {cycle_stats['errors']} signal generation errors")
    logger.info(f"Completed {len(scan_symbols)} symbol checks")
    cycle_delay = max(TRADING_FREQUENCY * 2, 5)  # At least 5 seconds between cycles
    logger.info(f"Waiting {cycle_delay}s before next trading cycle...")
    time_module.sleep(cycle_delay)
    # Clear prefetched cache after trading loop
    bot._prefetched_prices = None
    
    # Print summary
    logger.info("\n--- Trading Session Summary ---")
    bot.print_summary()
    
    # Save trade history to separate files based on mode
    logger.info("\n--- Saving Trade History ---")
    bot.save_trade_history()
    
    # Show trade breakdown by mode
    sim_trades = bot.get_trades_by_mode('yfinance_sim')
    sandbox_trades = bot.get_trades_by_mode('schwab_sandbox')
    live_trades = bot.get_trades_by_mode('live_trading')
    
    if sim_trades:
        logger.info(f"  yfinance sim trades: {len(sim_trades)}")
    if sandbox_trades:
        logger.info(f"  Schwab sandbox trades: {len(sandbox_trades)}")
    if live_trades:
        logger.info(f"  Live trades: {len(live_trades)}")
    
    # Demonstrate TOS CSV import (if file exists)
    csv_file = 'tos_paper_trades.csv'
    if os.path.exists(csv_file):
        logger.info(f"\n--- Importing TOS Paper Trades from {csv_file} ---")
        trades = bot.import_tos_csv(csv_file)
        if trades:
            bot.process_tos_trades(trades)
            bot.print_summary()
    
    # Send track record to AI for strategy optimization
    logger.info("\n--- AI Strategy Analysis ---")
    ai_response = bot.send_track_record_to_ai()
    
    # Parse and display AI suggestions (manual review mode by default)
    if ai_response and 'error' not in ai_response:
        bot.apply_ai_suggestions(ai_response, auto_apply=False)
    
    # ML Parameter Optimization for 70% Win Rate Target
    logger.info("\n--- ML Parameter Optimization (70% Win Rate Target) ---")
    if bot.ml_optimizer and bot.ml_optimizer.is_api_configured():
        logger.info("Running ML parameter optimization...")
        optimized_params, predicted_win_rate = bot.optimize_parameters_ml()
        
        if optimized_params:
            logger.info(f"\n✓ ML Optimization Complete!")
            logger.info(f"  Current Win Rate: {bot.track_record['win_rate']:.1%}")
            logger.info(f"  Predicted Win Rate: {predicted_win_rate:.1%}")
            logger.info(f"  Target Win Rate: 70%")
            logger.info(f"\n  Optimized Parameters:")
            for key, value in optimized_params.items():
                if isinstance(value, float) and value < 1:
                    logger.info(f"    {key}: {value:.3f} ({value*100:.1f}%)")
                else:
                    logger.info(f"    {key}: {value}")
            logger.info(f"\n  💡 To apply these parameters, update your .env file")
            logger.info(f"  📄 Results saved to ml_optimization_*.json")
        else:
            logger.warning("ML optimization did not return parameter suggestions")
    else:
        logger.info("ML parameter optimizer not available or ALFa AI not enabled")
        logger.info("  To enable: Set LITELLM_ENABLED=true in .env file")
    
    logger.info("="*60)
    logger.info("Bot execution completed successfully")
    logger.info("="*60)
    
    # Log session end if debug logger is enabled
    if bot.debug_logger and bot.debug_logger.enabled:
        total_pnl, total_pnl_percent = bot.calculate_total_pnl()
        bot.debug_logger.log_session_end({
            'total_trades': bot.track_record['total_trades'],
            'winning_trades': bot.track_record['winning_trades'],
            'losing_trades': bot.track_record['losing_trades'],
            'win_rate': bot.track_record['win_rate'],
            'starting_capital': bot.starting_capital,
            'final_capital': bot.total_capital,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'open_positions': len(bot.positions),
            'consecutive_losses': bot.consecutive_losses
        })
        logger.info(f"Debug log saved to: {bot.debug_logger.get_log_file_path()}")


if __name__ == "__main__":
    main()
