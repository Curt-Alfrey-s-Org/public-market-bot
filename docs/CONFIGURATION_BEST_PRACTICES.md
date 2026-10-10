# Configuration Best Practices Guide

**Date:** January 26, 2026  
**Purpose:** Best practices for configuring the trading bot for optimal performance and safety

---

## 🎯 Configuration Philosophy

### Start Conservative, Scale Gradually

1. **Begin with Paper Trading:** Always start in paper mode
2. **Use Conservative Settings:** Lower risk, smaller positions
3. **Monitor and Adjust:** Watch performance, then optimize
4. **Scale Gradually:** Increase risk/position sizes slowly

---

## 📊 Recommended Configuration Tiers

### Tier 1: Beginner (Paper Trading)

**Goal:** Learn the system, validate features

```bash
# Trading Mode
PAPER_TRADING_MODE=true
ENABLE_STOCK_SCREENER=true
MAX_DISCOVERED_STOCKS=10

# Capital (Paper)
BOT_STARTING_CAPITAL=10000.00
BOT_POSITION_SIZE=0.01          # 1% per position
BOT_MAX_OPEN_POSITIONS=3       # Start small

# Risk Management
BOT_RISK_THRESHOLD=0.01        # 1% risk per trade
BOT_STOP_LOSS_PERCENT=0.05     # 5% stop loss
HIGH_SALE_PERCENT=0.08         # 8% take profit
CAPITAL_FLOOR_PERCENT=0.20     # 20% floor (conservative)

# AI/ML (All Enabled for Learning)
ENABLE_ML_SIGNAL_FILTER=true
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.65    # Higher threshold
ML_SIGNAL_FILTER_MIN_WIN_PROB=0.60      # Higher threshold

ENABLE_PORTFOLIO_OPTIMIZATION=true
PORTFOLIO_OPTIMIZATION_METHOD=sharpe

ENABLE_ADAPTIVE_LEARNING=true
ADAPTIVE_LEARNING_EXPLORATION=true      # Enable exploration

ENABLE_REALTIME_ML_OPTIMIZATION=true
ML_OPTIMIZATION_INTERVAL_TRADES=10      # More frequent for learning

# Alerts
ENABLE_ALERTS=true
ALERT_MIN_SEVERITY=WARNING              # Only important alerts
```

---

### Tier 2: Intermediate (Extended Paper Trading)

**Goal:** Extended validation, performance optimization

```bash
# Increase activity
MAX_DISCOVERED_STOCKS=20
BOT_MAX_OPEN_POSITIONS=5
BOT_POSITION_SIZE=0.02          # 2% per position

# Slightly more aggressive
BOT_RISK_THRESHOLD=0.015        # 1.5% risk
BOT_STOP_LOSS_PERCENT=0.06     # 6% stop loss
HIGH_SALE_PERCENT=0.10         # 10% take profit

# ML Settings (After Model Retraining)
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.60    # Lower threshold (more trades)
ML_SIGNAL_FILTER_MIN_WIN_PROB=0.55

# Adaptive Learning (After Initial Learning)
ADAPTIVE_LEARNING_EXPLORATION=false     # Less exploration, more exploitation
ML_OPTIMIZATION_INTERVAL_TRADES=20      # Less frequent
```

---

### Tier 3: Advanced (Live Trading - Small Capital)

**Goal:** Live trading with small capital, careful monitoring

```bash
# Live Trading
PAPER_TRADING_MODE=false
SCHWAB_API_ENABLED=on
BOT_STARTING_CAPITAL=5000.00    # Start small

# Conservative Risk
BOT_POSITION_SIZE=0.01          # 1% per position
BOT_MAX_OPEN_POSITIONS=3
BOT_RISK_THRESHOLD=0.01         # 1% risk
CAPITAL_FLOOR_PERCENT=0.30      # 30% floor (very conservative)

# Strict ML Filtering
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.70    # High confidence only
ML_SIGNAL_FILTER_MIN_WIN_PROB=0.65

# Alerts (All Critical)
ALERT_MIN_SEVERITY=CRITICAL     # Only critical alerts
EMAIL_MAX_PER_HOUR=10           # Lower email rate
```

---

### Tier 4: Production (Live Trading - Full Capital)

**Goal:** Full production trading with optimized settings

```bash
# Full Capital
BOT_STARTING_CAPITAL=25000.00   # PDT compliance threshold

# Optimized Settings (Based on Performance)
BOT_POSITION_SIZE=0.02          # 2% per position
BOT_MAX_OPEN_POSITIONS=5
BOT_RISK_THRESHOLD=0.02         # 2% risk

# ML Settings (Tuned from Performance Data)
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.65    # Tuned threshold
ML_SIGNAL_FILTER_MIN_WIN_PROB=0.60

# Adaptive Learning (Exploitation Mode)
ADAPTIVE_LEARNING_EXPLORATION=false     # No exploration
ML_OPTIMIZATION_INTERVAL_TRADES=30     # Less frequent

# Alerts
ALERT_MIN_SEVERITY=WARNING      # WARNING and CRITICAL
EMAIL_MAX_PER_HOUR=20
```

---

## 🔧 Configuration by Feature

### ML Signal Filter

**Conservative (Fewer Trades, Higher Quality):**
```bash
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.70
ML_SIGNAL_FILTER_MIN_WIN_PROB=0.65
```

**Balanced (Recommended):**
```bash
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.60
ML_SIGNAL_FILTER_MIN_WIN_PROB=0.55
```

**Aggressive (More Trades):**
```bash
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.50
ML_SIGNAL_FILTER_MIN_WIN_PROB=0.50
```

**Tip:** Start conservative, lower thresholds after model retrains with real data.

---

### Portfolio Optimization

**Best Risk-Adjusted Returns:**
```bash
PORTFOLIO_OPTIMIZATION_METHOD=sharpe
```

**Lower Risk:**
```bash
PORTFOLIO_OPTIMIZATION_METHOD=min_variance
```

**Equal Risk Distribution:**
```bash
PORTFOLIO_OPTIMIZATION_METHOD=risk_parity
```

**Simple Equal Allocation:**
```bash
PORTFOLIO_OPTIMIZATION_METHOD=equal
# Or disable:
ENABLE_PORTFOLIO_OPTIMIZATION=false
```

---

### Adaptive Learning

**Learning Phase (Paper Trading):**
```bash
ADAPTIVE_LEARNING_EXPLORATION=true     # Explore strategies
ADAPTIVE_LEARNING_METHOD=qlearning     # Q-Learning for state-based learning
```

**Production Phase (Live Trading):**
```bash
ADAPTIVE_LEARNING_EXPLORATION=false    # Exploit learned knowledge
ADAPTIVE_LEARNING_METHOD=qlearning     # Or bandit for simpler approach
```

---

### Email Alerts

**Minimal Alerts (Production):**
```bash
ALERT_MIN_SEVERITY=CRITICAL
EMAIL_MAX_PER_HOUR=10
EMAIL_MIN_INTERVAL_SECONDS=120
```

**Standard Alerts (Recommended):**
```bash
ALERT_MIN_SEVERITY=WARNING
EMAIL_MAX_PER_HOUR=20
EMAIL_MIN_INTERVAL_SECONDS=60
```

**All Alerts (Testing/Debugging):**
```bash
ALERT_MIN_SEVERITY=INFO
EMAIL_MAX_PER_HOUR=50
EMAIL_MIN_INTERVAL_SECONDS=30
```

---

## ⚠️ Safety Settings

### Capital Protection

```bash
# Conservative (Recommended for Live)
CAPITAL_FLOOR_PERCENT=0.30      # Stop at 30% loss
BOT_STARTING_CAPITAL=10000.00

# Moderate
CAPITAL_FLOOR_PERCENT=0.20      # Stop at 20% loss

# Aggressive (Not Recommended)
CAPITAL_FLOOR_PERCENT=0.10      # Stop at 10% loss
```

### Position Sizing

```bash
# Conservative (1% per position)
BOT_POSITION_SIZE=0.01
BOT_MAX_OPEN_POSITIONS=3

# Moderate (2% per position)
BOT_POSITION_SIZE=0.02
BOT_MAX_OPEN_POSITIONS=5

# Aggressive (5% per position - Not Recommended)
BOT_POSITION_SIZE=0.05
BOT_MAX_OPEN_POSITIONS=10
```

### Risk Per Trade

```bash
# Conservative (1% risk)
BOT_RISK_THRESHOLD=0.01
BOT_STOP_LOSS_PERCENT=0.05

# Moderate (2% risk)
BOT_RISK_THRESHOLD=0.02
BOT_STOP_LOSS_PERCENT=0.06

# Aggressive (3% risk - Not Recommended)
BOT_RISK_THRESHOLD=0.03
BOT_STOP_LOSS_PERCENT=0.08
```

---

## 📈 Performance Optimization

### For Raspberry Pi 5

```bash
# Resource Throttling
BOT_ENABLE_THROTTLING=true
BOT_MAX_CPU_PERCENT=75.0
BOT_MAX_MEMORY_PERCENT=75.0

# Trading Frequency
TRADING_FREQUENCY=2              # 2 seconds between trades

# Caching
PORTFOLIO_OPTIMIZATION_CACHE_TTL=300
ML_PREDICTION_CACHE_TTL=60
```

### For More Powerful Systems

```bash
# Less Aggressive Throttling
BOT_MAX_CPU_PERCENT=85.0
BOT_MAX_MEMORY_PERCENT=85.0

# Faster Trading
TRADING_FREQUENCY=1              # 1 second between trades

# Longer Cache TTLs
PORTFOLIO_OPTIMIZATION_CACHE_TTL=600
ML_PREDICTION_CACHE_TTL=120
```

---

## 🎯 Configuration Workflow

### Step 1: Initial Setup (Paper Trading)

1. Copy `.env.example` to `.env`
2. Set `PAPER_TRADING_MODE=true`
3. Use Tier 1 (Beginner) settings
4. Run for 20-50 trades
5. Monitor performance

### Step 2: Optimization (Extended Paper Trading)

1. Retrain ML model with real trade data
2. Adjust ML filter thresholds based on results
3. Move to Tier 2 (Intermediate) settings
4. Run for 100+ trades
5. Validate all integrations working

### Step 3: Live Trading Preparation

1. Review all trades and performance
2. Set Tier 3 (Advanced) settings
3. Configure email alerts
4. Test in sandbox mode (if available)
5. Start with small capital

### Step 4: Production (Full Capital)

1. After successful small-capital trading
2. Gradually increase position sizes
3. Move to Tier 4 (Production) settings
4. Monitor closely for first month
5. Continue optimization based on results

---

## ✅ Configuration Checklist

Before going live:

- [ ] Paper trading tested (20+ trades minimum)
- [ ] ML model trained with real data
- [ ] All integrations validated
- [ ] Email alerts configured and tested
- [ ] Capital floor set appropriately
- [ ] Position sizes conservative
- [ ] Risk thresholds appropriate
- [ ] PDT compliance understood
- [ ] Backup and monitoring in place
- [ ] Configuration documented

---

## 🔍 Configuration Validation

### Quick Check

```bash
# Validate configuration
python3 -c "
from main import *
print('Paper Mode:', PAPER_TRADING_MODE)
print('ML Filter:', ENABLE_ML_SIGNAL_FILTER)
print('Portfolio Opt:', ENABLE_PORTFOLIO_OPTIMIZATION)
print('Adaptive Learning:', ENABLE_ADAPTIVE_LEARNING)
print('Alerts:', ENABLE_ALERTS)
"
```

### Test All Features

```bash
# Test integrations
python3 validate_integrations.py

# Test email alerts
python3 test_email_alerts.py --test-all

# Test bot initialization
python3 test_integrated_bot.py
```

---

## 📝 Configuration Template

See `.env.example` for complete configuration template with all options documented.

---

## 🎓 Learning Path

1. **Week 1:** Tier 1 settings, paper trading, learn system
2. **Week 2:** Tier 2 settings, extended paper trading, optimize
3. **Week 3:** Tier 3 settings, small-capital live trading
4. **Week 4+:** Tier 4 settings, full production (if successful)

---

**Remember: Start conservative, scale gradually, monitor closely!**
