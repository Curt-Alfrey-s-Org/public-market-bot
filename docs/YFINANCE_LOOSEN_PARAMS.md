# yfinance Mode: Loosening Params to See Trades

**Goal:** Bot shows 16 tickers in Decision Report but no data / no trades. This doc explains which settings block trading and how to loosen them **one at a time** so you can see trades, then tighten again once things work.

---

## Log Analysis Summary

From `trading_bot.log` and code:

1. **Decision Report “no data”**  
   - Bot has 16 candidates (`current_symbols`) but `candidate_decisions` can be empty if:
     - The first cycle is still loading (screener or first-symbol OHLCV can take 1–2 min).
     - Every symbol is skipped before a decision is recorded (e.g. insufficient bars, ML filter, HOLD only).

2. **Why trades don’t execute (in order of impact)**  
   - **ML Signal Filter** – Model accuracy ~0.45 but min confidence 0.60, min win prob 0.55 → most BUY/SELL signals are **rejected** and turned into HOLD.  
   - **50-bar requirement** – Strategy needs ≥50 OHLCV bars; yfinance can return fewer for some symbols → logged as “insufficient data (N bars, need 50) — skip”.  
   - **Manual approval** – If `MANUAL_TRADE_APPROVAL_MODE=true`, trades go to Pending and don’t auto-execute.  
   - **Strategy only HOLD** – Many symbols get HOLD from strategies → no BUY/SELL to execute.  
   - **Stock filter** – Price/volume/volatility filters can reject symbols before execution.  
   - **Risk threshold** – In non-yfinance-sim path, risk check can skip (yfinance mode often bypasses position limit; risk check still applies in some paths).

---

## Params to Loosen (One at a Time)

**Change these in the GUI:** **Settings → Strategy** (and **Trading** for Manual Trade Approval). Restart the bot after changing.

Adjust **one** of these, restart the bot, watch Logs + Decision Report. Then try the next if needed.

### 1. **ML Signal Filter (highest impact)**

**Problem:** ML filter rejects most BUY/SELL signals (model accuracy 0.45 vs required confidence 0.60).

**In GUI: Settings → Strategy**
- **Option A:** Turn **ML signal filter** OFF (fastest way to see trades).
- **Option B:** Lower **ML min confidence** and **ML min win prob** (e.g. 0.3 and 0.35).

**Check:** In logs, look for “ML signal filter rejected” vs “decision=BUY → action BUY”. After loosening, you should see fewer “rejected” and more “action BUY/SELL”.

---

### 2. **Strategy min bars (more symbols get a signal)**

**Problem:** Strategy requires 50 OHLCV bars; some symbols have fewer → “insufficient data (N bars, need 50) — skip”.

**In GUI: Settings → Strategy**  
Set **Min OHLCV bars for signal** to **20** (or 30). Min allowed is 10; 20–30 is a good balance for testing.

**Check:** In logs, look for “insufficient data (N bars, need 20)” vs “need 50”. Fewer “insufficient data” skips and more symbols evaluated.

---

### 3. **Manual trade approval**

**Problem:** Trades wait for approval and don’t execute automatically.

**In GUI: Settings → Trading**  
Turn **Manual Trade Approval** OFF.

**Check:** Trades should execute in paper/sim without going to Pending. If you had Pending trades before, they still need manual approval; new trades will auto-execute.

---

### 4. **Stock screener / price range**

**Problem:** Screener uses MIN_STOCK_PRICE and MAX_STOCK_PRICE (e.g. $2–$50). If your 16 tickers are all above $50 or below $2, they might not match; or the screener returns few symbols.

**In GUI: Settings → Discovery**  
Set **Min stock price** and **Max stock price** (e.g. 2 and 500) so more symbols pass.

**Check:** Logs show “Price Range: $X - $Y” and “Loaded N symbols”. Increase N or adjust range so more symbols pass.

---

### 5. **Random fallback (so strategy can still get a signal)**

**Problem:** If yfinance fails for price/volume, strategy can get `(HOLD, None, None)` and skip.

**Keep on for testing (default):**

```bash
ALLOW_RANDOM_FALLBACK=true
```

If you set this to `false`, ensure yfinance is returning price/volume or you’ll see more “no price/volume — skip”.

---

### 6. **Position / risk (usually not the blocker in yfinance)**

In yfinance mode, position limit is often not enforced (`using_yfinance_sim`), so `BOT_MAX_OPEN_POSITIONS` is less likely the cause. If you want to be sure:

```bash
BOT_MAX_OPEN_POSITIONS=20
```

Risk threshold can still skip in some paths; if you’ve fixed the above and still no trades, try:

```bash
BOT_RISK_THRESHOLD=0.05
```

---

## Suggested order (one at a time)

1. **Settings → Strategy:** Turn **ML signal filter** OFF → restart → check Logs + Decision Report for BUY/SELL and executed trades.  
2. If still no or few signals: **Settings → Strategy:** set **Min OHLCV bars for signal** to **20** → restart → check “insufficient data” in logs.  
3. **Settings → Trading:** Ensure **Manual Trade Approval** is OFF so trades auto-execute.  
4. If Decision Report still empty for a long time: check that the first cycle completes (first symbol can take 1–2 min); **Settings → Discovery:** check **Max discovered stocks** and **Min/Max stock price** so symbols actually load.  
5. **Settings → Strategy:** Optionally lower **ML min confidence** and **ML min win prob** instead of turning the filter off.

---

## After you see trades

- Turn **`ENABLE_ML_SIGNAL_FILTER`** back to `true` and set **`ML_SIGNAL_FILTER_MIN_CONFIDENCE`** / **`ML_SIGNAL_FILTER_MIN_WIN_PROB`** to stricter values (e.g. 0.5 / 0.5).  
- Set **`STRATEGY_MIN_BARS=50`** again for production.  
- Keep **`MANUAL_TRADE_APPROVAL_MODE`** as you prefer for safety.

---

## Params reference (.env)

| Param | Default | Loosen for testing | Effect |
|-------|---------|--------------------|--------|
| `ENABLE_ML_SIGNAL_FILTER` | true | false | Stops ML from turning BUY/SELL into HOLD |
| `ML_SIGNAL_FILTER_MIN_CONFIDENCE` | 0.6 | 0.3 | Allow lower-confidence signals |
| `ML_SIGNAL_FILTER_MIN_WIN_PROB` | 0.55 | 0.35 | Allow lower win-probability signals |
| `STRATEGY_MIN_BARS` | 50 | 20 | Fewer bars needed for strategy signal |
| `MANUAL_TRADE_APPROVAL_MODE` | false | false | Trades execute without approval |
| `MIN_STOCK_PRICE` / `MAX_STOCK_PRICE` | 2 / 50 | 2 / 500 | More symbols pass screener |
| `ALLOW_RANDOM_FALLBACK` | true | true | Fallback when yfinance fails |

**Last updated:** January 2026.
