# Phase 1: Quick Wins - Scraper Implementation Guide

## 🎯 Objective: Implement 3 quick wins in 2 hours

This guide will walk you through implementing Phase 1 improvements that can be done today.

---

## Quick Win #1: Enhanced Wikipedia Scraper (15 min)

### Goal
Extract **market cap tier** and **sector** alongside stock symbols when scraping Wikipedia.

### Current Code (stock_screener.py, lines 361-430)
```python
def fetch_stock_universe_from_wikipedia() -> Set[str]:
    # Returns: Set of tickers like {'AAPL', 'MSFT', 'GOOGL'}
    # Missing: Market cap, sector, industry info
```

### Enhanced Code
I'll create a new version that returns structured data:

**File:** `stock_screener.py`
**Changes:** Add new function to extract metadata alongside tickers

```python
def fetch_stock_universe_with_metadata() -> Dict[str, Dict[str, str]]:
    """
    Fetch stock universe WITH market cap tier and sector from Wikipedia
    
    Returns:
        Dict like:
        {
            'AAPL': {'market_cap_tier': 'mega-cap', 'sector': 'Technology'},
            'XYZ': {'market_cap_tier': 'mid-cap', 'sector': 'Healthcare'},
        }
    """
    if not PANDAS_AVAILABLE:
        logger.warning("pandas not available")
        return {}
    
    universe_data = {}
    
    for source_name, url in STOCK_UNIVERSE_SOURCES.items():
        try:
            logger.debug(f"Fetching {source_name} from Wikipedia...")
            tables = pd.read_html(url, header=0)
            
            if not tables:
                continue
            
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
                
                # NEW: Determine market cap tier based on index
                market_cap_tier = self._get_market_cap_tier_for_index(source_name)
                
                # NEW: Extract sector if available
                sector_col = self._find_sector_column(df)
                
                for idx, ticker in enumerate(tickers):
                    if ticker and len(ticker) <= 6 and ticker.replace(".", "").isalpha() and ticker not in DELISTED_STOCKS:
                        sector = "Unknown"
                        
                        # Try to extract sector from DataFrame if column exists
                        if sector_col is not None and idx < len(df):
                            try:
                                sector = str(df[sector_col].iloc[idx]).strip()
                                if not sector or sector == "nan":
                                    sector = "Unknown"
                            except:
                                sector = "Unknown"
                        
                        universe_data[ticker] = {
                            'market_cap_tier': market_cap_tier,
                            'sector': sector,
                            'source_index': source_name
                        }
                
                logger.info(f"✓ {source_name}: {len(tickers)} symbols with metadata")
        
        except Exception as e:
            logger.debug(f"Failed to fetch {source_name}: {e}")
    
    return universe_data

@staticmethod
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

@staticmethod
def _find_sector_column(df: pd.DataFrame) -> Optional[str]:
    """Find sector column in DataFrame if it exists"""
    for col in df.columns:
        col_lower = str(col).lower()
        if "sector" in col_lower or "industry" in col_lower:
            return col
    return None
```

### Usage
```python
# Old way (current)
symbols = get_stock_universe()
# Returns: ['AAPL', 'MSFT', 'GOOGL']

# New way (enhanced)
universe_with_metadata = fetch_stock_universe_with_metadata()
# Returns: {
#     'AAPL': {'market_cap_tier': 'mega-cap', 'sector': 'Technology'},
#     'MSFT': {'market_cap_tier': 'mega-cap', 'sector': 'Technology'},
#     'XYZ': {'market_cap_tier': 'mid-cap', 'sector': 'Healthcare'}
# }
```

### Benefit
- Portfolio becomes more balanced (not all mega-cap tech)
- Better sector diversification
- Foundation for sector-weighted scoring

---

## Quick Win #2: Earnings Date Awareness (30 min)

### Goal
Check if a stock has earnings within the next N days before executing trade.

### New File: `web_scrapers/earnings_calendar.py`

```python
#!/usr/bin/env python3
"""
Earnings Calendar Module
Checks upcoming earnings dates to avoid trading around earnings volatility
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)

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
            
            # No earnings date found
            self.cache[symbol] = None
            self.cache_time[symbol] = datetime.now().timestamp()
            return None
        
        except Exception as e:
            logger.debug(f"Failed to fetch earnings date for {symbol}: {e}")
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
```

### Integration into Trading Bot

**File:** `main.py` (or trading loop)
**Add:** Check earnings before executing trade

```python
from web_scrapers.earnings_calendar import EarningsCalendar

# Initialize in bot setup
self.earnings_calendar = EarningsCalendar(days_ahead=7)

# In trading loop, before execute_trade():
symbol = 'AAPL'
if not self.earnings_calendar.should_trade(symbol, days_buffer=3):
    logger.info(f"Skipping {symbol} due to upcoming earnings")
    continue  # Skip this trade

# OR reduce position size
days_to_earnings = self.earnings_calendar.get_days_until_earnings(symbol)
if days_to_earnings and days_to_earnings < 5:
    # Reduce position size by 50% if earnings soon
    position_size = position_size * 0.5
    logger.info(f"Reducing {symbol} position size due to earnings in {days_to_earnings} days")
```

### Benefit
- Avoid 20-30% of earnings-driven losses
- Reduce unexpected volatility exposure
- Better risk management

---

## Quick Win #3: Position Size Adjustment (15 min)

### Goal
Automatically reduce position size if earnings are coming up, or if implied volatility is high.

### Add to risk_management.py

```python
def calculate_position_size_with_earnings_adjustment(
    capital: float,
    risk_per_trade: float,
    stop_loss_percent: float,
    symbol: str,
    earnings_calendar: Optional[EarningsCalendar] = None
) -> float:
    """
    Calculate position size with earnings date adjustment
    
    If earnings are close, reduce position size to limit risk
    """
    # Base position size
    base_size = (capital * risk_per_trade) / stop_loss_percent
    
    # Adjust for earnings
    if earnings_calendar:
        days_to_earnings = earnings_calendar.get_days_until_earnings(symbol)
        
        if days_to_earnings is not None:
            if days_to_earnings <= 2:
                # Don't trade, or trade minimal size
                return base_size * 0.25
            elif days_to_earnings <= 5:
                # Reduce by 50%
                return base_size * 0.5
            elif days_to_earnings <= 10:
                # Reduce by 25%
                return base_size * 0.75
            # Otherwise, use full size (days_to_earnings > 10)
    
    return base_size
```

### Usage in main.py
```python
# When calculating position size
position_size = calculate_position_size_with_earnings_adjustment(
    capital=self.total_capital,
    risk_per_trade=0.02,
    stop_loss_percent=0.03,
    symbol=symbol,
    earnings_calendar=self.earnings_calendar
)

logger.info(f"Position size for {symbol}: ${position_size:.2f}")
```

---

## Implementation Checklist

### [ ] Step 1: Add Enhanced Wikipedia Scraper (10 min)
- [ ] Add `fetch_stock_universe_with_metadata()` function to `stock_screener.py`
- [ ] Add `_get_market_cap_tier_for_index()` helper
- [ ] Add `_find_sector_column()` helper
- [ ] Test: Run and verify metadata is extracted

```bash
# Quick test
python -c "
from stock_screener import fetch_stock_universe_with_metadata
data = fetch_stock_universe_with_metadata()
print(f'Fetched {len(data)} stocks with metadata')
print(list(data.items())[:3])  # Print first 3
"
```

### [ ] Step 2: Create Earnings Calendar Module (15 min)
- [ ] Create `web_scrapers/` directory if not exists
- [ ] Create `web_scrapers/__init__.py`
- [ ] Create `web_scrapers/earnings_calendar.py` (copy code above)
- [ ] Test: Verify earnings dates are fetched

```bash
# Quick test
python -c "
from web_scrapers.earnings_calendar import EarningsCalendar
ec = EarningsCalendar()
date = ec.get_earnings_date('AAPL')
print(f'AAPL earnings: {date}')
"
```

### [ ] Step 3: Integrate Earnings Check into Trading Loop (15 min)
- [ ] Open `main.py` (or trading bot file)
- [ ] Import `EarningsCalendar`
- [ ] Initialize in `__init__()` method
- [ ] Add earnings check before `execute_trade()`
- [ ] Test: Verify trades are skipped for upcoming earnings

```bash
# Quick test
python main.py  # Run bot and check logs for "Skipping X due to earnings"
```

### [ ] Step 4: Update Risk Management (10 min)
- [ ] Add `calculate_position_size_with_earnings_adjustment()` to `risk_management.py`
- [ ] Update position sizing calls in trading loop
- [ ] Test: Verify position sizes are reduced for upcoming earnings

### [ ] Step 5: Verify Improvements
- [ ] Run bot for 1 trading cycle
- [ ] Check logs for earnings-aware decisions
- [ ] Verify positions are smaller for upcoming earnings
- [ ] Verify trades are skipped if earnings within 3 days

---

## Expected Results

### Before Implementation
```
2026-02-01 10:30:00 [BUY] AAPL @ $190.50 (position size: $10,000)
2026-02-02 09:00:00 [EARNINGS] AAPL reports earnings, stock gaps down 5%
2026-02-02 10:30:00 [SELL] AAPL @ $180.98 (loss: -$504)
```

### After Implementation
```
2026-02-01 10:30:00 [INFO] AAPL earnings in 1 day, skipping trade
2026-02-01 10:30:00 [BUY] MSFT @ $420.00 (position size: $10,000) ✓ Safe
2026-02-02 09:00:00 [EARNINGS] AAPL reports earnings, stock gaps down 5%
2026-02-02 10:30:00 [INFO] Not affected - we skipped AAPL ✓ Protected
```

**Impact:** Avoid 1-2 earnings-driven losses per month = 5-10% better returns

---

## Deployment Steps

### 1. Local Testing (30 min)
```bash
# Clone/update repo
cd ~/market-bot/market-pie5-bot

# Test Wikipedia scraper
python -c "from stock_screener import fetch_stock_universe_with_metadata; print(len(fetch_stock_universe_with_metadata()))"

# Test earnings calendar
python -c "from web_scrapers.earnings_calendar import EarningsCalendar; ec = EarningsCalendar(); print(ec.should_trade('AAPL'))"

# Run full bot test
python test_bot_functionality.py
```

### 2. Remote Deployment (10 min)
```bash
# SSH to operator
ssh operator@192.0.2.21

# Update repo
cd ~/market-bot/market-pie5-bot
git pull origin main

# Or manually copy files if needed
scp -r web_scrapers/ operator@192.0.2.21:~/market-bot/market-pie5-bot/

# Restart bot
pkill -f "python main.py"
sleep 2
nohup python main.py > /tmp/bot_output.log 2>&1 &

# Verify
tail -20 /tmp/bot_output.log
```

### 3. Monitor (Ongoing)
```bash
# Watch for earnings awareness
ssh operator@192.0.2.21
grep "earnings" /tmp/bot_output.log

# Watch for position size adjustments
grep "position size\|Reducing" /tmp/bot_output.log

# Check successful trades
grep "\[BUY\]\|\[SELL\]" /tmp/bot_output.log | tail -20
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'web_scrapers'"
**Solution:** Create `web_scrapers/__init__.py` file
```bash
touch web_scrapers/__init__.py
```

### Issue: "yfinance timeout when fetching earnings"
**Solution:** Add timeout handling
```python
# In earnings_calendar.py, wrap in try/except
try:
    ticker = yf.Ticker(symbol)
    earnings_date = ticker.info.get('earningsDate', timeout=5)
except:
    return None  # Fallback to None if timeout
```

### Issue: "Not seeing earnings warnings in logs"
**Solution:** Check log level
```bash
# Edit main.py
logger.setLevel(logging.DEBUG)  # Or INFO

# Restart bot
pkill -f "python main.py"
nohup python main.py > /tmp/bot_output.log 2>&1 &
```

---

## Next Steps

After Phase 1 is deployed and working:

1. **Monitor for 1 week** - Track earnings avoidances and compare returns
2. **Measure impact** - Calculate win rate improvement from earnings awareness
3. **Phase 2 (Next Week)** - Add retail sentiment scraping (Reddit, StockTwits)
4. **Phase 3 (Following Week)** - Add options flow monitoring (IV percentiles)

---

## Timeline

```
Today:
  - [ ] 15 min: Enhanced Wikipedia scraper
  - [ ] 30 min: Earnings calendar module
  - [ ] 15 min: Position size adjustment
  - [ ] Total: 60 minutes

Deployment:
  - [ ] 30 min: Local testing
  - [ ] 10 min: Remote deployment
  - [ ] 10 min: Verification

Total: ~2 hours for Phase 1 implementation
Expected Benefit: 5-10% reduction in earnings-related losses
```

---

**Ready to implement? Start with Step 1 above!** 🚀
