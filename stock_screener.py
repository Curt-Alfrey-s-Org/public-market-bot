#!/usr/bin/env python3
"""
Stock Screener Module for market-pie5-bot

Dynamically discovers and filters stocks based on trading parameters.
Searches across major indices (S&P 500, NASDAQ-100, S&P 400, Russell 1000, etc.)
for trading opportunities that match user-defined criteria.

Enhanced with:
- Sentiment analysis integration for news-based filtering
- ML signal quality assessment for better trade selection
- Portfolio optimization for diversification analysis
"""

import logging
import os
import pickle
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Try to import yfinance for stock data
try:
    import yfinance as yf

    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Try to import pandas for reading HTML tables (Wikipedia stock lists)
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Try to import sentiment analyzer
try:
    from sentiment_analyzer import SentimentAnalyzer

    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False

# Try to import ML signal filter
try:
    from ml_signal_filter import MLSignalFilter

    ML_FILTER_AVAILABLE = True
except ImportError:
    ML_FILTER_AVAILABLE = False

# Try to import portfolio optimizer
try:
    from portfolio_optimizer import PortfolioOptimizer

    PORTFOLIO_OPTIMIZER_AVAILABLE = True
except ImportError:
    PORTFOLIO_OPTIMIZER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Load screening parameters from environment
MIN_STOCK_PRICE = float(os.getenv("MIN_STOCK_PRICE", "5.0"))
MAX_STOCK_PRICE = float(os.getenv("MAX_STOCK_PRICE", "1000.0"))
MIN_DAILY_VOLUME = int(os.getenv("MIN_DAILY_VOLUME", "500000"))
MAX_STOCK_VOLATILITY = float(os.getenv("MAX_STOCK_VOLATILITY", "0.15"))

# Advanced filtering parameters
ENABLE_SENTIMENT_FILTER = (
    os.getenv("ENABLE_SENTIMENT_FILTER", "false").lower() == "true"
)
ENABLE_ML_FILTER = os.getenv("ENABLE_ML_FILTER", "false").lower() == "true"
ENABLE_PORTFOLIO_OPTIMIZATION = (
    os.getenv("ENABLE_PORTFOLIO_OPTIMIZATION", "false").lower() == "true"
)
MIN_SENTIMENT_SCORE = float(os.getenv("MIN_SENTIMENT_SCORE", "0.0"))
MIN_ML_CONFIDENCE = float(os.getenv("MIN_ML_CONFIDENCE", "0.6"))
MIN_ML_WIN_PROBABILITY = float(os.getenv("MIN_ML_WIN_PROBABILITY", "0.55"))
MIN_DIVERSIFICATION_SCORE = float(os.getenv("MIN_DIVERSIFICATION_SCORE", "0.3"))

# Stock universe configuration
STOCK_UNIVERSE_CACHE_FILE = ".stock_universe_cache.pkl"
STOCK_UNIVERSE_CACHE_DURATION = 86400  # 24 hours in seconds

# Stock scanning and prioritization configuration
# MAX_STOCKS_TO_SCAN: Max symbols to fetch when building filtered universe (goal: ~200 filtered like TOS).
#     Fetch full pool in batches; no early exit. Default 600 so we don't miss good candidates.
MAX_STOCKS_TO_SCAN = int(os.getenv("MAX_STOCKS_TO_SCAN", "600"))
# TOP_STOCKS_TO_TRADE: Final number of top-ranked stocks to return after sorting
TOP_STOCKS_TO_TRADE = int(os.getenv("TOP_STOCKS_TO_TRADE", "50"))
# SCREENER_TARGET_FILTERED: Reference target (~200) for "universe" size before sorting (TOS-like).
#     We fetch full scan pool, filter all, then sort—no early cutoff that misses candidates.
SCREENER_TARGET_FILTERED = int(os.getenv("SCREENER_TARGET_FILTERED", "200"))
# SCREENER_BATCH_SIZE: Chunk size per yf.download call. Larger = fewer API round-trips.
SCREENER_BATCH_SIZE = int(os.getenv("SCREENER_BATCH_SIZE", "200"))
# SCREENER_USE_BATCH_FETCH: Use yf.download batch for Phase 1 (fetch+filter). Goal ~3s for 200 filtered.
SCREENER_USE_BATCH_FETCH = os.getenv("SCREENER_USE_BATCH_FETCH", "true").lower() == "true"
# Enable detailed timing breakdown (useful for performance analysis)
ENABLE_SCREENER_TIMING = os.getenv("ENABLE_SCREENER_TIMING", "true").lower() == "true"

# Scoring weights for stock prioritization (TOS-like ranking)
SCORE_WEIGHT_MOMENTUM = float(os.getenv("SCORE_WEIGHT_MOMENTUM", "0.3"))
SCORE_WEIGHT_VOLUME = float(os.getenv("SCORE_WEIGHT_VOLUME", "0.2"))
SCORE_WEIGHT_VOLATILITY = float(os.getenv("SCORE_WEIGHT_VOLATILITY", "0.2"))
SCORE_WEIGHT_LIQUIDITY = float(os.getenv("SCORE_WEIGHT_LIQUIDITY", "0.15"))
SCORE_WEIGHT_SENTIMENT = float(os.getenv("SCORE_WEIGHT_SENTIMENT", "0.15"))

# Scoring thresholds (configurable for strategy tuning)
# Momentum scoring thresholds
MOMENTUM_OPTIMAL_VOL_MIN = float(os.getenv("MOMENTUM_OPTIMAL_VOL_MIN", "0.05"))  # 5%
MOMENTUM_OPTIMAL_VOL_MAX = float(os.getenv("MOMENTUM_OPTIMAL_VOL_MAX", "0.10"))  # 10%

# Volatility scoring thresholds (sweet spot for swing trading)
VOLATILITY_OPTIMAL_MIN = float(os.getenv("VOLATILITY_OPTIMAL_MIN", "0.03"))  # 3%
VOLATILITY_OPTIMAL_MAX = float(os.getenv("VOLATILITY_OPTIMAL_MAX", "0.08"))  # 8%

# Market cap thresholds for liquidity scoring
MEGA_CAP_THRESHOLD = float(os.getenv("MEGA_CAP_THRESHOLD", "200000000000"))  # $200B
LARGE_CAP_THRESHOLD = float(os.getenv("LARGE_CAP_THRESHOLD", "10000000000"))  # $10B
MID_CAP_THRESHOLD = float(os.getenv("MID_CAP_THRESHOLD", "2000000000"))  # $2B

# Wikipedia URLs for major stock indices
# These are free, public, and frequently updated
STOCK_UNIVERSE_SOURCES = {
    "sp500": "https://en.wikipedia.org/",
    "nasdaq100": "https://en.wikipedia.org/wiki/Nasdaq-100",
    "dowjones": "https://en.wikipedia.org/",
    "sp400": "https://en.wikipedia.org/",  # Mid-cap
    "russell1000": "https://en.wikipedia.org/wiki/Russell_1000_Index",  # ~1000 largest US; skips small-cap "bottom"
}

# Known delisted or merged stocks to filter out
# Updated periodically to avoid checking inactive stocks
DELISTED_STOCKS = {
    "ATVI",  # Acquired by Microsoft in 2023
    "PXD",  # Acquired by ExxonMobil in 2024
    "DISCA",  # Merged into WBD
    "DISCK",  # Merged into WBD
    "VIAC",  # Became PARA
    "TWTR",  # Acquired by Elon Musk, became private
    "INFO",  # Acquired in 2021
}

# Fallback list for when Wikipedia is unavailable or pandas not installed
# This is a curated list of major stocks across sectors for basic functionality
FALLBACK_STOCK_UNIVERSE = [
    # Major tech stocks
    "AAPL",
    "MSFT",
    "GOOGL",
    "GOOG",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "AVGO",
    "ORCL",
    "ADBE",
    "CRM",
    "CSCO",
    "AMD",
    "INTC",
    "QCOM",
    "TXN",
    "IBM",
    "AMAT",
    "MU",
    # Healthcare
    "UNH",
    "JNJ",
    "LLY",
    "ABBV",
    "MRK",
    "TMO",
    "ABT",
    "PFE",
    "DHR",
    "BMY",
    "AMGN",
    "CVS",
    "MDT",
    "GILD",
    "VRTX",
    "ISRG",
    "ZTS",
    "REGN",
    "HUM",
    "CI",
    # Financial
    "JPM",
    "V",
    "MA",
    "BAC",
    "WFC",
    "MS",
    "GS",
    "BLK",
    "C",
    "SCHW",
    "AXP",
    "USB",
    "PNC",
    "TFC",
    "BK",
    "COF",
    "CME",
    "ICE",
    "SPGI",
    "MCO",
    # Consumer
    "WMT",
    "HD",
    "MCD",
    "NKE",
    "SBUX",
    "TGT",
    "LOW",
    "DIS",
    "COST",
    "PG",
    "KO",
    "PEP",
    "PM",
    "MO",
    "CL",
    "EL",
    "KMB",
    "GIS",
    "HSY",
    "MDLZ",
    # Energy
    "XOM",
    "CVX",
    "COP",
    "SLB",
    "EOG",
    "MPC",
    "PSX",
    "VLO",
    "OXY",
    "HAL",
    "BKR",
    "KMI",
    "WMB",
    "OKE",
    "HES",
    "DVN",
    "FANG",
    "MRO",
    "APA",
    # Industrial
    "BA",
    "CAT",
    "HON",
    "UPS",
    "RTX",
    "LMT",
    "GE",
    "MMM",
    "DE",
    "UNP",
    "FDX",
    "NSC",
    "CSX",
    "EMR",
    "ETN",
    "ITW",
    "PH",
    "CMI",
    "ROK",
    "CARR",
    # Communications
    "NFLX",
    "CMCSA",
    "VZ",
    "T",
    "TMUS",
    "CHTR",
    "EA",
    "TTWO",
    "NXST",
    # Materials
    "LIN",
    "APD",
    "ECL",
    "DD",
    "NEM",
    "FCX",
    "DOW",
    "PPG",
    "SHW",
    "MLM",
    # Utilities
    "NEE",
    "DUK",
    "SO",
    "D",
    "AEP",
    "EXC",
    "SRE",
    "PEG",
    "XEL",
    "ED",
    # Real Estate
    "AMT",
    "PLD",
    "CCI",
    "EQIX",
    "PSA",
    "SPG",
    "WELL",
    "DLR",
    "O",
    "AVB",
]


def _load_universe_cache() -> Optional[Set[str]]:
    """Load cached stock universe from disk"""
    try:
        if not os.path.exists(STOCK_UNIVERSE_CACHE_FILE):
            return None

        # Check cache age
        cache_age = time.time() - os.path.getmtime(STOCK_UNIVERSE_CACHE_FILE)
        if cache_age > STOCK_UNIVERSE_CACHE_DURATION:
            logger.debug("Stock universe cache expired")
            return None

        with open(STOCK_UNIVERSE_CACHE_FILE, "rb") as f:
            cached_data = pickle.load(f)
            logger.info(f"Loaded {len(cached_data)} stocks from cache")
            return cached_data
    except Exception as e:
        logger.debug(f"Failed to load cache: {e}")
        return None


def _save_universe_cache(universe: Set[str]):
    """Save stock universe to disk cache"""
    try:
        with open(STOCK_UNIVERSE_CACHE_FILE, "wb") as f:
            pickle.dump(universe, f)
        logger.debug(f"Saved {len(universe)} stocks to cache")
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")


def fetch_stock_universe_from_wikipedia() -> Set[str]:
    """
    Fetch comprehensive stock universe from Wikipedia tables

    Returns:
        Set of stock ticker symbols from major indices
    """
    if not PANDAS_AVAILABLE:
        logger.warning("pandas not available - cannot fetch from Wikipedia")
        return set()

    all_symbols = set()

    for source_name, url in STOCK_UNIVERSE_SOURCES.items():
        try:
            logger.debug(f"Fetching {source_name} from Wikipedia...")

            # Read HTML tables from Wikipedia
            tables = pd.read_html(url, header=0)

            if not tables:
                logger.debug(f"No tables found for {source_name}")
                continue

            # Use first table that has a Symbol/Ticker column (e.g. Russell 1000 has Record/Returns before Components)
            df = None
            ticker_col = None
            for t in tables:
                for col in t.columns:
                    col_lower = str(col).lower()
                    if "symbol" in col_lower or "ticker" in col_lower:
                        df = t
                        ticker_col = col
                        break
                if df is not None:
                    break
            if df is None and len(tables) > 0:
                df = tables[0]
                ticker_col = df.columns[0] if len(df.columns) > 0 else None

            if df is not None and ticker_col is not None:
                # Extract tickers, clean them
                tickers = df[ticker_col].astype(str).str.strip().str.upper()
                # Remove any non-alphanumeric characters except dots
                tickers = tickers.str.replace(r"[^A-Z0-9.]", "", regex=True)
                # Filter out empty strings, invalid tickers, and known delisted stocks
                tickers = [
                    t
                    for t in tickers
                    if t
                    and len(t) <= 6
                    and t.replace(".", "").isalpha()
                    and t not in DELISTED_STOCKS
                ]

                all_symbols.update(tickers)
                logger.info(f"✓ {source_name}: Found {len(tickers)} symbols")

        except Exception as e:
            logger.debug(f"Failed to fetch {source_name}: {e}")

    # Filter out any delisted stocks that might have slipped through
    all_symbols = all_symbols - DELISTED_STOCKS

    return all_symbols


def fetch_stock_universe_with_metadata() -> Dict[str, Dict[str, str]]:
    """
    Fetch stock universe WITH market cap tier and sector from Wikipedia
    
    Returns:
        Dict with structure:
        {
            'AAPL': {'market_cap_tier': 'mega-cap', 'sector': 'Technology'},
            'XYZ': {'market_cap_tier': 'mid-cap', 'sector': 'Healthcare'},
        }
    """
    if not PANDAS_AVAILABLE:
        logger.warning("pandas not available - cannot fetch universe with metadata")
        return {}
    
    universe_data = {}
    
    for source_name, url in STOCK_UNIVERSE_SOURCES.items():
        try:
            logger.debug(f"Fetching {source_name} from Wikipedia with metadata...")
            tables = pd.read_html(url, header=0)
            
            if not tables:
                logger.debug(f"No tables found for {source_name}")
                continue
            
            # Find table with Symbol/Ticker column
            df = None
            ticker_col = None
            for t in tables:
                for col in t.columns:
                    col_lower = str(col).lower()
                    if "symbol" in col_lower or "ticker" in col_lower:
                        df = t
                        ticker_col = col
                        break
                if df is not None:
                    break
            
            if df is None and len(tables) > 0:
                df = tables[0]
                ticker_col = df.columns[0] if len(df.columns) > 0 else None
            
            if df is not None and ticker_col is not None:
                # Extract tickers
                tickers = df[ticker_col].astype(str).str.strip().str.upper()
                tickers = tickers.str.replace(r"[^A-Z0-9.]", "", regex=True)
                
                # Determine market cap tier based on index
                market_cap_tier = _get_market_cap_tier_for_index(source_name)
                
                # Try to find sector column
                sector_col = _find_sector_column(df)
                
                # Extract metadata for each ticker
                for idx, ticker in enumerate(tickers):
                    if ticker and len(ticker) <= 6 and ticker.replace(".", "").isalpha() and ticker not in DELISTED_STOCKS:
                        sector = "Unknown"
                        
                        # Try to extract sector from DataFrame if column exists
                        if sector_col is not None and idx < len(df):
                            try:
                                sector = str(df[sector_col].iloc[idx]).strip()
                                if not sector or sector == "nan":
                                    sector = "Unknown"
                            except Exception:
                                sector = "Unknown"
                        
                        universe_data[ticker] = {
                            'market_cap_tier': market_cap_tier,
                            'sector': sector,
                            'source_index': source_name
                        }
                
                logger.info(f"✓ {source_name}: {len([t for t in tickers if t and t not in DELISTED_STOCKS])} symbols with metadata")
        
        except Exception as e:
            logger.debug(f"Failed to fetch {source_name} with metadata: {e}")
    
    return universe_data


def _get_market_cap_tier_for_index(index_name: str) -> str:
    """Map index name to market cap tier"""
    tier_map = {
        "sp500": "large-cap",
        "nasdaq100": "large-cap",
        "dowjones": "mega-cap",
        "sp400": "mid-cap",
        "russell1000": "large-cap"
    }
    return tier_map.get(index_name.lower(), "unknown")


def _find_sector_column(df) -> Optional[str]:
    """Find sector column in DataFrame if it exists"""
    if df is None:
        return None
    try:
        for col in df.columns:
            col_lower = str(col).lower()
            if "sector" in col_lower or "industry" in col_lower:
                return col
    except Exception:
        pass
    return None


def get_stock_universe(
    use_cache: bool = True, force_refresh: bool = False
) -> List[str]:
    """
    Get comprehensive stock universe for screening

    Args:
        use_cache: Whether to use cached universe
        force_refresh: Force refresh from Wikipedia even if cache valid

    Returns:
        List of stock ticker symbols
    """
    # Try to load from cache first
    if use_cache and not force_refresh:
        cached = _load_universe_cache()
        if cached:
            return sorted(list(cached))

    logger.info("Building stock universe...")

    # Try to fetch from Wikipedia
    universe = fetch_stock_universe_from_wikipedia()

    # If Wikipedia fetch succeeded, cache and return
    if len(universe) > 100:  # Sanity check: should have at least 100 stocks
        logger.info(f"✓ Built universe of {len(universe)} stocks from Wikipedia")
        _save_universe_cache(universe)
        return sorted(list(universe))

    # Fallback to predefined list
    logger.warning("Using fallback stock universe")
    universe = set(FALLBACK_STOCK_UNIVERSE)

    # Remove any delisted stocks from fallback list
    universe = universe - DELISTED_STOCKS

    # Save fallback to cache
    _save_universe_cache(universe)

    return sorted(list(universe))


class StockScreener:
    """
    Stock screener that dynamically discovers and filters trading opportunities
    from a comprehensive stock universe.

    Enhanced with:
    - Sentiment analysis for news-based filtering
    - ML signal quality assessment
    - Portfolio optimization for diversification
    """
    
    # Class-level constant for logging format
    LOG_SEPARATOR_LENGTH = 70

    def __init__(
        self,
        stock_universe: Optional[List[str]] = None,
        enable_sentiment: bool = ENABLE_SENTIMENT_FILTER,
        enable_ml: bool = ENABLE_ML_FILTER,
        enable_portfolio_opt: bool = ENABLE_PORTFOLIO_OPTIMIZATION,
    ):
        """
        Initialize the stock screener

        Args:
            stock_universe: Optional predefined list of stocks to screen.
                          If None, will dynamically build universe from major indices.
            enable_sentiment: Enable sentiment analysis filtering
            enable_ml: Enable ML signal quality filtering
            enable_portfolio_opt: Enable portfolio optimization features
        """
        self.cache = {}  # Cache for stock data
        self.cache_duration = 300  # Cache duration in seconds (5 minutes)
        self.last_screen_time = None
        self.last_screened_stocks = []

        # Build or use provided stock universe
        if stock_universe:
            self.stock_universe = stock_universe
            logger.info("="*self.LOG_SEPARATOR_LENGTH)
            logger.info("[STOCK SCREENER INIT] Using predefined stock universe")
            logger.info(f"[STOCK SCREENER INIT] Universe size: {len(stock_universe)} stocks")
            logger.info("="*self.LOG_SEPARATOR_LENGTH)
        else:
            logger.info("="*self.LOG_SEPARATOR_LENGTH)
            logger.info("[STOCK SCREENER INIT] Building TOS-like dynamic universe...")
            logger.info("[STOCK SCREENER INIT] Sources: S&P 500, NASDAQ-100, Dow Jones, S&P 400, Russell 1000")
            self.stock_universe = get_stock_universe(use_cache=True)
            logger.info(f"[STOCK SCREENER INIT] ✓ Universe built: {len(self.stock_universe)} stocks")
            logger.info("="*self.LOG_SEPARATOR_LENGTH)

        logger.info(f"Stock Screening Criteria (from .env):")
        logger.info(f"  • Price Range: ${MIN_STOCK_PRICE:.2f} - ${MAX_STOCK_PRICE:.2f}")
        logger.info(f"  • Min Daily Volume: {MIN_DAILY_VOLUME:,} shares")
        logger.info(f"  • Max Volatility: {MAX_STOCK_VOLATILITY:.1%}")
        logger.info(f"  • Scan Pool Size: {MAX_STOCKS_TO_SCAN} stocks")
        logger.info(f"  • Top N to Trade: {TOP_STOCKS_TO_TRADE} stocks")
        if SCREENER_USE_BATCH_FETCH:
            logger.info(
                f"  • Batch mode: chunks of {SCREENER_BATCH_SIZE}, goal ~{SCREENER_TARGET_FILTERED} filtered in ~3s, no early cutoff"
            )
        logger.info("="*self.LOG_SEPARATOR_LENGTH)

        # Initialize advanced filtering components
        self.sentiment_analyzer = None
        self.ml_filter = None
        self.portfolio_optimizer = None

        # Setup sentiment analyzer
        if enable_sentiment and SENTIMENT_AVAILABLE:
            try:
                self.sentiment_analyzer = SentimentAnalyzer()
                logger.info("✓ Sentiment analysis filtering enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize sentiment analyzer: {e}")
        elif enable_sentiment and not SENTIMENT_AVAILABLE:
            logger.warning(
                "Sentiment filtering requested but sentiment_analyzer not available"
            )

        # Setup ML filter
        if enable_ml and ML_FILTER_AVAILABLE:
            try:
                self.ml_filter = MLSignalFilter(model_type="random_forest")
                logger.info("✓ ML signal quality filtering enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize ML filter: {e}")
        elif enable_ml and not ML_FILTER_AVAILABLE:
            logger.warning("ML filtering requested but ml_signal_filter not available")

        # Setup portfolio optimizer
        if enable_portfolio_opt and PORTFOLIO_OPTIMIZER_AVAILABLE:
            try:
                self.portfolio_optimizer = PortfolioOptimizer()
                logger.info("✓ Portfolio optimization enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize portfolio optimizer: {e}")
        elif enable_portfolio_opt and not PORTFOLIO_OPTIMIZER_AVAILABLE:
            logger.warning(
                "Portfolio optimization requested but portfolio_optimizer not available"
            )

    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached stock data is still valid"""
        if symbol not in self.cache:
            return False

        cache_age = (datetime.now() - self.cache[symbol]["timestamp"]).total_seconds()
        return cache_age < self.cache_duration

    def _cache_stock_data(self, symbol: str, data: Dict):
        """Cache stock data with timestamp"""
        self.cache[symbol] = {"data": data, "timestamp": datetime.now()}

    def _get_cached_data(self, symbol: str) -> Optional[Dict]:
        """Get cached stock data if valid"""
        if self._is_cache_valid(symbol):
            return self.cache[symbol]["data"]
        return None

    def fetch_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        Fetch stock information using yfinance

        Returns:
            Dict with keys: price, volume, volatility, marketCap, etc.
            None if fetch fails
        """
        # Check cache first
        cached = self._get_cached_data(symbol)
        if cached:
            logger.debug(f"Using cached data for {symbol}")
            return cached

        if not YFINANCE_AVAILABLE:
            logger.warning("yfinance not available - cannot fetch stock info")
            return None

        # Add small delay between fetches to reduce CPU load and avoid rate limiting
        # This is especially important during startup screening
        # Only apply delay when making actual API calls (not for cached data)
        fetch_delay_raw = os.getenv("STOCK_FETCH_DELAY", "0.1")
        try:
            fetch_delay = float(fetch_delay_raw)
        except (TypeError, ValueError):
            logger.warning(
                f"Invalid STOCK_FETCH_DELAY value {fetch_delay_raw!r}; falling back to default 0.1"
            )
            fetch_delay = 0.1

        if fetch_delay < 0:
            logger.warning(
                f"Negative STOCK_FETCH_DELAY value {fetch_delay}; clamping to 0 seconds"
            )
            fetch_delay = 0.0

        if fetch_delay > 0:
            logger.debug(f"Throttling: sleeping {fetch_delay}s before fetching {symbol}")
            time.sleep(fetch_delay)

        try:
            # Temporarily suppress yfinance logging while fetching (avoids noisy warnings for invalid/delisted symbols)
            yf_logger = logging.getLogger("yfinance")
            original_level = yf_logger.level
            yf_logger.setLevel(logging.CRITICAL)

            try:
                # Time API calls separately
                api_start = time.time()
                ticker = yf.Ticker(symbol)

                # Get current price and volume
                try:
                    price = ticker.fast_info.get("lastPrice")
                    volume = ticker.fast_info.get("lastVolume", 0)
                except:
                    # Fallback to info dict
                    info = ticker.info
                    price = info.get("currentPrice") or info.get("regularMarketPrice")
                    volume = info.get("volume") or info.get("regularMarketVolume", 0)

                if price is None or price <= 0:
                    logger.debug(f"Invalid price for {symbol} (possibly delisted)")
                    return None

                # Get historical data for volatility calculation
                hist = ticker.history(period="1mo")
                api_time = time.time() - api_start
                if api_time > 1.0:  # Log slow API calls
                    logger.debug(f"  {symbol}: API call took {api_time:.2f}s")
                if hist.empty or len(hist) < 2:
                    logger.debug(
                        f"Insufficient historical data for {symbol} (possibly delisted)"
                    )
                    return None
            finally:
                # Restore original logging level
                yf_logger.setLevel(original_level)

            # Calculate volatility (standard deviation of returns)
            returns = hist["Close"].pct_change().dropna()
            volatility = returns.std() if len(returns) > 0 else 0.0

            # Get market cap if available
            try:
                market_cap = ticker.fast_info.get("marketCap", 0)
            except:
                market_cap = ticker.info.get("marketCap", 0)

            stock_data = {
                "symbol": symbol,
                "price": float(price),
                "volume": int(volume),
                "volatility": float(volatility),
                "marketCap": int(market_cap) if market_cap else 0,
                "avgVolume": int(hist["Volume"].mean()) if "Volume" in hist else volume,
            }

            # Cache the data
            self._cache_stock_data(symbol, stock_data)

            return stock_data

        except Exception as e:
            logger.debug(f"Failed to fetch info for {symbol}: {e}")
            return None

    def _fetch_batch_stock_info(self, symbols: List[str]) -> List[Dict]:
        """
        Fetch stock info for multiple symbols via yf.download (batch).
        Phase 1: build filtered universe fast (~3s goal for ~200 filtered, TOS-like).
        Returns list of {symbol, price, volume, volatility, avgVolume, marketCap=0}.
        marketCap is 0 (batch download has no cap); scoring uses neutral liquidity.
        """
        if not YFINANCE_AVAILABLE or not PANDAS_AVAILABLE or not symbols:
            return []

        # Suppress yfinance errors for delisted stocks and other non-critical issues
        # yfinance logs errors directly to stderr and through its logger, so we need to suppress at multiple levels
        yf_logger = logging.getLogger("yfinance")
        original_level = yf_logger.level
        original_propagate = yf_logger.propagate
        yf_logger.setLevel(logging.CRITICAL + 1)  # Set above CRITICAL to suppress all
        yf_logger.propagate = False  # Prevent propagation to root logger
        
        # Also suppress warnings from yfinance about delisted stocks
        import warnings
        import sys
        from io import StringIO
        
        # Capture stderr to suppress yfinance error messages
        old_stderr = sys.stderr
        stderr_capture = StringIO()
        
        # Add a custom filter to the yfinance logger to suppress delisted stock messages
        class DelistedStockFilter(logging.Filter):
            def filter(self, record):
                msg = record.getMessage()
                return not any(keyword in msg.lower() for keyword in ['delisted', 'no data found', 'failed downloads', 'possibly delisted'])
        
        delisted_filter = DelistedStockFilter()
        yf_logger.addFilter(delisted_filter)
        
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message=r'.*delisted.*')
                warnings.filterwarnings('ignore', message=r'.*No data found.*')
                warnings.filterwarnings('ignore', message=r'.*possibly delisted.*')
                warnings.filterwarnings('ignore', message=r'.*Failed downloads.*')
                
                # Redirect stderr to capture yfinance errors
                sys.stderr = stderr_capture
                
                try:
                    # Disable threading to prevent thread exhaustion
                    # Use sequential downloads instead of parallel to avoid RuntimeError: can't start new thread
                    data = yf.download(
                        symbols,
                        period="1mo",
                        interval="1d",
                        group_by="ticker",
                        threads=False,  # Changed from True to prevent thread exhaustion
                        progress=False,
                        auto_adjust=True,
                    )
                except Exception as e:
                    # Log only critical errors, not delisted stock errors
                    if "delisted" not in str(e).lower() and "no data found" not in str(e).lower():
                        logger.warning(f"Error downloading data for symbols: {e}")
                    data = None
        finally:
            # Restore stderr
            sys.stderr = old_stderr
            yf_logger.setLevel(original_level)
            yf_logger.propagate = original_propagate  # Restore propagation
            # Remove the filter we added
            if 'delisted_filter' in locals():
                yf_logger.removeFilter(delisted_filter)
            
            # Check captured stderr for non-delisted errors (but don't log delisted stock errors)
            stderr_output = stderr_capture.getvalue()
            if stderr_output and "delisted" not in stderr_output.lower() and "no data found" not in stderr_output.lower() and "failed downloads" not in stderr_output.lower():
                # Only log if it's not a delisted stock error
                logger.debug(f"yfinance stderr output: {stderr_output[:200]}")

        if data is None or data.empty:
            return []

        results = []
        # Multi-ticker: columns (Ticker, OHLCV) or flat for single ticker
        multi = isinstance(data.columns, pd.MultiIndex)
        if multi:
            tickers = data.columns.get_level_values(0).unique().tolist()
        else:
            tickers = [symbols[0]] if symbols else []

        for sym in tickers:
            try:
                if multi:
                    sub = data[sym].copy()
                else:
                    sub = data.copy()
                if not isinstance(sub, pd.DataFrame) or sub.empty or len(sub) < 2:
                    continue
                if "Close" not in sub.columns or "Volume" not in sub.columns:
                    continue
                close = sub["Close"].dropna()
                vol = sub["Volume"].dropna()
                if close.empty or vol.empty:
                    continue
                price = float(close.iloc[-1])
                v = vol.iloc[-1]
                volume = int(v) if (pd.notna(v) and v >= 0) else 0
                if price <= 0:
                    continue
                returns = close.pct_change().dropna()
                volatility = float(returns.std()) if len(returns) > 0 else 0.0
                avg_vol = int(vol.mean()) if not vol.empty else volume
                results.append({
                    "symbol": sym,
                    "price": price,
                    "volume": volume,
                    "volatility": volatility,
                    "avgVolume": avg_vol,
                    "marketCap": 0,
                })
            except Exception as e:
                logger.debug(f"Batch parse skip {sym}: {e}")
                continue

        return results

    def filter_stock(self, stock_data: Dict) -> Tuple[bool, str]:
        """
        Filter stock based on screening criteria

        Args:
            stock_data: Dictionary with stock information

        Returns:
            Tuple of (passes_filter, reason)
        """
        symbol = stock_data["symbol"]
        price = stock_data["price"]
        volume = stock_data["volume"]
        volatility = stock_data["volatility"]

        # Check price range
        if price < MIN_STOCK_PRICE:
            return False, f"Price ${price:.2f} below minimum ${MIN_STOCK_PRICE:.2f}"

        if price > MAX_STOCK_PRICE:
            return False, f"Price ${price:.2f} exceeds maximum ${MAX_STOCK_PRICE:.2f}"

        # Check volume
        if volume < MIN_DAILY_VOLUME:
            return False, f"Volume {volume:,} below minimum {MIN_DAILY_VOLUME:,}"

        # Check volatility
        if volatility > MAX_STOCK_VOLATILITY:
            return (
                False,
                f"Volatility {volatility:.1%} exceeds maximum {MAX_STOCK_VOLATILITY:.1%}",
            )

        return True, "Passed all filters"

    def filter_by_sentiment(self, symbol: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Filter stock based on sentiment analysis

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (passes_filter, reason, sentiment_data)
        """
        if not self.sentiment_analyzer:
            return True, "Sentiment analysis not enabled", None

        try:
            sentiment = self.sentiment_analyzer.get_sentiment_score(symbol, days=7)

            # Check if we have enough data
            if sentiment["article_count"] < 3:
                return (
                    True,
                    f"Insufficient news data ({sentiment['article_count']} articles)",
                    sentiment,
                )

            # Check sentiment score
            score = sentiment["overall_score"]
            signal = sentiment["sentiment_signal"]

            if score < MIN_SENTIMENT_SCORE and signal == "BEARISH":
                return (
                    False,
                    f"Negative sentiment (score={score:.2f}, signal={signal})",
                    sentiment,
                )

            return True, f"Sentiment OK (score={score:.2f}, signal={signal})", sentiment

        except Exception as e:
            logger.debug(f"Sentiment filtering error for {symbol}: {e}")
            return True, "Sentiment analysis unavailable", None

    def filter_by_ml_quality(
        self, symbol: str, stock_data: Dict, indicators: Optional[Dict] = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Filter stock based on ML signal quality prediction

        Args:
            symbol: Stock symbol
            stock_data: Basic stock data
            indicators: Optional technical indicators

        Returns:
            Tuple of (passes_filter, reason, ml_scores)
        """
        if not self.ml_filter or not self.ml_filter.is_trained:
            return True, "ML filtering not enabled or model not trained", None

        try:
            # Prepare signal data for ML prediction
            signal_data = {
                "signal": "BUY",  # Assuming we're screening for buy candidates
                "price": stock_data["price"],
                "indicators": indicators or {},
                "market_conditions": {
                    "volume": stock_data["volume"],
                    "volatility": stock_data["volatility"],
                },
            }

            # Get ML prediction
            should_filter, scores = self.ml_filter.should_filter_signal(
                signal_data,
                min_confidence=MIN_ML_CONFIDENCE,
                min_win_prob=MIN_ML_WIN_PROBABILITY,
            )

            if should_filter:
                return (
                    False,
                    (
                        f"Low ML quality (confidence={scores['confidence']:.2f}, "
                        f"win_prob={scores['win_probability']:.2f})"
                    ),
                    scores,
                )

            return (
                True,
                (
                    f"Good ML quality (confidence={scores['confidence']:.2f}, "
                    f"win_prob={scores['win_probability']:.2f})"
                ),
                scores,
            )

        except Exception as e:
            logger.debug(f"ML filtering error for {symbol}: {e}")
            return True, "ML filtering unavailable", None

    def calculate_stock_score(
        self, 
        symbol: str, 
        stock_data: Dict,
        sentiment_data: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate a composite score for a stock based on multiple factors
        (TOS-like prioritization system)
        
        Args:
            symbol: Stock symbol
            stock_data: Stock data from fetch_stock_info
            sentiment_data: Optional sentiment analysis data
            
        Returns:
            Dictionary with scoring breakdown and composite score
        """
        scores = {
            "symbol": symbol,
            "momentum_score": 0.0,
            "volume_score": 0.0,
            "volatility_score": 0.0,
            "liquidity_score": 0.0,
            "sentiment_score": 0.5,  # Neutral default
            "composite_score": 0.0,
        }
        
        try:
            # 1. Momentum Score (price action strength)
            # Higher momentum = higher score
            # Calculate from price vs moving average if available
            price = stock_data.get("price", 0)
            if price > 0:
                # Simple momentum proxy: normalize volatility as trend strength
                # In a real TOS-like system, this would use RSI, MACD, etc.
                volatility = stock_data.get("volatility", 0)
                # Convert volatility to momentum score (0-1)
                # Medium volatility gets highest score (configurable sweet spot)
                if MOMENTUM_OPTIMAL_VOL_MIN <= volatility <= MOMENTUM_OPTIMAL_VOL_MAX:
                    scores["momentum_score"] = 1.0
                elif volatility < MOMENTUM_OPTIMAL_VOL_MIN:
                    scores["momentum_score"] = volatility / MOMENTUM_OPTIMAL_VOL_MIN  # Scale up low vol
                else:
                    scores["momentum_score"] = max(0.0, 1.0 - (volatility - MOMENTUM_OPTIMAL_VOL_MAX) / MOMENTUM_OPTIMAL_VOL_MIN)
            
            # 2. Volume Score (trading activity)
            # Higher volume = better liquidity and interest
            volume = stock_data.get("volume", 0)
            avg_volume = stock_data.get("avgVolume", volume)
            if avg_volume > 0:
                volume_ratio = volume / avg_volume
                # Normalize: 1.0 = average, >1.0 = above average
                scores["volume_score"] = min(1.0, volume_ratio)
            else:
                scores["volume_score"] = 0.5  # Neutral if no volume data
            
            # 3. Volatility Score (risk/opportunity balance)
            # Moderate volatility preferred for swing trading
            volatility = stock_data.get("volatility", 0)
            if volatility <= 0:
                scores["volatility_score"] = 0.5  # Neutral
            elif VOLATILITY_OPTIMAL_MIN <= volatility <= VOLATILITY_OPTIMAL_MAX:  # Sweet spot
                scores["volatility_score"] = 1.0
            elif volatility < VOLATILITY_OPTIMAL_MIN:  # Too low
                scores["volatility_score"] = volatility / VOLATILITY_OPTIMAL_MIN
            else:  # Too high
                range_above = VOLATILITY_OPTIMAL_MAX - VOLATILITY_OPTIMAL_MIN
                scores["volatility_score"] = max(0.0, 1.0 - (volatility - VOLATILITY_OPTIMAL_MAX) / range_above)
            
            # 4. Liquidity Score (market cap and volume)
            market_cap = stock_data.get("marketCap", 0)
            if market_cap > 0:
                # Normalize by market cap tiers (configurable thresholds)
                if market_cap >= MEGA_CAP_THRESHOLD:  # Mega cap
                    scores["liquidity_score"] = 1.0
                elif market_cap >= LARGE_CAP_THRESHOLD:  # Large cap
                    scores["liquidity_score"] = 0.9
                elif market_cap >= MID_CAP_THRESHOLD:  # Mid cap
                    scores["liquidity_score"] = 0.7
                else:  # Small cap
                    scores["liquidity_score"] = 0.5
            else:
                scores["liquidity_score"] = 0.5  # Neutral if no market cap
            
            # 5. Sentiment Score (news sentiment if available)
            if sentiment_data:
                # Normalize sentiment from [-1, 1] to [0, 1]
                sentiment_score = sentiment_data.get("overall_score", 0.0)
                scores["sentiment_score"] = (sentiment_score + 1.0) / 2.0
            
            # Calculate composite score (weighted average)
            scores["composite_score"] = (
                scores["momentum_score"] * SCORE_WEIGHT_MOMENTUM +
                scores["volume_score"] * SCORE_WEIGHT_VOLUME +
                scores["volatility_score"] * SCORE_WEIGHT_VOLATILITY +
                scores["liquidity_score"] * SCORE_WEIGHT_LIQUIDITY +
                scores["sentiment_score"] * SCORE_WEIGHT_SENTIMENT
            )
            
            # Normalize to 0-100 scale for easier interpretation
            scores["composite_score"] *= 100
            
        except Exception as e:
            logger.debug(f"Error calculating score for {symbol}: {e}")
            scores["composite_score"] = 50.0  # Neutral score on error
        
        return scores

    def calculate_portfolio_diversification(
        self, symbols: List[str]
    ) -> Tuple[float, str]:
        """
        Calculate diversification score for a set of symbols

        Args:
            symbols: List of stock symbols

        Returns:
            Tuple of (diversification_score, reason)
        """
        if not self.portfolio_optimizer or len(symbols) < 2:
            return 1.0, "Portfolio optimization not enabled or insufficient symbols"

        try:
            # Add price history for symbols (using cached stock data)
            for symbol in symbols:
                if (
                    symbol in self.cache
                    and "price_history" in self.cache[symbol]["data"]
                ):
                    prices = self.cache[symbol]["data"]["price_history"]
                    self.portfolio_optimizer.add_price_data(symbol, prices)

            # Calculate diversification score
            score = self.portfolio_optimizer.calculate_diversification_score(symbols)

            if score < MIN_DIVERSIFICATION_SCORE:
                return score, f"Low diversification (score={score:.2f})"

            return score, f"Good diversification (score={score:.2f})"

        except Exception as e:
            logger.debug(f"Diversification calculation error: {e}")
            return 1.0, "Diversification calculation unavailable"

    def screen_stocks(
        self,
        candidate_symbols: Optional[List[str]] = None,
        max_results: int = 10,
        use_cache: bool = True,
        use_advanced_filters: bool = True,
        prioritize: bool = True,
    ) -> List[str]:
        """
        Screen stocks and return list of symbols that pass filters

        Args:
            candidate_symbols: Optional list of symbols to screen.
                             If None, uses the comprehensive stock universe.
            max_results: Maximum number of stocks to return
            use_cache: Whether to use cached screening results
            use_advanced_filters: Whether to apply sentiment/ML filtering
            prioritize: Whether to score and prioritize stocks (True) or return first N passing (False)

        Returns:
            List of stock symbols that pass screening criteria
        """
        # Check if we should use cached results
        if use_cache and self.last_screened_stocks and self.last_screen_time:
            cache_age = (datetime.now() - self.last_screen_time).total_seconds()
            if cache_age < self.cache_duration:
                logger.info(
                    f"Using cached screening results ({len(self.last_screened_stocks)} stocks)"
                )
                return self.last_screened_stocks[:max_results]

        # Use stock universe if no candidates provided
        universe_size = 0
        if candidate_symbols is None:
            candidate_symbols = self.stock_universe.copy()
            universe_size = len(candidate_symbols)
            # Shuffle to get variety and avoid always starting with same symbols
            random.shuffle(candidate_symbols)
        else:
            universe_size = len(candidate_symbols)

        passing_stocks = []
        stock_scores = []  # Store stocks with scores for prioritization
        checked_count = 0
        filtered_stats = {"basic": 0, "sentiment": 0, "ml": 0, "total_checked": 0}

        # Limit how many we check to keep it fast and CPU-friendly
        # Default to 100 stocks max (configurable via STOCK_SCREENER_MAX_CHECK)
        max_check_env = os.getenv("STOCK_SCREENER_MAX_CHECK", "100")
        try:
            max_check = int(max_check_env)
        except ValueError:
            logger.warning(
                f"Invalid STOCK_SCREENER_MAX_CHECK value '{max_check_env}'; falling back to 100"
            )
            max_check = 100

        if max_check < 1:
            logger.warning(
                f"STOCK_SCREENER_MAX_CHECK={max_check} is less than 1; using minimum value of 1"
            )
            max_check = 1

        # Use MAX_STOCKS_TO_SCAN if prioritizing, else use max_check
        # Batch mode: full scan pool, no early cutoff (goal ~200 filtered in ~3s, then sort).
        # Legacy: cap by max_results*3 to keep runs bounded.
        use_batch = SCREENER_USE_BATCH_FETCH and YFINANCE_AVAILABLE and PANDAS_AVAILABLE
        if use_batch:
            scan_limit = min(MAX_STOCKS_TO_SCAN, len(candidate_symbols))
        else:
            scan_limit = MAX_STOCKS_TO_SCAN if prioritize else max_check
            scan_limit = min(scan_limit, max(max_results * 3, 50), len(candidate_symbols))
        to_scan = candidate_symbols[:scan_limit]

        logger.info(
            f"Screening up to {len(to_scan)} stocks from universe of {universe_size} "
            f"(returning up to {max_results} that fit .env: price ${MIN_STOCK_PRICE:.2f}-${MAX_STOCK_PRICE:.2f}, vol ≥ {MIN_DAILY_VOLUME:,})"
        )
        if use_batch:
            logger.info(
                f"Batch mode: fetch full pool in chunks of {SCREENER_BATCH_SIZE}, "
                f"filter all, then sort (goal ~{SCREENER_TARGET_FILTERED} filtered in ~3s, no early cutoff)."
            )

        # Timing instrumentation
        screen_start = time.time()
        timing_stats = {
            "fetch_total": 0.0,
            "fetch_count": 0,
            "filter_total": 0.0,
            "filter_count": 0,
            "sentiment_total": 0.0,
            "sentiment_count": 0,
            "ml_total": 0.0,
            "ml_count": 0,
            "score_total": 0.0,
            "score_count": 0,
        }

        if use_batch:
            # Phase 1: batch fetch + basic filter. Phase 2: score + sort. No early exit.
            chunks = [
                to_scan[i : i + SCREENER_BATCH_SIZE]
                for i in range(0, len(to_scan), SCREENER_BATCH_SIZE)
            ]
            phase1_start = time.time()
            total_fetched = 0
            total_ran_filter = 0
            for chunk in chunks:
                batch_data = self._fetch_batch_stock_info(chunk)
                total_fetched += len(chunk)
                total_ran_filter += len(batch_data)
                for d in batch_data:
                    filter_start = time.time()
                    passes, reason = self.filter_stock(d)
                    timing_stats["filter_total"] += time.time() - filter_start
                    timing_stats["filter_count"] += 1
                    if not passes:
                        filtered_stats["basic"] += 1
                        logger.debug(f"✗ {d['symbol']}: {reason}")
                        continue
                    self._cache_stock_data(d["symbol"], d)
                    logger.info(
                        f"✓ {d['symbol']}: ${d['price']:.2f}, "
                        f"Vol: {d['volume']:,}, Volatility: {d['volatility']:.1%}"
                    )
                    passing_stocks.append(d["symbol"])
                    if prioritize:
                        score_start = time.time()
                        score_data = self.calculate_stock_score(
                            d["symbol"], d, sentiment_data=None
                        )
                        timing_stats["score_total"] += time.time() - score_start
                        timing_stats["score_count"] += 1
                        stock_scores.append(score_data)
            phase1_time = time.time() - phase1_start
            timing_stats["fetch_total"] = phase1_time
            timing_stats["fetch_count"] = total_fetched
            filtered_stats["total_checked"] = total_ran_filter

            if use_advanced_filters and (
                self.sentiment_analyzer or (self.ml_filter and self.ml_filter.is_trained)
            ):
                logger.info(
                    "Batch mode: advanced filters (sentiment/ML) skipped; "
                    "disable SCREENER_USE_BATCH_FETCH for full filtering."
                )

            # Phase 2: sort
            phase2_start = time.time()
            num_passed = len(stock_scores) if (prioritize and stock_scores) else len(passing_stocks)
            if prioritize and stock_scores:
                stock_scores.sort(key=lambda x: x["composite_score"], reverse=True)
                passing_stocks = [s["symbol"] for s in stock_scores[:max_results]]
                logger.info(f"Top stocks by priority (showing top {len(passing_stocks)}):")
                for rank, s in enumerate(stock_scores[:max_results], start=1):
                    logger.info(
                        f"  #{rank}: {s['symbol']} - Score: {s['composite_score']:.3f}"
                    )
            else:
                passing_stocks = passing_stocks[:max_results]
            phase2_time = time.time() - phase2_start

            screen_total = time.time() - screen_start
            if ENABLE_SCREENER_TIMING:
                logger.info("=" * 60)
                logger.info(
                    f"SCREENING TIMING BREAKDOWN (total: {screen_total:.2f}s)"
                )
                logger.info("=" * 60)
                logger.info(
                    f"  Phase 1 (fetch+filter): {phase1_time:.2f}s — "
                    f"{num_passed} filtered from {total_fetched} fetched (batch, no early cutoff)"
                )
                logger.info(f"  Phase 2 (sort): {phase2_time:.2f}s")
                logger.info("=" * 60)
            else:
                logger.info(f"Screening completed in {screen_total:.2f}s")

            logger.info(
                f"Screening complete: {num_passed}/{filtered_stats['total_checked']} stocks passed filters"
            )
            self.last_screened_stocks = passing_stocks
            self.last_screen_time = datetime.now()
            return passing_stocks

        for symbol in to_scan:
            # Stop early if we have enough results AND not prioritizing
            if not prioritize and len(passing_stocks) >= max_results:
                break

            checked_count += 1
            filtered_stats["total_checked"] += 1

            # Fetch stock info (timed)
            fetch_start = time.time()
            stock_data = self.fetch_stock_info(symbol)
            fetch_time = time.time() - fetch_start
            timing_stats["fetch_total"] += fetch_time
            timing_stats["fetch_count"] += 1
            if stock_data is None:
                continue

            # Apply basic filters (timed)
            filter_start = time.time()
            passes, reason = self.filter_stock(stock_data)
            filter_time = time.time() - filter_start
            timing_stats["filter_total"] += filter_time
            timing_stats["filter_count"] += 1

            if not passes:
                filtered_stats["basic"] += 1
                logger.debug(f"✗ {symbol}: {reason}")
                continue

            # Store sentiment data for scoring
            sentiment_data = None
            
            # Apply advanced filters if enabled (timed)
            if use_advanced_filters:
                # Sentiment filter
                if self.sentiment_analyzer:
                    sentiment_start = time.time()
                    sentiment_passes, sentiment_reason, sentiment_data = (
                        self.filter_by_sentiment(symbol)
                    )
                    sentiment_time = time.time() - sentiment_start
                    timing_stats["sentiment_total"] += sentiment_time
                    timing_stats["sentiment_count"] += 1
                    if not sentiment_passes:
                        filtered_stats["sentiment"] += 1
                        logger.info(
                            f"✗ {symbol}: Sentiment filter - {sentiment_reason}"
                        )
                        continue
                    else:
                        logger.debug(f"  {symbol}: {sentiment_reason}")

                # ML filter (if model is trained)
                if self.ml_filter and self.ml_filter.is_trained:
                    ml_start = time.time()
                    ml_passes, ml_reason, ml_scores = self.filter_by_ml_quality(
                        symbol, stock_data, indicators=None
                    )
                    ml_time = time.time() - ml_start
                    timing_stats["ml_total"] += ml_time
                    timing_stats["ml_count"] += 1
                    if not ml_passes:
                        filtered_stats["ml"] += 1
                        logger.info(f"✗ {symbol}: ML filter - {ml_reason}")
                        continue
                    else:
                        logger.debug(f"  {symbol}: {ml_reason}")

            # Stock passed all filters
            logger.info(
                f"✓ {symbol}: ${stock_data['price']:.2f}, "
                f"Vol: {stock_data['volume']:,}, "
                f"Volatility: {stock_data['volatility']:.1%}"
            )
            passing_stocks.append(symbol)
            
            # Calculate and store score if prioritizing (timed)
            if prioritize:
                score_start = time.time()
                score_data = self.calculate_stock_score(symbol, stock_data, sentiment_data)
                score_time = time.time() - score_start
                timing_stats["score_total"] += score_time
                timing_stats["score_count"] += 1
                stock_scores.append(score_data)

        # Sort by composite score if prioritizing
        if prioritize and stock_scores:
            stock_scores.sort(key=lambda x: x["composite_score"], reverse=True)
            passing_stocks = [s["symbol"] for s in stock_scores[:max_results]]
            
            # Log priority ranking
            logger.info(f"Top stocks by priority (showing top {len(passing_stocks)}):")
            for rank, score_data in enumerate(stock_scores[:max_results], start=1):
                logger.info(
                    f"  #{rank}: {score_data['symbol']} - "
                    f"Score: {score_data['composite_score']:.3f}"
                )
        elif not prioritize:
            # When not prioritizing, limit to max_results
            passing_stocks = passing_stocks[:max_results]
        
        # Calculate total time
        screen_total = time.time() - screen_start

        # Log timing breakdown (if enabled)
        if ENABLE_SCREENER_TIMING:
            logger.info("=" * 60)
            logger.info(f"SCREENING TIMING BREAKDOWN (total: {screen_total:.2f}s)")
            logger.info("=" * 60)
            if timing_stats["fetch_count"] > 0:
                avg_fetch = timing_stats["fetch_total"] / timing_stats["fetch_count"]
                logger.info(
                    f"  Fetch stock info: {timing_stats['fetch_total']:.2f}s total "
                    f"({timing_stats['fetch_count']} calls, {avg_fetch:.3f}s avg/call, "
                    f"{timing_stats['fetch_total']/screen_total*100:.1f}% of total)"
                )
            if timing_stats["filter_count"] > 0:
                avg_filter = timing_stats["filter_total"] / timing_stats["filter_count"]
                logger.info(
                    f"  Basic filtering: {timing_stats['filter_total']:.2f}s total "
                    f"({timing_stats['filter_count']} calls, {avg_filter:.3f}s avg/call, "
                    f"{timing_stats['filter_total']/screen_total*100:.1f}% of total)"
                )
            if timing_stats["sentiment_count"] > 0:
                avg_sentiment = timing_stats["sentiment_total"] / timing_stats["sentiment_count"]
                logger.info(
                    f"  Sentiment filter: {timing_stats['sentiment_total']:.2f}s total "
                    f"({timing_stats['sentiment_count']} calls, {avg_sentiment:.3f}s avg/call, "
                    f"{timing_stats['sentiment_total']/screen_total*100:.1f}% of total)"
                )
            if timing_stats["ml_count"] > 0:
                avg_ml = timing_stats["ml_total"] / timing_stats["ml_count"]
                logger.info(
                    f"  ML filter: {timing_stats['ml_total']:.2f}s total "
                    f"({timing_stats['ml_count']} calls, {avg_ml:.3f}s avg/call, "
                    f"{timing_stats['ml_total']/screen_total*100:.1f}% of total)"
                )
            if timing_stats["score_count"] > 0:
                avg_score = timing_stats["score_total"] / timing_stats["score_count"]
                logger.info(
                    f"  Scoring/ranking: {timing_stats['score_total']:.2f}s total "
                    f"({timing_stats['score_count']} calls, {avg_score:.3f}s avg/call, "
                    f"{timing_stats['score_total']/screen_total*100:.1f}% of total)"
                )
            other_time = screen_total - (
                timing_stats["fetch_total"] + timing_stats["filter_total"] +
                timing_stats["sentiment_total"] + timing_stats["ml_total"] +
                timing_stats["score_total"]
            )
            if other_time > 0.1:  # Only log if significant
                logger.info(
                    f"  Other (sorting, cache, etc.): {other_time:.2f}s "
                    f"({other_time/screen_total*100:.1f}% of total)"
                )
            logger.info("=" * 60)
        else:
            # Still log total time even if detailed breakdown is disabled
            logger.info(f"Screening completed in {screen_total:.2f}s")

        # Log filtering statistics
        logger.info(
            f"Screening complete: {len(passing_stocks)}/{checked_count} stocks passed filters"
        )
        if use_advanced_filters:
            logger.info(
                f"  Filtered out: {filtered_stats['basic']} by basic, "
                f"{filtered_stats['sentiment']} by sentiment, "
                f"{filtered_stats['ml']} by ML"
            )

        # Provide helpful warning if no stocks passed filters
        if len(passing_stocks) == 0 and checked_count > 0:
            logger.warning("=" * 60)
            logger.warning("⚠️  NO STOCKS PASSED SCREENING FILTERS")
            logger.warning("=" * 60)
            logger.warning(f"Checked {checked_count} stocks from universe")
            logger.warning(f"Filters applied:")
            logger.warning(f"  - Price range: ${MIN_STOCK_PRICE:.2f} - ${MAX_STOCK_PRICE:.2f}")
            logger.warning(f"  - Minimum volume: {MIN_DAILY_VOLUME:,}")
            logger.warning(f"  - Maximum volatility: {MAX_STOCK_VOLATILITY:.1%}")
            
            # Provide specific recommendations based on filter values
            if MAX_STOCK_PRICE < 50:
                logger.warning(f"⚠️  MAX_STOCK_PRICE=${MAX_STOCK_PRICE:.2f} may be too low!")
                logger.warning(f"   Most liquid stocks in S&P 500/NASDAQ are priced $50-$500+")
                logger.warning(f"   Recommendation: Set MAX_STOCK_PRICE=1000.0 or higher")
            
            if MIN_STOCK_PRICE > 100:
                logger.warning(f"⚠️  MIN_STOCK_PRICE=${MIN_STOCK_PRICE:.2f} may be too high!")
                logger.warning(f"   This excludes many good trading opportunities")
                logger.warning(f"   Recommendation: Set MIN_STOCK_PRICE=5.0 to 20.0")
            
            if MIN_DAILY_VOLUME > 5000000:
                logger.warning(f"⚠️  MIN_DAILY_VOLUME={MIN_DAILY_VOLUME:,} may be too high!")
                logger.warning(f"   This limits to only the most heavily traded stocks")
                logger.warning(f"   Recommendation: Set MIN_DAILY_VOLUME=500000 to 1000000")
            
            logger.warning("")
            logger.warning("Suggested action: Adjust filter values in .env file:")
            logger.warning("  MIN_STOCK_PRICE=5.0")
            logger.warning("  MAX_STOCK_PRICE=1000.0")
            logger.warning("  MIN_DAILY_VOLUME=500000")
            logger.warning("=" * 60)

        # Check portfolio diversification if optimizer enabled
        if len(passing_stocks) >= 2 and self.portfolio_optimizer:
            div_score, div_reason = self.calculate_portfolio_diversification(
                passing_stocks
            )
            logger.info(f"Portfolio diversification: {div_reason}")

        # Cache results
        self.last_screened_stocks = passing_stocks
        self.last_screen_time = datetime.now()

        return passing_stocks

    def get_popular_stocks(self, count: int = 10) -> List[str]:
        """
        Get a list of stocks from the universe without filtering (fallback only).

        Used when screening yields no results (e.g. criteria too strict). Returns
        the first `count` symbols from the universe list, which is sorted
        alphabetically (from Wikipedia indices or FALLBACK_STOCK_UNIVERSE). This is
        NOT "best today" or "best yesterday" — it is a static alphabetical slice.
        For performance-based selection, use screening (ensure criteria pass) or
        extend this to sort by volume/momentum before slicing.

        Args:
            count: Number of stocks to return

        Returns:
            List of stock symbols (first N from universe, alphabetical order)
        """
        popular = self.stock_universe[:count]
        logger.info(f"Returning {len(popular)} popular stocks from universe")
        return popular

    def get_screened_or_fallback(self, max_results: int = 10) -> List[str]:
        """
        Get screened stocks, or fallback to popular stocks if screening fails

        Args:
            max_results: Maximum number of stocks to return

        Returns:
            List of stock symbols
        """
        try:
            screened = self.screen_stocks(max_results=max_results)

            if len(screened) > 0:
                return screened
            else:
                # Changed from WARNING to INFO - this is expected behavior, not an error
                # The screener falls back to popular stocks when criteria are too restrictive
                logger.info(
                    "No stocks passed screening criteria, using popular stocks from universe"
                )
                return self.get_popular_stocks(count=max_results)

        except Exception as e:
            logger.error(f"Stock screening failed: {e}")
            logger.info("Falling back to popular stocks from universe")
            return self.get_popular_stocks(count=max_results)

    def get_swing_trade_candidates(
        self,
        max_results: int = 10,
        sentiment_weight: float = 0.3,
        ml_weight: float = 0.4,
        diversification_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Get top swing trading candidates with comprehensive scoring

        This method combines:
        - Basic technical filters (price, volume, volatility)
        - Sentiment analysis (news sentiment scoring)
        - ML signal quality (win probability prediction)
        - Portfolio diversification (correlation analysis)

        Args:
            max_results: Maximum number of candidates to return
            sentiment_weight: Weight for sentiment score (0-1)
            ml_weight: Weight for ML quality score (0-1)
            diversification_weight: Weight for diversification (0-1)

        Returns:
            List of dictionaries with symbol and comprehensive scoring
        """
        logger.info("=" * 60)
        logger.info("SWING TRADE CANDIDATE SELECTION")
        logger.info("=" * 60)

        # First pass: Basic screening
        logger.info("\nPhase 1: Basic Technical Screening...")
        candidates = self.screen_stocks(
            max_results=max_results * 3, use_advanced_filters=False
        )

        if not candidates:
            logger.warning("No candidates passed basic screening")
            logger.warning("Attempting fallback to popular stocks from universe...")
            
            # Try to use popular stocks as fallback
            fallback_candidates = self.get_popular_stocks(count=max_results * 3)
            if fallback_candidates:
                logger.info(f"✓ Using {len(fallback_candidates)} popular stocks as fallback")
                candidates = fallback_candidates
            else:
                logger.error("No fallback stocks available - returning empty list")
                return []

        logger.info(f"  {len(candidates)} candidates passed basic screening")

        # Second pass: Enhanced scoring
        logger.info("\nPhase 2: Advanced Scoring (Sentiment + ML + Diversification)...")
        scored_candidates = []

        for symbol in candidates:
            scores = {
                "symbol": symbol,
                "sentiment_score": 0.5,  # Neutral default
                "ml_confidence": 0.5,
                "ml_win_probability": 0.5,
                "composite_score": 0.0,
            }

            # Get cached stock data
            stock_data = self._get_cached_data(symbol)
            if not stock_data:
                continue

            # Sentiment scoring
            if self.sentiment_analyzer:
                sentiment_passes, sentiment_reason, sentiment_data = (
                    self.filter_by_sentiment(symbol)
                )
                if sentiment_data:
                    # Normalize sentiment score from [-1, 1] to [0, 1]
                    scores["sentiment_score"] = (
                        sentiment_data["overall_score"] + 1
                    ) / 2
                    scores["sentiment_signal"] = sentiment_data["sentiment_signal"]
                    scores["article_count"] = sentiment_data["article_count"]

            # ML scoring
            if self.ml_filter and self.ml_filter.is_trained:
                ml_passes, ml_reason, ml_scores = self.filter_by_ml_quality(
                    symbol, stock_data
                )
                if ml_scores:
                    scores["ml_confidence"] = ml_scores["confidence"]
                    scores["ml_win_probability"] = ml_scores["win_probability"]

            # Calculate composite score
            scores["composite_score"] = (
                scores["sentiment_score"] * sentiment_weight
                + scores["ml_win_probability"] * ml_weight
                + 0.5 * diversification_weight  # Neutral diversification contribution
            )

            scored_candidates.append(scores)

        # Sort by composite score
        scored_candidates.sort(key=lambda x: x["composite_score"], reverse=True)

        # Take top candidates
        top_candidates = scored_candidates[:max_results]

        # Check portfolio diversification
        if len(top_candidates) >= 2 and self.portfolio_optimizer:
            symbols = [c["symbol"] for c in top_candidates]
            div_score, div_reason = self.calculate_portfolio_diversification(symbols)
            logger.info(f"\nPhase 3: Portfolio Analysis...")
            logger.info(f"  {div_reason}")

            # Add diversification score to candidates
            for candidate in top_candidates:
                candidate["portfolio_diversification"] = div_score

        # Log results
        logger.info("\n" + "=" * 60)
        logger.info(f"TOP {len(top_candidates)} SWING TRADE CANDIDATES")
        logger.info("=" * 60)
        for i, candidate in enumerate(top_candidates, 1):
            logger.info(f"{i}. {candidate['symbol']}")
            logger.info(f"   Composite Score: {candidate['composite_score']:.3f}")
            if "sentiment_signal" in candidate:
                logger.info(
                    f"   Sentiment: {candidate['sentiment_signal']} "
                    f"(score={candidate['sentiment_score']:.2f})"
                )
            if self.ml_filter:
                logger.info(
                    f"   ML: confidence={candidate['ml_confidence']:.2f}, "
                    f"win_prob={candidate['ml_win_probability']:.2f}"
                )
        logger.info("=" * 60)

        return top_candidates

    def refresh_universe(self, force: bool = False) -> int:
        """
        Refresh the stock universe from Wikipedia

        Args:
            force: Force refresh even if cache is valid

        Returns:
            Number of stocks in refreshed universe
        """
        logger.info("Refreshing stock universe...")
        self.stock_universe = get_stock_universe(
            use_cache=not force, force_refresh=force
        )
        logger.info(f"Universe refreshed: {len(self.stock_universe)} stocks")
        return len(self.stock_universe)

    def get_top_performers(
        self,
        max_results: int = 50,
        min_universe_size: int = 100,
        sentiment_weight: float = 0.3,
        ml_weight: float = 0.5,
        diversification_weight: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """
        Get top performing stocks ranked by win probability

        This method screens the stock universe (minimum 100 stocks) and ranks them
        by their probability of winning, combining:
        - ML win probability predictions
        - Sentiment analysis scores
        - Technical indicators
        - Diversification potential

        Args:
            max_results: Maximum number of top performers to return (default 50)
            min_universe_size: Minimum stocks in universe before screening (default 100)
            sentiment_weight: Weight for sentiment score (0-1)
            ml_weight: Weight for ML win probability (0-1)
            diversification_weight: Weight for diversification (0-1)

        Returns:
            List of dictionaries with stock data sorted by win probability (highest first)
            Each dict contains: symbol, win_probability, composite_score, sentiment_score,
            ml_confidence, price, volume, volatility
        """
        logger.info("=" * 60)
        logger.info("TOP PERFORMERS WATCHLIST GENERATION")
        logger.info("=" * 60)

        # Ensure we have enough stocks in universe
        if len(self.stock_universe) < min_universe_size:
            logger.warning(
                f"Stock universe has only {len(self.stock_universe)} stocks, "
                f"refreshing to meet minimum of {min_universe_size}"
            )
            self.refresh_universe(force=True)

        logger.info(f"\nScanning {len(self.stock_universe)} stocks from universe...")

        # Use get_swing_trade_candidates with larger pool
        # Request 3x the desired results to ensure we have enough after filtering
        candidates = self.get_swing_trade_candidates(
            max_results=max_results * 3,
            sentiment_weight=sentiment_weight,
            ml_weight=ml_weight,
            diversification_weight=diversification_weight,
        )

        # Enhance candidates with additional metrics
        top_performers = []
        for candidate in candidates:
            symbol = candidate["symbol"]

            # Get price and volume data
            stock_data = self._get_cached_data(symbol)
            if not stock_data:
                continue

            performer = {
                "symbol": symbol,
                "win_probability": candidate.get("ml_win_probability", 0.5),
                "composite_score": candidate.get("composite_score", 0.0),
                "sentiment_score": candidate.get("sentiment_score", 0.5),
                "ml_confidence": candidate.get("ml_confidence", 0.5),
                "sentiment_signal": candidate.get("sentiment_signal", "Neutral"),
                "price": stock_data.get("price", 0.0),
                "volume": stock_data.get("volume", 0),
                "volatility": stock_data.get("volatility", 0.0),
                "last_updated": datetime.now().isoformat(),
            }

            top_performers.append(performer)

        # Sort by win probability (highest first)
        top_performers.sort(key=lambda x: x["win_probability"], reverse=True)

        # Take top N
        top_performers = top_performers[:max_results]

        # Log results
        logger.info("\n" + "=" * 60)
        logger.info(f"TOP {len(top_performers)} PERFORMERS (Sorted by Win Probability)")
        logger.info("=" * 60)
        for i, performer in enumerate(top_performers[:10], 1):  # Show top 10 in logs
            logger.info(f"{i}. {performer['symbol']}")
            logger.info(f"   Win Probability: {performer['win_probability']:.2%}")
            logger.info(f"   Composite Score: {performer['composite_score']:.3f}")
            logger.info(f"   Price: ${performer['price']:.2f}")
            if performer.get("sentiment_signal"):
                logger.info(f"   Sentiment: {performer['sentiment_signal']}")

        if len(top_performers) > 10:
            logger.info(f"   ... and {len(top_performers) - 10} more")

        logger.info("=" * 60)

        return top_performers


# Convenience function for easy integration
def screen_for_trades(max_stocks: int = 10) -> List[str]:
    """
    Convenience function to screen for tradeable stocks

    Args:
        max_stocks: Maximum number of stocks to return

    Returns:
        List of stock symbols that pass screening criteria
    """
    screener = StockScreener()
    return screener.get_screened_or_fallback(max_results=max_stocks)


def get_top_performers_watchlist(max_stocks: int = 50) -> List[Dict[str, Any]]:
    """
    Convenience function to get top performing stocks for watchlist

    This function screens a large universe of stocks (100+) and returns
    the top performers ranked by win probability. Use this for the
    watchlist feature on the dashboard.

    Args:
        max_stocks: Maximum number of top performers to return (default 50)

    Returns:
        List of dictionaries with stock data sorted by win probability
        Each dict contains: symbol, win_probability, composite_score,
        sentiment_score, price, volume, etc.
    """
    screener = StockScreener()
    return screener.get_top_performers(max_results=max_stocks)


if __name__ == "__main__":
    # Test the screener
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("Testing Dynamic Stock Screener")
    print("=" * 60)

    # Test universe building
    print("\n1. Building stock universe...")
    universe = get_stock_universe(use_cache=False, force_refresh=True)
    print(f"   ✓ Universe size: {len(universe)} stocks")
    print(f"   Sample tickers: {', '.join(universe[:10])}")

    # Test screener
    print("\n2. Testing stock screener...")
    screener = StockScreener()
    print(f"   ✓ Screener initialized with {len(screener.stock_universe)} stocks")

    # Screen for tradeable stocks
    print("\n3. Screening for tradeable stocks...")
    print(f"   Criteria:")
    print(f"     - Price: ${MIN_STOCK_PRICE} - ${MAX_STOCK_PRICE}")
    print(f"     - Volume: {MIN_DAILY_VOLUME:,}+")
    print(f"     - Volatility: <{MAX_STOCK_VOLATILITY:.1%}")

    results = screener.screen_stocks(max_results=10)

    print(f"\n   ✓ Found {len(results)} tradeable stocks:")
    for i, symbol in enumerate(results, 1):
        print(f"     {i}. {symbol}")

    # Test cache
    print("\n4. Testing cache...")
    results2 = screener.screen_stocks(max_results=10)
    if results == results2:
        print("   ✓ Cache working correctly")
    else:
        print("   ✗ Cache not working as expected")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
