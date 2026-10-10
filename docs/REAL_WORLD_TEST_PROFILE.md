# Real-World Test Profile (Yfinance Training Mode)

This profile configures the bot to **maximize realistic trade volume** with **real market data only** (no random/simulated prices), so you can see how it behaves under conditions close to live trading.

---

## Goal

- **~1000 swing trades per day** (or as many as the strategy and data allow) with **$10k paper capital**.
- **Real market numbers only**: wait for yfinance data; no simulated closes or random prices.
- **Mix of risk profiles**: use the screener’s ranked universe (low/med/high risk mix via existing filters).
- Disregard capital floor, T+1, risk threshold, and max-position limits (yfinance mode already does this) so the test focuses on **throughput and real-data behavior**.

---

## Environment profile (copy into `.env` or set before starting)

Use **Training (yfinance)** mode from the Dashboard so `SCHWAB_API_ENABLED=off` and the bot uses yfinance only.

```bash
# Capital & allocation (high throughput)
BOT_TOTAL_CAPITAL=10000.0
BOT_MIN_ALLOCATION=50.0
BOT_MAX_ALLOCATION=200.0

# High throughput: many symbols, many concurrent positions
MAX_DISCOVERED_STOCKS=200
BOT_MAX_OPEN_POSITIONS=100
ENABLE_STOCK_SCREENER=true
TOP_STOCKS_TO_TRADE=100

# Shorter hold = more round-trips per day (0 = same-day close allowed)
SWING_MIN_HOLD_DAYS=0

# Real data only — no random price fallback
ALLOW_RANDOM_FALLBACK=false

# Fast cycles (yfinance mode already uses minimal delay; this caps cycle wait)
WEB_GUI_CYCLE_DELAY=1

# Exit price = fresh fetch from yfinance (more realistic closes)
EXIT_REFRESH_PRICE=true
```

**Notes:**

- **1000 trades/day** is a target. Actual count depends on: number of BUY/SELL signals, yfinance rate/availability, and how many symbols pass the screener. With 200 symbols, short hold, and 1s cycle delay you get many cycles per day; actual trades = signals × executions.
- **Risk groups**: The screener does **not** have explicit “low / med / high risk” tiers yet (see ROADMAP). It ranks by a **composite score** (momentum, volume, volatility, liquidity, sentiment). To get a broader mix (including more “medium” risk names), you can raise `MAX_STOCK_VOLATILITY` slightly (e.g. `0.20`–`0.25`) so more volatile symbols are included. True risk-tier allocation is a future enhancement.

---

## How “real data only” works

- **`ALLOW_RANDOM_FALLBACK=false`**  
  The bot loop passes `use_random_fallback=False` into the strategy. If yfinance fails for a symbol, the bot does **not** use random prices; it either uses **last close from the same OHLCV history** (still real data) or skips that symbol for that cycle.

- **Execution prices**  
  Entry/exit prices come from **yfinance** (live last price or last close). Exit uses a **refresh** when `EXIT_REFRESH_PRICE=true` so closes reflect the latest available price.

- **No sim closes**  
  Simulated (random) prices are never used when `ALLOW_RANDOM_FALLBACK=false`. Any fallback is to last close from yfinance history, not random.

---

## Suggestions for the most accurate trade data

1. **Run during market hours (e.g. 9:30–16:00 ET)**  
   yfinance “last price” is then more representative of current trading. Outside hours you still get real data (last close), but it’s not live tick.

2. **Keep `ALLOW_RANDOM_FALLBACK=false`**  
   Ensures every fill is either live/last price or last close from yfinance — no random numbers.

3. **Keep `EXIT_REFRESH_PRICE=true`**  
   Exit price is re-fetched from yfinance right before the simulated close, so P&amp;L uses current data.

4. **Save trade history regularly**  
   Use the bot’s “Save trade history” (or equivalent) so you get a timestamped JSON with symbol, action, price, quantity, timestamp, mode. That gives you a clean dataset for win rate, P&amp;L, and strategy tuning.

5. **Log level**  
   For analysis, `LOG_LEVEL=INFO` or `DEBUG=true` helps trace why trades did or didn’t fire (signals, filters, data availability).

6. **Optional: tag market hours in analysis**  
   Trade records include `timestamp`. In post-processing you can flag “market open” vs “market closed” (e.g. 9:30–16:00 ET) to compare behavior and fill quality.

7. **Compare to backtest**  
   After collecting a day of real-time yfinance trades, run a backtest over the same date range and symbols to compare strategy behavior (same logic, different execution path).

---

## Quick start

1. Set the variables above in `.env` (or ensure they’re set when starting the API).
2. In the Dashboard, select **Training (yfinance)** and start the bot.
3. Let it run (ideally during market hours) and monitor trade count and logs.
4. Save trade history when done; use it for win rate, P&amp;L, and tuning across all modes.

This setup gives you a **real-world-style test** with real market numbers and no sim closes, so you can tune and compare behavior across modes with confidence.
