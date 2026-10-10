# Testing Guide - Integrated Bot

**Date:** January 26, 2026  
**Status:** Ready for Extended Testing

---

## ✅ Pre-Testing Validation

All integration tests passed:
- ✅ ML Signal Filter: Model loaded and ready
- ✅ Portfolio Optimizer: Working
- ✅ Adaptive Learning: Working
- ✅ Real-time ML Optimization: Ready
- ✅ Performance Caching: Working

---

## 🚀 Testing Options

### Option 1: Web GUI (Recommended)

**Start:**
```bash
./start_web_gui.sh
```

**Advantages:**
- Visual dashboard
- Real-time monitoring
- Easy to start/stop
- See all integrations in action

**What to Watch:**
- Signal generation and filtering
- Trade execution
- Portfolio allocations
- Performance metrics

---

### Option 2: CLI Paper Trading

**Start:**
```bash
python3 main.py --mode paper
```

**Advantages:**
- Full log output
- See all integration messages
- Easy to monitor logs

**What to Watch in Logs:**
- `Signal filtered:` - ML filter rejecting signals
- `Portfolio optimization` - Allocation decisions
- `Updated adaptive learning` - Learning updates
- `ML optimization complete` - Parameter optimization

---

## 📊 What to Monitor

### 1. ML Signal Filter

**Look for in logs:**
```
Signal filtered: confidence=0.45, win_prob=0.50
Signal accepted: confidence=0.75, win_prob=0.65
```

**What it means:**
- Signals with low confidence/win probability are filtered
- Only high-quality signals proceed to execution
- Should improve win rate

**Expected:** Some signals filtered, win rate improves on remaining trades

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

---

### 3. Adaptive Learning

**Look for in logs:**
```
Updated SMA strategy weight: 1.00 -> 1.15
Updated RSI strategy weight: 1.00 -> 0.85
```

**What it means:**
- Strategy weights adapt based on performance
- Better strategies get higher weights
- Bot learns which strategies work best

**Expected:** Strategy weights change over 10+ trades

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

## 📈 Success Metrics

### Short Term (20-50 trades):

1. **ML Signal Filter:**
   - Some signals filtered (10-30%)
   - Win rate on remaining signals improves

2. **Portfolio Optimizer:**
   - Allocations optimized
   - Better diversification

3. **Adaptive Learning:**
   - Strategy weights changing
   - Better strategies emerging

4. **Real-time ML Optimization:**
   - Parameters optimizing periodically
   - Runtime updates working

5. **Performance:**
   - Cache hits occurring
   - Faster execution

### Long Term (100+ trades):

1. **Win Rate:** +5-10% improvement
2. **Risk-Adjusted Returns:** +10-15% improvement
3. **Adaptability:** Continuous improvement
4. **Efficiency:** Faster execution

---

## 🔍 Troubleshooting

### ML Signal Filter Not Filtering

**Check:**
- Is model loaded? (Check logs for "Model loaded from...")
- Are confidence thresholds too low?
- Check `ML_SIGNAL_FILTER_MIN_CONFIDENCE` and `ML_SIGNAL_FILTER_MIN_WIN_PROB`

**Fix:**
- Verify model file exists: `ls -lh ml_signal_filter_model.pkl`
- Check model is trained: Model accuracy should be > 0.5

### Portfolio Optimizer Not Used

**Check:**
- Is `ENABLE_PORTFOLIO_OPTIMIZATION=true`?
- Are symbols loaded? (Check `bot.current_symbols`)

**Fix:**
- Verify `.env` settings
- Ensure symbols are loaded before trading

### Adaptive Learning Not Updating

**Check:**
- Are trades being closed? (Learning happens in `close_position()`)
- Is `ENABLE_ADAPTIVE_LEARNING=true`?

**Fix:**
- Ensure trades complete (not just opened)
- Check adaptive learning statistics

### Performance Issues

**Check:**
- Cache hit rates
- API call frequency
- Resource throttling

**Fix:**
- Increase cache TTLs if data doesn't change frequently
- Check resource throttling settings

---

## 📝 Testing Checklist

- [ ] Run integration validation: `python3 validate_integrations.py`
- [ ] Start paper trading session
- [ ] Monitor ML signal filtering
- [ ] Monitor portfolio optimization
- [ ] Monitor adaptive learning
- [ ] Monitor real-time ML optimization
- [ ] Monitor performance caching
- [ ] Collect 20-50 trades
- [ ] Retrain ML model with real data
- [ ] Compare performance before/after integration

---

## 🎯 Next Steps After Testing

1. **Retrain ML Model:**
   ```bash
   python3 train_ml_signal_filter.py
   ```
   (Without --use-synthetic to use real trade data)

2. **Tune Configuration:**
   - Adjust ML filter thresholds based on results
   - Adjust adaptive learning exploration rate
   - Fine-tune optimization intervals

3. **Production Validation:**
   - Test in sandbox mode
   - Validate resource usage
   - Final performance validation

---

**Ready to start testing!**
