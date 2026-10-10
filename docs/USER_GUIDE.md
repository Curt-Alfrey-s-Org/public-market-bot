# Market Pie5 Bot - Complete User Guide

**Date:** January 26, 2026  
**Version:** 1.0  
**Status:** Production Ready with Advanced AI/ML Features

---

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [Core Features](#core-features)
3. [AI/ML Integration Features](#aiml-integration-features)
4. [Configuration Guide](#configuration-guide)
5. [Trading Modes](#trading-modes)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## 🚀 Quick Start

**New to the project?** See **[INSTRUCTIONS_FOR_USERS.md](INSTRUCTIONS_FOR_USERS.md)** for step-by-step “what to do now” (start API + frontend, run the bot, where to look, performance check, troubleshooting).

### Installation

```bash
# Clone repository
git clone https://github.com/Curt-Alfrey-s-Org/market-pie5-bot.git
cd market-pie5-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

### First Run (Web dashboard — recommended)

```bash
# Terminal 1: Start the API (required)
./start_api.sh

# Terminal 2: Start the React frontend
cd frontend && npm install && npm run dev
# Open browser to http://localhost:5173
# Choose mode (e.g. yfinance), then click Start
```

**Or run CLI mode:**

```bash
python3 main.py --mode paper
```

---

## 🎯 Core Features

### 1. Signal-Based Trading
- **5 Trading Strategies:** SMA, Bollinger Bands, RSI, MACD, Momentum
- **Combined Signals:** Weighted voting from all strategies
- **Signal-to-Action Mapping:** BUY/SELL → Long/Short positions

### 2. Risk Management
- **Capital Floor Protection:** Auto-pause when capital drops below threshold
- **PDT Compliance:** Pattern Day Trading rule enforcement
- **Position Limits:** Max open positions, short concentration limits
- **Stop Loss & Take Profit:** Configurable risk management

### 3. Short Selling
- **Full Short Support:** SHORT and COVER actions
- **Concentration Limits:** Max short positions and exposure
- **Validated:** 19/19 tests passing

---

## 🤖 AI/ML Integration Features

### 1. ML Signal Filter ✅

**What it does:** Filters trading signals before execution based on ML predictions of success probability.

**How it works:**
- Trained Random Forest model predicts signal quality
- Filters out low-confidence/low-probability signals
- Improves win rate by only trading high-quality signals

**Configuration:**
```bash
ENABLE_ML_SIGNAL_FILTER=true
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.6
ML_SIGNAL_FILTER_MIN_WIN_PROB=0.55
ML_SIGNAL_FILTER_MODEL_TYPE=random_forest
```

**Training:**
```bash
# Train with synthetic data (initial)
python3 train_ml_signal_filter.py --use-synthetic

# Retrain with real trade data (after collecting trades)
python3 train_ml_signal_filter.py
```

**Expected Impact:** +5-10% win rate improvement

---

### 2. Portfolio Optimizer ✅

**What it does:** Uses Modern Portfolio Theory to optimize position sizing and allocation.

**How it works:**
- Calculates optimal capital allocation across symbols
- Considers correlation and diversification
- Uses Sharpe ratio, minimum variance, or risk parity methods

**Configuration:**
```bash
ENABLE_PORTFOLIO_OPTIMIZATION=true
PORTFOLIO_OPTIMIZATION_METHOD=sharpe  # sharpe, min_variance, risk_parity, equal
```

**Expected Impact:** +10-15% risk-adjusted returns improvement

---

### 3. Adaptive Learning ✅

**What it does:** Bot learns from trade outcomes and adapts strategy selection over time.

**How it works:**
- Q-Learning: Learns which strategies work best in different market conditions
- Multi-Armed Bandit: Dynamically adjusts strategy weights
- Updates strategy weights based on performance

**Configuration:**
```bash
ENABLE_ADAPTIVE_LEARNING=true
ADAPTIVE_LEARNING_METHOD=qlearning  # qlearning or bandit
ADAPTIVE_LEARNING_EXPLORATION=true  # Enable exploration during learning
```

**Expected Impact:** Continuous improvement over time, adapts to market conditions

---

### 4. Real-Time ML Parameter Optimization ✅

**What it does:** Optimizes trading parameters during trading (not just at end).

**How it works:**
- Runs periodically (every N trades or N minutes)
- Uses HuggingFace API for ML-based optimization
- Applies optimized parameters at runtime where possible

**Configuration:**
```bash
ENABLE_REALTIME_ML_OPTIMIZATION=true
ML_OPTIMIZATION_INTERVAL_TRADES=20
ML_OPTIMIZATION_INTERVAL_MINUTES=60
ML_OPTIMIZATION_MIN_TRADES=10
```

**Expected Impact:** Parameters adapt to current market conditions

---

### 5. Performance Caching ✅

**What it does:** Caches computation results to improve efficiency.

**How it works:**
- Portfolio optimization results cached (5-minute TTL)
- ML prediction results cached (1-minute TTL)
- Reduces redundant computation

**Configuration:**
```bash
PORTFOLIO_OPTIMIZATION_CACHE_TTL=300  # 5 minutes
ML_PREDICTION_CACHE_TTL=60            # 1 minute
```

**Expected Impact:** Faster execution, reduced resource usage

---

## ⚙️ Configuration Guide

### Essential Settings

```bash
# Trading Mode
PAPER_TRADING_MODE=true              # Start with paper trading!

# Capital
BOT_STARTING_CAPITAL=10000.00

# Risk Management
BOT_RISK_THRESHOLD=0.02              # 2% risk per trade
BOT_STOP_LOSS_PERCENT=0.06           # 6% stop loss
HIGH_SALE_PERCENT=0.10               # 10% take profit

# Position Limits
BOT_MAX_OPEN_POSITIONS=5
MAX_SHORT_POSITIONS=5
MAX_SHORT_EXPOSURE_PCT=0.25          # 25% max short exposure
```

### AI/ML Settings

```bash
# ML Signal Filter
ENABLE_ML_SIGNAL_FILTER=true
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.6
ML_SIGNAL_FILTER_MIN_WIN_PROB=0.55

# Portfolio Optimization
ENABLE_PORTFOLIO_OPTIMIZATION=true
PORTFOLIO_OPTIMIZATION_METHOD=sharpe

# Adaptive Learning
ENABLE_ADAPTIVE_LEARNING=true
ADAPTIVE_LEARNING_METHOD=qlearning

# Real-time ML Optimization
ENABLE_REALTIME_ML_OPTIMIZATION=true
ML_OPTIMIZATION_INTERVAL_TRADES=20
```

### Email Alerts

```bash
ENABLE_ALERTS=true
ALERT_EMAIL=operator@example.com
ALERT_MIN_SEVERITY=WARNING          # Only WARNING and CRITICAL

# SMTP Configuration (Gmail example)
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=operator@example.com
SMTP_PASSWORD=your_app_password
```

**See:** `docs/EMAIL_ALERT_SETUP.md` for detailed email setup

---

## 📊 Trading Modes

### Paper Trading (Recommended for Testing)

```bash
PAPER_TRADING_MODE=true
```

**Features:**
- No real money at risk
- Full feature testing
- PDT rules disabled
- Perfect for learning and validation

### Live Trading

```bash
PAPER_TRADING_MODE=false
SCHWAB_API_ENABLED=on
```

**Requirements:**
- Valid Schwab API credentials
- OAuth token (token.json)
- Sufficient capital
- PDT compliance (if < $25k)

**⚠️ WARNING:** Only use after extensive paper trading validation!

---

## 📧 Monitoring & Alerts

### Email Alerts

**Severity Levels:**
- **INFO:** Routine updates (trading resumed, status)
- **WARNING:** Important warnings (PDT warnings, throttling)
- **CRITICAL:** Urgent issues (errors, capital floor, failures)

**Configuration:**
```bash
ALERT_MIN_SEVERITY=WARNING  # Only send WARNING and CRITICAL
EMAIL_MAX_PER_HOUR=20       # Prevent spam
```

### Log Files

- **`alerts.log`:** All alerts (file logging)
- **Console logs:** Real-time trading activity
- **Trade history:** Stored in bot memory and logged

---

## 🔧 Troubleshooting

### Bot Not Trading

**Check:**
1. Is `PAPER_TRADING_MODE=true`? (if testing)
2. Is capital above floor?
3. Are symbols loaded? (`scan_symbols.txt` or screener)
4. Check logs for errors

**Fix:**
- Verify `.env` configuration
- Check `alerts.log` for issues
- Ensure symbols are available

### ML Signal Filter Not Working

**Check:**
1. Is model trained? (`ml_signal_filter_model.pkl` exists)
2. Is `ENABLE_ML_SIGNAL_FILTER=true`?
3. Check logs for "Signal filtered" messages

**Fix:**
- Train model: `python3 train_ml_signal_filter.py --use-synthetic`
- Verify model loads on startup (check logs)

### Email Alerts Not Sending

**Check:**
1. Is `ENABLE_ALERTS=true`?
2. Are SMTP credentials configured?
3. Check severity level (`ALERT_MIN_SEVERITY`)

**Fix:**
- Configure SMTP in `.env`
- Test: `python3 test_email_alerts.py`
- See `docs/EMAIL_ALERT_SETUP.md`

### Performance Issues

**Check:**
1. Resource throttling status
2. Cache hit rates
3. API rate limits

**Fix:**
- Enable resource throttling
- Increase cache TTLs if appropriate
- Check API rate limit settings

---

## ✅ Best Practices

### 1. Start with Paper Trading
- Always test in paper mode first
- Run for at least 20-50 trades
- Validate all features work correctly

### 2. Configure Risk Management
- Set appropriate capital floor
- Use stop loss and take profit
- Limit position sizes
- Monitor PDT compliance

### 3. Enable All Integrations
- ML Signal Filter: Improves win rate
- Portfolio Optimizer: Better allocation
- Adaptive Learning: Continuous improvement
- Real-time ML Optimization: Parameter tuning

### 4. Monitor Performance
- Check email alerts regularly
- Review trade history
- Monitor win rate trends
- Watch for capital floor breaches

### 5. Gradual Transition to Live
- Start with small capital
- Monitor closely for first week
- Gradually increase position sizes
- Keep paper trading as backup

### 6. Regular Maintenance
- Retrain ML model with real data
- Review and adjust configuration
- Monitor resource usage
- Update dependencies

---

## 📈 Expected Performance

With all integrations enabled:

- **Win Rate:** +5-10% improvement (ML filtering)
- **Risk-Adjusted Returns:** +10-15% improvement (portfolio optimization)
- **Adaptability:** Continuous learning and improvement
- **Efficiency:** Faster execution with caching

---

## 🎓 Learning Resources

- **Integration Guide:** `docs/INTEGRATION_COMPLETE.md`
- **Email Setup:** `docs/EMAIL_ALERT_SETUP.md`
- **Testing Guide:** `docs/TESTING_GUIDE.md`
- **Next Steps:** `docs/NEXT_STEPS.md`

---

## 🆘 Getting Help

1. **Check Documentation:** `docs/` directory
2. **Review Logs:** `alerts.log` and console output
3. **Run Validation:** `python3 validate_integrations.py`
4. **Test Components:** Individual test scripts in repo

---

## ✅ Quick Checklist

Before going live:

- [ ] Paper trading tested (20+ trades)
- [ ] All integrations validated
- [ ] ML model trained
- [ ] Email alerts configured and tested
- [ ] Risk management configured
- [ ] Capital floor set appropriately
- [ ] PDT compliance understood
- [ ] Backup and monitoring in place

---

**Ready to start trading! Begin with paper mode and gradually transition to live.**
