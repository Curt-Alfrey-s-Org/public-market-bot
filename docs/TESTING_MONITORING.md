# Testing & Monitoring Guide

**Date:** January 26, 2026  
**Purpose:** Guide for monitoring integration testing and paper trading sessions

---

## 🚀 Quick Start Testing

### Option 1: Web GUI (Recommended)

```bash
./start_web_gui.sh
# Open browser to http://localhost:8050
# Click 'Start' button
```

**Advantages:**
- Visual dashboard
- Real-time charts
- Easy monitoring
- Point-and-click controls

### Option 2: CLI Paper Trading

```bash
python3 main.py --mode paper
```

**Advantages:**
- Full log output
- See all integration messages
- Easy to grep/search logs

---

## 📊 What to Monitor

### 1. ML Signal Filter

**Look for in logs:**
```
Signal filtered: confidence=0.45, win_prob=0.50
Signal accepted: confidence=0.75, win_prob=0.65
```

**What it means:**
- Low-confidence signals are filtered out
- Only high-quality signals proceed
- Should improve win rate

**Expected:** Some signals filtered (10-30% typical)

---

### 2. Portfolio Optimizer

**Look for in logs:**
```
Optimal allocation (sharpe):
  AAPL: $3333.33 (33.33%)
  MSFT: $3333.33 (33.33%)
  GOOGL: $3333.33 (33.33%)
```

**What it means:**
- Allocations optimized based on correlation
- Better risk-adjusted returns
- Diversification improved

**Expected:** Allocations differ from simple equal allocation

**Note:** Requires `ENABLE_PORTFOLIO_OPTIMIZATION=true` and symbols list available

---

### 3. Adaptive Learning

**Look for in logs:**
```
Updated SMA strategy weight: 1.00 -> 1.15
Updated RSI strategy weight: 1.00 -> 0.85
Updated adaptive learning for AAPL: reward=0.0500, strategy=SMA
```

**What it means:**
- Strategy weights adapt based on performance
- Better strategies get higher weights
- Bot learns which strategies work best

**Expected:** Strategy weights change after 10+ trades

---

### 4. Real-time ML Optimization

**Look for in logs:**
```
Running periodic ML parameter optimization (trade #20)...
ML optimization complete: predicted win rate 65.0%
Applied optimized BOT_TRAILING_STOP_PERCENT: 0.0500 -> 0.0450
```

**What it means:**
- Parameters optimize during trading
- Applied at runtime where possible
- Bot adapts to current conditions

**Expected:** Optimization runs every 20 trades or 60 minutes

---

### 5. Performance Caching

**Look for in logs:**
```
Using cached portfolio allocation (age: 45.2s)
Using cached ML prediction for AAPL (age: 12.3s)
```

**What it means:**
- Caching reduces redundant computation
- Faster execution
- Better resource utilization

**Expected:** Cache hits after first computation

---

## 🔍 Log Monitoring Commands

### Watch for ML Signal Filter Activity

```bash
# In terminal while bot is running
tail -f alerts.log | grep -i "signal filter\|signal accepted\|signal filtered"
```

### Watch for Portfolio Optimization

```bash
tail -f alerts.log | grep -i "optimal allocation\|portfolio"
```

### Watch for Adaptive Learning

```bash
tail -f alerts.log | grep -i "strategy weight\|adaptive learning\|updated.*strategy"
```

### Watch for ML Optimization

```bash
tail -f alerts.log | grep -i "ml optimization\|optimized parameter"
```

### Watch for Cache Hits

```bash
tail -f alerts.log | grep -i "cached\|cache"
```

---

## 📈 Performance Metrics to Track

### Short Term (First 20 Trades)

1. **ML Signal Filter:**
   - How many signals filtered?
   - Win rate on remaining signals
   - Confidence/win probability distribution

2. **Portfolio Optimizer:**
   - Allocation decisions
   - Diversification score
   - Risk-adjusted returns

3. **Adaptive Learning:**
   - Strategy weight changes
   - Which strategies performing best
   - Learning progress

4. **Real-time ML Optimization:**
   - Optimization cycles
   - Parameter changes
   - Predicted vs actual performance

5. **Performance:**
   - Cache hit rates
   - Execution speed
   - Resource usage

### Long Term (100+ Trades)

1. **Win Rate:** Overall improvement
2. **Risk-Adjusted Returns:** Sharpe ratio improvement
3. **Adaptability:** Strategy selection evolution
4. **Efficiency:** Performance improvements

---

## 🎯 Success Indicators

### Integration Working Correctly:

- ✅ ML Signal Filter filtering some signals
- ✅ Portfolio Optimizer providing optimized allocations
- ✅ Adaptive Learning updating strategy weights
- ✅ Real-time ML Optimization running periodically
- ✅ Performance caching reducing computation
- ✅ No critical errors in logs
- ✅ Trades executing successfully

### Performance Improving:

- ✅ Win rate trending upward
- ✅ Better risk-adjusted returns
- ✅ Strategy weights converging to best performers
- ✅ Parameters optimizing appropriately
- ✅ Faster execution with caching

---

## ⚠️ Warning Signs

### Issues to Watch For:

1. **No ML Filtering:**
   - All signals passing through
   - Check model training status
   - Verify thresholds not too low

2. **No Portfolio Optimization:**
   - Simple equal allocation used
   - Check `ENABLE_PORTFOLIO_OPTIMIZATION=true`
   - Verify symbols list available

3. **No Adaptive Learning Updates:**
   - Strategy weights not changing
   - Check trades completing (not just opening)
   - Verify `ENABLE_ADAPTIVE_LEARNING=true`

4. **No ML Optimization:**
   - Parameters not optimizing
   - Check `ENABLE_REALTIME_ML_OPTIMIZATION=true`
   - Verify trade count reaching threshold

5. **Performance Issues:**
   - Slow execution
   - High resource usage
   - Check cache hit rates
   - Verify resource throttling

---

## 📝 Testing Checklist

### Pre-Test:

- [ ] All integrations validated (`python3 validate_integrations.py`)
- [ ] ML model trained (`ml_signal_filter_model.pkl` exists)
- [ ] Configuration reviewed
- [ ] Paper trading mode enabled
- [ ] Email alerts configured (optional)

### During Test:

- [ ] Bot starts successfully
- [ ] Trades executing
- [ ] ML Signal Filter active
- [ ] Portfolio Optimizer active
- [ ] Adaptive Learning updating
- [ ] Real-time ML Optimization running
- [ ] Performance acceptable
- [ ] No critical errors

### Post-Test:

- [ ] Review trade history
- [ ] Analyze performance metrics
- [ ] Check integration activity
- [ ] Retrain ML model if needed
- [ ] Adjust configuration
- [ ] Document findings

---

## 🔧 Troubleshooting During Testing

### Bot Not Trading

1. Check capital above floor
2. Verify symbols loaded
3. Check for errors in logs
4. Verify paper trading mode

### Integrations Not Active

1. Check configuration in `.env`
2. Verify integrations initialized (check startup logs)
3. Run validation: `python3 validate_integrations.py`
4. Check for errors in logs

### Performance Issues

1. Check resource throttling status
2. Verify cache hit rates
3. Monitor system resources
4. Adjust cache TTLs if needed

---

## 📊 Sample Test Session

### Expected Output (First 10 Trades):

```
[Trade 1]
  Signal: BUY
  ML Filter: Signal accepted (confidence=0.72, win_prob=0.62)
  Portfolio Allocation: $2000.00 (optimized)
  Strategy: SMA (weight=1.00)
  Executed: BUY 10 shares of AAPL at $150.00

[Trade 2]
  Signal: SELL
  ML Filter: Signal filtered (confidence=0.45, win_prob=0.48)
  Result: Trade skipped (filtered by ML)

[Trade 3]
  Signal: BUY
  ML Filter: Signal accepted (confidence=0.68, win_prob=0.58)
  Portfolio Allocation: $2000.00 (cached)
  Strategy: RSI (weight=1.00)
  Executed: BUY 8 shares of MSFT at $250.00

[Trade 10]
  Signal: SELL
  ML Filter: Signal accepted (confidence=0.75, win_prob=0.65)
  Strategy: MACD (weight=1.12)  # Weight increased from learning
  Executed: SELL 10 shares of AAPL at $155.00
  P&L: +$50.00 (+3.33%)
  Adaptive Learning: Updated (reward=0.0333)
  Strategy Weight: MACD 1.00 -> 1.12
```

---

## 🎯 Testing Goals

### Minimum Test (20 Trades):

- Verify all integrations working
- See ML filtering in action
- Observe adaptive learning updates
- Confirm performance acceptable

### Extended Test (50+ Trades):

- Validate performance improvements
- See strategy weight evolution
- Observe ML optimization cycles
- Collect data for model retraining

### Production Validation (100+ Trades):

- Long-term stability
- Performance trends
- Integration synergy
- Ready for live trading

---

**Happy Testing! Monitor closely and adjust as needed.**
