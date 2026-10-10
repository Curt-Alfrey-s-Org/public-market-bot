# Why the Bot Is Not Trading — Checklist

This doc lists the main reasons the bot may not execute trades and how to verify or fix each.

**Yfinance / Training mode:** When running in **Training** mode (Dashboard: Training, or `SCHWAB_API_ENABLED=off` with paper trading), the bot does **not** enforce: capital floor, T+1 settlement, risk threshold, or max open positions. That way you can test and learn continuously without those limits. PDT is already disabled in all paper/training modes.

---

## 1. **Bot not started (Web GUI)**

The trading loop only runs after you click **Start** on the Dashboard.

- **Check:** Dashboard shows "Stopped" and you have not clicked Start.
- **Fix:** Choose mode (Live / Sandbox / Training / Dry-run), then click **Start**.

---

## 2. **No symbols to trade**

If symbol loading returns an empty list, the loop exits immediately and never trades.

- **Code:** `api/bot_manager.py`: `scan_symbols = bot.load_scan_symbols(...)`; if `not scan_symbols` → "No symbols available for trading", loop exits.
- **Causes:**
  - **Screener:** `ENABLE_STOCK_SCREENER=true` but `screen_for_trades()` returns `[]` (filters too strict, or screener/API error), and `get_popular_stocks()` also returns `[]` (empty universe).
  - **Universe:** Stock universe failed to load (e.g. "Using fallback stock universe" with an empty or tiny list).
  - **Static file:** `ENABLE_STOCK_SCREENER=false` and `scan_symbols.txt` is empty or missing.
- **Check:** Look in logs for:
  - "No symbols available for trading"
  - "Stock screener found 0 stocks"
  - "Loaded 0 symbols"
- **Fix:**
  - Relax `.env`: `MIN_STOCK_PRICE`, `MAX_STOCK_PRICE`, `MIN_DAILY_VOLUME`, `MAX_STOCK_VOLATILITY` (see `.env.example`).
  - Or set `ENABLE_STOCK_SCREENER=false` and put symbols in `scan_symbols.txt`.

---

## 3. **Capital floor**

Trading is paused when capital is at or below the floor.

- **Code:** `main.py`: `check_capital_floor()`; `execute_trade_paper_mode` / `execute_trade_live_mode` return `paused` / skip if `total_capital <= capital_floor`.
- **Check:** Logs or alerts: "Capital below floor", "Trading paused due to capital floor breach".
- **Fix:** Increase capital (e.g. `BOT_TOTAL_CAPITAL` in `.env` or GUI Settings) or lower `CAPITAL_FLOOR_PERCENT` (default 10%).

---

## 4. **All signals are HOLD**

The loop only executes when the strategy returns BUY or SELL (not HOLD).

- **Code:** `api/bot_manager.py`: `signal, price, volume = bot.get_strategy_signal(symbol, ...)`; if `signal == 'HOLD'` → skip. `main.py`: `get_strategy_signal` needs enough OHLCV (e.g. ≥50 bars); otherwise it can return HOLD or fail.
- **Causes:**
  - Not enough history for indicators (e.g. need 50+ bars).
  - Strategy logic: indicators say neither strong buy nor sell.
  - Data issues: yfinance/Schwab returning no or bad data for symbols.
- **Check:** Run with `DEBUG=true` and look for "Strategy signal HOLD for …" or "Insufficient OHLCV for …".
- **Fix:** Ensure symbols have sufficient data; relax or tune strategy thresholds if they are too strict.

---

## 5. **Price or volume missing**

Even with BUY/SELL, the loop skips if price or volume is missing.

- **Code:** `api/bot_manager.py`: `if price is None or volume is None` → "No price/volume for … — skipping".
- **Check:** Logs: "No price/volume for SYMBOL (signal=BUY/SELL) — skipping".
- **Fix:** Check data source (yfinance or Schwab), symbol validity, and rate limits/errors.

---

## 6. **No action from position state**

`_signal_to_action` can return `None` (e.g. BUY when already long, SELL when no position).

- **Code:** `main.py`: `_signal_to_action(symbol, signal)`; `api/bot_manager.py`: `if action is None` → skip.
- **Check:** DEBUG logs: "Strategy signal BUY/SELL for … — no action (position state); skipping".
- **Fix:** Expected when position state and signal don’t match; no change needed unless you expect different behavior.

---

## 7. **Manual trade approval**

If every trade requires approval, nothing executes until you approve.

- **Code:** `main.py`: When `MANUAL_TRADE_APPROVAL_MODE` is true, trades go to pending; execution only after approval.
- **Check:** GUI Settings → Trading → "Manual Trade Approval" is ON; Pending Trades list has items but none approved.
- **Fix:** Approve trades in the UI, or turn off Manual Trade Approval in Settings.

---

## 8. **PDT (pattern day trader) limit**

In production (non‑paper) mode, PDT rules can block opening new positions.

- **Code:** `main.py`: `check_pdt_compliance()`; if not allowed → trade returns `skipped` with `pdt_limit_reached`.
- **Check:** Logs: "PDT CHECK FAILED - TRADE SKIPPED", "pdt_limit_reached".
- **Fix:** Use paper/sandbox mode for testing, or ensure account is PDT‑compliant (e.g. ≥$25k if day trading).

---

## 9. **T+1 settlement**

BUY/SHORT can be skipped if there isn’t enough settled capital.

- **Code:** `main.py`: `check_settled_capital_available(current_allocation)`; if false → "T+1 SETTLEMENT CHECK FAILED - TRADE SKIPPED".
- **Check:** Logs: "T+1 SETTLEMENT CHECK FAILED", "t1_settlement_pending".
- **Fix:** Reduce size/number of trades, or wait for settlement; in paper mode this depends on bot’s settlement logic.

---

## 10. **Risk threshold**

Trade can be rejected if potential loss exceeds the configured risk limit.

- **Code:** `main.py`: `validate_trade()` / risk checks; if "Exceeds risk threshold" → auto_decision REJECT.
- **Check:** Logs or reasoning: "Exceeds risk threshold", "within_risk_limit: False".
- **Fix:** Increase `BOT_RISK_THRESHOLD` or reduce position size / `BOT_MAX_ALLOCATION`.

---

## 11. **Live mode credentials**

In live mode, invalid or missing Schwab credentials cause order calls to fail.

- **Code:** `main.py`: `execute_trade_live_mode`; alerts: "Live mode credentials not configured or invalid".
- **Check:** Alerts or logs: "Failed to execute BUY/SELL for …: Live mode credentials not configured or invalid".
- **Fix:** Use Sandbox or Training mode until credentials are set; in Live, configure and validate Schwab API keys and token.

---

## 12. **Sentiment / ML filter**

Sentiment or ML filters can block a trade even when the strategy says BUY/SELL.

- **Code:** `main.py`: `check_sentiment_filter()` in `execute_trade_paper_mode`; ML filter in `get_strategy_signal`.
- **Check:** Logs: sentiment or ML filter rejecting the trade.
- **Fix:** Temporarily disable sentiment/ML in `.env` or relax filter thresholds.

---

## 13. **Resource throttling**

Heavy CPU/memory throttling can delay or affect symbol loading and strategy runs.

- **Code:** `main.py`: `throttler.check_resources()` before `load_scan_symbols`; throttling can slow or block work.
- **Check:** Logs: "[RESOURCE THROTTLE - SYMBOL LOADING]", throttling messages.
- **Fix:** Increase `BOT_MAX_CPU_PERCENT` / `BOT_MAX_MEMORY_PERCENT` or reduce load (e.g. fewer symbols, less frequent runs).

---

## Quick diagnostic order

1. Confirm **Start** was clicked and status is "Running".
2. Check logs for **"No symbols available for trading"** or **"Loaded 0 symbols"**.
3. Check for **capital floor**, **PDT**, **T+1 settlement**, or **risk** skip messages.
4. With **DEBUG=true**, check for **HOLD**, **no price/volume**, or **no action (position state)**.
5. If in **Live** mode, confirm **Schwab credentials** and no "credentials not configured" errors.
6. If **Manual Trade Approval** is ON, check **Pending Trades** and approve.

The bot’s **no-trade reasons** (and optional alerts) are collected in `no_trade_reasons`; checking the logs and the Dashboard/API for these messages will usually point to the exact blocker.
