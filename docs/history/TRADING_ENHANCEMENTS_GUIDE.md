# Stock Trading Enhancements - Tutorial and Guide

## Overview

The market-pie5-bot has been enhanced with professional-grade stock trading tools, strategies, and datasets. This guide will help you understand and use the new features.

## Table of Contents

1. [Features Overview](#features-overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Trading Strategies](#trading-strategies)
5. [Technical Indicators](#technical-indicators)
6. [Data Sources](#data-sources)
7. [Risk Management](#risk-management)
8. [Backtesting](#backtesting)
9. [Example Workflows](#example-workflows)
10. [API Configuration](#api-configuration)

---

## Features Overview

### 1. **Trading Strategies**
- **SMA Crossover**: Momentum trading with moving average crossovers
- **Bollinger Bands**: Mean reversion strategy identifying overbought/oversold
- **Strategy Manager**: Combine multiple strategies with weighted signals

### 2. **Technical Indicators** 
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- SMA/EMA (Simple/Exponential Moving Averages)
- Bollinger Bands
- ATR (Average True Range)
- ADX (Average Directional Index)
- Stochastic Oscillator

### 3. **Data Integration**
- **yfinance**: Real-time and historical price data
- **Alpha Vantage**: Fundamental data (P/E ratios, earnings, financials)
- Comprehensive data fetching with caching

### 4. **Risk Management**
- Position sizing (fixed risk, percentage of capital, Kelly Criterion)
- Risk/reward ratio calculations
- Portfolio risk assessment
- Value at Risk (VaR)
- Sharpe Ratio and Max Drawdown

### 5. **Advanced Backtesting**
- **Backtrader** integration for realistic backtesting
- Built-in backtesting with rolling metrics
- Baseline comparison (buy-and-hold)
- Performance analytics

---

## Installation

### 1. Update Dependencies

```bash
cd market-pie5-bot
pip install -r requirements.txt
```

New dependencies added:
- `alpha-vantage>=2.3.1` - Fundamental data
- `backtrader>=1.9.78.123` - Advanced backtesting
- `pandas-ta>=0.4.67b0` (optional, requires Python >=3.12) - Alternative technical indicators library

### 2. Configure API Keys

Create or update `.env` file:

```bash
# Alpha Vantage API (for fundamentals)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Existing Schwab API keys
SCHWAB_API_KEY=your_app_key
SCHWAB_APP_SECRET=your_app_secret
# ... other existing keys
```

**Get Free API Keys:**
- **Alpha Vantage**: https://www.alphavantage.co/support/#api-key (Free tier: 5 API calls/min, 500/day)

---

## Quick Start

### Example 1: Using SMA Crossover Strategy

```python
#!/usr/bin/env python3
from strategies import SMAStrategy, StrategyManager
from data_fetcher import DataFetcher
import pandas as pd

# Fetch historical data
fetcher = DataFetcher()
data = fetcher.fetch_historical_data_yfinance('AAPL', period='3mo', interval='1d')

# Initialize SMA strategy
sma_strategy = SMAStrategy(fast_period=20, slow_period=50)

# Generate signal
signal = sma_strategy.generate_signal(data)
print(f"Signal: {signal}")  # BUY, SELL, or HOLD

# Get indicator values
indicators = sma_strategy.get_indicator_values(data)
print(f"Fast SMA: ${indicators['sma_fast']:.2f}")
print(f"Slow SMA: ${indicators['sma_slow']:.2f}")
```

### Example 2: Using Bollinger Bands

```python
from strategies import BollingerBandsStrategy

# Initialize Bollinger Bands strategy
bb_strategy = BollingerBandsStrategy(period=20, num_std=2.0)

# Generate signal
signal = bb_strategy.generate_signal(data)
print(f"Signal: {signal}")

# Get indicator values
indicators = bb_strategy.get_indicator_values(data)
print(f"Price: ${indicators['price']:.2f}")
print(f"Upper Band: ${indicators['upper_band']:.2f}")
print(f"Lower Band: ${indicators['lower_band']:.2f}")
print(f"Band Width: {indicators['band_width']:.4f}")
```

### Example 3: Combining Strategies

```python
from strategies import StrategyManager, SMAStrategy, BollingerBandsStrategy

# Create strategy manager
manager = StrategyManager()

# Add strategies with weights
manager.add_strategy(SMAStrategy(fast_period=20, slow_period=50), weight=1.0)
manager.add_strategy(BollingerBandsStrategy(period=20, num_std=2.0), weight=1.0)

# Generate combined signal
combined_signal = manager.generate_combined_signal(data)
print(f"Combined Signal: {combined_signal}")

# Get all indicators
all_indicators = manager.get_all_indicator_values(data)
for strategy_name, indicators in all_indicators.items():
    print(f"\n{strategy_name}:")
    for key, value in indicators.items():
        print(f"  {key}: {value}")
```

---

## Trading Strategies

### SMA Crossover (Momentum Trading)

**Concept**: Follows trends by detecting when fast-moving average crosses slow-moving average.

**Signals**:
- **BUY**: Fast SMA crosses above slow SMA (Golden Cross) - bullish trend
- **SELL**: Fast SMA crosses below slow SMA (Death Cross) - bearish trend
- **HOLD**: No crossover

**Best For**: Trending markets, medium to long-term trades

**Parameters**:
- `fast_period`: Fast SMA period (default: 20)
- `slow_period`: Slow SMA period (default: 50)

**Example Configuration**:
```python
# Conservative (longer periods, fewer signals)
sma = SMAStrategy(fast_period=50, slow_period=200)

# Aggressive (shorter periods, more signals)
sma = SMAStrategy(fast_period=10, slow_period=30)

# Default (balanced)
sma = SMAStrategy(fast_period=20, slow_period=50)
```

### Bollinger Bands (Mean Reversion)

**Concept**: Assumes prices revert to the mean. Identifies overbought/oversold conditions.

**Signals**:
- **BUY**: Price touches or crosses below lower band (oversold)
- **SELL**: Price touches or crosses above upper band (overbought)
- **HOLD**: Price within bands

**Best For**: Range-bound markets, short to medium-term trades

**Parameters**:
- `period`: Moving average period (default: 20)
- `num_std`: Number of standard deviations (default: 2.0)

**Example Configuration**:
```python
# Tight bands (more signals, higher false positives)
bb = BollingerBandsStrategy(period=20, num_std=1.5)

# Wide bands (fewer signals, higher confidence)
bb = BollingerBandsStrategy(period=20, num_std=2.5)

# Default (balanced)
bb = BollingerBandsStrategy(period=20, num_std=2.0)
```

---

## Technical Indicators

### Using Technical Indicators Module

```python
from indicators import TechnicalIndicators

# Initialize with data
indicators = TechnicalIndicators(data)

# Calculate all indicators
all_indicators = indicators.get_all_indicators()

# Get latest values
latest = indicators.get_latest_values()
print(f"RSI: {latest.get('rsi_14', 'N/A')}")
print(f"MACD: {latest.get('macd_line', 'N/A')}")

# Get interpretations and trading signals
interpretations = indicators.interpret_indicators()

for indicator_name, interpretation in interpretations.items():
    print(f"\n{indicator_name.upper()}:")
    print(f"  Signal: {interpretation.get('signal', 'N/A')}")
    print(f"  Action: {interpretation.get('action', 'N/A')}")
```

### Indicator Reference

| Indicator | Purpose | Overbought | Oversold |
|-----------|---------|------------|----------|
| **RSI** | Momentum oscillator | > 70 | < 30 |
| **MACD** | Trend and momentum | Line > Signal | Line < Signal |
| **Stochastic** | Momentum oscillator | > 80 | < 20 |
| **Bollinger Bands** | Volatility | At upper band | At lower band |
| **ADX** | Trend strength | > 25 (strong) | < 20 (weak) |
| **ATR** | Volatility measurement | High = high volatility | Low = low volatility |

---

## Data Sources

### yfinance (Price Data)

```python
from data_fetcher import DataFetcher

fetcher = DataFetcher()

# Fetch historical data
data = fetcher.fetch_historical_data_yfinance(
    symbol='AAPL',
    period='1y',      # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval='1d'     # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
)

print(data.head())
```

### Alpha Vantage (Fundamentals)

```python
# Fetch fundamental data
fundamentals = fetcher.fetch_fundamentals_alpha_vantage('AAPL')

if fundamentals:
    print(f"P/E Ratio: {fundamentals.get('pe_ratio')}")
    print(f"EPS: {fundamentals.get('eps')}")
    print(f"Market Cap: ${fundamentals.get('market_cap'):,}")
    print(f"Dividend Yield: {fundamentals.get('dividend_yield'):.2%}")
    print(f"Profit Margin: {fundamentals.get('profit_margin'):.2%}")
    print(f"ROE: {fundamentals.get('return_on_equity'):.2%}")
    print(f"Beta: {fundamentals.get('beta')}")

# Analyze fundamentals
analysis = fetcher.analyze_fundamentals(fundamentals)
print(f"\nRecommendation: {analysis.get('recommendation')}")
print(f"Valuation Score: {analysis.get('valuation_score')}")
print(f"Profitability Score: {analysis.get('profitability_score')}")

for signal in analysis.get('signals', []):
    print(f"  - {signal}")
```

### Comprehensive Data Fetching

```python
# Get everything at once
comprehensive = fetcher.get_comprehensive_data('AAPL', period='1y')

# Access different data types
historical = comprehensive['historical_data']
fundamentals = comprehensive['fundamentals']
earnings = comprehensive['earnings']
current_price = comprehensive['current_price']

print(f"Data sources: {comprehensive['data_sources']}")
```

---

## Risk Management

### Position Sizing

```python
from risk_management import RiskManager

# Initialize risk manager
risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)

# Method 1: Fixed risk position sizing
entry_price = 150.0
stop_loss = 147.0

position = risk_mgr.calculate_position_size_fixed_risk(entry_price, stop_loss)

print(f"Shares: {position['shares']:.2f}")
print(f"Position Value: ${position['position_value']:.2f}")
print(f"Risk Amount: ${position['risk_amount']:.2f}")

# Method 2: Percentage of capital
position = risk_mgr.calculate_position_size_pct_capital(entry_price, allocation_pct=0.10)

# Method 3: Kelly Criterion (optimal sizing)
kelly_pct = risk_mgr.calculate_kelly_criterion(
    win_rate=0.60,
    avg_win=300,
    avg_loss=200
)
print(f"Optimal position size: {kelly_pct:.2%}")
```

### Risk/Reward Analysis

```python
# Calculate risk/reward ratio
target_price = 159.0

rr = risk_mgr.calculate_risk_reward_ratio(entry_price, stop_loss, target_price)

print(f"Risk: ${rr['risk']:.2f} ({rr['risk_pct']:.2f}%)")
print(f"Reward: ${rr['reward']:.2f} ({rr['reward_pct']:.2f}%)")
print(f"Risk/Reward Ratio: 1:{rr['risk_reward_ratio']:.2f}")
print(f"Recommendation: {rr['recommendation']}")
```

### Trade Validation

```python
# Validate trade before execution
validation = risk_mgr.validate_trade(
    entry_price=150.0,
    stop_loss_price=147.0,
    target_price=159.0,
    current_positions={}  # Dict of current positions
)

if validation['is_valid']:
    print("✓ Trade passes validation")
else:
    print("✗ Trade failed validation:")
    for reason in validation['reasons']:
        print(f"  - {reason}")

for warning in validation['warnings']:
    print(f"⚠ {warning}")
```

### Portfolio Risk Assessment

```python
# Assess overall portfolio risk
positions = {
    'AAPL': {'risk_amount': 200, 'position_value': 1500},
    'MSFT': {'risk_amount': 150, 'position_value': 1200},
}

portfolio_risk = risk_mgr.assess_portfolio_risk(positions)

print(f"Total Positions: {portfolio_risk['total_positions']}")
print(f"Total Risk: ${portfolio_risk['total_risk']:.2f}")
print(f"Total Risk %: {portfolio_risk['total_risk_pct']:.2f}%")
print(f"Can Open New: {portfolio_risk['can_open_new']}")
```

---

## Backtesting

### Using Built-in Backtester

```python
from backtesting import Backtester
from main import TradingBot

# Create backtester
backtester = Backtester(initial_capital=10000.0)

# Generate or load historical data
historical_data = backtester.generate_historical_data(
    symbol='TEST',
    days=252,
    start_price=100.0,
    volatility=0.02
)

# Create trading bot
bot = TradingBot(total_capital=10000.0)

# Run backtest
backtest_result = backtester.run_backtest(bot, historical_data)

# Run baseline (buy-and-hold)
baseline_result = backtester.run_baseline(historical_data)

# Compare results
comparison = backtester.compare_with_baseline(backtest_result, baseline_result)

# Generate report
backtester.generate_report('backtest_report.json')
```

### Using Backtrader Engine

```python
from backtrader_engine import BacktraderEngine, SMABacktraderStrategy

# Initialize engine
engine = BacktraderEngine(initial_cash=10000.0, commission=0.001)

# Setup Cerebro
engine.setup_cerebro()

# Add data
engine.add_data(historical_data)

# Add strategy
engine.add_strategy(
    SMABacktraderStrategy,
    fast_period=20,
    slow_period=50,
    risk_per_trade=0.02
)

# Run backtest
results = engine.run()

# Print results
engine.print_results(results)

# Plot (if matplotlib available)
engine.plot()
```

---

## Example Workflows

### Workflow 1: Complete Trading System

```python
#!/usr/bin/env python3
"""
Complete trading workflow with strategies, risk management, and backtesting
"""

from data_fetcher import DataFetcher
from strategies import SMAStrategy, BollingerBandsStrategy, StrategyManager
from indicators import TechnicalIndicators
from risk_management import RiskManager
from backtesting import Backtester
from main import TradingBot

# Step 1: Fetch data
fetcher = DataFetcher()
symbol = 'AAPL'
data = fetcher.fetch_historical_data_yfinance(symbol, period='1y')
fundamentals = fetcher.fetch_fundamentals_alpha_vantage(symbol)

# Step 2: Analyze fundamentals
if fundamentals:
    analysis = fetcher.analyze_fundamentals(fundamentals)
    print(f"Fundamental Recommendation: {analysis['recommendation']}")
    
    # Skip if fundamentals are poor
    if analysis['recommendation'] in ['STRONG SELL', 'SELL']:
        print("Skipping due to poor fundamentals")
        exit()

# Step 3: Calculate technical indicators
indicators = TechnicalIndicators(data)
interpretations = indicators.interpret_indicators()

print("\nTechnical Signals:")
for indicator_name, interpretation in interpretations.items():
    print(f"  {indicator_name}: {interpretation.get('action', 'N/A')}")

# Step 4: Generate trading signals
manager = StrategyManager()
manager.add_strategy(SMAStrategy(fast_period=20, slow_period=50), weight=1.0)
manager.add_strategy(BollingerBandsStrategy(period=20, num_std=2.0), weight=1.0)

signal = manager.generate_combined_signal(data)
print(f"\nCombined Strategy Signal: {signal}")

# Step 5: Risk management
if signal == 'BUY':
    current_price = data['close'].iloc[-1]
    stop_loss = current_price * 0.97  # 3% stop loss
    target = current_price * 1.06     # 6% target
    
    risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    # Calculate position size
    position = risk_mgr.calculate_position_size_fixed_risk(current_price, stop_loss)
    
    # Validate trade
    validation = risk_mgr.validate_trade(current_price, stop_loss, target)
    
    if validation['is_valid']:
        print(f"\n✓ Trade validated")
        print(f"  Shares: {position['shares']:.2f}")
        print(f"  Position Value: ${position['position_value']:.2f}")
        print(f"  Risk: ${position['risk_amount']:.2f}")
    else:
        print(f"\n✗ Trade validation failed: {validation['summary']}")

# Step 6: Backtest strategy
print("\n" + "="*60)
print("Running Backtest")
print("="*60)

backtester = Backtester(initial_capital=10000.0)
bot = TradingBot(total_capital=10000.0)

backtest_result = backtester.run_backtest(bot, data)
baseline_result = backtester.run_baseline(data)
comparison = backtester.compare_with_baseline(backtest_result, baseline_result)

print("\nBacktest complete!")
```

### Workflow 2: Fundamental Screening

```python
"""
Screen stocks based on fundamental criteria
"""

from data_fetcher import DataFetcher

# Symbols to screen
symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

fetcher = DataFetcher()
screened = []

for symbol in symbols:
    print(f"\nScreening {symbol}...")
    
    fundamentals = fetcher.fetch_fundamentals_alpha_vantage(symbol)
    
    if not fundamentals:
        continue
    
    # Screening criteria
    pe_ratio = fundamentals.get('pe_ratio', 0)
    roe = fundamentals.get('return_on_equity', 0)
    profit_margin = fundamentals.get('profit_margin', 0)
    
    # Apply filters
    if pe_ratio and pe_ratio < 25 and roe and roe > 0.15 and profit_margin and profit_margin > 0.10:
        screened.append({
            'symbol': symbol,
            'pe_ratio': pe_ratio,
            'roe': roe,
            'profit_margin': profit_margin
        })
        print(f"  ✓ Passed screening")
    else:
        print(f"  ✗ Failed screening")

print("\n" + "="*60)
print("Screening Results")
print("="*60)

for stock in screened:
    print(f"{stock['symbol']}: P/E={stock['pe_ratio']:.2f}, ROE={stock['roe']:.2%}, Margin={stock['profit_margin']:.2%}")
```

---

## API Configuration

### Required Environment Variables

Add to `.env` file:

```bash
# Alpha Vantage (for fundamental data)
ALPHA_VANTAGE_API_KEY=your_key_here

# Existing Schwab API credentials
SCHWAB_API_KEY=your_app_key
SCHWAB_APP_SECRET=your_app_secret
SCHWAB_CALLBACK_URL=https://127.0.0.1:8182
SCHWAB_ACCOUNT_ID=your_account_number

# Existing bot configuration
PAPER_TRADING_MODE=true
SCHWAB_SANDBOX_MODE=true
BOT_RISK_THRESHOLD=0.02
BOT_MIN_ALLOCATION=50
BOT_MAX_ALLOCATION=500
BOT_TRAILING_STOP_PERCENT=0.03
```

### Getting API Keys

**Alpha Vantage** (Free):
1. Visit https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Get your API key instantly
4. Free tier: 5 API calls/minute, 500/day

**Schwab API** (see main README.md for full instructions)

---

## Best Practices

### 1. **Strategy Selection**
- Use **SMA Crossover** for trending markets
- Use **Bollinger Bands** for range-bound markets
- Combine strategies for more robust signals

### 2. **Risk Management**
- Never risk more than 2% per trade
- Always use stop losses
- Target minimum 2:1 risk/reward ratio
- Limit portfolio risk to 6%

### 3. **Backtesting**
- Test on at least 1 year of data
- Compare against buy-and-hold baseline
- Account for commissions and slippage
- Walk-forward optimize parameters

### 4. **Technical Indicators**
- Use multiple indicators for confirmation
- Avoid using too many (causes analysis paralysis)
- Understand what each indicator measures
- Check for indicator divergence

### 5. **Fundamental Analysis**
- Screen stocks before technical analysis
- Focus on profitable companies (positive ROE)
- Avoid extremely high P/E ratios
- Consider sector and industry trends

---

## Troubleshooting

### pandas-ta (Optional)

The bot includes built-in manual implementations for all technical indicators, so pandas-ta is optional.

```bash
# To use pandas-ta (requires Python >=3.12)
pip install pandas-ta

# If you have Python 3.11 or earlier
# The bot will automatically use built-in fallback calculations
# No action needed - all indicators work without pandas-ta!
```

### Alpha Vantage Rate Limits

```python
# The DataFetcher has built-in caching (1 hour)
# To avoid rate limits, space out API calls

import time
for symbol in symbols:
    data = fetcher.fetch_fundamentals_alpha_vantage(symbol)
    time.sleep(12)  # 5 calls/minute = 12 seconds between calls
```

### Backtrader Import Errors

```bash
# Install matplotlib for plotting
pip install matplotlib

# If backtrader fails
pip install backtrader --upgrade
```

---

## Additional Resources

- **pandas-ta Documentation**: https://github.com/twopirllc/pandas-ta
- **Alpha Vantage API Docs**: https://www.alphavantage.co/documentation/
- **Backtrader Documentation**: https://www.backtrader.com/docu/
- **yfinance Documentation**: https://pypi.org/project/yfinance/

---

## Next Steps

1. Configure your API keys in `.env`
2. Run the example scripts in each module
3. Try the example workflows above
4. Backtest strategies on your favorite stocks
5. Paper trade before going live

For more help, see the main README.md or create an issue on GitHub.

---

**Happy Trading! 🚀📈**
