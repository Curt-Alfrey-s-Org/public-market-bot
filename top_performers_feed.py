"""
Top Performers Feed - Live feed of top performing stocks (TOS-like)

This module implements a live feed of top performing stocks that:
- Shows live ticker results (real-time price updates)
- Auto-replaces stocks that fall off with higher performers
- Keeps best performers at the top
- Is checked FIRST before watchlist/screener in the bot loop

Roadmap idea #2: Top performers / popular symbols feed (TOS-like)
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from threading import Lock

logger = logging.getLogger(__name__)

# Configuration
FEED_ENABLED = os.getenv('ENABLE_TOP_PERFORMERS_FEED', 'true').lower() == 'true'
FEED_SIZE = int(os.getenv('TOP_PERFORMERS_FEED_SIZE', '50'))  # Number of stocks in feed
FEED_UPDATE_INTERVAL = int(os.getenv('TOP_PERFORMERS_FEED_UPDATE_INTERVAL', '300'))  # 5 minutes
FEED_PERFORMANCE_WINDOW = int(os.getenv('TOP_PERFORMERS_FEED_PERFORMANCE_WINDOW', '3600'))  # 1 hour
FEED_REPLACEMENT_THRESHOLD = float(os.getenv('TOP_PERFORMERS_FEED_REPLACEMENT_THRESHOLD', '0.05'))  # 5% drop triggers replacement


class TopPerformersFeed:
    """
    Live feed of top performing stocks with real-time updates and auto-replacement.
    
    Tracks stock performance over time and automatically replaces underperformers
    with better candidates. Maintains a ranked list with live ticker data.
    """
    
    def __init__(self):
        self.feed_data: List[Dict[str, Any]] = []  # Current feed stocks
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}  # {symbol: [performance snapshots]}
        self.last_update: Optional[datetime] = None
        self.lock = Lock()  # Thread-safe access
        self.is_updating = False
        
    def get_feed_symbols(self) -> List[str]:
        """
        Get list of symbols from the feed (in priority order).
        
        Returns:
            List of stock symbols, highest performers first
        """
        with self.lock:
            return [stock['symbol'] for stock in self.feed_data]
    
    def get_feed_data(self) -> List[Dict[str, Any]]:
        """
        Get full feed data with live ticker information.
        
        Returns:
            List of stock dictionaries with current price, volume, performance metrics
        """
        with self.lock:
            return self.feed_data.copy()
    
    def update_feed(self, candidates: List[Dict[str, Any]]) -> bool:
        """
        Update the feed with new candidates, replacing underperformers.
        
        Args:
            candidates: List of candidate stocks with performance metrics
            
        Returns:
            True if feed was updated, False otherwise
        """
        if not FEED_ENABLED:
            return False
        
        with self.lock:
            if self.is_updating:
                logger.debug("Feed update already in progress, skipping")
                return False
            
            self.is_updating = True
        
        try:
            # Sort candidates by performance (win probability or composite score)
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x.get('win_probability', x.get('composite_score', 0.0)),
                reverse=True
            )
            
            # Update performance history for existing stocks
            current_symbols = {stock['symbol'] for stock in self.feed_data}
            for candidate in sorted_candidates:
                symbol = candidate['symbol']
                if symbol in current_symbols:
                    self._record_performance(symbol, candidate)
            
            # Identify underperformers to replace
            to_replace = self._identify_underperformers()
            
            # Build new feed: keep top performers, replace underperformers
            new_feed = []
            used_symbols = set()
            
            # First, keep existing top performers that aren't underperforming
            for stock in self.feed_data:
                if stock['symbol'] not in to_replace:
                    new_feed.append(stock)
                    used_symbols.add(stock['symbol'])
            
            # Then, add new candidates to fill gaps
            for candidate in sorted_candidates:
                if len(new_feed) >= FEED_SIZE:
                    break
                if candidate['symbol'] not in used_symbols:
                    # Add live ticker data
                    candidate['last_price_update'] = datetime.now().isoformat()
                    new_feed.append(candidate)
                    used_symbols.add(candidate['symbol'])
            
            # Sort final feed by performance
            new_feed.sort(
                key=lambda x: x.get('win_probability', x.get('composite_score', 0.0)),
                reverse=True
            )
            
            # Update feed
            with self.lock:
                self.feed_data = new_feed[:FEED_SIZE]
                self.last_update = datetime.now()
            
            logger.info(f"Top performers feed updated: {len(self.feed_data)} stocks")
            if to_replace:
                logger.info(f"Replaced {len(to_replace)} underperformers: {', '.join(to_replace)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating top performers feed: {e}", exc_info=True)
            return False
        finally:
            with self.lock:
                self.is_updating = False
    
    def _record_performance(self, symbol: str, data: Dict[str, Any]):
        """Record performance snapshot for a symbol."""
        if symbol not in self.performance_history:
            self.performance_history[symbol] = []
        
        snapshot = {
            'timestamp': datetime.now(),
            'win_probability': data.get('win_probability', 0.0),
            'composite_score': data.get('composite_score', 0.0),
            'price': data.get('price', 0.0),
            'volume': data.get('volume', 0),
        }
        
        self.performance_history[symbol].append(snapshot)
        
        # Keep only recent history (within performance window)
        cutoff = datetime.now() - timedelta(seconds=FEED_PERFORMANCE_WINDOW)
        self.performance_history[symbol] = [
            s for s in self.performance_history[symbol]
            if s['timestamp'] > cutoff
        ]
    
    def _identify_underperformers(self) -> List[str]:
        """
        Identify stocks that should be replaced due to poor performance.
        
        Returns:
            List of symbols to replace
        """
        underperformers = []
        
        for stock in self.feed_data:
            symbol = stock['symbol']
            if symbol not in self.performance_history:
                continue  # New stock, give it time
            
            history = self.performance_history[symbol]
            if len(history) < 2:
                continue  # Need at least 2 snapshots to detect decline
            
            # Check if performance has dropped significantly
            initial_score = history[0].get('win_probability', history[0].get('composite_score', 0.0))
            latest_score = history[-1].get('win_probability', history[-1].get('composite_score', 0.0))
            
            if initial_score > 0:
                drop_pct = (initial_score - latest_score) / initial_score
                if drop_pct >= FEED_REPLACEMENT_THRESHOLD:
                    underperformers.append(symbol)
                    logger.debug(f"Marking {symbol} for replacement: {drop_pct:.1%} performance drop")
        
        return underperformers
    
    def update_live_prices(self, price_updates: Dict[str, Dict[str, Any]]):
        """
        Update live ticker prices for stocks in the feed.
        
        Args:
            price_updates: Dict mapping symbol to {price, volume, timestamp, ...}
        """
        with self.lock:
            for stock in self.feed_data:
                symbol = stock['symbol']
                if symbol in price_updates:
                    update = price_updates[symbol]
                    stock['price'] = update.get('price', stock.get('price', 0.0))
                    stock['volume'] = update.get('volume', stock.get('volume', 0))
                    stock['last_price_update'] = update.get('timestamp', datetime.now().isoformat())
                    stock['price_change'] = update.get('change', 0.0)
                    stock['price_change_pct'] = update.get('change_pct', 0.0)
    
    def should_refresh(self) -> bool:
        """Check if feed should be refreshed based on update interval."""
        if self.last_update is None:
            return True
        
        time_since_update = (datetime.now() - self.last_update).total_seconds()
        return time_since_update >= FEED_UPDATE_INTERVAL
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feed statistics."""
        with self.lock:
            return {
                'enabled': FEED_ENABLED,
                'size': len(self.feed_data),
                'max_size': FEED_SIZE,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'update_interval': FEED_UPDATE_INTERVAL,
                'is_updating': self.is_updating,
            }


# Global feed instance
_feed_instance: Optional[TopPerformersFeed] = None


def get_top_performers_feed() -> TopPerformersFeed:
    """Get or create the global top performers feed instance."""
    global _feed_instance
    if _feed_instance is None:
        _feed_instance = TopPerformersFeed()
    return _feed_instance


def get_feed_symbols() -> List[str]:
    """Convenience function to get feed symbols."""
    if not FEED_ENABLED:
        return []
    return get_top_performers_feed().get_feed_symbols()


def get_feed_data() -> List[Dict[str, Any]]:
    """Convenience function to get feed data."""
    if not FEED_ENABLED:
        return []
    return get_top_performers_feed().get_feed_data()
