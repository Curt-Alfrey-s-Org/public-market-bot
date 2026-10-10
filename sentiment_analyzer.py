#!/usr/bin/env python3
"""
Sentiment Analysis Module for market-pie5-bot
Integrates news sentiment analysis for trading decisions
"""

import os
import requests
import logging
import stat
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time

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

# Try to import aiohttp for async support
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not available - async sentiment analysis disabled")

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

# News API configuration
NEWS_API_KEY = get_decrypted_env('NEWS_API_KEY', '')
NEWS_API_BASE_URL = "https://newsapi.org/v2"

# Alternative: Finnhub for financial news
FINNHUB_API_KEY = get_decrypted_env('FINNHUB_API_KEY', '')
FINNHUB_API_BASE_URL = "https://finnhub.io/api/v1"

# Sentiment analysis method - supported: 'vader', 'textblob', or any other value (falls back to neutral)
# This is the DETERMINISTIC FALLBACK used when the ALFa AI brain is unavailable.
SENTIMENT_METHOD = os.getenv('SENTIMENT_METHOD', 'vader')

# Primary sentiment path: the ALFa AI brain (LiteLLM). One batched call per
# symbol over its headlines -- the brain understands financial context far
# better than the lexicon fallback. Set SENTIMENT_USE_BRAIN=false to force the
# local VADER/TextBlob path. The brain is only used when LITELLM_ENABLED=true;
# on any brain error the code falls back to the local method automatically.
SENTIMENT_USE_BRAIN = os.getenv('SENTIMENT_USE_BRAIN', 'true').lower() in ('true', '1', 'yes')

# Max headlines sent to the brain in a single sentiment call (cost/latency cap).
SENTIMENT_BRAIN_MAX_HEADLINES = int(os.getenv('SENTIMENT_BRAIN_MAX_HEADLINES', '15'))

# Maximum articles to use for confidence calculation
MAX_ARTICLES_FOR_FULL_CONFIDENCE = 20

# Rate limiting configuration
# NewsAPI free tier: 100 requests per 24 hours (50 every 12 hours)
NEWS_API_MAX_CALLS_PER_DAY = int(os.getenv('NEWS_API_MAX_CALLS_PER_DAY', '100'))
NEWS_API_TIME_WINDOW = int(os.getenv('NEWS_API_TIME_WINDOW_HOURS', '24')) * 3600  # Convert to seconds

# Finnhub free tier: 60 API calls per minute
FINNHUB_MAX_CALLS_PER_MINUTE = int(os.getenv('FINNHUB_MAX_CALLS_PER_MINUTE', '60'))
FINNHUB_TIME_WINDOW = int(os.getenv('FINNHUB_TIME_WINDOW_SECONDS', '60'))  # seconds

# Try to import sentiment analysis libraries
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
    logger.info("VADER sentiment analyzer loaded successfully")
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("VADER sentiment analyzer not available")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
    logger.info("TextBlob sentiment analyzer loaded successfully")
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob sentiment analyzer not available")


class SentimentAnalyzer:
    """
    Sentiment analysis for stock symbols using news articles
    Provides sentiment scores to inform trading decisions
    """
    
    def __init__(self, news_api_key: Optional[str] = None, 
                 finnhub_api_key: Optional[str] = None,
                 method: str = SENTIMENT_METHOD):
        """
        Initialize sentiment analyzer
        
        Args:
            news_api_key: NewsAPI.org API key (optional, uses env var if not provided)
            finnhub_api_key: Finnhub API key (optional, uses env var if not provided)
            method: Sentiment analysis method ('vader' or 'textblob')
        """
        self.news_api_key = news_api_key or NEWS_API_KEY
        self.finnhub_api_key = finnhub_api_key or FINNHUB_API_KEY
        self.method = method
        
        # Initialize sentiment analyzer based on method
        self.vader_analyzer = None
        if method == 'vader' and VADER_AVAILABLE:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("Using VADER for sentiment analysis")
        elif method == 'textblob' and TEXTBLOB_AVAILABLE:
            logger.info("Using TextBlob for sentiment analysis")
        else:
            logger.warning(f"Sentiment method '{method}' not available, using fallback")
        
        # Cache for sentiment data
        self.sentiment_cache = {}
        self.cache_duration = 3600  # 1 hour cache
        
        # API availability flags
        self.news_api_available = bool(self.news_api_key and self.news_api_key != '')
        self.finnhub_available = bool(self.finnhub_api_key and self.finnhub_api_key != '')
        
        # Initialize rate limiters
        self.news_api_limiter = RateLimiter(
            max_calls=NEWS_API_MAX_CALLS_PER_DAY,
            time_window=NEWS_API_TIME_WINDOW,
            name="NewsAPI"
        )
        self.finnhub_limiter = RateLimiter(
            max_calls=FINNHUB_MAX_CALLS_PER_MINUTE,
            time_window=FINNHUB_TIME_WINDOW,
            name="Finnhub"
        )
        
        if self.news_api_available:
            logger.info("NewsAPI configured for news fetching")
        if self.finnhub_available:
            logger.info("Finnhub configured for financial news")
        
        if not (self.news_api_available or self.finnhub_available):
            logger.warning("No news API keys configured - sentiment analysis limited")
    
    def _get_cache_key(self, symbol: str) -> str:
        """Generate cache key for symbol"""
        return f"{symbol}_sentiment"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.sentiment_cache:
            return False
        
        cached_data = self.sentiment_cache[cache_key]
        age = (datetime.now() - cached_data['timestamp']).total_seconds()
        
        return age < self.cache_duration
    
    def _cache_sentiment(self, cache_key: str, data: Dict):
        """Cache sentiment data with timestamp"""
        self.sentiment_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def _get_cached_sentiment(self, cache_key: str) -> Optional[Dict]:
        """Retrieve cached sentiment if valid"""
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached sentiment for {cache_key}")
            return self.sentiment_cache[cache_key]['data']
        return None
    
    def fetch_news_newsapi(self, symbol: str, days: int = 7) -> List[Dict]:
        """
        Fetch news articles for a symbol from NewsAPI.org
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back (default: 7)
            
        Returns:
            List of news articles with title, description, source, publishedAt
        """
        if not self.news_api_available:
            logger.warning("NewsAPI key not configured")
            return []
        
        # Check rate limit before making API call
        if not self.news_api_limiter.can_make_call():
            wait_time = self.news_api_limiter.get_wait_time()
            logger.warning(
                f"NewsAPI rate limit reached (0/{NEWS_API_MAX_CALLS_PER_DAY} calls available). "
                f"Next call available in {wait_time/3600:.1f} hours. Skipping fetch for {symbol}."
            )
            return []
        
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # Build query - search for company name and symbol
            query = f"{symbol} OR stock OR shares"
            
            # API endpoint
            url = f"{NEWS_API_BASE_URL}/everything"
            params = {
                'q': query,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 50,  # Max articles
                'apiKey': self.news_api_key
            }
            
            logger.debug(f"Fetching news for {symbol} from NewsAPI...")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # Record the API call only on successful responses.
                # Note: NewsAPI counts most failed requests against your quota,
                # but we only track successful calls locally for simplicity.
                self.news_api_limiter.record_call()
                remaining = self.news_api_limiter.get_remaining_calls()
                logger.debug(
                    f"NewsAPI call made. Remaining calls: {remaining}/{NEWS_API_MAX_CALLS_PER_DAY}"
                )
                
                data = response.json()
                articles = data.get('articles', [])
                logger.info(f"Fetched {len(articles)} articles for {symbol} from NewsAPI")
                return articles
            elif response.status_code == 429:
                # Record 429 responses as they still count against the NewsAPI quota.
                self.news_api_limiter.record_call()
                remaining = self.news_api_limiter.get_remaining_calls()
                logger.debug(
                    f"NewsAPI 429 received. Remaining calls: {remaining}/{NEWS_API_MAX_CALLS_PER_DAY}"
                )
                logger.error(f"NewsAPI error 429 (rate limited): {response.text}")
                return []
            else:
                # Do not record other non-success responses in the local limiter to avoid
                # over-constraining our own rate limit for transient or client-side issues.
                # Log 401 errors at debug level since they're expected when API keys are missing/invalid
                if response.status_code == 401:
                    logger.debug(f"NewsAPI error {response.status_code}: {response.text}")
                else:
                    logger.error(f"NewsAPI error {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch news from NewsAPI for {symbol}: {e}")
            return []
    
    def fetch_news_finnhub(self, symbol: str, days: int = 7) -> List[Dict]:
        """
        Fetch company news for a symbol from Finnhub
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back (default: 7)
            
        Returns:
            List of news articles with headline, summary, source, datetime
        """
        if not self.finnhub_available:
            logger.warning("Finnhub API key not configured")
            return []
        
        # Check rate limit before making API call
        if not self.finnhub_limiter.can_make_call():
            wait_time = self.finnhub_limiter.get_wait_time()
            logger.warning(
                f"Finnhub rate limit reached (0/{FINNHUB_MAX_CALLS_PER_MINUTE} calls available). "
                f"Next call available in {wait_time:.1f} seconds. Skipping fetch for {symbol}."
            )
            return []
        
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # API endpoint for company news
            url = f"{FINNHUB_API_BASE_URL}/company-news"
            params = {
                'symbol': symbol,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'token': self.finnhub_api_key
            }
            
            logger.debug(f"Fetching news for {symbol} from Finnhub...")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # Record the API call only on successful responses.
                self.finnhub_limiter.record_call()
                remaining = self.finnhub_limiter.get_remaining_calls()
                logger.debug(f"Finnhub call made. Remaining calls: {remaining}/{FINNHUB_MAX_CALLS_PER_MINUTE}")
                
                articles = response.json()
                logger.info(f"Fetched {len(articles)} articles for {symbol} from Finnhub")
                return articles
            elif response.status_code == 429:
                # Record 429 responses as they still count against the Finnhub quota.
                self.finnhub_limiter.record_call()
                remaining = self.finnhub_limiter.get_remaining_calls()
                logger.debug(f"Finnhub 429 received. Remaining calls: {remaining}/{FINNHUB_MAX_CALLS_PER_MINUTE}")
                logger.error(f"Finnhub error 429 (rate limited): {response.text}")
                return []
            else:
                # Do not record other non-success responses in the local limiter.
                # Log 401 errors at debug level since they're expected when API keys are missing/invalid
                if response.status_code == 401:
                    logger.debug(f"Finnhub error {response.status_code}: {response.text}")
                else:
                    logger.error(f"Finnhub error {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch news from Finnhub for {symbol}: {e}")
            return []
    
    # ====================================================================
    # ASYNC METHODS FOR CONCURRENT API CALLS
    # ====================================================================
    
    async def fetch_news_newsapi_async(self, symbol: str, days: int = 7) -> List[Dict]:
        """
        Fetch company news for a symbol from NewsAPI (async version)
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back (default: 7)
            
        Returns:
            List of news articles with title, description, source, publishedAt
        """
        if not self.news_api_available:
            logger.debug("NewsAPI key not configured")
            return []
        
        if not AIOHTTP_AVAILABLE:
            # Fall back to synchronous version
            logger.debug("aiohttp not available, using synchronous NewsAPI fetch")
            return self.fetch_news_newsapi(symbol, days)
        
        # Check rate limit before making API call
        if not self.news_api_limiter.can_make_call():
            wait_time = self.news_api_limiter.get_wait_time()
            logger.warning(
                f"NewsAPI rate limit reached (0/{NEWS_API_MAX_CALLS_PER_DAY} calls available). "
                f"Next call available in {wait_time/3600:.1f} hours. Skipping fetch for {symbol}."
            )
            return []
        
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # Build query
            query = f"{symbol} OR stock OR shares"
            
            # API endpoint
            url = f"{NEWS_API_BASE_URL}/everything"
            params = {
                'q': query,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 50,
                'apiKey': self.news_api_key
            }
            
            logger.debug(f"Fetching news for {symbol} from NewsAPI (async)...")
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        # Record the API call only on successful responses.
                        self.news_api_limiter.record_call()
                        remaining = self.news_api_limiter.get_remaining_calls()
                        logger.debug(f"NewsAPI call made. Remaining calls: {remaining}/{NEWS_API_MAX_CALLS_PER_DAY}")
                        
                        data = await response.json()
                        articles = data.get('articles', [])
                        logger.info(f"Fetched {len(articles)} articles for {symbol} from NewsAPI (async)")
                        return articles
                    elif response.status == 429:
                        # Record 429 responses as they still count against the NewsAPI quota.
                        self.news_api_limiter.record_call()
                        remaining = self.news_api_limiter.get_remaining_calls()
                        logger.debug(f"NewsAPI 429 received. Remaining calls: {remaining}/{NEWS_API_MAX_CALLS_PER_DAY}")
                        text = await response.text()
                        logger.error(f"NewsAPI error 429 (rate limited): {text}")
                        return []
                    else:
                        # Do not record other non-success responses.
                        # Log 401 errors at debug level since they're expected when API keys are missing/invalid
                        text = await response.text()
                        if response.status == 401:
                            logger.debug(f"NewsAPI error {response.status}: {text}")
                        else:
                            logger.error(f"NewsAPI error {response.status}: {text}")
                        return []
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching news from NewsAPI for {symbol}")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch news from NewsAPI for {symbol} (async): {e}")
            return []
    
    async def fetch_news_finnhub_async(self, symbol: str, days: int = 7) -> List[Dict]:
        """
        Fetch company news for a symbol from Finnhub (async version)
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back (default: 7)
            
        Returns:
            List of news articles with headline, summary, source, datetime
        """
        if not self.finnhub_available:
            logger.debug("Finnhub API key not configured")
            return []
        
        if not AIOHTTP_AVAILABLE:
            # Fall back to synchronous version
            logger.debug("aiohttp not available, using synchronous Finnhub fetch")
            return self.fetch_news_finnhub(symbol, days)
        
        # Check rate limit before making API call
        if not self.finnhub_limiter.can_make_call():
            wait_time = self.finnhub_limiter.get_wait_time()
            remaining = self.finnhub_limiter.get_remaining_calls()
            logger.warning(
                f"Finnhub rate limit reached (0/{FINNHUB_MAX_CALLS_PER_MINUTE} calls available). "
                f"Next call available in {wait_time:.1f} seconds. Skipping fetch for {symbol}."
            )
            return []
        
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # API endpoint for company news
            url = f"{FINNHUB_API_BASE_URL}/company-news"
            params = {
                'symbol': symbol,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'token': self.finnhub_api_key
            }
            
            logger.debug(f"Fetching news for {symbol} from Finnhub (async)...")
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        # Record the API call only on successful responses.
                        self.finnhub_limiter.record_call()
                        remaining = self.finnhub_limiter.get_remaining_calls()
                        logger.debug(f"Finnhub call made. Remaining calls: {remaining}/{FINNHUB_MAX_CALLS_PER_MINUTE}")
                        
                        articles = await response.json()
                        logger.info(f"Fetched {len(articles)} articles for {symbol} from Finnhub (async)")
                        return articles
                    elif response.status == 429:
                        # Record 429 responses as they still count against the Finnhub quota.
                        self.finnhub_limiter.record_call()
                        remaining = self.finnhub_limiter.get_remaining_calls()
                        logger.debug(f"Finnhub 429 received. Remaining calls: {remaining}/{FINNHUB_MAX_CALLS_PER_MINUTE}")
                        text = await response.text()
                        logger.error(f"Finnhub error 429 (rate limited): {text}")
                        return []
                    else:
                        # Do not record other non-success responses.
                        # Log 401 errors at debug level since they're expected when API keys are missing/invalid
                        text = await response.text()
                        if response.status == 401:
                            logger.debug(f"Finnhub error {response.status}: {text}")
                        else:
                            logger.error(f"Finnhub error {response.status}: {text}")
                        return []
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching news from Finnhub for {symbol}")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch news from Finnhub for {symbol} (async): {e}")
            return []
    
    async def get_sentiment_score_async(self, symbol: str, days: int = 7) -> Dict:
        """
        Get sentiment score for a stock symbol (async version with concurrent API calls)
        
        This method fetches news from both Finnhub and NewsAPI concurrently,
        significantly reducing wait time compared to sequential fetching.
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
            
        Returns:
            Dictionary with:
            - overall_score: Aggregated sentiment score (-1 to 1)
            - positive_ratio: Ratio of positive articles
            - negative_ratio: Ratio of negative articles
            - neutral_ratio: Ratio of neutral articles
            - article_count: Number of articles analyzed
            - sentiment_signal: 'BULLISH', 'BEARISH', or 'NEUTRAL'
        """
        # Check cache first
        cache_key = self._get_cache_key(symbol)
        cached = self._get_cached_sentiment(cache_key)
        if cached:
            return cached
        
        if not AIOHTTP_AVAILABLE:
            # Fall back to synchronous version
            logger.debug("aiohttp not available, using synchronous sentiment analysis")
            return self.get_sentiment_score(symbol, days)
        
        logger.info(f"Analyzing sentiment for {symbol} (async with concurrent fetching)...")
        
        # Fetch news from both sources concurrently
        tasks = []
        if self.finnhub_available:
            tasks.append(self.fetch_news_finnhub_async(symbol, days))
        if self.news_api_available:
            tasks.append(self.fetch_news_newsapi_async(symbol, days))
        
        if not tasks:
            logger.warning(f"No news APIs configured for {symbol}")
            result = {
                'overall_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 1.0,
                'article_count': 0,
                'sentiment_signal': 'NEUTRAL',
                'confidence': 0.0
            }
            self._cache_sentiment(cache_key, result)
            return result
        
        # Execute API calls concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in concurrent news fetching for {symbol}: {e}")
            results = []
        
        # Combine articles from all sources
        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"News fetch exception for {symbol}: {result}")
        
        if not articles:
            logger.debug(f"No news articles found for {symbol}")
            result = {
                'overall_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 1.0,
                'article_count': 0,
                'sentiment_signal': 'NEUTRAL',
                'confidence': 0.0
            }
            self._cache_sentiment(cache_key, result)
            return result
        
        # Primary path: ALFa AI brain (one batched call). The brain client is
        # blocking (requests), so run it in a thread to avoid stalling the loop.
        # Falls back to the local VADER aggregation below on any brain failure.
        try:
            loop = asyncio.get_event_loop()
            brain_result = await loop.run_in_executor(
                None, self._brain_sentiment, symbol, articles
            )
        except Exception as e:
            logger.debug(f"Brain sentiment executor failed for {symbol}: {e}")
            brain_result = None
        if brain_result is not None:
            self._cache_sentiment(cache_key, brain_result)
            return brain_result
        
        # Analyze sentiment for each article (synchronous - fast operation)
        sentiments = []
        for article in articles:
            # Extract text from article
            text = ""
            if 'headline' in article:  # Finnhub format
                headline = article.get('headline') or ''
                summary = article.get('summary') or ''
                text = str(headline) + " " + str(summary)
            elif 'title' in article:  # NewsAPI format
                title = article.get('title') or ''
                description = article.get('description') or ''
                text = str(title) + " " + str(description)
            
            if text.strip():
                sentiment = self.analyze_sentiment(text)
                sentiments.append(sentiment)
        
        if not sentiments:
            logger.warning(f"No sentiment data extracted for {symbol}")
            result = {
                'overall_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 1.0,
                'article_count': 0,
                'sentiment_signal': 'NEUTRAL',
                'confidence': 0.0
            }
            self._cache_sentiment(cache_key, result)
            return result
        
        # Aggregate sentiments
        avg_compound = sum(s['compound'] for s in sentiments) / len(sentiments)
        avg_pos = sum(s['pos'] for s in sentiments) / len(sentiments)
        avg_neg = sum(s['neg'] for s in sentiments) / len(sentiments)
        avg_neu = sum(s['neu'] for s in sentiments) / len(sentiments)
        
        # Calculate ratios
        positive_count = sum(1 for s in sentiments if s['compound'] > 0.05)
        negative_count = sum(1 for s in sentiments if s['compound'] < -0.05)
        neutral_count = len(sentiments) - positive_count - negative_count
        
        positive_ratio = positive_count / len(sentiments)
        negative_ratio = negative_count / len(sentiments)
        neutral_ratio = neutral_count / len(sentiments)
        
        # Determine signal
        if avg_compound > 0.2:
            signal = 'BULLISH'
        elif avg_compound < -0.2:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'
        
        # Calculate confidence
        confidence = min(1.0, len(sentiments) / MAX_ARTICLES_FOR_FULL_CONFIDENCE) * abs(avg_compound)
        
        result = {
            'overall_score': avg_compound,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'neutral_ratio': neutral_ratio,
            'article_count': len(sentiments),
            'sentiment_signal': signal,
            'confidence': confidence,
            'avg_pos': avg_pos,
            'avg_neg': avg_neg,
            'avg_neu': avg_neu
        }
        
        # Cache the result
        self._cache_sentiment(cache_key, result)
        
        logger.info(f"Sentiment for {symbol}: {signal} (score: {avg_compound:.3f}, "
                   f"articles: {len(sentiments)}, confidence: {confidence:.2f})")
        
        return result
    
    async def analyze_portfolio_sentiment_async(self, symbols: List[str], days: int = 7) -> Dict[str, Dict]:
        """
        Analyze sentiment for multiple symbols concurrently
        
        This provides significant speedup when analyzing portfolios with many symbols.
        Example: 50 symbols in ~50 seconds instead of ~500 seconds (10x faster)
        
        Args:
            symbols: List of stock symbols
            days: Number of days to look back
            
        Returns:
            Dictionary mapping symbol to sentiment analysis results
        """
        if not AIOHTTP_AVAILABLE:
            # Fall back to sequential processing
            logger.warning("aiohttp not available, analyzing portfolio sentiment sequentially")
            results = {}
            for symbol in symbols:
                results[symbol] = self.get_sentiment_score(symbol, days)
            return results
        
        logger.info(f"Analyzing sentiment for {len(symbols)} symbols concurrently...")
        
        # Create tasks for concurrent execution
        tasks = [self.get_sentiment_score_async(symbol, days) for symbol in symbols]
        
        # Execute concurrently
        try:
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in portfolio sentiment analysis: {e}")
            return {}
        
        # Process results
        results = {}
        for symbol, result in zip(symbols, results_list):
            if isinstance(result, Exception):
                logger.error(f"Exception analyzing {symbol}: {result}")
                results[symbol] = {
                    'overall_score': 0.0,
                    'sentiment_signal': 'NEUTRAL',
                    'error': str(result)
                }
            else:
                results[symbol] = result
        
        logger.info(f"Successfully analyzed sentiment for {len(results)}/{len(symbols)} symbols")
        return results
    
    # Synchronous wrappers for backward compatibility
    
    def analyze_portfolio_sentiment(self, symbols: List[str], days: int = 7) -> Dict[str, Dict]:
        """
        Synchronous wrapper for analyze_portfolio_sentiment_async
        
        Args:
            symbols: List of stock symbols
            days: Number of days to look back
            
        Returns:
            Dictionary mapping symbol to sentiment analysis results
        """
        if not AIOHTTP_AVAILABLE:
            # Use sequential processing
            results = {}
            for symbol in symbols:
                results[symbol] = self.get_sentiment_score(symbol, days)
            return results
        
        try:
            # Try to get running event loop
            try:
                loop = asyncio.get_running_loop()
                # Event loop is already running, create a new one in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.analyze_portfolio_sentiment_async(symbols, days)
                    )
                    return future.result()
            except RuntimeError:
                # No event loop running, safe to create one
                return asyncio.run(self.analyze_portfolio_sentiment_async(symbols, days))
        except Exception as e:
            logger.error(f"Error in synchronous wrapper: {e}")
            # Fall back to sequential processing
            results = {}
            for symbol in symbols:
                results[symbol] = self.get_sentiment_score(symbol, days)
            return results
    
    # ====================================================================
    # END ASYNC METHODS
    # ====================================================================
    
    @staticmethod
    def _extract_article_text(article: Dict) -> str:
        """Extract headline+summary (Finnhub) or title+description (NewsAPI)."""
        if 'headline' in article:  # Finnhub format
            headline = article.get('headline') or ''
            summary = article.get('summary') or ''
            return f"{headline} {summary}".strip()
        if 'title' in article:  # NewsAPI format
            title = article.get('title') or ''
            description = article.get('description') or ''
            return f"{title} {description}".strip()
        return ""

    def _brain_sentiment(self, symbol: str, articles: List[Dict]) -> Optional[Dict]:
        """
        Aggregate sentiment for a symbol via the ALFa AI brain (LiteLLM), in one
        batched call over the symbol's headlines.

        Returns a result dict in the same shape as get_sentiment_score(), or
        None if the brain is disabled/unreachable or the response is unusable
        (caller then falls back to the local VADER path). Never raises.
        """
        if not SENTIMENT_USE_BRAIN:
            return None

        try:
            from api.services.litellm_client import (
                is_litellm_enabled,
                litellm_chat_completion_sync,
            )
        except Exception:
            return None

        if not is_litellm_enabled():
            return None

        headlines = []
        for article in articles:
            text = self._extract_article_text(article)
            if text:
                headlines.append(text)
            if len(headlines) >= SENTIMENT_BRAIN_MAX_HEADLINES:
                break
        if not headlines:
            return None

        numbered = "\n".join(f"{i + 1}. {h}" for i, h in enumerate(headlines))
        system = (
            "You are a financial news sentiment classifier. Given recent "
            "headlines about one stock, judge the aggregate sentiment for that "
            "stock's near-term price. Account for financial context (guidance, "
            "downgrades, lawsuits, beats/misses), not just positive words. "
            "Respond with ONLY a compact JSON object and no other text."
        )
        user = (
            f"Ticker: {symbol}\nHeadlines:\n{numbered}\n\n"
            "Return JSON with keys: overall_score (float -1..1), signal "
            "(one of BULLISH, BEARISH, NEUTRAL), confidence (float 0..1), "
            "positive_ratio (0..1), negative_ratio (0..1), neutral_ratio (0..1)."
        )

        result = litellm_chat_completion_sync(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
            max_tokens=200,
            feature="sentiment",
            trust_zone="app_authenticated",
        )
        if result.get("error") or not result.get("content"):
            logger.debug("Brain sentiment for %s failed: %s", symbol, result.get("error"))
            return None

        parsed = self._parse_brain_sentiment(result["content"])
        if parsed is None:
            logger.debug("Brain sentiment for %s: unparseable response", symbol)
            return None

        parsed["article_count"] = len(headlines)
        parsed["source"] = "alfa_ai_brain"
        logger.info(
            "Sentiment for %s (brain): %s (score=%.3f, headlines=%d, confidence=%.2f)",
            symbol, parsed["sentiment_signal"], parsed["overall_score"],
            len(headlines), parsed["confidence"],
        )
        return parsed

    @staticmethod
    def _parse_brain_sentiment(content: str) -> Optional[Dict]:
        """Parse the brain's JSON sentiment reply into the standard result dict."""
        import json
        import re

        text = content.strip()
        # Tolerate code fences or surrounding prose: grab the first JSON object.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except (ValueError, TypeError):
            return None

        def _clamp(value, low, high, default=0.0):
            try:
                return max(low, min(high, float(value)))
            except (TypeError, ValueError):
                return default

        score = _clamp(data.get("overall_score"), -1.0, 1.0)
        signal = str(data.get("signal", "")).upper()
        if signal not in ("BULLISH", "BEARISH", "NEUTRAL"):
            signal = "BULLISH" if score > 0.2 else "BEARISH" if score < -0.2 else "NEUTRAL"
        return {
            "overall_score": score,
            "positive_ratio": _clamp(data.get("positive_ratio"), 0.0, 1.0),
            "negative_ratio": _clamp(data.get("negative_ratio"), 0.0, 1.0),
            "neutral_ratio": _clamp(data.get("neutral_ratio"), 0.0, 1.0, 1.0),
            "sentiment_signal": signal,
            "confidence": _clamp(data.get("confidence"), 0.0, 1.0),
        }

    def analyze_sentiment_vader(self, text: str) -> Dict:
        """
        Analyze sentiment using VADER
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores (positive, negative, neutral, compound)
        """
        if not self.vader_analyzer:
            logger.warning("VADER analyzer not available")
            return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}
        
        scores = self.vader_analyzer.polarity_scores(text)
        return scores
    
    def analyze_sentiment_textblob(self, text: str) -> Dict:
        """
        Analyze sentiment using TextBlob
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores (polarity, subjectivity)
        """
        if not TEXTBLOB_AVAILABLE:
            logger.warning("TextBlob not available")
            return {'polarity': 0.0, 'subjectivity': 0.0}
        
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,  # -1 to 1
            'subjectivity': blob.sentiment.subjectivity,  # 0 to 1
            # Convert to VADER-like format for consistency
            'compound': blob.sentiment.polarity,
            'pos': max(0, blob.sentiment.polarity),
            'neg': abs(min(0, blob.sentiment.polarity)),
            'neu': 1 - abs(blob.sentiment.polarity)
        }
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment using configured method
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        if self.method == 'vader' and self.vader_analyzer:
            return self.analyze_sentiment_vader(text)
        elif self.method == 'textblob' and TEXTBLOB_AVAILABLE:
            return self.analyze_sentiment_textblob(text)
        else:
            # Fallback to neutral sentiment
            logger.warning("No sentiment analysis method available, returning neutral")
            return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}
    
    def get_sentiment_score(self, symbol: str, days: int = 7) -> Dict:
        """
        Get aggregated sentiment score for a symbol
        
        Note: When aiohttp is available and both news APIs are configured,
        this will use async concurrent fetching for better performance.
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
            
        Returns:
            Dictionary with:
            - overall_score: Aggregated sentiment score (-1 to 1)
            - positive_ratio: Ratio of positive articles
            - negative_ratio: Ratio of negative articles
            - neutral_ratio: Ratio of neutral articles
            - article_count: Number of articles analyzed
            - sentiment_signal: 'BULLISH', 'BEARISH', or 'NEUTRAL'
        """
        # If both APIs are available and aiohttp is installed, use async version for speed
        if AIOHTTP_AVAILABLE and self.finnhub_available and self.news_api_available:
            try:
                # Try to get existing event loop
                try:
                    loop = asyncio.get_running_loop()
                    # Event loop already running - cannot use asyncio.run() here
                    # Fall through to synchronous version below
                    logger.debug(f"Event loop already running, using synchronous sentiment analysis for {symbol}")
                except RuntimeError:
                    # No event loop running, safe to create one with asyncio.run()
                    logger.debug(f"Using async concurrent sentiment analysis for {symbol}")
                    return asyncio.run(self.get_sentiment_score_async(symbol, days))
            except Exception as e:
                logger.warning(f"Async sentiment analysis failed, falling back to sync: {e}")
        
        # Synchronous version (original implementation)
        # Check cache first
        cache_key = self._get_cache_key(symbol)
        cached = self._get_cached_sentiment(cache_key)
        if cached:
            return cached
        
        logger.info(f"Analyzing sentiment for {symbol}...")
        
        # Fetch news from available sources
        articles = []
        
        # Try Finnhub first (better for stock-specific news)
        if self.finnhub_available:
            finnhub_articles = self.fetch_news_finnhub(symbol, days)
            articles.extend(finnhub_articles)
        
        # Fallback to NewsAPI if needed
        if not articles and self.news_api_available:
            newsapi_articles = self.fetch_news_newsapi(symbol, days)
            articles.extend(newsapi_articles)
        
        if not articles:
            logger.debug(f"No news articles found for {symbol}")
            result = {
                'overall_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 1.0,
                'article_count': 0,
                'sentiment_signal': 'NEUTRAL',
                'confidence': 0.0
            }
            self._cache_sentiment(cache_key, result)
            return result
        
        # Primary path: ALFa AI brain (one batched call). Falls back to the
        # local VADER aggregation below if the brain is disabled/unreachable.
        brain_result = self._brain_sentiment(symbol, articles)
        if brain_result is not None:
            self._cache_sentiment(cache_key, brain_result)
            return brain_result
        
        # Analyze sentiment for each article
        sentiments = []
        for article in articles:
            # Extract text from article
            text = ""
            if 'headline' in article:  # Finnhub format
                headline = article.get('headline') or ''
                summary = article.get('summary') or ''
                text = str(headline) + " " + str(summary)
            elif 'title' in article:  # NewsAPI format
                title = article.get('title') or ''
                description = article.get('description') or ''
                text = str(title) + " " + str(description)
            
            if text.strip():
                sentiment = self.analyze_sentiment(text)
                sentiments.append(sentiment)
        
        if not sentiments:
            logger.warning(f"No sentiment data extracted for {symbol}")
            result = {
                'overall_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 1.0,
                'article_count': 0,
                'sentiment_signal': 'NEUTRAL',
                'confidence': 0.0
            }
            self._cache_sentiment(cache_key, result)
            return result
        
        # Aggregate sentiments
        avg_compound = sum(s['compound'] for s in sentiments) / len(sentiments)
        avg_pos = sum(s['pos'] for s in sentiments) / len(sentiments)
        avg_neg = sum(s['neg'] for s in sentiments) / len(sentiments)
        avg_neu = sum(s['neu'] for s in sentiments) / len(sentiments)
        
        # Calculate ratios
        positive_count = sum(1 for s in sentiments if s['compound'] > 0.05)
        negative_count = sum(1 for s in sentiments if s['compound'] < -0.05)
        neutral_count = len(sentiments) - positive_count - negative_count
        
        positive_ratio = positive_count / len(sentiments)
        negative_ratio = negative_count / len(sentiments)
        neutral_ratio = neutral_count / len(sentiments)
        
        # Determine signal
        if avg_compound > 0.2:
            signal = 'BULLISH'
        elif avg_compound < -0.2:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'
        
        # Calculate confidence based on article count and sentiment consistency
        confidence = min(1.0, len(sentiments) / MAX_ARTICLES_FOR_FULL_CONFIDENCE) * abs(avg_compound)
        
        result = {
            'overall_score': avg_compound,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'neutral_ratio': neutral_ratio,
            'article_count': len(sentiments),
            'sentiment_signal': signal,
            'confidence': confidence,
            'avg_positive': avg_pos,
            'avg_negative': avg_neg,
            'avg_neutral': avg_neu
        }
        
        logger.info(
            f"Sentiment for {symbol}: {signal} "
            f"(score={avg_compound:.3f}, articles={len(sentiments)}, confidence={confidence:.2f})"
        )
        
        # Cache the result
        self._cache_sentiment(cache_key, result)
        
        return result
    
    def should_trade_based_on_sentiment(self, symbol: str, 
                                       min_score: float = 0.1,
                                       min_confidence: float = 0.3) -> Tuple[bool, str]:
        """
        Determine if sentiment supports trading a symbol
        
        Args:
            symbol: Stock symbol
            min_score: Minimum sentiment score threshold
            min_confidence: Minimum confidence threshold
            
        Returns:
            Tuple of (should_trade, reason)
        """
        sentiment = self.get_sentiment_score(symbol)
        
        score = sentiment['overall_score']
        confidence = sentiment['confidence']
        signal = sentiment['sentiment_signal']
        
        # Check if we have enough data
        if sentiment['article_count'] < 3:
            return True, f"Insufficient news data ({sentiment['article_count']} articles)"
        
        # Check confidence
        if confidence < min_confidence:
            return True, f"Low sentiment confidence ({confidence:.2f} < {min_confidence})"
        
        # Check for strongly negative sentiment
        if score < -min_score and signal == 'BEARISH':
            return False, f"Negative sentiment (score={score:.2f}, signal={signal})"
        
        # Neutral or positive sentiment
        return True, f"Sentiment OK (score={score:.2f}, signal={signal})"
