# Stock Screener Enhancements - Sentiment & ML Integration

## Overview

The stock screener module has been enhanced with advanced filtering capabilities that integrate:
- **Sentiment Analysis**: Filter stocks based on news sentiment to avoid trading stocks with negative news
- **ML Signal Quality**: Use machine learning to predict trade quality and filter low-probability signals
- **Portfolio Optimization**: Analyze portfolio diversification and correlation for better risk management

## What Changed

### Previous Capabilities
- Basic filtering by price range, volume, and volatility
- Dynamic stock universe discovery from major indices
- Simple pass/fail filtering

### New Capabilities
1. **Sentiment-Based Filtering**
   - Integrates with `sentiment_analyzer.py` to fetch and analyze news
   - Filters out stocks with strongly negative sentiment
   - Provides sentiment scoring and confidence metrics

2. **ML-Based Signal Quality**
   - Integrates with `ml_signal_filter.py` for quality prediction
   - Filters out low-quality trade signals based on ML predictions
   - Provides confidence scores and win probability estimates

3. **Portfolio Diversification Analysis**
   - Integrates with `portfolio_optimizer.py` for correlation analysis
   - Calculates diversification scores for stock selections
   - Helps ensure portfolio isn't over-concentrated

4. **Swing Trade Candidate Selection**
   - New `get_swing_trade_candidates()` method
   - Comprehensive scoring combining sentiment, ML, and diversification
   - Ranks candidates by composite quality score

## How to Enable

### Environment Variables

Add these to your `.env` file:

```bash
# Enable sentiment analysis filtering (requires NEWS_API_KEY or FINNHUB_API_KEY)
ENABLE_SENTIMENT_FILTER=true
MIN_SENTIMENT_SCORE=0.0

# Enable ML signal quality filtering (requires trained ML model)
ENABLE_ML_FILTER=true
MIN_ML_CONFIDENCE=0.6
MIN_ML_WIN_PROBABILITY=0.55

# Enable portfolio optimization features (requires scipy)
ENABLE_PORTFOLIO_OPTIMIZATION=true
MIN_DIVERSIFICATION_SCORE=0.3
```

### Dependencies

Install optional dependencies for full functionality:

```bash
# For sentiment analysis
pip install vaderSentiment textblob

# For ML filtering (already installed)
pip install scikit-learn

# For portfolio optimization
pip install scipy numpy pandas
```

## Usage Examples

### Basic Usage (Backward Compatible)

The screener still works exactly as before when advanced features are disabled:

```python
from stock_screener import StockScreener

# Basic screener (no changes needed to existing code)
screener = StockScreener()
results = screener.screen_stocks(max_results=10)
```

### Advanced Usage with Sentiment & ML

```python
from stock_screener import StockScreener

# Create screener with all features enabled
screener = StockScreener(
    enable_sentiment=True,
    enable_ml=True,
    enable_portfolio_opt=True
)

# Screen stocks with advanced filtering
results = screener.screen_stocks(
    max_results=10,
    use_advanced_filters=True
)

# Results are filtered by:
# 1. Price, volume, volatility (basic)
# 2. Sentiment (news analysis)
# 3. ML quality (signal prediction)
# 4. Diversification check (if multiple stocks)
```

### Swing Trade Candidate Selection

Get comprehensive scoring for swing trading:

```python
from stock_screener import StockScreener

screener = StockScreener(
    enable_sentiment=True,
    enable_ml=True,
    enable_portfolio_opt=True
)

# Get top swing trade candidates with scoring
candidates = screener.get_swing_trade_candidates(
    max_results=10,
    sentiment_weight=0.3,      # 30% weight on sentiment
    ml_weight=0.4,             # 40% weight on ML quality
    diversification_weight=0.3  # 30% weight on diversification
)

# Results include comprehensive scores:
for candidate in candidates:
    print(f"{candidate['symbol']}:")
    print(f"  Composite Score: {candidate['composite_score']:.3f}")
    print(f"  Sentiment: {candidate['sentiment_signal']} ({candidate['sentiment_score']:.2f})")
    print(f"  ML Confidence: {candidate['ml_confidence']:.2f}")
    print(f"  Win Probability: {candidate['ml_win_probability']:.2f}")
```

### Manual Filter Testing

Test individual filters:

```python
from stock_screener import StockScreener

screener = StockScreener(enable_sentiment=True, enable_ml=True)

# Test sentiment filter
passes, reason, sentiment_data = screener.filter_by_sentiment('AAPL')
print(f"Sentiment: {reason}")
if sentiment_data:
    print(f"  Score: {sentiment_data['overall_score']:.2f}")
    print(f"  Signal: {sentiment_data['sentiment_signal']}")
    print(f"  Articles: {sentiment_data['article_count']}")

# Test ML filter
stock_data = {'price': 150.0, 'volume': 70000000, 'volatility': 0.05}
passes, reason, ml_scores = screener.filter_by_ml_quality('AAPL', stock_data)
print(f"ML Quality: {reason}")
if ml_scores:
    print(f"  Confidence: {ml_scores['confidence']:.2f}")
    print(f"  Win Probability: {ml_scores['win_probability']:.2f}")

# Test diversification
symbols = ['AAPL', 'MSFT', 'GOOGL']
score, reason = screener.calculate_portfolio_diversification(symbols)
print(f"Diversification: {reason}")
```

## Integration with Main Bot

The enhanced screener can be used in the main trading bot:

```python
# In main.py or your trading script
from stock_screener import StockScreener

# Initialize with advanced features
screener = StockScreener(
    enable_sentiment=True,
    enable_ml=True,
    enable_portfolio_opt=True
)

# Get high-quality swing trade candidates
candidates = screener.get_swing_trade_candidates(max_results=10)

# Trade only the top-scored candidates
for candidate in candidates[:5]:
    symbol = candidate['symbol']
    if candidate['composite_score'] > 0.6:  # High quality threshold
        # Execute trade
        execute_trade(symbol, 'BUY')
```

## Testing

Run the test suite:

```bash
# Test sentiment integration
python3 -m unittest test_stock_screener_enhancements.TestStockScreenerSentimentIntegration -v

# Test ML integration
python3 -m unittest test_stock_screener_enhancements.TestStockScreenerMLIntegration -v

# Test portfolio integration
python3 -m unittest test_stock_screener_enhancements.TestStockScreenerPortfolioIntegration -v

# Test swing candidate selection
python3 -m unittest test_stock_screener_enhancements.TestStockScreenerSwingCandidates -v

# Test backward compatibility
python3 -m unittest test_stock_screener_enhancements.TestStockScreenerBackwardCompatibility -v

# Run all enhancement tests
python3 -m unittest test_stock_screener_enhancements -v

# Run original tests to verify no regressions
python3 -m unittest test_stock_screener -v
```

## Performance Considerations

### With Advanced Filters Disabled (Default)
- Performance: Same as before (~2 seconds for 200 stocks)
- No additional API calls
- No ML computations
- Backward compatible

### With Sentiment Filter Enabled
- Additional time: ~0.5-1 second per stock (cached for 1 hour)
- API calls: 1 per stock per hour (NewsAPI or Finnhub)
- Rate limits: Consider API tier limits

### With ML Filter Enabled
- Additional time: ~0.01 seconds per stock
- No API calls
- Requires trained model (can be pre-trained)

### With Portfolio Optimization Enabled
- Additional time: ~0.5 seconds for diversification calculation
- No API calls
- Only runs once per screening session

## Configuration Tips

### Conservative Trading (Focus on Quality)
```bash
ENABLE_SENTIMENT_FILTER=true
ENABLE_ML_FILTER=true
ENABLE_PORTFOLIO_OPTIMIZATION=true
MIN_SENTIMENT_SCORE=0.2        # Require positive sentiment
MIN_ML_CONFIDENCE=0.7           # High confidence
MIN_ML_WIN_PROBABILITY=0.6      # Good win probability
MIN_DIVERSIFICATION_SCORE=0.5   # Well-diversified
```

### Aggressive Trading (More Opportunities)
```bash
ENABLE_SENTIMENT_FILTER=true
ENABLE_ML_FILTER=false          # Don't filter by ML
ENABLE_PORTFOLIO_OPTIMIZATION=false
MIN_SENTIMENT_SCORE=-0.2        # Allow some negative sentiment
```

### ML-Focused Trading
```bash
ENABLE_SENTIMENT_FILTER=false
ENABLE_ML_FILTER=true
ENABLE_PORTFOLIO_OPTIMIZATION=true
MIN_ML_CONFIDENCE=0.65
MIN_ML_WIN_PROBABILITY=0.58
```

## Troubleshooting

### "Sentiment filtering requested but sentiment_analyzer not available"
- **Solution**: Install sentiment libraries: `pip install vaderSentiment textblob`
- Configure API keys: `NEWS_API_KEY` or `FINNHUB_API_KEY` in `.env`

### "ML filtering requested but ml_signal_filter not available"
- **Solution**: Ensure `ml_signal_filter.py` is in the same directory
- Check that scikit-learn is installed: `pip install scikit-learn`

### "Portfolio optimization requested but portfolio_optimizer not available"
- **Solution**: Install scipy: `pip install scipy`
- Ensure `portfolio_optimizer.py` is in the same directory

### ML filter always disabled: "Model not trained"
- **Solution**: ML filter requires a trained model
- Train model using historical data or use pre-trained model
- Alternatively, disable ML filter: `ENABLE_ML_FILTER=false`

### Low diversification warning
- **Issue**: Selected stocks are highly correlated
- **Solution**: Increase `MAX_DISCOVERED_STOCKS` to get more variety
- Adjust screening criteria to include stocks from different sectors

## Backward Compatibility

All existing code continues to work without modifications:
- ✅ Old initialization: `StockScreener()` works as before
- ✅ Basic screening: `screen_stocks()` returns same results when filters disabled
- ✅ Helper functions: `screen_for_trades()` unchanged
- ✅ All existing tests pass

New features are opt-in via:
- Environment variables
- Constructor parameters
- Method parameters

## Future Enhancements

Potential future improvements:
- Real-time sentiment updates
- Ensemble ML models for better predictions
- Dynamic weight optimization for composite scoring
- Sector-based diversification analysis
- Custom scoring formulas
- Integration with more data sources

## See Also

- [SENTIMENT_PORTFOLIO_GUIDE.md](SENTIMENT_PORTFOLIO_GUIDE.md) - Detailed sentiment & portfolio docs
- [STOCK_SCREENER_GUIDE.md](STOCK_SCREENER_GUIDE.md) - Original screener documentation
- [ML_GUIDE.md](ML_GUIDE.md) - Machine learning features
- `.env.example` - Complete configuration reference

## Support

For issues or questions:
1. Check logs for error messages
2. Verify environment variables are set correctly
3. Ensure dependencies are installed
4. Review test suite for usage examples
5. Create GitHub issue with details

---

**Last Updated**: January 2026  
**Version**: 1.0  
**Status**: Production Ready
