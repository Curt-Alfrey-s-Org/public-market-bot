# .env Simplification & Mode Buttons

This doc explains the **4 mode buttons**, when to add more, and how to simplify `.env` so you can see what affects what.

---

## 1. Mode Buttons (Current)

The Web GUI has **4 mode buttons** on the homepage:

| Mode | What it does |
|------|----------------|
| **Schwab API (Sandbox)** | Paper trading + Schwab sandbox API. Orders go to ThinkorSwim paperMoney. |
| **Schwab API (Live)** | Live trading. Real orders in your Schwab account. |
| **yfinance Training Mode** | No Schwab. Uses yfinance for data, simulates trades. No API keys needed. |
| **Dry-run (Live)** | Like Live: real credentials & risk checks, but **no orders placed**. Uses `DRY_RUN_MODE=true` for the session. Validate config before going live. |

Selecting a mode **overrides** `PAPER_TRADING_MODE`, `SCHWAB_SANDBOX_MODE`, `SCHWAB_API_ENABLED`, and (for Dry-run) `DRY_RUN_MODE` for that session. One click, clear behavior.

---

## 2. Adding More Mode Buttons?

**Dry-run (Live)** is implemented as the 4th button.

**When it makes sense**

- **Backtest**  
  Run in backtest mode from the GUI. Today backtest is typically CLI-only; a “Backtest” button could launch that flow from the UI.

**When to avoid**

- Don’t add modes for every `.env` toggle (e.g. “High volatility” vs “Low volatility”). Use Settings for that.
- Keep modes as **execution context**: *where* orders go (sandbox / live / none) and *whether* they’re real.

---

## 3. .env Simplification

### 3.1 What affects what (quick map)

| You want to… | Main .env vars |
|--------------|-----------------|
| **Control paper vs live** | `PAPER_TRADING_MODE`, `SCHWAB_SANDBOX_MODE` (or use mode buttons) |
| **Control which stocks are screened** | `MIN_STOCK_PRICE`, `MAX_STOCK_PRICE`, `MIN_DAILY_VOLUME`, `MAX_STOCK_VOLATILITY` |
| **Control how many to scan / trade** | `MAX_STOCKS_TO_SCAN`, `TOP_STOCKS_TO_TRADE`, `MAX_DISCOVERED_STOCKS` |
| **Control order types** | `BOT_DEFAULT_BUY_ORDER_TYPE`, `BOT_DEFAULT_SELL_ORDER_TYPE`, `VALID_ORDER_TYPES` |
| **Control risk** | `BOT_RISK_THRESHOLD`, `BOT_POSITION_SIZE`, `BOT_STOP_LOSS_PERCENT`, `BOT_TRAILING_STOP_PERCENT` |
| **Control shorts** | `ALLOW_SHORTS_IN_PAPER`, `SCHWAB_SHORT_SELLING_ENABLED`, `MAX_SHORT_POSITIONS`, `MAX_SHORT_EXPOSURE_PCT` |

### 3.2 Duplicates to remove

- **Stock screener block** appeared twice (one “TOS-like” section, one “Stock Screener Configuration”). Consolidated into a single **Stock Discovery** section.
- **SCORE_WEIGHT_***, **MAX_STOCKS_TO_SCAN**, **TOP_STOCKS_TO_TRADE**, **MAX_DISCOVERED_STOCKS**, **ENABLE_SENTIMENT_FILTER**, etc. were duplicated. Now defined once.

### 3.3 Vars that don’t need to be in .env (or can move)

- **ENABLE_PDT_RULES** – Deprecated; PDT is driven by `PAPER_TRADING_MODE`. Safe to remove from `.env`.
- **Rate-limit windows** (e.g. `HUGGINGFACE_TIME_WINDOW_SECONDS`) – Usually fine as code defaults. Document in comments; no need to set unless you tune.
- **VOLATILITY_NORMALIZATION_MIN/RANGE** – Niche; keep as code defaults.
- **COPILOT_DEBUG_MODE** – Dev-only. Optional “Development” section or leave out of minimal .env.
- **TOP_PERFORMERS_*** (refresh, min universe, startup delay) – Keep `ENABLE_TOP_PERFORMERS_WATCHLIST` and `TOP_PERFORMERS_WATCHLIST_SIZE`; rest can be code defaults.
- **BOT_THROTTLE_DELAY**, **BOT_MAX_NETWORK_MBPS** – Pi-specific; “Advanced” section only.

### 3.4 Suggested .env layout

1. **Trading control** – Paper/live, dry-run, sandbox, capital, risk, allocation, order types.
2. **APIs** – Keys, token path, callback. Optional rate-limit overrides.
3. **Stock discovery** – Screener on/off, price/volume/volatility, scan/top/max discovered, weights, timing.
4. **Optional features** – Sentiment, ML, portfolio optimization, alerts, throttling.
5. **Advanced / dev** – Throttling tuning, Copilot debug, etc.

---

## 4. Changes applied

- **Universe:** Use **Russell 1000** (`Russell 1000 Index` on Wikipedia) for “Russell index” breadth. ~1000 largest US names; skips the small-cap “bottom” (Russell 2000). Wikipedia has no full Russell 2000 list; Russell 1000 has a full Components table with Symbol.
- **.env.example:** Consolidated duplicate Stock Discovery blocks, removed redundant screener section, dropped `ENABLE_PDT_RULES`, grouped into the sections above, and added a short “What affects what” summary at the top.
- **Mode buttons:** **Dry-run (Live)** added as 4th button. `web_gui.py`: `mode-dryrun-live-button`; `select_mode` handles it; `control_bot` sets Live-like `PAPER_TRADING_MODE`/`SCHWAB_SANDBOX_MODE`/`SCHWAB_API_ENABLED` plus `DRY_RUN_MODE=true` for the session when Start is clicked.

---

## 5. References

- **Mode buttons:** `web_gui.py` – `mode-sandbox-button`, `mode-live-button`, `mode-yfinance-button`, `mode-dryrun-live-button`; `select_mode` callback; `control_bot` applies overrides.
- **Stock universe:** `stock_screener.py` – `STOCK_UNIVERSE_SOURCES`, `get_stock_universe`, `fetch_stock_universe_from_wikipedia`.
- **.env usage:** `main.py`, `stock_screener.py`, `web_gui.py` – `os.getenv` / `load_dotenv`.
