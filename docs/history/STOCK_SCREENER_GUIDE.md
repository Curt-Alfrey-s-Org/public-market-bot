# Stock Screener Guide

## Overview

The market-pie5-bot now includes a **dynamic stock screener** that automatically discovers tradeable stocks from major market indices instead of relying on preloaded lists. This guide explains how to use and configure the stock screener.

## Key Features

### 🚀 Dynamic Stock Discovery
- **Automatic Universe Building**: Fetches stocks from S&P 500, NASDAQ-100, and Dow Jones via Wikipedia
- **Comprehensive Coverage**: Access to 500+ stocks across all major sectors
- **No API Keys Required**: Uses free, public Wikipedia tables
- **Smart Fallback**: 160+ stock fallback list when Wikipedia unavailable

### ⚡ Performance Optimized
- **Fast Screening**: Limits checks to 200 stocks for ~2-second performance (TOS-like speed)
- **24-Hour Universe Cache**: Refreshes stock lists once per day
- **5-Minute Screening Cache**: Reuses recent screening results
- **Persistent Cache**: Survives bot restarts

### 🎯 Filtering by Your Criteria
Automatically filters stocks based on your `.env` settings:
- `MIN_STOCK_PRICE`: Minimum stock price (default: $5.00)
- `MAX_STOCK_PRICE`: Maximum stock price (default: $1000.00)
- `MIN_DAILY_VOLUME`: Minimum daily volume (default: 500,000)
- `MAX_STOCK_VOLATILITY`: Maximum volatility (default: 0.15 or 15%)

## Configuration

### Enable Stock Screener

In your `.env` file:

```bash
# Enable dynamic stock discovery
ENABLE_STOCK_SCREENER=true

# Maximum number of stocks to discover and trade
MAX_DISCOVERED_STOCKS=10
```

### Configure Filtering Criteria

```bash
# Stock Filtering Configuration
MIN_STOCK_PRICE=5.0              # Avoid penny stocks
MAX_STOCK_PRICE=1000.0           # Avoid very expensive stocks
MIN_DAILY_VOLUME=500000          # Ensure liquidity
MAX_STOCK_VOLATILITY=0.15        # Limit to 15% volatility
```

### Example Configurations

#### Conservative Trading (Large Cap, Low Volatility)
```bash
MIN_STOCK_PRICE=50.0
MAX_STOCK_PRICE=500.0
MIN_DAILY_VOLUME=5000000         # 5M+ volume
MAX_STOCK_VOLATILITY=0.10        # 10% max volatility
```

#### Aggressive Trading (Small/Mid Cap, Higher Volatility)
```bash
MIN_STOCK_PRICE=10.0
MAX_STOCK_PRICE=200.0
MIN_DAILY_VOLUME=1000000         # 1M+ volume
MAX_STOCK_VOLATILITY=0.25        # 25% max volatility
```

#### Tech Focus (Higher Price Range)
```bash
MIN_STOCK_PRICE=100.0
MAX_STOCK_PRICE=1000.0
MIN_DAILY_VOLUME=2000000
MAX_STOCK_VOLATILITY=0.20
```

## How It Works

### 1. Universe Building

When the bot starts, it builds a stock universe:

```
Priority Order:
1. Dynamic API (if DYNAMIC_SCAN_API_URL configured)
2. Wikipedia Stock Lists (S&P 500, NASDAQ-100, Dow Jones)
3. Fallback List (160+ major stocks across sectors)
```

### 2. Screening Process

The screener applies your filters:

```python
For each stock in universe:
    ✓ Check: Is price in range?
    ✓ Check: Is volume sufficient?
    ✓ Check: Is volatility acceptable?
    ✓ If passes all checks: Add to tradeable list
```

### 3. Caching

To maintain performance:

- **Universe Cache**: Stored in `.stock_universe_cache.pkl` (24-hour lifespan)
- **Screening Cache**: In-memory cache (5-minute lifespan)
- **Automatic Refresh**: Universe refreshes daily, screening every 5 minutes

## Usage Examples

### Basic Usage (Automatic)

When `ENABLE_STOCK_SCREENER=true`, the bot automatically uses the screener:

```bash
$ python3 main.py

[STOCK SCREENER] Discovering tradeable stocks...
  Searching for stocks matching criteria:
  - Price: $5.00 - $1000.00
  - Volume: 500,000+
  - Volatility: <15.0%

[STOCK SCREENER] Found 10 tradeable stocks:
  1. AAPL
  2. MSFT
  3. GOOGL
  ...
```

### Manual Testing

Test the screener independently:

```bash
$ python3 stock_screener.py

Testing Dynamic Stock Screener
============================================================
1. Building stock universe...
   ✓ Universe size: 503 stocks
   ✓ Source: Wikipedia

2. Testing stock screener...
   ✓ Screener initialized with 503 stocks

3. Screening for tradeable stocks...
   ✓ Found 10 tradeable stocks:
     1. AAPL
     2. MSFT
     ...
```

### Programmatic Usage

Use in your own scripts:

```python
from stock_screener import StockScreener, screen_for_trades

# Quick screening
symbols = screen_for_trades(max_stocks=10)
print(f"Found {len(symbols)} stocks: {symbols}")

# Advanced usage
screener = StockScreener()
screener.refresh_universe(force=True)  # Force refresh
results = screener.screen_stocks(max_results=20)

# Custom universe
custom_screener = StockScreener(stock_universe=['AAPL', 'MSFT', 'GOOGL'])
results = custom_screener.screen_stocks(max_results=5)
```

## Comparison: Before vs After

### Before (Preloaded Lists)
- ❌ Limited to 100 hardcoded stocks
- ❌ Manual updates required
- ❌ Two stocks in scan_symbols.txt (AAPL, MSFT)
- ❌ No filtering by criteria
- ❌ Same stocks always checked

### After (Dynamic Discovery)
- ✅ 500+ stocks from major indices
- ✅ Automatic updates from Wikipedia
- ✅ Fallback to 160+ stocks
- ✅ Filters by price, volume, volatility
- ✅ Randomized selection for variety

## Troubleshooting

### "Using fallback stock universe"

This message appears when:
- pandas is not installed: `pip install pandas>=2.0.0`
- Wikipedia is unreachable
- Network connectivity issues

**Solution**: Install pandas for Wikipedia integration, or rely on the 160-stock fallback.

### "No stocks passed screening criteria"

Your filters may be too strict. Try:
- Increase `MAX_STOCK_PRICE`
- Decrease `MIN_DAILY_VOLUME`
- Increase `MAX_STOCK_VOLATILITY`

### Slow Screening Performance

To improve speed:
- Ensure cache file exists: `.stock_universe_cache.pkl`
- Reduce `MAX_DISCOVERED_STOCKS` in `.env`
- Check that caching is enabled (`use_cache=True`)

## Technical Details

### Stock Universe Sources

1. **S&P 500**: ~500 large-cap US stocks
   - Source: `https://en.wikipedia.org/

2. **NASDAQ-100**: Top 100 non-financial NASDAQ stocks
   - Source: `https://en.wikipedia.org/wiki/Nasdaq-100`

3. **Dow Jones**: 30 blue-chip industrial stocks
   - Source: `https://en.wikipedia.org/

### Fallback Universe

When Wikipedia unavailable, uses a curated list of 160 stocks:
- 20 major tech stocks
- 20 healthcare stocks
- 20 financial stocks
- 20 consumer stocks
- 20 energy stocks
- 20 industrial stocks
- 20 communications stocks
- 20 materials stocks
- 10 utilities
- 10 real estate

### Cache File Format

- **File**: `.stock_universe_cache.pkl`
- **Format**: Python pickle (set of strings)
- **Lifespan**: 24 hours
- **Size**: ~5-10 KB
- **Location**: Bot root directory

## Best Practices

1. **Start Conservative**: Begin with strict filters, relax as needed
2. **Monitor Performance**: Watch for stocks meeting criteria
3. **Regular Updates**: Let cache refresh naturally (24 hours)
4. **Diversification**: Use `MAX_DISCOVERED_STOCKS >= 10` for better diversity
5. **Test First**: Run `python3 stock_screener.py` before live trading

## Related Environment Variables

```bash
# Stock Screener
ENABLE_STOCK_SCREENER=true
MAX_DISCOVERED_STOCKS=10

# Filtering
MIN_STOCK_PRICE=5.0
MAX_STOCK_PRICE=1000.0
MIN_DAILY_VOLUME=500000
MAX_STOCK_VOLATILITY=0.15

# Fallback
SCAN_SYMBOLS_FILE=scan_symbols.txt
```

## See Also

- [README.md](README.md): Main documentation
- [TRADING_ENHANCEMENTS_GUIDE.md](TRADING_ENHANCEMENTS_GUIDE.md): Trading features
- [.env.example](.env.example): Full configuration reference
