# Yfinance Mode – Log Analysis Summary

This document summarizes what is happening when the bot runs in yfinance mode, based on `trading_bot.log`.

---

## 1. **Most Recent Run (Jan 26, 21:47)**

- **Mode:** PAPER TRADING, yfinance simulation, $10k capital.
- **Symbols:** 10 (fallback list: AAPL, ABBV, ABT, ADBE, AEP, AMAT, AMD, AMGN, AMT, AMZN).
- **Outcome:** Session ended with **"Trading cancelled by user"** before any trading cycle completed.

### Why only 10 symbols and fallback?

- **Screening:** Price range in logs was **$2.00 – $50.00** (from `.env`: `MIN_STOCK_PRICE=2`, `MAX_STOCK_PRICE=50`).
- **Phase 1:** "Screening complete: **0/0** stocks passed filters" → no symbol in the universe (158 names) passed price/volume/volatility.
- **Reason:** Most S&P/Nasdaq names are **above $50**. With `MAX_STOCK_PRICE=50`, almost the entire universe is excluded.
- **Fallback:** "No stocks passed screening criteria, using popular stocks from universe" → bot fell back to 10 popular symbols. Many of those (e.g. AAPL, AMZN, AMAT) are still above $50, so actual tradeable set may be smaller under that cap.

**Recommendation:** For a broader real-world test, raise `MAX_STOCK_PRICE` in `.env` (e.g. `100` or `1000`) so more names pass the screener. See `docs/REAL_WORLD_TEST_PROFILE.md`.

---

## 2. **Earlier Run (Jan 26, 21:24) – Watchlist / Top Performers**

- **Phase 1:** 16 stocks passed basic screening (INTC, APA, HAL, SLB, DOW, DVN, OXY, KMI, GIS, CSX, CMCSA, EXC, DD, T, PFE, VZ).
- **Phase 2:** "**TOP 0 SWING TRADE CANDIDATES**" and "**TOP 0 PERFORMERS**" → advanced scoring returned **no** candidates.
- **Effect:** "No candidates available from screener" and "Watchlist initialized with **0** stocks".

### Why Phase 2 returns 0 when Phase 1 has 16

- In `get_swing_trade_candidates`, Phase 2 scores only symbols for which **`_get_cached_data(symbol)`** returns data.
- If the cache is empty or invalid for those 16 symbols (e.g. different screener instance, or cache not populated for that path), every symbol is skipped and the result is 0 candidates.
- So the likely cause is **cache miss in Phase 2**: same run has 16 passing Phase 1, but when building swing candidates the code relies on cached per-symbol data; if that cache is not filled or is from another instance, you get TOP 0.

**Recommendation:** If you need the watchlist/top performers to be populated, ensure the screener cache is populated for the same instance that runs Phase 2, or add a fallback in Phase 2 to **fetch** symbol data when cache misses (e.g. call `fetch_stock_info(symbol)` and then score).

---

## 3. **Yfinance / Data Issues**

- **Failed downloads:** `yfinance - ERROR - 2 Failed downloads: ['HES', 'MRO']: possibly delisted; no price data found`.  
  HES and MRO are likely delisted or renamed; the bot or universe list can be updated to exclude them to avoid noise.

---

## 4. **ML Signal Filter (when enabled)**

- **Model:** Loaded from `ml_signal_filter_model.pkl`; **accuracy 0.45** (45%).
- **Thresholds:** Min confidence **0.60**, min win probability **0.55**.
- Many runs had **`ENABLE_ML_FILTER=false`**, so the ML filter was not applied in those cycles.
- When the ML filter **is** enabled, a 45% accuracy model with 60%/55% thresholds will **reject** many BUY/SELL signals and turn them into **HOLD**, so you see fewer trades.

**Recommendation:** To see more trades in yfinance mode you can:
- Set **`ENABLE_ML_FILTER=false`** (already the case in some logs), or
- Lower **`MIN_ML_CONFIDENCE`** / **`MIN_ML_WIN_PROBABILITY`** in `.env`, or
- Retrain the ML model for better accuracy and then keep the filter enabled.

---

## 5. **Configuration Warnings in Logs**

- **Obsolete PDT setting:** `ENABLE_PDT_RULES` is obsolete; PDT is determined by `PAPER_TRADING_MODE`. You can remove `ENABLE_PDT_RULES` from `.env`.
- **Redundant:** `SCHWAB_SANDBOX_MODE` and `SCHWAB_API_ENABLED=off` – when API is disabled, sandbox is irrelevant.

---

## 6. **Quick Checklist for “More Action” in Yfinance Mode**

| Goal                         | Action |
|-----------------------------|--------|
| More symbols pass screening | Raise `MAX_STOCK_PRICE` (e.g. 100 or 1000). |
| Watchlist / top performers  | Fix Phase 2 cache (same instance or refetch on cache miss). |
| More BUY/SELL, fewer HOLD   | Set `ENABLE_ML_FILTER=false` or lower ML thresholds; or retrain model. |
| Cleaner logs                | Remove delisted tickers (e.g. HES, MRO) from universe or ignore in logs. |

---

---

## 7. **Who Picked the Fallback Symbols, and When?**

**Who:** The **stock screener** (`stock_screener.py`) picks them when screening returns **0** results. It calls `get_popular_stocks(count=max_results)`.

**What “popular” actually means:** It does **not** mean “best today” or “best yesterday.” The code returns **`self.stock_universe[:count]`** — i.e. the **first N symbols** of the stock universe list. That list is **sorted alphabetically** (from Wikipedia indices or the hardcoded `FALLBACK_STOCK_UNIVERSE`). So you get the **first 10 alphabetically** (e.g. AEP, AAPL, ABBV, ABT, ADBE, AEP, AMAT, AMD, AMGN, AMT, AMZN). No ranking by performance, volume, or momentum.

**When:** Symbols are chosen **once at bot start** (when `load_scan_symbols()` runs). They are **not** re-picked each trading cycle. The universe list itself may be **cached for 24 hours** (`STOCK_UNIVERSE_CACHE_DURATION = 86400` in `stock_screener.py`), so the pool can be up to a day old.

**Implication:** The fallback list is **not** “best stocks today.” It is a static, alphabetical slice of a possibly cached universe. For “best today” behavior you need screening to pass (e.g. raise `MAX_STOCK_PRICE` so the screener returns real candidates) or a different fallback (e.g. sort by volume/momentum before taking the first N).

---

*Generated from analysis of `trading_bot.log` (tail and grep).*
