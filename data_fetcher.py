#!/usr/bin/env python3
"""
Data fetching module for market-pie5-bot
Handles fetching stock data from multiple sources:
- yfinance (real-time prices and historical data)
- Alpha Vantage (fundamentals: P/E ratio, earnings, etc.)
"""

import warnings
# Suppress pandas/yfinance Timestamp.utcnow deprecation (Pandas4Warning); apply before yfinance use
warnings.filterwarnings('ignore', message=r'.*Timestamp\.utcnow.*')

import os
import requests
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import logging
import time
import stat

logger = logging.getLogger(__name__)

# Import rate limiter from shared module
try:
    from rate_limiter import RateLimiter
except ImportError:
    logger.warning("rate_limiter module not available - rate limiting disabled")
    # Fallback: create a dummy RateLimiter that allows all calls
    class RateLimiter:
        def __init__(self, *args, **kwargs):
            pass
        def can_make_call(self):
            return True
        def record_call(self):
            pass
        def get_wait_time(self):
            return 0.0
        def get_remaining_calls(self):
            return 999

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import encryption library for decrypting sensitive environment variables
try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False

# Sensitive environment variable keys that may be encrypted
SENSITIVE_ENV_KEYS = {
    "ALPHA_VANTAGE_API_KEY",
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
        logger.error(f"Failed to check permissions for {file_path}: {e}")
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
        logger.info(f"Fixed permissions for {file_path} to 0o600")
        return True
    except OSError as e:
        logger.error(f"Failed to fix permissions for {file_path}: {e}")
        return False

def _get_encryption_key():
    """Return a Fernet key for encrypting/decrypting sensitive configuration values."""
    if not FERNET_AVAILABLE:
        return None
    
    # Check for key rotation flag
    if os.environ.get("MP5_ROTATE_ENCRYPTION_KEY", "").lower() == "true":
        logger.warning("Key rotation requested via MP5_ROTATE_ENCRYPTION_KEY - generating new key")
        key = Fernet.generate_key()
        key_path = ".env.key"
        try:
            with open(key_path, "wb") as f:
                f.write(key)
            os.chmod(key_path, 0o600)
            logger.warning("Generated new encryption key at %s - store securely!", key_path)
            # Clear the rotation flag to avoid repeated rotation (safe deletion)
            os.environ.pop("MP5_ROTATE_ENCRYPTION_KEY", None)
        except (OSError, IOError, PermissionError) as e:
            logger.error("Failed to persist encryption key during rotation: %s", e)
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
            logger.warning(
                "Insecure permissions detected on %s - should be 0o600. Attempting to fix...",
                key_path
            )
            if not _fix_file_permissions(key_path):
                logger.error(
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
        logger.warning("Generated new encryption key at %s - store securely!", key_path)
    except (OSError, IOError, PermissionError) as e:
        logger.error("Failed to persist encryption key: %s", e)
        # Return the key anyway for this process
    return key

def _decrypt_sensitive_value(value):
    """
    Decrypt a sensitive configuration value that was encrypted.
    
    If the value starts with 'enc:', it will be decrypted.
    Otherwise, it will be returned as-is.
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
                return ""
            fernet = Fernet(key)
            encrypted_token = value[4:]  # Remove 'enc:' prefix
            decrypted_bytes = fernet.decrypt(encrypted_token.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            # Log decryption failure for debugging
            logger.debug(f"Failed to decrypt environment variable: {e}")
            return ""
    
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

ALPHA_VANTAGE_API_KEY = get_decrypted_env('ALPHA_VANTAGE_API_KEY', '')

# Rate limiting configuration
ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE = int(os.getenv('ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE', '5'))
ALPHA_VANTAGE_TIME_WINDOW_SECONDS = int(os.getenv('ALPHA_VANTAGE_TIME_WINDOW_SECONDS', '60'))
YFINANCE_MAX_CALLS_PER_MINUTE = int(os.getenv('YFINANCE_MAX_CALLS_PER_MINUTE', '30'))
YFINANCE_TIME_WINDOW_SECONDS = int(os.getenv('YFINANCE_TIME_WINDOW_SECONDS', '60'))

# YahooQuery rate limiting and provider selection
YAHOOQUERY_MAX_CALLS_PER_MINUTE = int(os.getenv('YAHOOQUERY_MAX_CALLS_PER_MINUTE', '120'))
YAHOOQUERY_TIME_WINDOW_SECONDS = int(os.getenv('YAHOOQUERY_TIME_WINDOW_SECONDS', '60'))
# Default to YAHOOQUERY for faster multi-ticker quotes; override via MARKET_DATA_PROVIDER env
MARKET_DATA_PROVIDER = os.getenv('MARKET_DATA_PROVIDER', 'YAHOOQUERY').upper()

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    logger.info("yfinance library loaded successfully")
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available")

# Try to import yahooquery (more efficient multi-ticker Yahoo Finance JSON client)
try:
    from yahooquery import Ticker as YQTicker
    YAHOOQUERY_AVAILABLE = True
    logger.info("yahooquery library loaded successfully")
except ImportError:
    YAHOOQUERY_AVAILABLE = False
    logger.warning("yahooquery not available")


class DataFetcher:
    """
    Unified data fetcher for stock market data from multiple sources
    """
    
    def __init__(self, alpha_vantage_key: Optional[str] = None):
        """
        Initialize data fetcher
        
        Args:
            alpha_vantage_key: Alpha Vantage API key (optional, uses env var if not provided)
        """
        self.av_api_key = alpha_vantage_key or ALPHA_VANTAGE_API_KEY
        self.cache = {}  # Cache for API responses
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
        
        # Initialize rate limiters
        self.alpha_vantage_limiter = RateLimiter(
            max_calls=ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE,
            time_window=ALPHA_VANTAGE_TIME_WINDOW_SECONDS,
            name="Alpha Vantage"
        )
        
        self.yfinance_limiter = RateLimiter(
            max_calls=YFINANCE_MAX_CALLS_PER_MINUTE,
            time_window=YFINANCE_TIME_WINDOW_SECONDS,
            name="yfinance"
        )

        self.yahooquery_limiter = RateLimiter(
            max_calls=YAHOOQUERY_MAX_CALLS_PER_MINUTE,
            time_window=YAHOOQUERY_TIME_WINDOW_SECONDS,
            name="yahooquery"
        )
        
        if self.av_api_key and self.av_api_key != '':
            logger.info("Alpha Vantage API key configured")
        else:
            logger.warning("Alpha Vantage API key not configured - fundamentals unavailable")
        
        if YFINANCE_AVAILABLE:
            logger.info("yfinance available for price data")
        else:
            logger.warning("yfinance not available - price data limited")
        if YAHOOQUERY_AVAILABLE:
            logger.info("yahooquery available for batch quotes")
        else:
            logger.warning("yahooquery not available - multi-ticker quotes may be slower")
    
    def _get_cache_key(self, symbol: str, data_type: str) -> str:
        """Generate cache key for symbol and data type"""
        return f"{symbol}_{data_type}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_data = self.cache[cache_key]
        age = (datetime.now() - cached_data['timestamp']).total_seconds()
        
        return age < self.cache_duration
    
    def _cache_data(self, cache_key: str, data: any):
        """Cache data with timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def _get_cached_data(self, cache_key: str) -> Optional[any]:
        """Retrieve cached data if valid"""
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached data for {cache_key}")
            return self.cache[cache_key]['data']
        return None
    
    def fetch_historical_data_yfinance(self, symbol: str, period: str = '1y',
                                       interval: str = '1d') -> Optional[pd.DataFrame]:
        """
        Fetch historical data using yfinance
        
        Args:
            symbol: Stock symbol
            period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        if not YFINANCE_AVAILABLE:
            logger.warning("yfinance not available")
            return None
        
    def fetch_batch_prices_yfinance(
        self,
        symbols: List[str],
        period: str = '1d',
        interval: str = '1m',
        price_field: str = 'close'
    ) -> Dict[str, Tuple[Optional[float], Optional[int]]]:
        """
        Fetch latest prices for multiple symbols in a single logical call using yfinance.

        Args:
            symbols: List of stock symbols
            period: Historical window used to infer latest price (default: '1d')
            interval: Interval for intraday data (default: '1m')
            price_field: Column name to extract ('close' or 'adj close')

        Returns:
            Mapping of symbol -> latest price (float) or None if unavailable

        Notes:
            - Uses `yf.download` with multiple tickers; result is a DataFrame that may
              have MultiIndex columns when grouping by ticker.
            - Records a single limiter call per batch to respect app-level quotas.
            - If rate limit is reached, returns a dict with None values for requested symbols.
        """
        results: Dict[str, Tuple[Optional[float], Optional[int]]] = {s: (None, None) for s in symbols}

        if not YFINANCE_AVAILABLE or not symbols:
            logger.warning("yfinance not available or empty symbols list")
            return results

        # Check rate limit before making API call
        if not self.yfinance_limiter.can_make_call():
            wait_time = self.yfinance_limiter.get_wait_time()
            remaining = self.yfinance_limiter.get_remaining_calls()
            logger.warning(
                f"yfinance rate limit reached ({remaining}/{self.yfinance_limiter.max_calls} "
                f"calls available). Next batch call in {wait_time:.1f}s. Skipping batch for {len(symbols)} symbols."
            )
            return results

        try:
            logger.info(
                f"Fetching batch prices for {len(symbols)} symbols (period={period}, interval={interval})"
            )

            # Perform a multi-ticker download. group_by='ticker' produces MultiIndex columns.
            data = yf.download(
                tickers=" ".join(symbols),
                period=period,
                interval=interval,
                group_by='ticker',
                threads=True,
                progress=False
            )

            # Record the API call immediately after request
            self.yfinance_limiter.record_call()
            remaining = self.yfinance_limiter.get_remaining_calls()
            logger.debug(
                f"yfinance batch call made. Remaining calls: {remaining}/{self.yfinance_limiter.max_calls}"
            )

            if data is None or (hasattr(data, 'empty') and data.empty):
                logger.debug("No data returned in batch download")
                return results

            # Normalize column names where applicable
            # For group_by='ticker', columns are MultiIndex: (symbol, OHLCV)
            # We'll iterate per requested symbol and try to extract the latest price.
            for symbol in symbols:
                latest_price: Optional[float] = None
                latest_volume: Optional[int] = None

                try:
                    # Case 1: MultiIndex columns grouped by ticker
                    if isinstance(data.columns, pd.MultiIndex):
                        if symbol in set([lvl[0] for lvl in data.columns]):
                            sub = data[symbol]
                            cols = [c.lower() for c in sub.columns]
                            # Map back to original column names
                            col_map = {c.lower(): c for c in sub.columns}
                            target_col = price_field if price_field in cols else ('adj close' if 'adj close' in cols else None)
                            if target_col:
                                src_col = col_map[target_col]
                                if len(sub[src_col]) > 0:
                                    latest_price = float(sub[src_col].dropna().iloc[-1])
                            # Try to extract volume
                            vol_col = None
                            for cand in ('volume', 'vol'):
                                if cand in cols:
                                    vol_col = col_map[cand]
                                    break
                            if vol_col and len(sub[vol_col]) > 0:
                                try:
                                    latest_volume = int(sub[vol_col].dropna().iloc[-1])
                                except Exception:
                                    latest_volume = None
                    else:
                        # Case 2: Single-index columns where columns include tuples flattened
                        # Try common patterns: ('Close', symbol) or symbol-specific columns
                        # Fallback: attempt last non-null Close for entire frame
                        lower_cols = [str(c).lower() for c in data.columns]
                        target_candidates = [
                            f"{symbol} {price_field}", f"{symbol} adj close", price_field, 'adj close'
                        ]
                        chosen = None
                        for cand in target_candidates:
                            if cand in lower_cols:
                                chosen = data.columns[lower_cols.index(cand)]
                                break
                        if chosen is not None:
                            series = data[chosen]
                            if len(series) > 0:
                                latest_price = float(series.dropna().iloc[-1])
                        # Try to find volume column
                        vol_candidates = [f"{symbol} volume", "volume"]
                        chosen_vol = None
                        for vc in vol_candidates:
                            if vc in lower_cols:
                                chosen_vol = data.columns[lower_cols.index(vc)]
                                break
                        if chosen_vol is not None:
                            vol_series = data[chosen_vol]
                            if len(vol_series) > 0:
                                try:
                                    latest_volume = int(vol_series.dropna().iloc[-1])
                                except Exception:
                                    latest_volume = None
                    results[symbol] = (latest_price, latest_volume)
                except Exception as e:
                    logger.debug(f"Failed to parse batch price for {symbol}: {e}")
                    results[symbol] = (None, None)

            return results

        except Exception as e:
            logger.error(f"Error fetching batch prices via yfinance: {e}")
            return results

    def fetch_batch_prices_yahooquery(
        self,
        symbols: List[str]
    ) -> Dict[str, Tuple[Optional[float], Optional[int]]]:
        """
        Fetch latest prices for multiple symbols using yahooquery in a single request.

        Args:
            symbols: List of stock symbols

        Returns:
            Mapping of symbol -> latest price (float) or None
        """
        results: Dict[str, Tuple[Optional[float], Optional[int]]] = {s: (None, None) for s in symbols}

        if not YAHOOQUERY_AVAILABLE or not symbols:
            logger.warning("yahooquery not available or empty symbols list")
            return results

        # Check rate limit
        if not self.yahooquery_limiter.can_make_call():
            wait_time = self.yahooquery_limiter.get_wait_time()
            remaining = self.yahooquery_limiter.get_remaining_calls()
            logger.warning(
                f"yahooquery rate limit reached ({remaining}/{self.yahooquery_limiter.max_calls} calls available). "
                f"Next batch call in {wait_time:.1f}s. Skipping batch for {len(symbols)} symbols."
            )
            return results

        try:
            logger.info(f"Fetching yahooquery batch prices for {len(symbols)} symbols")
            tq = YQTicker(" ".join(symbols))
            data = tq.price  # dict keyed by symbol

            # Record limiter call
            self.yahooquery_limiter.record_call()
            remaining = self.yahooquery_limiter.get_remaining_calls()
            logger.debug(
                f"yahooquery batch call made. Remaining calls: {remaining}/{self.yahooquery_limiter.max_calls}"
            )

            if not isinstance(data, dict) or not data:
                logger.debug("No price data returned from yahooquery")
                return results

            for symbol in symbols:
                info = data.get(symbol) or data.get(symbol.upper())
                price_val: Optional[float] = None
                vol_val: Optional[int] = None
                try:
                    if isinstance(info, dict):
                        # Prefer real-time price fields; fall back to cached ones
                        for key in (
                            'regularMarketPrice', 'postMarketPrice', 'preMarketPrice',
                            'price', 'bid', 'ask'
                        ):
                            val = info.get(key)
                            if val is not None:
                                price_val = float(val)
                                break
                        # Volume candidates
                        for vkey in (
                            'regularMarketVolume', 'postMarketVolume', 'preMarketVolume',
                            'volume'
                        ):
                            v = info.get(vkey)
                            if v is not None:
                                try:
                                    vol_val = int(v)
                                except Exception:
                                    vol_val = None
                                break
                    results[symbol] = (price_val, vol_val)
                except Exception as e:
                    logger.debug(f"Failed to parse yahooquery price for {symbol}: {e}")
                    results[symbol] = (None, None)

            return results
        except Exception as e:
            logger.error(f"Error fetching batch prices via yahooquery: {e}")
            return results

    def fetch_batch_prices(
        self,
        symbols: List[str],
        period: str = '1d',
        interval: str = '1m',
        price_field: str = 'close'
    ) -> Dict[str, Tuple[Optional[float], Optional[int]]]:
        """
        Provider-selecting batch fetch helper. Uses MARKET_DATA_PROVIDER env:
        - 'YAHOOQUERY': yahooquery batch quotes
        - 'YFINANCE' (default): yfinance batch via download
        """
        provider = MARKET_DATA_PROVIDER
        if provider == 'YAHOOQUERY' and YAHOOQUERY_AVAILABLE:
            return self.fetch_batch_prices_yahooquery(symbols)
        # Fallback to yfinance if yahooquery unavailable or provider set to YFINANCE
        return self.fetch_batch_prices_yfinance(symbols, period=period, interval=interval, price_field=price_field)

    def fetch_fundamentals_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """
        Fetch fundamental data using Alpha Vantage API
        
        Includes:
        - P/E Ratio
        - EPS (Earnings Per Share)
        - Market Cap
        - Dividend Yield
        - 52 Week High/Low
        - And more...
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with fundamental data or None if fetch fails
        """
        if not self.av_api_key or self.av_api_key == '':
            logger.warning("Alpha Vantage API key not configured")
            return None
        
        cache_key = self._get_cache_key(symbol, "fundamentals")
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            return cached
        
        # Check rate limit before making API call
        if not self.alpha_vantage_limiter.can_make_call():
            wait_time = self.alpha_vantage_limiter.get_wait_time()
            remaining = self.alpha_vantage_limiter.get_remaining_calls()
            logger.warning(
                f"Alpha Vantage rate limit reached ({remaining}/{self.alpha_vantage_limiter.max_calls} "
                f"calls available). Next call available in {wait_time:.1f}s. Skipping fetch for {symbol}."
            )
            return None
        
        try:
            logger.info(f"Fetching fundamentals for {symbol} from Alpha Vantage")
            
            # Alpha Vantage OVERVIEW endpoint
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.av_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            # Record the API call immediately after request, regardless of status code
            # to ensure accurate rate limiting (failed requests count against quota too)
            self.alpha_vantage_limiter.record_call()
            
            # Log remaining calls
            remaining = self.alpha_vantage_limiter.get_remaining_calls()
            logger.debug(f"Alpha Vantage call made. Remaining calls: {remaining}/{self.alpha_vantage_limiter.max_calls}")
            
            # Check status code
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                return None
            
            if not data or 'Symbol' not in data:
                logger.warning(f"No fundamental data returned for {symbol}")
                return None
            
            # Extract key fundamentals
            fundamentals = {
                'symbol': data.get('Symbol', symbol),
                'name': data.get('Name', ''),
                'exchange': data.get('Exchange', ''),
                'sector': data.get('Sector', ''),
                'industry': data.get('Industry', ''),
                'market_cap': self._parse_number(data.get('MarketCapitalization')),
                'pe_ratio': self._parse_number(data.get('PERatio')),
                'peg_ratio': self._parse_number(data.get('PEGRatio')),
                'price_to_book': self._parse_number(data.get('PriceToBookRatio')),
                'eps': self._parse_number(data.get('EPS')),
                'dividend_per_share': self._parse_number(data.get('DividendPerShare')),
                'dividend_yield': self._parse_number(data.get('DividendYield')),
                'profit_margin': self._parse_number(data.get('ProfitMargin')),
                'operating_margin': self._parse_number(data.get('OperatingMarginTTM')),
                'return_on_equity': self._parse_number(data.get('ReturnOnEquityTTM')),
                'return_on_assets': self._parse_number(data.get('ReturnOnAssetsTTM')),
                'revenue_ttm': self._parse_number(data.get('RevenueTTM')),
                'gross_profit_ttm': self._parse_number(data.get('GrossProfitTTM')),
                'analyst_target_price': self._parse_number(data.get('AnalystTargetPrice')),
                '52_week_high': self._parse_number(data.get('52WeekHigh')),
                '52_week_low': self._parse_number(data.get('52WeekLow')),
                'beta': self._parse_number(data.get('Beta')),
                'shares_outstanding': self._parse_number(data.get('SharesOutstanding')),
            }
            
            logger.info(f"Fetched fundamentals for {symbol}")
            self._cache_data(cache_key, fundamentals)
            
            return fundamentals
            
        except requests.exceptions.Timeout:
            logger.error(f"Alpha Vantage request timeout for {symbol}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpha Vantage request error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return None
    
    def _parse_number(self, value: Optional[str]) -> Optional[float]:
        """Parse numeric value from string, handle 'None' and empty strings"""
        if value is None or value == '' or value == 'None':
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def fetch_earnings_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """
        Fetch earnings data using Alpha Vantage
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with earnings data or None if fetch fails
        """
        if not self.av_api_key or self.av_api_key == '':
            logger.warning("Alpha Vantage API key not configured")
            return None
        
        cache_key = self._get_cache_key(symbol, "earnings")
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            return cached
        
        # Check rate limit before making API call
        if not self.alpha_vantage_limiter.can_make_call():
            wait_time = self.alpha_vantage_limiter.get_wait_time()
            remaining = self.alpha_vantage_limiter.get_remaining_calls()
            logger.warning(
                f"Alpha Vantage rate limit reached ({remaining}/{self.alpha_vantage_limiter.max_calls} "
                f"calls available). Next call available in {wait_time:.1f}s. Skipping fetch for {symbol}."
            )
            return None
        
        try:
            logger.info(f"Fetching earnings for {symbol} from Alpha Vantage")
            
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'EARNINGS',
                'symbol': symbol,
                'apikey': self.av_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            # Record the API call immediately after request, regardless of status code
            self.alpha_vantage_limiter.record_call()
            
            # Log remaining calls
            remaining = self.alpha_vantage_limiter.get_remaining_calls()
            logger.debug(f"Alpha Vantage call made. Remaining calls: {remaining}/{self.alpha_vantage_limiter.max_calls}")
            
            # Check status code
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                return None
            
            logger.info(f"Fetched earnings data for {symbol}")
            self._cache_data(cache_key, data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
            return None
    
    def get_comprehensive_data(self, symbol: str, period: str = '1y') -> Dict:
        """
        Fetch comprehensive data for a symbol from all sources
        
        Args:
            symbol: Stock symbol
            period: Historical data period (default: 1y)
            
        Returns:
            Dictionary with all available data
        """
        logger.info(f"Fetching comprehensive data for {symbol}")
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'historical_data': None,
            'fundamentals': None,
            'earnings': None,
            'current_price': None,
            'data_sources': []
        }
        
        # Fetch historical data
        historical = self.fetch_historical_data_yfinance(symbol, period=period)
        if historical is not None:
            result['historical_data'] = historical
            result['data_sources'].append('yfinance_historical')
            
            # Get current price from historical data
            if 'close' in historical.columns and len(historical) > 0:
                result['current_price'] = historical['close'].iloc[-1]
        
        # Fetch fundamentals
        fundamentals = self.fetch_fundamentals_alpha_vantage(symbol)
        if fundamentals is not None:
            result['fundamentals'] = fundamentals
            result['data_sources'].append('alphavantage_fundamentals')
        
        # Fetch earnings
        earnings = self.fetch_earnings_alpha_vantage(symbol)
        if earnings is not None:
            result['earnings'] = earnings
            result['data_sources'].append('alphavantage_earnings')
        
        logger.info(f"Comprehensive data fetched for {symbol} from {len(result['data_sources'])} sources")
        
        return result
    
    def analyze_fundamentals(self, fundamentals: Dict) -> Dict:
        """
        Analyze fundamental data and provide insights
        
        Args:
            fundamentals: Fundamental data dictionary
            
        Returns:
            Dictionary with analysis and signals
        """
        if not fundamentals:
            return {}
        
        analysis = {
            'valuation_score': 0,  # -2 (undervalued) to +2 (overvalued)
            'profitability_score': 0,  # -2 (unprofitable) to +2 (highly profitable)
            'signals': []
        }
        
        # P/E Ratio analysis
        pe_ratio = fundamentals.get('pe_ratio')
        if pe_ratio is not None:
            if pe_ratio < 15:
                analysis['valuation_score'] -= 1
                analysis['signals'].append('Potentially undervalued (low P/E)')
            elif pe_ratio > 30:
                analysis['valuation_score'] += 1
                analysis['signals'].append('Potentially overvalued (high P/E)')
        
        # Profitability analysis
        profit_margin = fundamentals.get('profit_margin')
        if profit_margin is not None:
            if profit_margin > 0.15:  # > 15%
                analysis['profitability_score'] += 1
                analysis['signals'].append('Strong profit margin')
            elif profit_margin < 0:
                analysis['profitability_score'] -= 1
                analysis['signals'].append('Negative profit margin')
        
        # ROE analysis
        roe = fundamentals.get('return_on_equity')
        if roe is not None:
            if roe > 0.15:  # > 15%
                analysis['profitability_score'] += 1
                analysis['signals'].append('Strong return on equity')
            elif roe < 0:
                analysis['profitability_score'] -= 1
                analysis['signals'].append('Negative return on equity')
        
        # Dividend yield
        div_yield = fundamentals.get('dividend_yield')
        if div_yield is not None and div_yield > 0.03:  # > 3%
            analysis['signals'].append(f'Good dividend yield ({div_yield:.2%})')
        
        # Beta (volatility)
        beta = fundamentals.get('beta')
        if beta is not None:
            if beta > 1.5:
                analysis['signals'].append('High volatility stock (beta > 1.5)')
            elif beta < 0.5:
                analysis['signals'].append('Low volatility stock (beta < 0.5)')
        
        # Overall recommendation
        total_score = analysis['valuation_score'] + analysis['profitability_score']
        if total_score <= -2:
            analysis['recommendation'] = 'STRONG BUY'
        elif total_score == -1:
            analysis['recommendation'] = 'BUY'
        elif total_score == 0:
            analysis['recommendation'] = 'HOLD'
        elif total_score == 1:
            analysis['recommendation'] = 'SELL'
        else:
            analysis['recommendation'] = 'STRONG SELL'
        
        return analysis


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Data Fetcher Module - Example Usage")
    print("="*60)
    
    # Initialize fetcher
    fetcher = DataFetcher()
    
    # Test symbol
    test_symbol = 'AAPL'
    
    print(f"\nTesting data fetching for {test_symbol}...")
    
    # Fetch historical data
    if YFINANCE_AVAILABLE:
        print("\n" + "-"*60)
        print("Fetching Historical Data (yfinance)")
        print("-"*60)
        
        historical = fetcher.fetch_historical_data_yfinance(test_symbol, period='1mo')
        if historical is not None:
            print(f"Fetched {len(historical)} days of data")
            print(f"Columns: {list(historical.columns)}")
            print(f"\nLatest data:")
            print(historical.tail(3))
    
    # Fetch fundamentals
    if fetcher.av_api_key and fetcher.av_api_key != '':
        print("\n" + "-"*60)
        print("Fetching Fundamentals (Alpha Vantage)")
        print("-"*60)
        
        fundamentals = fetcher.fetch_fundamentals_alpha_vantage(test_symbol)
        if fundamentals is not None:
            print("Key Fundamentals:")
            for key in ['name', 'sector', 'market_cap', 'pe_ratio', 'eps', 
                       'dividend_yield', 'profit_margin', 'beta']:
                value = fundamentals.get(key)
                if value is not None:
                    if isinstance(value, float):
                        print(f"  {key}: {value:.4f}")
                    else:
                        print(f"  {key}: {value}")
            
            # Analyze fundamentals
            print("\n" + "-"*60)
            print("Fundamental Analysis")
            print("-"*60)
            
            analysis = fetcher.analyze_fundamentals(fundamentals)
            print(f"Recommendation: {analysis.get('recommendation', 'N/A')}")
            print(f"Valuation Score: {analysis.get('valuation_score', 0)}")
            print(f"Profitability Score: {analysis.get('profitability_score', 0)}")
            print("\nSignals:")
            for signal in analysis.get('signals', []):
                print(f"  - {signal}")
    else:
        print("\n[SKIPPED] Alpha Vantage API key not configured")
        print("Set ALPHA_VANTAGE_API_KEY in your .env file to enable fundamentals")
    
    print("\n" + "="*60)
    print("Data Fetcher module initialized successfully")
    print("="*60)
