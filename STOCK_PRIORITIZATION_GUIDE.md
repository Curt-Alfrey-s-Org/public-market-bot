# Stock Prioritization Guide - TOS-like Scanning

## Overview

The market-pie5-bot now includes **TOS-like stock prioritization** that scans a large pool of stocks and ranks them by quality, then trades the best opportunities first. This mimics the behavior of ThinkOrSwim (TOS) stock scanners.

## Key Features

### 🎯 Smart Prioritization
- **Scan Many, Trade Best**: Scans 100+ stocks but only trades the top-ranked opportunities
- **Multi-Factor Scoring**: Ranks stocks based on momentum, volume, volatility, liquidity, and sentiment
- **Customizable Weights**: Adjust scoring factors to match your trading strategy
- **Priority Trading Order**: Bot trades #1 first, then #2, #3, etc. in order of quality

### ⚡ TOS-like Behavior
- **Large Initial Scan**: Screens up to 100 stocks from major indices (configurable)
- **Intelligent Filtering**: Applies price, volume, and volatility filters
- **Quality Ranking**: Scores each stock on a 0-100 scale
- **Top N Selection**: Returns only the best 50 stocks (configurable)

### 📊 Composite Scoring System

Each stock is scored on 5 factors:

1. **Momentum Score (30% weight)**: Price action strength and trend
2. **Volume Score (20% weight)**: Trading activity vs average
3. **Volatility Score (20% weight)**: Risk/opportunity balance (moderate preferred)
4. **Liquidity Score (15% weight)**: Market cap and ease of trading
5. **Sentiment Score (15% weight)**: News sentiment (if enabled)

**Composite Score = (Momentum × 0.30) + (Volume × 0.20) + (Volatility × 0.20) + (Liquidity × 0.15) + (Sentiment × 0.15)**

## Configuration

### Basic Setup

In your `.env` file:

```bash
# Enable stock screener with prioritization
ENABLE_STOCK_SCREENER=true

# How many stocks to scan initially (larger = better selection)
MAX_STOCKS_TO_SCAN=100

# How many top stocks to trade after ranking
TOP_STOCKS_TO_TRADE=50

# How many stocks to actually trade (from the top-ranked list)
MAX_DISCOVERED_STOCKS=10
```

### Scoring Weights

Customize how stocks are ranked:

```bash
# Scoring weights (must sum to ~1.0)
SCORE_WEIGHT_MOMENTUM=0.3       # Price trend strength
SCORE_WEIGHT_VOLUME=0.2          # Trading activity
SCORE_WEIGHT_VOLATILITY=0.2      # Price stability
SCORE_WEIGHT_LIQUIDITY=0.15      # Market cap/ease of trading
SCORE_WEIGHT_SENTIMENT=0.15      # News sentiment
```

### Filtering Criteria

Set your screening parameters:

```bash
# Stock Filtering
MIN_STOCK_PRICE=5.0              # Minimum price per share
MAX_STOCK_PRICE=1000.0           # Maximum price per share
MIN_DAILY_VOLUME=500000          # Minimum daily trading volume
MAX_STOCK_VOLATILITY=0.15        # Maximum volatility (15%)
```

## How It Works

### Step 1: Universe Selection
```
Bot starts with 500+ stocks from:
- S&P 500
- NASDAQ-100
- Dow Jones
- S&P 400 Mid-Cap
```

### Step 2: Initial Screening
```
Apply basic filters:
✓ Price in range ($5 - $1000)
✓ Volume > 500,000 daily
✓ Volatility < 15%
```

### Step 3: Scoring & Ranking
```
For each passing stock:
1. Calculate momentum score (0-1)
2. Calculate volume score (0-1)
3. Calculate volatility score (0-1)
4. Calculate liquidity score (0-1)
5. Calculate sentiment score (0-1) [if enabled]
6. Compute weighted composite score (0-100)
```

### Step 4: Prioritization
```
Sort stocks by composite score (highest first)
Select top 50 stocks (or TOP_STOCKS_TO_TRADE)
Return prioritized list
```

### Step 5: Trading
```
Trade stocks in priority order:
  #1: Best opportunity (highest score)
  #2: Second best
  #3: Third best
  ...and so on
```

## Usage Examples

### Example 1: Conservative Trading (Large Cap Focus)

```bash
# Focus on large, stable companies
MAX_STOCKS_TO_SCAN=50
TOP_STOCKS_TO_TRADE=20
MAX_DISCOVERED_STOCKS=5

MIN_STOCK_PRICE=50.0
MAX_STOCK_PRICE=500.0
MIN_DAILY_VOLUME=5000000         # 5M+
MAX_STOCK_VOLATILITY=0.10        # 10% max

# Emphasize liquidity and stability
SCORE_WEIGHT_MOMENTUM=0.2
SCORE_WEIGHT_VOLUME=0.2
SCORE_WEIGHT_VOLATILITY=0.2
SCORE_WEIGHT_LIQUIDITY=0.3       # Higher weight
SCORE_WEIGHT_SENTIMENT=0.1
```

### Example 2: Aggressive Trading (Momentum Focus)

```bash
# Look for high-momentum opportunities
MAX_STOCKS_TO_SCAN=150
TOP_STOCKS_TO_TRADE=75
MAX_DISCOVERED_STOCKS=20

MIN_STOCK_PRICE=10.0
MAX_STOCK_PRICE=200.0
MIN_DAILY_VOLUME=1000000         # 1M+
MAX_STOCK_VOLATILITY=0.25        # 25% max (higher risk)

# Emphasize momentum and volume
SCORE_WEIGHT_MOMENTUM=0.4        # Higher weight
SCORE_WEIGHT_VOLUME=0.3          # Higher weight
SCORE_WEIGHT_VOLATILITY=0.1
SCORE_WEIGHT_LIQUIDITY=0.1
SCORE_WEIGHT_SENTIMENT=0.1
```

### Example 3: Balanced Strategy

```bash
# Default balanced approach
MAX_STOCKS_TO_SCAN=100
TOP_STOCKS_TO_TRADE=50
MAX_DISCOVERED_STOCKS=10

MIN_STOCK_PRICE=5.0
MAX_STOCK_PRICE=1000.0
MIN_DAILY_VOLUME=500000
MAX_STOCK_VOLATILITY=0.15

# Equal emphasis on all factors
SCORE_WEIGHT_MOMENTUM=0.3
SCORE_WEIGHT_VOLUME=0.2
SCORE_WEIGHT_VOLATILITY=0.2
SCORE_WEIGHT_LIQUIDITY=0.15
SCORE_WEIGHT_SENTIMENT=0.15
```

## Sample Output

When running the bot with prioritization:

```
[STOCK SCREENER] Discovering tradeable stocks with prioritization...
Prioritization enabled: scanning up to 100 stocks to find top 10

Screening from universe of 503 stocks...
✓ AAPL: $178.50, Score: 82.3
✓ MSFT: $410.25, Score: 79.8
✓ NVDA: $495.50, Score: 85.1
...

Prioritization complete: 10/87 top stocks selected
Top stocks by priority:
  #1: NVDA - Score: 85.1/100
  #2: AAPL - Score: 82.3/100
  #3: MSFT - Score: 79.8/100
  #4: GOOGL - Score: 78.5/100
  #5: AMD - Score: 77.2/100
  #6: META - Score: 76.8/100
  #7: TSLA - Score: 74.3/100
  #8: AVGO - Score: 72.1/100
  #9: ORCL - Score: 71.5/100
  #10: CRM - Score: 70.9/100

[READY TO START TRADING]
Symbols to trade: 10 (in priority order)
NOTE: Bot will trade stocks in priority order (best opportunities first)

--- Executing Paper Trading Trades (Priority Order) ---
Trading best opportunities first, then #2, #3, etc.

[Priority #1/10] Processing NVDA...
Retrieved price for NVDA: $495.50
Processing trade for NVDA...
✓ BUY executed: NVDA @ $495.50

[Priority #2/10] Processing AAPL...
Retrieved price for AAPL: $178.50
Processing trade for AAPL...
✓ BUY executed: AAPL @ $178.50

...
```

## Scoring Details

### Momentum Score
- **High Score**: Moderate volatility (5-10%), indicating healthy price action
- **Medium Score**: Low volatility (<5%) or high volatility (10-15%)
- **Low Score**: Extreme volatility (>15%)

### Volume Score
- **High Score**: Current volume >= average volume
- **Medium Score**: Current volume 50-100% of average
- **Low Score**: Current volume < 50% of average

### Volatility Score
- **High Score**: Volatility in sweet spot (3-8%) - ideal for swing trading
- **Medium Score**: Low volatility (<3%) or moderate high (8-12%)
- **Low Score**: High volatility (>12%)

### Liquidity Score
- **High Score**: Mega/Large cap (>$10B market cap)
- **Medium Score**: Mid cap ($2B-$10B)
- **Low Score**: Small cap (<$2B)

### Sentiment Score
- **High Score**: Positive news sentiment (>0.5)
- **Medium Score**: Neutral sentiment (0.3-0.5)
- **Low Score**: Negative sentiment (<0.3)

## Comparison: Before vs After

### Before (No Prioritization)
```
❌ Scanned first 10 stocks that passed filters
❌ No quality ranking
❌ No guarantee of best opportunities
❌ Random order based on symbol list
❌ May trade lower-quality stocks
```

### After (With Prioritization)
```
✅ Scans 100+ stocks to find best
✅ Ranks all candidates by quality
✅ Guarantees top opportunities traded first
✅ Trades in priority order (#1, #2, #3...)
✅ Consistent quality selection
```

## Best Practices

1. **Start with Defaults**: Use default settings first, then optimize
2. **Monitor Scores**: Watch the composite scores in logs to understand rankings
3. **Adjust Weights**: Tune scoring weights based on your strategy
4. **Balance Pool Size**: Larger scan pool = better selection but slower
5. **Consider Market Conditions**: Adjust volatility threshold based on market

## Troubleshooting

### "No stocks passed screening"
- Your filters may be too strict
- Try increasing `MAX_STOCK_PRICE` or `MAX_STOCK_VOLATILITY`
- Try decreasing `MIN_DAILY_VOLUME`

### "Screening takes too long"
- Reduce `MAX_STOCKS_TO_SCAN` (try 50 instead of 100)
- Increase `STOCK_FETCH_DELAY` to reduce API load
- Check internet connection speed

### "Scores seem wrong"
- Verify scoring weights sum to ~1.0
- Check that stock data is being fetched correctly
- Review individual score components in logs (enable debug logging)

### "Bot trades in wrong order"
- Ensure `ENABLE_STOCK_SCREENER=true`
- Verify `prioritize=True` in screen_stocks() call
- Check that composite scores are being calculated

## Advanced Tips

### Custom Scoring Strategy

To emphasize a specific factor, adjust weights:

```bash
# Momentum-heavy strategy
SCORE_WEIGHT_MOMENTUM=0.5
SCORE_WEIGHT_VOLUME=0.2
SCORE_WEIGHT_VOLATILITY=0.1
SCORE_WEIGHT_LIQUIDITY=0.1
SCORE_WEIGHT_SENTIMENT=0.1
```

### Combine with Other Features

```bash
# Use with sentiment analysis
ENABLE_SENTIMENT_FILTER=true
ENABLE_STOCK_SCREENER=true
SCORE_WEIGHT_SENTIMENT=0.25      # Increase sentiment weight

# Use with ML filtering
ENABLE_ML_FILTER=true
MIN_ML_CONFIDENCE=0.7
MIN_ML_WIN_PROBABILITY=0.60
```

### Performance Tuning

```bash
# Fast scanning (less thorough)
MAX_STOCKS_TO_SCAN=50
STOCK_FETCH_DELAY=0.05

# Thorough scanning (slower)
MAX_STOCKS_TO_SCAN=200
STOCK_FETCH_DELAY=0.2
```

## Related Configuration

```bash
# Stock Screener
ENABLE_STOCK_SCREENER=true
MAX_STOCKS_TO_SCAN=100
TOP_STOCKS_TO_TRADE=50
MAX_DISCOVERED_STOCKS=10

# Scoring Weights
SCORE_WEIGHT_MOMENTUM=0.3
SCORE_WEIGHT_VOLUME=0.2
SCORE_WEIGHT_VOLATILITY=0.2
SCORE_WEIGHT_LIQUIDITY=0.15
SCORE_WEIGHT_SENTIMENT=0.15

# Filtering
MIN_STOCK_PRICE=5.0
MAX_STOCK_PRICE=1000.0
MIN_DAILY_VOLUME=500000
MAX_STOCK_VOLATILITY=0.15

# Performance
STOCK_SCREENER_MAX_CHECK=100
STOCK_FETCH_DELAY=0.1
```

## See Also

- [STOCK_SCREENER_GUIDE.md](STOCK_SCREENER_GUIDE.md): Basic stock screener documentation
- [TRADING_ENHANCEMENTS_GUIDE.md](TRADING_ENHANCEMENTS_GUIDE.md): Trading strategies
- [.env.example](.env.example): Full configuration reference
- [README.md](README.md): Main documentation
