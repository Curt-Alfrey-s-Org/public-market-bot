# Top Performers Watchlist Guide

## Overview

The **Top Performers Watchlist** is an intelligent feature that displays the top 50 stocks with the highest probability of winning trades on the web GUI dashboard. The watchlist uses advanced ML predictions, sentiment analysis, and technical indicators to rank stocks, ensuring the bot trades the most promising opportunities first.

## Features

### 1. **Intelligent Stock Ranking**
- Combines multiple scoring factors:
  - **ML Win Probability**: Machine learning predictions of trade success
  - **Sentiment Analysis**: News sentiment scores from multiple sources
  - **Technical Indicators**: Price, volume, and volatility metrics
  - **Portfolio Diversification**: Correlation analysis for risk management

### 2. **Real-Time Updates**
- Auto-refreshes every 60 seconds (configurable)
- Manual refresh button for on-demand updates
- Displays current price, volume, and win probability for each stock

### 3. **Bot Integration**
- Bot automatically prioritizes watchlist stocks when trading
- Trades highest probability stocks first
- Falls back to traditional screener if watchlist is unavailable

### 4. **Interactive Dashboard**
- Clean, modern table design with dark theme
- Sortable columns for custom analysis
- Stock count indicator
- Visual feedback on refresh

## Configuration

### Environment Variables

Add these to your `.env` file to configure the watchlist:

```bash
# Enable/disable the watchlist (default: true)
ENABLE_TOP_PERFORMERS_WATCHLIST=true

# Number of top stocks to display (default: 50, max recommended: 100)
TOP_PERFORMERS_WATCHLIST_SIZE=50

# Auto-refresh interval in seconds (default: 60)
TOP_PERFORMERS_REFRESH_INTERVAL=60

# Minimum stocks in universe before screening (default: 100)
TOP_PERFORMERS_MIN_UNIVERSE=100
```

### Prerequisites

For best results, enable these features in your `.env`:

```bash
# Enable stock screener to discover stocks
ENABLE_STOCK_SCREENER=true

# Enable ML filtering for win probability predictions
ENABLE_ML_FILTER=true

# Enable sentiment analysis for news-based scoring
ENABLE_SENTIMENT_FILTER=true

# Enable portfolio optimization for diversification
ENABLE_PORTFOLIO_OPTIMIZATION=true
```

## Usage

### Accessing the Watchlist

1. **Start the Web GUI**:
   ```bash
   ./start_web_gui.sh
   ```

2. **Navigate to Dashboard**:
   - The watchlist appears on the main Dashboard tab
   - Located between the price chart and recent activity sections

3. **View Top Performers**:
   - Table shows ranked stocks sorted by win probability
   - Columns include: Rank, Symbol, Win Probability, Price, Volume, Sentiment, Score

### Manual Refresh

Click the **Refresh** button in the watchlist header to manually update the data:
- Fetches latest stock prices
- Recalculates win probabilities
- Updates sentiment scores
- Re-ranks all stocks

### Trading with Watchlist

When the bot starts, it will:
1. Check if watchlist is enabled (`ENABLE_TOP_PERFORMERS_WATCHLIST=true`)
2. Load top performers from watchlist (pre-sorted by win probability)
3. Trade stocks in priority order (highest probability first)
4. Fall back to traditional screener if watchlist is empty

**Bot Log Example**:
```
[10:30:15] Using top performers from watchlist (50 stocks)
[10:30:15] Trading priority: AAPL, MSFT, NVDA, GOOGL, AMZN... (top 5)
[10:30:15] Loaded 50 symbols for scanning
[10:30:15] Trading 5 symbols (MAX_SYMBOLS_TO_TRADE=5)
[10:30:15] Bot will trade highest probability stocks first: AAPL, MSFT, NVDA, GOOGL, AMZN
```

## Watchlist Data Structure

Each stock in the watchlist contains:

```python
{
    'symbol': 'AAPL',                    # Stock ticker symbol
    'win_probability': 0.75,             # ML-predicted win probability (0-1)
    'composite_score': 0.72,             # Overall composite score (0-1)
    'sentiment_score': 0.65,             # News sentiment score (0-1)
    'ml_confidence': 0.80,               # ML model confidence (0-1)
    'sentiment_signal': 'Positive',      # Sentiment classification
    'price': 150.00,                     # Current stock price
    'volume': 1000000,                   # Daily trading volume
    'volatility': 0.02,                  # Price volatility metric
    'last_updated': '2026-01-21T22:00:00'  # Last update timestamp
}
```

## API Reference

### Stock Screener Functions

#### `get_top_performers_watchlist(max_stocks=50)`

Convenience function to get top performing stocks for the watchlist.

**Parameters**:
- `max_stocks` (int): Maximum number of top performers to return (default: 50)

**Returns**:
- List of dictionaries with stock data sorted by win probability (highest first)

**Example**:
```python
from stock_screener import get_top_performers_watchlist

# Get top 25 performers
top_stocks = get_top_performers_watchlist(max_stocks=25)

for stock in top_stocks[:5]:
    print(f"{stock['symbol']}: {stock['win_probability']:.2%} win probability")
```

#### `StockScreener.get_top_performers(max_results=50, ...)`

Get top performing stocks ranked by win probability.

**Parameters**:
- `max_results` (int): Maximum number of top performers to return
- `min_universe_size` (int): Minimum stocks in universe before screening (default: 100)
- `sentiment_weight` (float): Weight for sentiment score 0-1 (default: 0.3)
- `ml_weight` (float): Weight for ML win probability 0-1 (default: 0.5)
- `diversification_weight` (float): Weight for diversification 0-1 (default: 0.2)

**Returns**:
- List of stock dictionaries sorted by win probability

**Example**:
```python
from stock_screener import StockScreener

screener = StockScreener()
performers = screener.get_top_performers(
    max_results=30,
    sentiment_weight=0.4,
    ml_weight=0.5,
    diversification_weight=0.1
)
```

### Web GUI Functions

#### `fetch_watchlist_data()`

Fetch top performers watchlist data from stock screener.

**Returns**:
- List of stock dictionaries sorted by win probability

#### `update_watchlist_data(force_refresh=False)`

Update the global watchlist data if needed.

**Parameters**:
- `force_refresh` (bool): Force refresh even if cache is valid

**Returns**:
- True if updated, False if skipped

#### `format_watchlist_table(watchlist)`

Format watchlist data as a Dash DataTable component.

**Parameters**:
- `watchlist` (list): List of stock dictionaries

**Returns**:
- Dash DataTable component or empty message div

## Performance Optimization

### Caching

The watchlist uses intelligent caching to minimize API calls:

- **Refresh Interval**: Only fetches new data every 60 seconds (default)
- **Stock Data Cache**: Individual stock data cached for 60 seconds
- **Universe Cache**: Stock universe cached for 24 hours
- **Manual Override**: Refresh button forces immediate update

### Resource Management

- **Lazy Loading**: Watchlist only loads when enabled
- **Batch Processing**: Processes multiple stocks in single screener call
- **Fallback Support**: Gracefully handles API failures
- **Rate Limiting**: Respects API rate limits with exponential backoff

## Troubleshooting

### Watchlist Not Appearing

**Symptom**: Watchlist section is hidden or shows "disabled" message

**Solutions**:
1. Check `.env` file: `ENABLE_TOP_PERFORMERS_WATCHLIST=true`
2. Ensure stock screener is enabled: `ENABLE_STOCK_SCREENER=true`
3. Restart the web GUI after changing settings

### Empty Watchlist

**Symptom**: Watchlist shows "No stocks in watchlist" message

**Possible Causes**:
1. **Stock screener not finding stocks**: Lower your filtering thresholds
   ```bash
   MIN_STOCK_PRICE=5.0
   MAX_STOCK_PRICE=1000.0
   MIN_DAILY_VOLUME=100000
   ```

2. **ML filter too strict**: Lower confidence thresholds
   ```bash
   MIN_ML_CONFIDENCE=0.5
   MIN_ML_WIN_PROBABILITY=0.5
   ```

3. **Sentiment filter too strict**: Lower sentiment threshold
   ```bash
   MIN_SENTIMENT_SCORE=-0.5
   ```

4. **Stock universe too small**: Increase universe size or disable filters temporarily

### Slow Loading

**Symptom**: Watchlist takes a long time to refresh

**Solutions**:
1. Reduce watchlist size: `TOP_PERFORMERS_WATCHLIST_SIZE=25`
2. Increase refresh interval: `TOP_PERFORMERS_REFRESH_INTERVAL=120`
3. Disable resource-intensive filters temporarily
4. Check internet connection and API status

### Incorrect Rankings

**Symptom**: Stocks don't appear to be ranked by win probability

**Solutions**:
1. Check ML model is trained: Run bot in training mode first
2. Verify sentiment API keys are configured
3. Ensure sufficient historical data exists
4. Review logs for scoring errors: Check terminal/logs tab

## Advanced Usage

### Custom Scoring Weights

Adjust the relative importance of different factors:

```python
from stock_screener import StockScreener

screener = StockScreener()

# Emphasize ML predictions over sentiment
performers = screener.get_top_performers(
    max_results=50,
    sentiment_weight=0.2,    # 20% sentiment
    ml_weight=0.6,           # 60% ML predictions
    diversification_weight=0.2  # 20% diversification
)
```

### Integration with Custom Trading Logic

Use watchlist data in your own trading algorithms:

```python
from stock_screener import get_top_performers_watchlist

# Get top performers
watchlist = get_top_performers_watchlist(max_stocks=50)

# Filter by your criteria
high_confidence = [
    stock for stock in watchlist
    if stock['win_probability'] > 0.7 and stock['ml_confidence'] > 0.75
]

# Trade filtered stocks
for stock in high_confidence[:5]:  # Top 5 only
    print(f"Trading {stock['symbol']} - {stock['win_probability']:.2%} win prob")
    # Your trading logic here
```

### Scheduled Watchlist Updates

Run watchlist updates on a schedule using cron:

```bash
# Update watchlist every 30 minutes during market hours
*/30 9-16 * * 1-5 cd /path/to/market-pie5-bot && ./venv/bin/python3 -c "from stock_screener import get_top_performers_watchlist; get_top_performers_watchlist()" >> watchlist.log 2>&1
```

## Best Practices

1. **Enable ML Features**: Train the ML model before relying on win probabilities
2. **Monitor Performance**: Track actual vs. predicted win rates
3. **Adjust Weights**: Fine-tune scoring weights based on your trading style
4. **Use Reasonable Sizes**: 25-50 stocks is optimal for most strategies
5. **Review Regularly**: Check watchlist composition changes over time
6. **Combine with Analysis**: Use watchlist as a starting point, not sole criterion
7. **Test Thoroughly**: Use paper trading mode to validate watchlist effectiveness

## See Also

- [Stock Screener Guide](STOCK_SCREENER_GUIDE.md) - Stock discovery and filtering
- [ML Guide](ML_GUIDE.md) - Machine learning features and training
- [Sentiment Analysis Guide](SENTIMENT_PORTFOLIO_GUIDE.md) - News sentiment integration
- [Web GUI Guide](WEB_GUI_GUIDE.md) - Web dashboard features
- [Trading Enhancements Guide](TRADING_ENHANCEMENTS_GUIDE.md) - Advanced trading features

## Support

If you encounter issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review logs in the Logs tab of the web GUI
3. Check [Known Issues](KNOWN_ISSUES.md)
4. Open an issue on GitHub with:
   - Your `.env` configuration (remove API keys!)
   - Relevant log messages
   - Steps to reproduce the problem
