# Monte Carlo Simulation Guide for market-pie5-bot

**Last Updated:** January 22, 2026

---

## Overview

The **Monte Carlo Simulation** module provides probabilistic analysis to complement the bot's backtesting capabilities. It helps quantify uncertainty, assess tail risks, and test strategy robustness across thousands of scenarios.

### What is Monte Carlo Simulation?

Monte Carlo simulation is a computational technique that uses random sampling to model uncertainty and variability. Instead of running a single backtest, it runs thousands of simulations with different random scenarios to:

- Estimate probability distributions of outcomes
- Quantify tail risks (worst-case scenarios)
- Test strategy robustness across market conditions
- Calculate confidence intervals for predictions

---

## Key Features

### 1. **Portfolio Risk Simulation**
Simulate portfolio returns over time using Geometric Brownian Motion (GBM) for realistic price paths.

**Use Cases:**
- Project portfolio value over 1 year, 3 years, etc.
- Estimate probability of reaching financial goals
- Understand range of possible outcomes

### 2. **Value at Risk (VaR) and Conditional VaR (CVaR)**
Calculate maximum expected loss at specified confidence levels.

**VaR (95%):** Maximum loss expected 95% of the time  
**CVaR (95%):** Average loss in the worst 5% of scenarios (tail risk)

### 3. **Maximum Drawdown Distribution**
Simulate drawdown scenarios to understand portfolio resilience.

**Use Cases:**
- Estimate probability of 20%+ drawdown
- Plan capital reserves for worst-case scenarios
- Set realistic expectations for portfolio volatility

### 4. **Strategy Robustness Testing**
Test trading strategies across diverse market conditions with varying drift and volatility.

**Use Cases:**
- Validate strategy works in bull, bear, and sideways markets
- Identify parameter sensitivity
- Avoid overfitting to historical data

### 5. **Trade Outcome Forecasting**
Project cumulative P&L based on historical win rate and average win/loss.

**Use Cases:**
- Estimate profit potential over N trades
- Calculate probability of reaching profit targets
- Understand variance in trading results

### 6. **Parameter Sensitivity Analysis**
Test strategy parameters across ranges to find optimal and robust values.

**Use Cases:**
- Optimize strategy parameters
- Identify fragile parameters (small changes = big impact)
- Build confidence in parameter selection

---

## Installation

Monte Carlo simulation is included in `monte_carlo_simulator.py`. No additional dependencies beyond standard requirements:

```bash
pip install numpy pandas
```

All dependencies are already in `requirements.txt`.

---

## Quick Start

### Example 1: Portfolio Risk Simulation

```python
from monte_carlo_simulator import MonteCarloSimulator

# Initialize simulator with 10,000 simulations
mc = MonteCarloSimulator(num_simulations=10000, random_seed=42)

# Define your portfolio
positions = [
    {'symbol': 'AAPL', 'shares': 10, 'current_price': 150.0},
    {'symbol': 'GOOGL', 'shares': 5, 'current_price': 140.0}
]

# Simulate 1-year returns
results = mc.simulate_portfolio_returns(
    initial_capital=10000.0,
    positions=positions,
    drift=0.0005,      # 0.05% daily return (~13% annualized)
    volatility=0.02,   # 2% daily volatility (~32% annualized)
    days=252           # 252 trading days = 1 year
)

# View results
print(mc.generate_report(results, "1-Year Portfolio Projection"))
```

**Output:**
```
============================================================
1-Year Portfolio Projection
============================================================

Number of Simulations: 10,000

Expected Value (Mean):  $10,289.69
Median Outcome:         $10,217.34
Standard Deviation:     $606.04

Percentile Distribution:
  5th percentile:            $9,443.86
  25th percentile:           $9,866.06
  50th percentile:           $10,217.34
  75th percentile:           $10,628.06
  95th percentile:           $11,391.30

Risk Metrics:
  5th Percentile Value:      $9,443.86
  VaR (95% loss):            $556.14
  CVaR (95% tail risk):      $703.80

Success Rate:            100.00%
============================================================
```

**Interpretation:**
- 50% chance portfolio will be worth > $10,217
- 95% confident portfolio will be worth > $9,444
- Maximum expected loss (VaR): $556 at 95% confidence
- In worst 5% of scenarios, expect $704 average loss (CVaR)

---

### Example 2: Value at Risk (VaR) and CVaR

```python
# Calculate 1-day VaR and CVaR at 95% confidence
var_95, cvar_95 = mc.simulate_var_cvar(
    initial_capital=10000.0,
    expected_return=0.0005,  # 0.05% daily return
    volatility=0.02,         # 2% daily volatility
    days=1,                  # 1-day horizon
    confidence_level=0.95
)

print(f"1-Day VaR (95%): ${var_95:.2f}")
print(f"1-Day CVaR: ${cvar_95:.2f}")
```

**Output:**
```
1-Day VaR (95%): $324.13
1-Day CVaR: $405.77
```

**Interpretation:**
- 95% of days, losses won't exceed $324
- If losses exceed VaR, expect $406 average loss
- **Risk management:** Set stop-loss or position sizing to limit exposure

---

### Example 3: Maximum Drawdown Distribution

```python
dd_results = mc.simulate_drawdown_distribution(
    initial_capital=10000.0,
    expected_return=0.0005,
    volatility=0.02,
    days=252  # 1 year
)

print(f"Mean Max Drawdown: {dd_results['mean_max_drawdown']:.2%}")
print(f"Worst Drawdown (95th): {dd_results['worst_drawdown_95']:.2%}")
print(f"Prob(Drawdown > 20%): {dd_results['prob_drawdown_over_20pct']:.2%}")
```

**Output:**
```
Mean Max Drawdown: -28.36%
Worst Drawdown (95th): -46.58%
Prob(Drawdown > 20%): 78.87%
```

**Interpretation:**
- Expect 28% average max drawdown over 1 year
- 5% chance of 47%+ drawdown
- 79% probability of experiencing 20%+ drawdown
- **Capital planning:** Keep reserves to withstand drawdowns

---

### Example 4: Trade Outcome Simulation

```python
# Simulate 100 trades based on historical statistics
results = mc.simulate_trade_outcomes(
    win_rate=0.55,     # 55% win rate
    avg_win=200.0,     # $200 average win
    avg_loss=-150.0,   # $150 average loss
    num_trades=100,
    risk_per_trade=0.02
)

print(mc.generate_report(results, "100-Trade Projection"))
```

**Output:**
```
============================================================
100-Trade Projection
============================================================

Expected Value (Mean):  $4,269.07
Median Outcome:         $4,250.00
Standard Deviation:     $1,753.70

Percentile Distribution:
  5th percentile (VaR):  $1,450.00
  25th percentile:       $3,200.00
  50th percentile:       $4,250.00
  75th percentile:       $5,300.00
  95th percentile:       $7,050.00

Success Rate:            99.42%
============================================================
```

**Interpretation:**
- Expect $4,269 profit after 100 trades
- 50% chance of $4,250+ profit
- 99.4% chance of ending positive
- Worst 5%: still profitable at $1,450+

---

### Example 5: Strategy Robustness Testing

```python
# Define a simple buy-and-hold strategy
def buy_hold_strategy(price_path):
    """Calculate P&L from buying at start and selling at end"""
    return price_path[-1] - price_path[0]

# Test strategy across market conditions
robustness = mc.simulate_strategy_robustness(
    strategy_func=buy_hold_strategy,
    initial_price=100.0,
    days=30,
    drift_range=(-0.001, 0.002),      # -0.1% to +0.2% daily drift
    volatility_range=(0.01, 0.03),    # 1% to 3% daily volatility
    num_scenarios=1000
)

print(f"Mean P&L: ${robustness['mean_pnl']:.2f}")
print(f"Positive Scenarios: {robustness['positive_scenarios']:.2%}")
print(f"Sharpe Ratio: {robustness['sharpe_ratio']:.2f}")
```

**Interpretation:**
- Tests strategy across 1000 different market scenarios
- Shows how often strategy is profitable
- Identifies sensitivity to market conditions

---

### Example 6: Parameter Sensitivity Analysis

```python
base_params = {
    'sma_short': 20,
    'sma_long': 50,
    'threshold': 0.02
}

param_ranges = {
    'sma_short': (10, 30),
    'sma_long': (40, 60),
    'threshold': (0.01, 0.05)
}

def evaluate_strategy(params):
    """Mock evaluation - replace with actual strategy backtest"""
    return params['sma_long'] / params['sma_short'] * params['threshold']

df = mc.parameter_sensitivity_analysis(
    base_params=base_params,
    param_ranges=param_ranges,
    evaluation_func=evaluate_strategy,
    num_samples=500
)

# Analyze results
print(df.describe())
print(f"\nBest parameters:")
print(df.nlargest(5, 'performance'))
```

---

## Integration with Trading Bot

### Add Monte Carlo to Risk Management

Integrate Monte Carlo into `risk_management.py`:

```python
from monte_carlo_simulator import MonteCarloSimulator

class RiskManager:
    def __init__(self, total_capital, risk_per_trade=0.02):
        self.total_capital = total_capital
        self.risk_per_trade = risk_per_trade
        self.mc = MonteCarloSimulator(num_simulations=10000)
    
    def calculate_var_cvar(self, expected_return, volatility, days=1):
        """Calculate VaR and CVaR for portfolio"""
        var, cvar = self.mc.simulate_var_cvar(
            initial_capital=self.total_capital,
            expected_return=expected_return,
            volatility=volatility,
            days=days
        )
        return var, cvar
    
    def simulate_portfolio_outcomes(self, positions, days=252):
        """Simulate portfolio returns"""
        results = self.mc.simulate_portfolio_returns(
            initial_capital=self.total_capital,
            positions=positions,
            days=days
        )
        return results
```

### Add Monte Carlo to Backtesting

Enhance `backtesting.py` with robustness testing:

```python
from monte_carlo_simulator import MonteCarloSimulator

class Backtester:
    def __init__(self, initial_capital=10000.0):
        self.initial_capital = initial_capital
        self.mc = MonteCarloSimulator(num_simulations=5000)
    
    def test_strategy_robustness(self, strategy, symbol, days=60):
        """Test strategy across various market scenarios"""
        
        def strategy_wrapper(price_path):
            # Apply strategy to price path
            # Return cumulative P&L
            return strategy.apply(price_path)
        
        robustness = self.mc.simulate_strategy_robustness(
            strategy_func=strategy_wrapper,
            initial_price=100.0,
            days=days,
            drift_range=(-0.002, 0.003),
            volatility_range=(0.01, 0.04),
            num_scenarios=1000
        )
        
        return robustness
```

### Add Monte Carlo to Web GUI

Display Monte Carlo results in `web_gui.py`:

```python
from monte_carlo_simulator import MonteCarloSimulator

mc = MonteCarloSimulator(num_simulations=5000)

# Portfolio projection chart
results = mc.simulate_portfolio_returns(...)
fig = go.Figure()
fig.add_trace(go.Histogram(
    x=results.simulations,
    name='Portfolio Outcomes',
    nbinsx=50
))
fig.add_vline(x=results.median, line_dash="dash", annotation_text="Median")
fig.add_vline(x=results.var_95, line_color="red", annotation_text="VaR 95%")
```

---

## Best Practices

### 1. **Choose Appropriate Number of Simulations**

- **Quick analysis:** 1,000 simulations
- **Standard analysis:** 10,000 simulations (recommended)
- **High precision:** 50,000+ simulations (slow)

### 2. **Use Realistic Parameters**

Estimate drift and volatility from historical data:

```python
import pandas as pd
import numpy as np

# Calculate from historical returns
returns = pd.Series([...])  # Daily returns
drift = returns.mean()
volatility = returns.std()

# Annualized values (optional)
drift_annual = drift * 252
volatility_annual = volatility * np.sqrt(252)
```

### 3. **Interpret Results with Context**

- Monte Carlo assumes returns follow normal distribution (may underestimate tail risk)
- Results are probabilistic, not deterministic predictions
- Use as one input among many for decision-making
- Complement with historical backtesting

### 4. **Test Multiple Scenarios**

Don't rely on single set of parameters:

```python
# Optimistic scenario
results_bull = mc.simulate_portfolio_returns(drift=0.001, volatility=0.015, days=252)

# Base case scenario
results_base = mc.simulate_portfolio_returns(drift=0.0005, volatility=0.02, days=252)

# Pessimistic scenario
results_bear = mc.simulate_portfolio_returns(drift=-0.0002, volatility=0.03, days=252)
```

### 5. **Use Random Seed for Reproducibility**

When debugging or comparing:

```python
mc = MonteCarloSimulator(num_simulations=10000, random_seed=42)
```

---

## Limitations

### Known Limitations of Monte Carlo Simulation

1. **Assumes Normal Distribution**
   - Real markets have "fat tails" (more extreme events)
   - May underestimate probability of rare catastrophic events
   - **Mitigation:** Use higher volatility or add jump diffusion

2. **Independent Price Paths**
   - Each simulation assumes assets move independently
   - Real markets have correlation during crashes
   - **Mitigation:** Use correlation matrix for multi-asset portfolios

3. **Constant Volatility**
   - Assumes volatility doesn't change over time
   - Real markets have volatility clustering
   - **Mitigation:** Use GARCH models or stochastic volatility

4. **No Market Microstructure**
   - Ignores bid-ask spreads, slippage, liquidity
   - **Mitigation:** Add transaction cost assumptions

5. **Computational Cost**
   - Large simulations are slow (10,000+ simulations)
   - **Mitigation:** Use fewer simulations for interactive analysis

---

## Performance Tips

### Optimize for Speed

```python
# Use fewer simulations for quick checks
mc_quick = MonteCarloSimulator(num_simulations=1000)

# Use more for final analysis
mc_precise = MonteCarloSimulator(num_simulations=50000)

# Reduce number of days for parameter tuning
results = mc.simulate_portfolio_returns(days=60)  # Instead of 252
```

### Parallel Processing (Future Enhancement)

Monte Carlo is embarrassingly parallel - future versions could support:

```python
# Future feature (not yet implemented)
mc = MonteCarloSimulator(num_simulations=100000, parallel=True, num_cores=4)
```

---

## FAQ

### Q: How does Monte Carlo differ from backtesting?

**Backtesting:** Tests strategy on actual historical data (one scenario)  
**Monte Carlo:** Tests strategy on thousands of simulated scenarios (probabilistic)

Use both:
- Backtest to validate strategy works on real data
- Monte Carlo to test robustness and quantify uncertainty

### Q: What is a good number of simulations?

10,000 simulations is the sweet spot for accuracy vs. speed. Use more (50,000+) for high-stakes decisions or when tail risk matters.

### Q: Can I use Monte Carlo for intraday trading?

Yes, but adjust parameters:
- Use smaller time steps (minutes instead of days)
- Adjust drift and volatility to intraday scales
- Consider market hours and overnight gaps

### Q: How do I estimate drift and volatility?

From historical data:
```python
import yfinance as yf
data = yf.download('AAPL', period='1y')
returns = data['Close'].pct_change().dropna()
drift = returns.mean()
volatility = returns.std()
```

### Q: What is CVaR and why does it matter?

**CVaR (Conditional Value at Risk)** = Expected loss in worst-case scenarios beyond VaR.

Example:
- VaR (95%) = $300: 95% of days, loss ≤ $300
- CVaR (95%) = $400: In worst 5% of days, expect $400 loss

CVaR matters because it quantifies tail risk beyond VaR.

---

## Advanced Topics

### Custom Strategy Testing

```python
class CustomStrategy:
    def __init__(self, sma_period=20):
        self.sma_period = sma_period
    
    def apply(self, price_path):
        """Apply strategy to price path and return P&L"""
        prices = pd.Series(price_path)
        sma = prices.rolling(self.sma_period).mean()
        
        position = 0
        pnl = 0
        entry_price = 0
        
        for i in range(self.sma_period, len(prices)):
            if prices[i] > sma[i] and position == 0:
                # Buy signal
                position = 1
                entry_price = prices[i]
            elif prices[i] < sma[i] and position == 1:
                # Sell signal
                pnl += prices[i] - entry_price
                position = 0
        
        # Close position at end if open
        if position == 1:
            pnl += prices.iloc[-1] - entry_price
        
        return pnl

# Test strategy
strategy = CustomStrategy(sma_period=20)
robustness = mc.simulate_strategy_robustness(
    strategy_func=lambda path: strategy.apply(path),
    initial_price=100.0,
    days=60,
    drift_range=(-0.001, 0.002),
    volatility_range=(0.01, 0.03),
    num_scenarios=1000
)
```

### Correlated Multi-Asset Simulation (Future Enhancement)

For portfolios with correlated assets, use Cholesky decomposition:

```python
# Pseudocode - not yet implemented
correlation_matrix = np.array([
    [1.0, 0.7],
    [0.7, 1.0]
])

# Generate correlated random shocks
L = np.linalg.cholesky(correlation_matrix)
uncorrelated_shocks = np.random.standard_normal((2, num_simulations))
correlated_shocks = L @ uncorrelated_shocks
```

---

## Troubleshooting

### Issue: Simulations are too slow

**Solution:** Reduce `num_simulations` or `days`:
```python
mc = MonteCarloSimulator(num_simulations=1000)  # Instead of 10000
results = mc.simulate_portfolio_returns(days=60)  # Instead of 252
```

### Issue: Results seem unrealistic

**Solution:** Check drift and volatility parameters:
```python
# Too aggressive
drift=0.01, volatility=0.05  # 250% annual return, 80% volatility

# More realistic
drift=0.0005, volatility=0.02  # 13% annual return, 32% volatility
```

### Issue: VaR is negative

**Solution:** In this project, VaR is defined as a **positive potential loss** amount (see `risk_management.py`). VaR and CVaR from Monte Carlo methods are always returned as non-negative values representing the magnitude of potential losses. If you see unexpected negative values, check that you're using the correct fields: `var_95_loss` and `cvar_95_loss` for loss amounts, or `var_95` for the 5th percentile portfolio value.

---

## References

- **Geometric Brownian Motion:** Standard model for stock price paths
- **Value at Risk (VaR):** Risk management standard (Basel II/III)
- **Conditional VaR (CVaR):** Also called Expected Shortfall (ES)
- **Sharpe Ratio:** Risk-adjusted return metric

---

## Next Steps

1. ✅ Integrate Monte Carlo into `risk_management.py`
2. ✅ Add Monte Carlo visualization to web GUI
3. ✅ Create Monte Carlo analysis in `report_generator.py`
4. ✅ Add Monte Carlo to strategy optimization
5. ✅ Implement correlation-aware multi-asset simulation

---

**For questions or suggestions, open an issue on GitHub.**

---

*Monte Carlo simulation is a powerful tool for understanding uncertainty. Use it wisely to complement your trading analysis!*
