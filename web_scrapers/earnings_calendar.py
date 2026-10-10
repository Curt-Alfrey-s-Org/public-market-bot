#!/usr/bin/env python3
"""
Earnings Calendar Module
Checks upcoming earnings dates to avoid trading around earnings volatility
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import yfinance for earnings data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available - earnings calendar disabled")


class EarningsCalendar:
    """Monitor upcoming earnings dates"""
    
    def __init__(self, days_ahead: int = 7):
        """
        Args:
            days_ahead: How many days ahead to check for earnings (default: 7)
        """
        self.days_ahead = days_ahead
        self.cache = {}  # Symbol -> earnings_date
        self.cache_time = {}  # Symbol -> cache_timestamp
        self.cache_ttl = 86400  # 24 hours
    
    def has_upcoming_earnings(self, symbol: str) -> bool:
        """
        Check if symbol has earnings in next N days
        
        Returns:
            True if earnings within days_ahead, False otherwise
        """
        earnings_date = self.get_earnings_date(symbol)
        if earnings_date is None:
            return False
        
        days_until_earnings = (earnings_date - datetime.now()).days
        return 0 <= days_until_earnings <= self.days_ahead
    
    def get_earnings_date(self, symbol: str) -> Optional[datetime]:
        """
        Get next earnings date for symbol
        
        Returns:
            datetime of next earnings, or None if not found
        """
        if not YFINANCE_AVAILABLE:
            return None
        
        # Check cache
        if symbol in self.cache:
            cache_age = datetime.now().timestamp() - self.cache_time.get(symbol, 0)
            if cache_age < self.cache_ttl:
                return self.cache[symbol]
        
        # Fetch from yfinance
        try:
            ticker = yf.Ticker(symbol)
            earnings_date = ticker.info.get('earningsDate')
            
            if earnings_date:
                # Convert to datetime if needed
                if isinstance(earnings_date, list):
                    # Sometimes it's a list, take first element
                    earnings_date = earnings_date[0]
                
                if isinstance(earnings_date, int):
                    # Unix timestamp
                    earnings_datetime = datetime.fromtimestamp(earnings_date)
                elif isinstance(earnings_date, datetime):
                    earnings_datetime = earnings_date
                else:
                    earnings_datetime = None
                
                # Cache result
                if earnings_datetime:
                    self.cache[symbol] = earnings_datetime
                    self.cache_time[symbol] = datetime.now().timestamp()
                    logger.debug(f"Cached earnings date for {symbol}: {earnings_datetime}")
                    return earnings_datetime
            
            # No earnings date found - cache None
            self.cache[symbol] = None
            self.cache_time[symbol] = datetime.now().timestamp()
            return None
        
        except Exception as e:
            logger.debug(f"Failed to fetch earnings date for {symbol}: {e}")
            # Cache the failure
            self.cache[symbol] = None
            self.cache_time[symbol] = datetime.now().timestamp()
            return None
    
    def get_days_until_earnings(self, symbol: str) -> Optional[int]:
        """
        Get number of days until earnings
        
        Returns:
            Number of days, or None if no earnings found
        """
        earnings_date = self.get_earnings_date(symbol)
        if earnings_date is None:
            return None
        
        days = (earnings_date - datetime.now()).days
        return max(0, days)  # Return 0 if earnings is today or past
    
    def should_trade(self, symbol: str, days_buffer: int = 3) -> bool:
        """
        Determine if we should trade based on earnings
        
        Args:
            symbol: Stock symbol
            days_buffer: Days before earnings to stop trading (default: 3)
        
        Returns:
            True if safe to trade, False if earnings too close
        """
        days_until = self.get_days_until_earnings(symbol)
        if days_until is None:
            # No earnings data, safe to trade
            return True
        
        if days_until >= days_buffer:
            # Earnings far enough away
            return True
        
        # Earnings too close
        logger.info(f"Skipping {symbol}: earnings in {days_until} days (buffer: {days_buffer})")
        return False
    
    def get_position_size_adjustment(self, symbol: str, days_buffer: int = 10) -> float:
        """
        Get position size multiplier based on earnings proximity
        
        Args:
            symbol: Stock symbol
            days_buffer: Maximum days before earnings to reduce size (default: 10)
        
        Returns:
            Multiplier (1.0 = full size, 0.5 = half size, 0.25 = quarter size)
        """
        days_until = self.get_days_until_earnings(symbol)
        if days_until is None:
            return 1.0
        
        if days_until >= days_buffer:
            # Far from earnings, no adjustment
            return 1.0
        elif days_until <= 2:
            # Very close to earnings, minimal position
            return 0.25
        elif days_until <= 5:
            # Close to earnings, reduce by 50%
            return 0.5
        else:
            # 5-10 days out, reduce by 25%
            return 0.75
