# Sentiment Analysis and Portfolio Optimization Guide

## Overview

The market-pie5-bot now includes advanced sentiment analysis and portfolio optimization capabilities to enhance trading decisions and portfolio management.

---

## 📊 Sentiment Analysis

### What is Sentiment Analysis?

Sentiment analysis evaluates news articles and media coverage to determine market sentiment (positive, negative, or neutral) for stocks. This helps avoid trading stocks with negative news and identify promising opportunities.

### Features

- **Multiple News Sources**: Integrates with NewsAPI and Finnhub for comprehensive coverage
- **Dual Analysis Methods**: Supports both VADER and TextBlob sentiment analysis
- **Smart Caching**: Reduces API calls by caching sentiment data for 1 hour
- **Automatic Filtering**: Blocks trades on stocks with strongly negative sentiment
- **Confidence Scoring**: Provides confidence metrics based on article count and consistency

### Setup

#### 1. Get API Keys

**NewsAPI (Optional but Recommended)**
- Visit: https://newsapi.org
- Sign up for free account
- Get API key (100 requests/day on free tier)
- Add to `.env`: `NEWS_API_KEY=your_api_key`

**Finnhub (Alternative/Supplement)**
- Visit: https://finnhub.io
- Sign up for free account
- Get API key (60 calls/minute on free tier)
- Add to `.env`: `FINNHUB_API_KEY=your_api_key`

#### 2. Install Dependencies

```bash
pip install vaderSentiment textblob
```

#### 3. Configure Sentiment Method

Add to `.env`:
```bash
# Choose sentiment analysis method
SENTIMENT_METHOD=vader  # or 'textblob'
```

### How It Works

1. **News Fetching**: When evaluating a stock, the bot fetches recent news articles (last 7 days by default)
2. **Sentiment Scoring**: Each article is analyzed for sentiment (positive/negative/neutral)
3. **Aggregation**: Sentiment scores are aggregated into an overall score (-1 to +1)
4. **Signal Generation**: 
   - Score > 0.2: BULLISH
   - Score < -0.2: BEARISH
   - Otherwise: NEUTRAL
5. **Trading Decision**: Trades are blocked if sentiment is strongly negative

### Sentiment Metrics

```python
{
    'overall_score': 0.45,        # -1 (very negative) to +1 (very positive)
    'sentiment_signal': 'BULLISH',  # BULLISH, BEARISH, or NEUTRAL
    'article_count': 15,            # Number of articles analyzed
    'confidence': 0.75,             # Confidence in sentiment (0-1)
    'positive_ratio': 0.67,         # Percentage of positive articles
    'negative_ratio': 0.13,         # Percentage of negative articles
    'neutral_ratio': 0.20           # Percentage of neutral articles
}
```

### Example Output

```
[SENTIMENT FILTER - TRADE SKIPPED]
  Symbol: XYZ
  Reason: Negative sentiment (score=-0.45, signal=BEARISH)
```

### Filtering Thresholds

You can customize sentiment filtering in your trading code:

```python
# Default thresholds
should_trade, reason = bot.sentiment_analyzer.should_trade_based_on_sentiment(
    symbol='AAPL',
    min_score=0.1,      # Minimum sentiment score
    min_confidence=0.3  # Minimum confidence threshold
)
```

---

## 📈 Portfolio Optimization

### What is Portfolio Optimization?

Portfolio optimization uses Modern Portfolio Theory (MPT) to determine the optimal allocation of capital across multiple stocks, balancing risk and return.

### Features

- **Multiple Optimization Methods**:
  - **Sharpe Ratio**: Maximize risk-adjusted returns
  - **Minimum Variance**: Minimize portfolio volatility
  - **Risk Parity**: Equal risk contribution from each asset
  - **Equal Weight**: Simple equal allocation (baseline)

- **Correlation Analysis**: Measures how stocks move together
- **Diversification Scoring**: Quantifies portfolio diversification (0-1)
- **Efficient Frontier**: Visualizes optimal risk-return tradeoffs
- **Rebalancing Suggestions**: Identifies when to rebalance portfolio

### Setup

#### Install Dependencies

```bash
pip install scipy numpy pandas
```

### Optimization Methods

#### 1. Maximum Sharpe Ratio (Recommended)

Finds the portfolio with the best risk-adjusted return.

```python
allocations = bot.get_portfolio_optimal_allocation(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    method='sharpe'
)
# Result: {'AAPL': 4000, 'MSFT': 3500, 'GOOGL': 2500}
```

**Best for**: Balancing returns and risk

#### 2. Minimum Variance

Finds the portfolio with the lowest volatility.

```python
allocations = bot.get_portfolio_optimal_allocation(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    method='min_variance'
)
```

**Best for**: Conservative investors prioritizing stability

#### 3. Risk Parity

Allocates so each asset contributes equally to portfolio risk.

```python
allocations = bot.get_portfolio_optimal_allocation(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    method='risk_parity'
)
```

**Best for**: Balanced risk exposure across assets

#### 4. Equal Weight

Simple equal allocation (baseline comparison).

```python
allocations = bot.get_portfolio_optimal_allocation(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    method='equal'
)
# Result: {'AAPL': 3333.33, 'MSFT': 3333.33, 'GOOGL': 3333.34}
```

**Best for**: Simplicity and avoiding optimization complexity

### Diversification Score

Measures how well-diversified your portfolio is:

```python
score = bot.calculate_portfolio_diversification(['AAPL', 'MSFT', 'GOOGL'])
# Result: 0.75 (0=low diversification, 1=high diversification)
```

- **0.0-0.3**: Low diversification (highly correlated assets)
- **0.3-0.7**: Moderate diversification
- **0.7-1.0**: High diversification (low correlation)

### Correlation Matrix

View how stocks move together:

```python
corr_matrix = bot.portfolio_optimizer.calculate_correlation_matrix(['AAPL', 'MSFT', 'GOOGL'])
```

- **1.0**: Perfect positive correlation (move together)
- **0.0**: No correlation (independent)
- **-1.0**: Perfect negative correlation (move opposite)

### Rebalancing

Automatically suggest rebalancing trades:

```python
current_positions = {'AAPL': 5000, 'MSFT': 3000, 'GOOGL': 2000}
target_allocations = {'AAPL': 3333, 'MSFT': 3333, 'GOOGL': 3334}

trades = bot.portfolio_optimizer.suggest_rebalancing(
    current_positions,
    target_allocations,
    threshold=0.05  # 5% deviation threshold
)
# Result: {'AAPL': -1667, 'GOOGL': 1334}  # Sell AAPL, Buy GOOGL
```

---

## 🔧 Integration with Trading Bot

### Automatic Integration

Both sentiment analysis and portfolio optimization are automatically integrated into the trading bot when the required dependencies are installed.

### Bot Summary Output

The bot summary now includes sentiment and portfolio status:

```
TRADING BOT UPDATED SUMMARY
============================================================
Mode: PAPER TRADING (Schwab Sandbox)
...

Sentiment Analysis: Enabled
  Method: vader
  NewsAPI: Configured
  Finnhub: Configured

Portfolio Optimization: Enabled
  Risk-Free Rate: 2.00%
  Portfolio Diversification: 0.72 (0=low, 1=high)
============================================================
```

### Trade Filtering

Sentiment filtering is automatically applied during stock filtering:

1. Price filter (avoid penny stocks)
2. Volume filter (ensure liquidity)
3. Volatility filter (manage risk)
4. **Sentiment filter (NEW)** - Blocks negative sentiment stocks

---

## 📖 Usage Examples

### Example 1: Sentiment-Aware Trading

```python
from main import TradingBot

bot = TradingBot(total_capital=10000)

# Check sentiment before trading
should_trade, reason = bot.check_sentiment_filter('AAPL')
if should_trade:
    # Proceed with trade
    bot.execute_trade('AAPL', 'BUY', 150.0)
else:
    print(f"Trade blocked: {reason}")
```

### Example 2: Portfolio Optimization

```python
from main import TradingBot

bot = TradingBot(total_capital=10000)

# Add price history for multiple symbols
symbols = ['AAPL', 'MSFT', 'GOOGL']

# Get optimal allocation
allocations = bot.get_portfolio_optimal_allocation(
    symbols,
    method='sharpe'  # or 'min_variance', 'risk_parity', 'equal'
)

print("Optimal Allocation:")
for symbol, amount in allocations.items():
    print(f"  {symbol}: ${amount:.2f}")

# Check diversification
diversification = bot.calculate_portfolio_diversification(symbols)
print(f"Portfolio Diversification: {diversification:.2f}")
```

### Example 3: Combined Sentiment + Optimization

```python
from main import TradingBot

bot = TradingBot(total_capital=10000)

# Candidate symbols
candidates = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

# Filter by sentiment
approved_symbols = []
for symbol in candidates:
    should_trade, reason = bot.check_sentiment_filter(symbol)
    if should_trade:
        approved_symbols.append(symbol)
        print(f"✓ {symbol}: {reason}")
    else:
        print(f"✗ {symbol}: {reason}")

# Optimize portfolio with approved symbols only
if approved_symbols:
    allocations = bot.get_portfolio_optimal_allocation(
        approved_symbols,
        method='sharpe'
    )
    
    print("\nOptimal Portfolio:")
    for symbol, amount in allocations.items():
        print(f"  {symbol}: ${amount:.2f}")
```

---

## 🧪 Testing

### Run Sentiment Tests

```bash
python3 -m unittest test_sentiment_analyzer -v
```

**Test Coverage**:
- Sentiment scoring (VADER and TextBlob)
- News fetching (NewsAPI and Finnhub)
- Caching mechanisms
- Trading decision logic
- Edge cases and error handling

### Run Portfolio Optimization Tests

```bash
python3 -m unittest test_portfolio_optimizer -v
```

**Test Coverage**:
- Correlation and covariance matrices
- All optimization methods
- Diversification scoring
- Rebalancing suggestions
- Edge cases and numerical stability

---

## ⚙️ Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Sentiment Analysis
NEWS_API_KEY=your_news_api_key
FINNHUB_API_KEY=your_finnhub_api_key
SENTIMENT_METHOD=vader

# Portfolio Optimization
BOT_RISK_FREE_RATE=0.02  # 2% risk-free rate for Sharpe ratio
```

### Customization Options

You can customize thresholds and parameters:

```python
# Sentiment filtering thresholds
min_score = 0.1        # Minimum sentiment score (-1 to 1)
min_confidence = 0.3   # Minimum confidence (0 to 1)

# Portfolio optimization
risk_free_rate = 0.02  # Risk-free rate for Sharpe ratio
rebalance_threshold = 0.05  # 5% deviation triggers rebalancing
```

---

## 📊 Performance Impact

### Sentiment Analysis
- **API Calls**: 1-2 per symbol (cached for 1 hour)
- **Processing Time**: < 1 second per symbol
- **Memory**: Minimal (< 1 MB cache per symbol)

### Portfolio Optimization
- **Processing Time**: < 1 second for 5-10 symbols
- **Memory**: Minimal (< 5 MB for price history)
- **CPU**: Moderate during optimization (scipy solver)

---

## 🔍 Troubleshooting

### Sentiment Analysis Issues

**Problem**: "No news articles found"
- **Solution**: Check API keys are configured correctly
- Verify symbols are traded on major exchanges
- Some symbols may have limited news coverage

**Problem**: "Sentiment method not available"
- **Solution**: Install required libraries:
  ```bash
  pip install vaderSentiment textblob
  ```

### Portfolio Optimization Issues

**Problem**: "Insufficient data for optimization"
- **Solution**: Ensure at least 20 price points per symbol
- Wait for more trading sessions to accumulate data
- Use 'equal' method as fallback

**Problem**: "Optimization failed"
- **Solution**: Check that scipy is installed:
  ```bash
  pip install scipy
  ```
- Verify price data is valid (no NaN values)

---

## 🚀 Best Practices

1. **Use Multiple News Sources**: Configure both NewsAPI and Finnhub for comprehensive coverage

2. **Monitor Sentiment Trends**: Track sentiment over time for better signals

3. **Combine Methods**: Use sentiment for filtering + portfolio optimization for allocation

4. **Regular Rebalancing**: Check rebalancing suggestions weekly or monthly

5. **Diversification**: Aim for diversification score > 0.5

6. **Test First**: Run in paper trading mode to validate sentiment accuracy

7. **Cache Management**: Sentiment cache expires after 1 hour - adjust if needed

8. **API Limits**: Be mindful of free tier limits:
   - NewsAPI: 100 requests/day
   - Finnhub: 60 requests/minute

---

## 📚 Additional Resources

- **Modern Portfolio Theory**: https://en.wikipedia.org/
- **Sentiment Analysis**: https://en.wikipedia.org/wiki/Sentiment_analysis
- **VADER Sentiment**: https://github.com/cjhutto/vaderSentiment
- **NewsAPI Documentation**: https://newsapi.org/docs
- **Finnhub Documentation**: https://finnhub.io/docs/api

---

## 💡 Future Enhancements

Potential future improvements:
- Social media sentiment (Twitter, Reddit)
- Real-time sentiment updates
- Sentiment-based stop losses
- Machine learning sentiment models
- Multi-asset class optimization
- Dynamic rebalancing automation

---

## 🆘 Support

If you encounter issues:
1. Check logs in `trading_bot.log`
2. Verify API keys are valid
3. Ensure dependencies are installed
4. Review test suite for examples
5. Create GitHub issue with details

---

**Last Updated**: January 2026
**Version**: 1.0
**Status**: Production Ready
