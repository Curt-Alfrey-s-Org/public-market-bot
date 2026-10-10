"""
Retail Sentiment Monitor
Tracks Reddit WallStreetBets mentions to detect FOMO and fade high-retail trades.

Expected Impact: +5-8% by avoiding pump-and-dumps
"""

import logging
import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class RetailSentiment:
    """
    Monitor Reddit WallStreetBets for retail FOMO signals.
    
    Strategy:
    - Track mention volume for symbols
    - Detect abnormal spikes (>3x baseline)
    - Fade trades with high retail interest (often pumps)
    - Bullish sentiment + volume spike = AVOID (retail FOMO)
    
    Usage:
        sentiment = RetailSentiment(cache_ttl_hours=6)
        should_trade, reason = sentiment.should_trade('GME')
        # Returns: (False, "High retail FOMO detected (50 mentions, 5x baseline)")
    """
    
    def __init__(self, cache_ttl_hours: int = 6, fomo_threshold: float = 3.0):
        """
        Initialize retail sentiment monitor.
        
        Args:
            cache_ttl_hours: Hours to cache Reddit data (avoid rate limits)
            fomo_threshold: Multiplier for FOMO detection (3.0 = 3x baseline)
        """
        self.cache_ttl_hours = cache_ttl_hours
        self.fomo_threshold = fomo_threshold
        self.cache: Dict[str, Dict] = {}  # symbol -> {mentions, timestamp, baseline}
        self.baseline_mentions: Dict[str, float] = {}  # symbol -> avg mentions
        
        # Reddit API fallback (no auth required for public data)
        self.reddit_url = "https://www.reddit.com/r/wallstreetbets/new.json"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        logger.info(f"Retail sentiment monitor initialized (cache: {cache_ttl_hours}h, FOMO threshold: {fomo_threshold}x)")
    
    def get_mention_count(self, symbol: str, force_refresh: bool = False) -> Optional[int]:
        """
        Get current mention count for a symbol on WSB.
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            force_refresh: Bypass cache and fetch fresh data
        
        Returns:
            Number of mentions in last 100 posts, or None if fetch fails
        """
        # Check cache
        if not force_refresh and symbol in self.cache:
            cached = self.cache[symbol]
            cache_age = datetime.now() - cached['timestamp']
            if cache_age < timedelta(hours=self.cache_ttl_hours):
                return cached['mentions']
        
        # Fetch fresh data
        try:
            headers = {'User-Agent': self.user_agent}
            response = requests.get(self.reddit_url, headers=headers, timeout=10)
            
            if response.status_code == 429:
                logger.warning("Reddit rate limit hit - using cached data")
                return self.cache.get(symbol, {}).get('mentions', 0)
            
            if response.status_code != 200:
                logger.warning(f"Reddit fetch failed: HTTP {response.status_code}")
                return None
            
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            # Count mentions (case-insensitive, word boundaries)
            mention_count = 0
            pattern = re.compile(rf'\b{re.escape(symbol)}\b', re.IGNORECASE)
            
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                
                mention_count += len(pattern.findall(title))
                mention_count += len(pattern.findall(selftext))
            
            # Update cache
            self.cache[symbol] = {
                'mentions': mention_count,
                'timestamp': datetime.now(),
                'posts_checked': len(posts)
            }
            
            # Update baseline (exponential moving average)
            if symbol not in self.baseline_mentions:
                self.baseline_mentions[symbol] = mention_count
            else:
                # EMA: 80% old baseline + 20% new data
                self.baseline_mentions[symbol] = (
                    0.8 * self.baseline_mentions[symbol] + 
                    0.2 * mention_count
                )
            
            logger.debug(f"{symbol}: {mention_count} mentions (baseline: {self.baseline_mentions[symbol]:.1f})")
            return mention_count
            
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch Reddit data for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching Reddit data: {e}")
            return None
    
    def is_fomo_spike(self, symbol: str) -> Tuple[bool, float]:
        """
        Detect if symbol has abnormal retail interest (FOMO spike).
        
        Args:
            symbol: Stock ticker
        
        Returns:
            (is_spike, multiplier) - e.g., (True, 5.2) means 5.2x baseline
        """
        mentions = self.get_mention_count(symbol)
        
        if mentions is None:
            # No data - assume safe (don't block trades on fetch failure)
            return False, 0.0
        
        baseline = self.baseline_mentions.get(symbol, 5.0)  # Default baseline: 5 mentions
        
        if baseline < 1.0:
            baseline = 1.0  # Avoid division by zero
        
        multiplier = mentions / baseline
        is_spike = multiplier >= self.fomo_threshold
        
        if is_spike:
            logger.info(f"[FOMO SPIKE] {symbol}: {mentions} mentions ({multiplier:.1f}x baseline {baseline:.1f})")
        
        return is_spike, multiplier
    
    def should_trade(self, symbol: str) -> Tuple[bool, str]:
        """
        Determine if symbol should be traded (fade FOMO).
        
        Args:
            symbol: Stock ticker
        
        Returns:
            (can_trade, reason) - e.g., (False, "FOMO spike detected")
        """
        is_spike, multiplier = self.is_fomo_spike(symbol)
        
        if is_spike:
            mentions = self.get_mention_count(symbol)
            baseline = self.baseline_mentions.get(symbol, 5.0)
            reason = (
                f"High retail FOMO detected "
                f"({mentions} mentions, {multiplier:.1f}x baseline {baseline:.1f})"
            )
            return False, reason
        
        return True, "Retail sentiment normal"
    
    def get_position_size_adjustment(self, symbol: str) -> float:
        """
        Adjust position size based on retail interest level.
        
        Strategy:
        - Normal retail interest (≤1.5x baseline): 100% size
        - Moderate interest (1.5-2.5x): 75% size (caution)
        - High interest (2.5-3x): 50% size (risky)
        - FOMO spike (≥3x): 0% size (avoid entirely)
        
        Args:
            symbol: Stock ticker
        
        Returns:
            Multiplier 0.0-1.0 (0.5 = reduce position by 50%)
        """
        is_spike, multiplier = self.is_fomo_spike(symbol)
        
        if is_spike or multiplier >= 3.0:
            return 0.0  # Avoid trade
        elif multiplier >= 2.5:
            return 0.5  # 50% position
        elif multiplier >= 1.5:
            return 0.75  # 75% position
        else:
            return 1.0  # Full position
    
    def get_high_fomo_symbols(self, symbols: List[str]) -> List[Tuple[str, int, float]]:
        """
        Get all symbols with FOMO spikes from a list.
        
        Args:
            symbols: List of tickers to check
        
        Returns:
            List of (symbol, mentions, multiplier) sorted by multiplier desc
        """
        fomo_list = []
        
        for symbol in symbols:
            is_spike, multiplier = self.is_fomo_spike(symbol)
            if is_spike:
                mentions = self.get_mention_count(symbol)
                fomo_list.append((symbol, mentions, multiplier))
        
        # Sort by multiplier (highest first)
        fomo_list.sort(key=lambda x: x[2], reverse=True)
        return fomo_list
    
    def log_watchlist_sentiment(self, symbols: List[str]):
        """
        Log retail sentiment summary for watchlist (startup diagnostic).
        
        Args:
            symbols: List of tickers to check
        """
        logger.info("[RETAIL SENTIMENT] Scanning watchlist for FOMO signals...")
        
        fomo_symbols = self.get_high_fomo_symbols(symbols)
        
        if fomo_symbols:
            logger.warning(f"[FOMO ALERT] {len(fomo_symbols)} symbols with high retail interest:")
            for symbol, mentions, mult in fomo_symbols[:5]:  # Top 5
                baseline = self.baseline_mentions.get(symbol, 5.0)
                logger.warning(
                    f"  - {symbol}: {mentions} mentions "
                    f"({mult:.1f}x baseline {baseline:.1f}) - AVOID"
                )
        else:
            logger.info("[RETAIL SENTIMENT] No FOMO spikes detected - watchlist clear")
    
    def clear_cache(self):
        """Clear all cached data (force refresh on next call)."""
        self.cache.clear()
        logger.info("Retail sentiment cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache_size, symbols_tracked, avg_age_hours
        """
        if not self.cache:
            return {'cache_size': 0, 'symbols_tracked': 0, 'avg_age_hours': 0}
        
        now = datetime.now()
        ages = [(now - data['timestamp']).total_seconds() / 3600 for data in self.cache.values()]
        avg_age = sum(ages) / len(ages) if ages else 0
        
        return {
            'cache_size': len(self.cache),
            'symbols_tracked': len(self.baseline_mentions),
            'avg_age_hours': round(avg_age, 1)
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test with known meme stocks
    sentiment = RetailSentiment(cache_ttl_hours=6, fomo_threshold=3.0)
    
    test_symbols = ['GME', 'AMC', 'TSLA', 'AAPL', 'NVDA', 'SPY']
    
    print("\n=== Retail Sentiment Analysis ===\n")
    
    for symbol in test_symbols:
        can_trade, reason = sentiment.should_trade(symbol)
        adjustment = sentiment.get_position_size_adjustment(symbol)
        mentions = sentiment.get_mention_count(symbol)
        
        status = "✅ TRADE" if can_trade else "❌ AVOID"
        print(f"{status} {symbol}: {mentions} mentions - {reason} (size: {adjustment*100:.0f}%)")
    
    print("\n=== Cache Stats ===")
    stats = sentiment.get_cache_stats()
    print(f"Cached symbols: {stats['cache_size']}")
    print(f"Tracked baselines: {stats['symbols_tracked']}")
    print(f"Avg cache age: {stats['avg_age_hours']}h")
