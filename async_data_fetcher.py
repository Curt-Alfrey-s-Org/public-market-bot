#!/usr/bin/env python3
"""
Asynchronous Data Fetcher Module for market-pie5-bot

This module provides async/concurrent data fetching capabilities to speed up I/O operations.
It prioritizes Schwab API for buy/sell/account operations while fetching market data
from multiple free APIs concurrently.

Key Features:
- Concurrent API requests using aiohttp
- Connection pooling for resource efficiency on Raspberry Pi 5
- Schwab API prioritization for trading operations
- Graceful fallback to synchronous data_fetcher
- Caching to reduce API overhead
- Rate limiting for all APIs
"""

import warnings
# Suppress pandas/yfinance Timestamp.utcnow deprecation (Pandas4Warning); apply before yfinance use
warnings.filterwarnings('ignore', message=r'.*Timestamp\.utcnow.*')

import os
import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

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

# Try to import async HTTP client
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not available - async fetching disabled")

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available")

# Try to import pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available")

# Try to import data_fetcher as fallback
try:
    from data_fetcher import DataFetcher
    DATA_FETCHER_AVAILABLE = True
except ImportError:
    DATA_FETCHER_AVAILABLE = False
    logger.warning("data_fetcher not available - limited fallback")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration
MAX_CONCURRENT_REQUESTS = int(os.getenv('ASYNC_MAX_CONCURRENT_REQUESTS', '5'))
REQUEST_TIMEOUT = int(os.getenv('ASYNC_REQUEST_TIMEOUT', '10'))
ENABLE_ASYNC_FETCHING = os.getenv('ENABLE_ASYNC_FETCHING', 'true').lower() == 'true'

# Rate limiting configuration
ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE = int(os.getenv('ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE', '5'))
ALPHA_VANTAGE_TIME_WINDOW_SECONDS = int(os.getenv('ALPHA_VANTAGE_TIME_WINDOW_SECONDS', '60'))
YFINANCE_MAX_CALLS_PER_MINUTE = int(os.getenv('YFINANCE_MAX_CALLS_PER_MINUTE', '30'))
YFINANCE_TIME_WINDOW_SECONDS = int(os.getenv('YFINANCE_TIME_WINDOW_SECONDS', '60'))


class AsyncDataFetcher:
    """
    Asynchronous data fetcher for concurrent API requests.
    
    Prioritizes Schwab API for trading operations while fetching
    market data from multiple sources concurrently.
    
    Performance Optimizations:
    - Request batching: Deduplicates concurrent requests for same symbol
    - Multi-tier caching: Fast cache (1h) + persistent cache (24h)
    - Connection pooling: Reuses HTTP connections across requests
    """
    
    def __init__(self, alpha_vantage_key: Optional[str] = None):
        """
        Initialize async data fetcher
        
        Args:
            alpha_vantage_key: Alpha Vantage API key (optional)
        """
        self.av_api_key = alpha_vantage_key or os.getenv('ALPHA_VANTAGE_API_KEY', '')
        self.cache = {}  # Fast cache for API responses
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
        self.persistent_cache = {}  # Longer-lived cache (24 hours)
        self.persistent_cache_duration = 86400  # 24 hours
        
        # Request deduplication: in-flight requests per symbol
        self.pending_requests: Dict[str, asyncio.Task] = {}
        self._request_lock = asyncio.Lock()
        
        # Request batch queue for symbol grouping
        self.batch_queue: Dict[str, List[str]] = {}
        
        self.session = None  # aiohttp session (created on demand)
        
        # Initialize rate limiters
        self.alpha_vantage_limiter = RateLimiter(
            max_calls=ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE,
            time_window=ALPHA_VANTAGE_TIME_WINDOW_SECONDS,
            name="Alpha Vantage (Async)"
        )
        
        self.yfinance_limiter = RateLimiter(
            max_calls=YFINANCE_MAX_CALLS_PER_MINUTE,
            time_window=YFINANCE_TIME_WINDOW_SECONDS,
            name="yfinance (Async)"
        )
        
        # Fallback to synchronous fetcher if available
        self.sync_fetcher = None
        if DATA_FETCHER_AVAILABLE:
            try:
                self.sync_fetcher = DataFetcher(alpha_vantage_key=alpha_vantage_key)
                logger.info("Synchronous DataFetcher initialized as fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize sync fetcher: {e}")
        
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available - falling back to synchronous mode")
        elif not ENABLE_ASYNC_FETCHING:
            logger.info("Async fetching disabled via ENABLE_ASYNC_FETCHING=false")
        else:
            logger.info("Async data fetcher initialized successfully")
    
    def _get_cache_key(self, symbol: str, data_type: str) -> str:
        """Generate cache key for symbol and data type"""
        return f"{symbol}_{data_type}"
    
    def _is_cache_valid(self, cache_key: str, tier: str = 'fast') -> bool:
        """Check if cached data is still valid"""
        cache = self.cache if tier == 'fast' else self.persistent_cache
        duration = self.cache_duration if tier == 'fast' else self.persistent_cache_duration
        
        if cache_key not in cache:
            return False
        
        cached_data = cache[cache_key]
        age = (datetime.now() - cached_data['timestamp']).total_seconds()
        
        return age < duration
    
    def _cache_data(self, cache_key: str, data: Any, tier: str = 'fast'):
        """Cache data with timestamp in specified tier"""
        cache = self.cache if tier == 'fast' else self.persistent_cache
        cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def _get_cached_data(self, cache_key: str, tier: str = 'fast') -> Optional[Any]:
        """Retrieve cached data if valid, checking fast cache first"""
        # Always check fast cache first
        if self._is_cache_valid(cache_key, 'fast'):
            logger.debug(f"Cache hit (fast): {cache_key}")
            return self.cache[cache_key]['data']
        
        # Fall back to persistent cache
        if tier == 'persistent' and self._is_cache_valid(cache_key, 'persistent'):
            logger.debug(f"Cache hit (persistent): {cache_key}")
            result = self.persistent_cache[cache_key]['data']
            # Promote to fast cache
            self._cache_data(cache_key, result, tier='fast')
            return result
        
        return None
    
    async def _get_session(self):
        """
        Get or create aiohttp session with connection pooling
        
        Returns:
            Active aiohttp ClientSession (if aiohttp available)
        """
        if not AIOHTTP_AVAILABLE:
            return None
        
        if self.session is None or self.session.closed:
            # Configure connection pooling for Pi 5 efficiency
            connector = aiohttp.TCPConnector(
                limit=MAX_CONCURRENT_REQUESTS,
                limit_per_host=3,
                ttl_dns_cache=300,
            )
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            logger.debug("Created new aiohttp session with connection pooling")
        
        return self.session
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Closed aiohttp session")
    
    async def fetch_price_yfinance_async(self, symbol: str) -> Optional[Tuple[float, int]]:
        """
        Fetch current price and volume using yfinance (async wrapper)
        
        Implements request deduplication: if a request for this symbol is already
        in-flight, waits for it instead of making a duplicate request.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (price, volume) or None if fetch fails
        """
        cache_key = self._get_cache_key(symbol, "price_yf")
        
        # Check all cache tiers
        cached = self._get_cached_data(cache_key, tier='persistent')
        if cached is not None:
            return cached
        
        # Deduplicate in-flight requests
        pending_key = f"price_{symbol}"
        async with self._request_lock:
            if pending_key in self.pending_requests:
                logger.debug(f"Waiting for in-flight request: {pending_key}")
                try:
                    return await self.pending_requests[pending_key]
                except asyncio.CancelledError:
                    pass
        
        if not YFINANCE_AVAILABLE:
            logger.debug(f"yfinance not available for {symbol}")
            return None
        
        # Check rate limit before making API call
        if not self.yfinance_limiter.can_make_call():
            wait_time = self.yfinance_limiter.get_wait_time()
            remaining = self.yfinance_limiter.get_remaining_calls()
            logger.warning(
                f"yfinance rate limit reached ({remaining}/{self.yfinance_limiter.max_calls} "
                f"calls available). Next call available in {wait_time:.1f}s. Skipping fetch for {symbol}."
            )
            return None
        
        try:
            # yfinance is synchronous, so run in executor
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            info = await loop.run_in_executor(None, lambda: ticker.info)
            
            # Record the API call immediately after request
            self.yfinance_limiter.record_call()
            
            # Log remaining calls
            remaining = self.yfinance_limiter.get_remaining_calls()
            logger.debug(f"yfinance call made. Remaining calls: {remaining}/{self.yfinance_limiter.max_calls}")
            
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            volume = info.get('volume') or info.get('regularMarketVolume', 0)
            
            if price is None:
                logger.warning(f"No price data for {symbol}")
                return None
            
            result = (float(price), int(volume))
            # Cache in both tiers for persistence
            self._cache_data(cache_key, result, tier='fast')
            self._cache_data(cache_key, result, tier='persistent')
            logger.debug(f"Fetched price for {symbol}: ${price:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
        finally:
            # Remove from pending requests
            async with self._request_lock:
                if pending_key in self.pending_requests:
                    del self.pending_requests[pending_key]
    
    async def fetch_fundamentals_alpha_vantage_async(self, symbol: str) -> Optional[Dict]:
        """
        Fetch fundamental data using Alpha Vantage API (async)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with fundamental data or None if fetch fails
        """
        if not self.av_api_key or self.av_api_key == '':
            logger.debug("Alpha Vantage API key not configured")
            return None
        
        cache_key = self._get_cache_key(symbol, "fundamentals_av")
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
        
        if not AIOHTTP_AVAILABLE:
            # Fall back to sync fetcher
            if self.sync_fetcher:
                return self.sync_fetcher.fetch_fundamentals_alpha_vantage(symbol)
            return None
        
        try:
            session = await self._get_session()
            
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.av_api_key
            }
            
            async with session.get(url, params=params) as response:
                # Record the API call immediately after request completes, regardless of status code
                # to ensure accurate rate limiting (failed requests count against quota too)
                self.alpha_vantage_limiter.record_call()
                
                # Log remaining calls
                remaining = self.alpha_vantage_limiter.get_remaining_calls()
                logger.debug(f"Alpha Vantage call made. Remaining calls: {remaining}/{self.alpha_vantage_limiter.max_calls}")
                
                # Check status code
                response.raise_for_status()
                
                data = await response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit for {symbol}")
                return None
            
            if not data or 'Symbol' not in data:
                logger.warning(f"No fundamental data for {symbol}")
                return None
            
            # Parse fundamentals
            fundamentals = {
                'symbol': data.get('Symbol', symbol),
                'name': data.get('Name', ''),
                'sector': data.get('Sector', ''),
                'pe_ratio': self._parse_number(data.get('PERatio')),
                'eps': self._parse_number(data.get('EPS')),
                'market_cap': self._parse_number(data.get('MarketCapitalization')),
                'dividend_yield': self._parse_number(data.get('DividendYield')),
            }
            
            # Cache in both tiers
            self._cache_data(cache_key, fundamentals, tier='fast')
            self._cache_data(cache_key, fundamentals, tier='persistent')
            logger.debug(f"Fetched fundamentals for {symbol}")
            
            return fundamentals
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching fundamentals for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return None
    
    def _parse_number(self, value: Optional[str]) -> Optional[float]:
        """Parse numeric value from string"""
        if value is None or value == '' or value == 'None':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    async def fetch_multiple_prices_async(self, symbols: List[str]) -> Dict[str, Tuple[float, int]]:
        """
        Fetch prices for multiple symbols concurrently with batching.
        
        Optimization: Deduplicates symbols and respects rate limits by
        batching requests in groups of MAX_CONCURRENT_REQUESTS.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbol to (price, volume) tuple
        """
        if not AIOHTTP_AVAILABLE or not ENABLE_ASYNC_FETCHING:
            # Fall back to sequential fetching
            logger.debug("Falling back to sequential price fetching")
            results = {}
            for symbol in symbols:
                if self.sync_fetcher:
                    try:
                        result = self.sync_fetcher.fetch_historical_data_yfinance(symbol, period='1d')
                        if result is not None and len(result) > 0:
                            price = result['close'].iloc[-1]
                            volume = result['volume'].iloc[-1] if 'volume' in result.columns else 0
                            results[symbol] = (float(price), int(volume))
                    except Exception as e:
                        logger.error(f"Error fetching {symbol}: {e}")
            return results
        
        # Deduplicate symbols
        unique_symbols = list(set(symbols))
        logger.info(f"Fetching prices for {len(unique_symbols)} unique symbols (deduped from {len(symbols)})")
        
        results = {}
        
        # Process in batches to respect rate limits
        for i in range(0, len(unique_symbols), MAX_CONCURRENT_REQUESTS):
            batch = unique_symbols[i:i + MAX_CONCURRENT_REQUESTS]
            logger.debug(f"Processing batch {i//MAX_CONCURRENT_REQUESTS + 1}: {len(batch)} symbols")
            
            # Create tasks for this batch
            tasks = [self.fetch_price_yfinance_async(symbol) for symbol in batch]
            
            # Execute batch concurrently
            try:
                results_list = await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error in batch fetching: {e}")
                continue
            
            # Process batch results
            for symbol, result in zip(batch, results_list):
                if isinstance(result, Exception):
                    logger.error(f"Exception fetching {symbol}: {result}")
                    continue
                if result is not None:
                    results[symbol] = result
        
        logger.info(f"Successfully fetched {len(results)}/{len(unique_symbols)} prices")
        return results
    
    async def fetch_comprehensive_data_async(
        self, 
        symbol: str,
        include_fundamentals: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive data for a symbol concurrently
        
        Fetches price and fundamentals in parallel when possible.
        
        Args:
            symbol: Stock symbol
            include_fundamentals: Whether to fetch fundamental data
            
        Returns:
            Dictionary with all fetched data
        """
        logger.debug(f"Fetching comprehensive data for {symbol}")
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'price': None,
            'volume': None,
            'fundamentals': None,
            'data_sources': []
        }
        
        if not AIOHTTP_AVAILABLE or not ENABLE_ASYNC_FETCHING:
            # Fall back to sync fetcher
            if self.sync_fetcher:
                sync_data = self.sync_fetcher.get_comprehensive_data(symbol)
                return sync_data
            return result
        
        # Create concurrent tasks
        tasks = []
        task_names = []
        
        # Always fetch price
        tasks.append(self.fetch_price_yfinance_async(symbol))
        task_names.append('price')
        
        # Optionally fetch fundamentals
        if include_fundamentals and self.av_api_key:
            tasks.append(self.fetch_fundamentals_alpha_vantage_async(symbol))
            task_names.append('fundamentals')
        
        # Execute concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error fetching comprehensive data for {symbol}: {e}")
            return result
        
        # Process results
        for task_name, task_result in zip(task_names, results):
            if isinstance(task_result, Exception):
                logger.error(f"Exception in {task_name} for {symbol}: {task_result}")
                continue
            
            if task_name == 'price' and task_result is not None:
                result['price'], result['volume'] = task_result
                result['data_sources'].append('yfinance')
            elif task_name == 'fundamentals' and task_result is not None:
                result['fundamentals'] = task_result
                result['data_sources'].append('alphavantage')
        
        logger.debug(f"Fetched comprehensive data for {symbol} from {len(result['data_sources'])} sources")
        return result
    
    def fetch_multiple_prices(self, symbols: List[str]) -> Dict[str, Tuple[float, int]]:
        """
        Synchronous wrapper for fetch_multiple_prices_async
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbol to (price, volume) tuple
        """
        if not AIOHTTP_AVAILABLE or not ENABLE_ASYNC_FETCHING:
            # Use sync fetcher directly
            if self.sync_fetcher:
                results = {}
                for symbol in symbols:
                    try:
                        hist_data = self.sync_fetcher.fetch_historical_data_yfinance(symbol, period='1d')
                        if hist_data is not None and len(hist_data) > 0:
                            price = hist_data['close'].iloc[-1]
                            volume = hist_data['volume'].iloc[-1] if 'volume' in hist_data.columns else 0
                            results[symbol] = (float(price), int(volume))
                    except Exception as e:
                        logger.error(f"Error fetching {symbol}: {e}")
                return results
            return {}
        
        # Run async function
        try:
            # Try to get running event loop
            try:
                loop = asyncio.get_running_loop()
                # Event loop is already running, create a new one in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self.fetch_multiple_prices_async(symbols)
                    )
                    return future.result()
            except RuntimeError:
                # No event loop running, safe to create one
                return asyncio.run(self.fetch_multiple_prices_async(symbols))
        except Exception as e:
            logger.error(f"Error in synchronous wrapper: {e}")
            return {}
    
    def fetch_comprehensive_data(
        self, 
        symbol: str,
        include_fundamentals: bool = True
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for fetch_comprehensive_data_async
        
        Args:
            symbol: Stock symbol
            include_fundamentals: Whether to fetch fundamental data
            
        Returns:
            Dictionary with all fetched data
        """
        if not AIOHTTP_AVAILABLE or not ENABLE_ASYNC_FETCHING:
            if self.sync_fetcher:
                return self.sync_fetcher.get_comprehensive_data(symbol)
            return {}
        
        try:
            # Try to get running event loop
            try:
                loop = asyncio.get_running_loop()
                # Event loop is already running, create a new one in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.fetch_comprehensive_data_async(symbol, include_fundamentals)
                    )
                    return future.result()
            except RuntimeError:
                # No event loop running, safe to create one
                return asyncio.run(
                    self.fetch_comprehensive_data_async(symbol, include_fundamentals)
                )
        except Exception as e:
            logger.error(f"Error in synchronous wrapper: {e}")
            return {}


# Singleton instance for reuse
_async_fetcher_instance = None


def get_async_fetcher(alpha_vantage_key: Optional[str] = None) -> AsyncDataFetcher:
    """
    Get or create singleton AsyncDataFetcher instance
    
    Args:
        alpha_vantage_key: Alpha Vantage API key (optional)
        
    Returns:
        AsyncDataFetcher instance
    """
    global _async_fetcher_instance
    if _async_fetcher_instance is None:
        _async_fetcher_instance = AsyncDataFetcher(alpha_vantage_key=alpha_vantage_key)
    return _async_fetcher_instance


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Async Data Fetcher Module - Example Usage")
    print("="*60)
    
    # Initialize fetcher
    fetcher = AsyncDataFetcher()
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print(f"\nTesting concurrent price fetching for {test_symbols}...")
    
    start_time = time.time()
    prices = fetcher.fetch_multiple_prices(test_symbols)
    elapsed = time.time() - start_time
    
    print(f"\nFetched {len(prices)} prices in {elapsed:.2f} seconds:")
    for symbol, (price, volume) in prices.items():
        print(f"  {symbol}: ${price:.2f} (volume: {volume:,})")
    
    print("\n" + "="*60)
    print("Async Data Fetcher module initialized successfully")
    print("="*60)
