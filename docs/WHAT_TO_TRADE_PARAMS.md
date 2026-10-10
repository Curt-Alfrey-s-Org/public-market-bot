# What to Trade: Parameters That Control Symbol Selection

The bot decides **what** to trade in three stages: (1) **symbol source** (which symbols are considered), (2) **per‑symbol filters** (price, volume, volatility), and (3) **optional filters** (sentiment, ML). All of these are controlled via **`.env` only** — there are no Settings UI controls for “what to trade.”

---

## 1. Symbol source (which symbols are considered)

| Param | Env var | Default | Description |
|-------|---------|---------|-------------|
| **Scan symbols file** | `SCAN_SYMBOLS_FILE` | `scan_symbols.txt` | Static list path. Used when screener is off. |
| **Dynamic scan API** | `DYNAMIC_SCAN_API_URL` | *(empty)* | Optional API URL that returns a list of symbols. Rarely used. |
| **Use stock screener** | `ENABLE_STOCK_SCREENER` | `true` | `true` = TOS‑like screener (recommended); `false` = use static file. |
| **Max stocks to scan** | `MAX_STOCKS_TO_SCAN` | `100` (main) / `600` (screener) | Max symbols to fetch/screen when building the universe. |
| **Max discovered stocks** | `MAX_DISCOVERED_STOCKS` | `10` | Max symbols returned from screener (main passes this as `max_symbols`). |
| **Top stocks to trade** | `TOP_STOCKS_TO_TRADE` | `50` | Screener: top N symbols after ranking. |

**Discovery order (first available wins):**

1. **Dynamic API** — if `DYNAMIC_SCAN_API_URL` is set, fetch symbols from that URL.
2. **Stock screener** — if `ENABLE_STOCK_SCREENER=true`, run `screen_for_trades()` (S&P 500, NASDAQ‑100, etc.) → filter by price/volume/volatility → rank → return up to `MAX_DISCOVERED_STOCKS` (or `TOP_STOCKS_TO_TRADE` in screener).
3. **Static file** — read `SCAN_SYMBOLS_FILE` (one symbol per line; `#` = comment).
4. **Hardcoded fallbacks** — e.g. `AAPL`, `MSFT`, `GOOGL`, `TSLA`, `NVDA` if nothing else works.

**Screener ranking (which symbols get prioritized):**  
The screener scores symbols and returns the top N. Weights are configurable via env:

- `SCORE_WEIGHT_MOMENTUM`, `SCORE_WEIGHT_VOLUME`, `SCORE_WEIGHT_VOLATILITY`, `SCORE_WEIGHT_LIQUIDITY`, `SCORE_WEIGHT_SENTIMENT` (defaults in `stock_screener.py` ~113–117).

These affect **which** symbols are chosen from the filtered universe, not whether a symbol is allowed.

**Code:**  
`main.py` `load_scan_symbols()` (5111–5254), `search_tradeable_stocks()` (3248–3410); startup (7206–7211, 7359–7366).  
`stock_screener.py` uses `MIN_STOCK_PRICE`, `MAX_STOCK_PRICE`, `MIN_DAILY_VOLUME`, `MAX_STOCK_VOLATILITY`, `MAX_STOCKS_TO_SCAN`, `TOP_STOCKS_TO_TRADE`, plus scoring weights (74–118).

---

## 2. Per‑symbol filters (price, volume, volatility)

Applied in `filter_stock()` and in stock search. Symbols outside these bounds are excluded.

| Param | Env var | Default | Description |
|-------|---------|---------|-------------|
| **Min stock price** | `MIN_STOCK_PRICE` | `5.0` | Minimum price (avoid penny stocks). |
| **Max stock price** | `MAX_STOCK_PRICE` | `1000.0` | Maximum price. |
| **Min daily volume** | `MIN_DAILY_VOLUME` | `500000` | Minimum daily volume (shares). |
| **Max stock volatility** | `MAX_STOCK_VOLATILITY` | `0.15` | Max volatility (e.g. 0.15 = 15%). Rejects high‑volatility names. |

**Additional logic in `filter_stock()` (no separate env):**

- **Trend gradient** — reject strong downtrends (gradient &lt; −2% per period).
- **Volatility pattern** — reject “unstable” or rapidly increasing volatility even if below `MAX_STOCK_VOLATILITY`.

**Code:**  
`main.py` 366–369, 3121–3196 (`filter_stock`), 3395–3410 (search pre‑filter).  
`stock_screener.py` 74–78.

---

## 3. Optional filters (sentiment, ML)

### Sentiment filter

| Param | Env var | Default | Description |
|-------|---------|---------|-------------|
| **Enable sentiment filter** | `ENABLE_SENTIMENT_FILTER` | `false` | If `true`, skip symbols that fail `check_sentiment_filter()` (news/sentiment). |

When enabled, the bot calls `check_sentiment_filter(symbol)` before opening. If it returns “don’t trade,” the symbol is skipped. Requires news/sentiment config (e.g. `NEWS_API_KEY`, `FINNHUB_API_KEY`) for full effect.

**Code:**  
`main.py` 564, 2699–2712 (`check_sentiment_filter`), 3649–3659 (simulation path), 6964–6968 (startup warning).

### ML signal filter

| Param | Env var | Default | Description |
|-------|---------|---------|-------------|
| **Enable ML signal filter** | `ENABLE_ML_SIGNAL_FILTER` | `true` | Use ML to filter BUY/SELL signals. |
| **Min confidence** | `ML_SIGNAL_FILTER_MIN_CONFIDENCE` | `0.6` | Min model confidence to allow trade. |
| **Min win probability** | `ML_SIGNAL_FILTER_MIN_WIN_PROB` | `0.55` | Min win probability to allow trade. |
| **Model type** | `ML_SIGNAL_FILTER_MODEL_TYPE` | `random_forest` | `random_forest` or `gradient_boosting`. |
| **Model path** | `ML_SIGNAL_FILTER_MODEL_PATH` | `ml_signal_filter_model.pkl` | Path to trained model file. |

When enabled and the model is trained, the bot runs `ml_signal_filter.should_filter_signal(...)` on BUY/SELL signals. If `should_filter` is true, the signal is turned into `HOLD` (trade skipped). Also used in `collect_trade_reasoning()` for manual‑approval “would execute” and ML reason.

**Code:**  
`main.py` 567–570, 1410–1435 (init), 6022–6071 (signal path), 2249–2257 (reasoning), 6052–6063.

---

## 4. Other “what”‑related limits

| Param | Env var | In Settings? | Description |
|-------|---------|--------------|-------------|
| **Max open positions** | `BOT_MAX_OPEN_POSITIONS` | Yes (Trading) | Max concurrent positions. Limits how many symbols you can hold, not which symbols are allowed. |

---

## 5. Summary table

| Purpose | Env vars | Where used |
|--------|----------|------------|
| **Symbol source** | `SCAN_SYMBOLS_FILE`, `DYNAMIC_SCAN_API_URL`, `ENABLE_STOCK_SCREENER`, `MAX_STOCKS_TO_SCAN`, `MAX_DISCOVERED_STOCKS`, `TOP_STOCKS_TO_TRADE` | `load_scan_symbols`, `search_tradeable_stocks`, screener, startup |
| **Screener ranking** | `SCORE_WEIGHT_MOMENTUM`, `SCORE_WEIGHT_VOLUME`, `SCORE_WEIGHT_VOLATILITY`, `SCORE_WEIGHT_LIQUIDITY`, `SCORE_WEIGHT_SENTIMENT` | `stock_screener` scoring |
| **Price/volume/volatility** | `MIN_STOCK_PRICE`, `MAX_STOCK_PRICE`, `MIN_DAILY_VOLUME`, `MAX_STOCK_VOLATILITY` | `filter_stock`, search, screener |
| **Sentiment** | `ENABLE_SENTIMENT_FILTER` | `check_sentiment_filter`, simulation execute path |
| **ML signal filter** | `ENABLE_ML_SIGNAL_FILTER`, `ML_SIGNAL_FILTER_MIN_CONFIDENCE`, `ML_SIGNAL_FILTER_MIN_WIN_PROB`, `ML_SIGNAL_FILTER_MODEL_TYPE`, `ML_SIGNAL_FILTER_MODEL_PATH` | ML filter init, signal path, `collect_trade_reasoning` |
| **Position limit** | `BOT_MAX_OPEN_POSITIONS` | `can_open_new_position`, Settings |

---

## 6. Where these are controlled

- **All “what to trade” params above are `.env` only.** The Settings UI (Trading, Risk, Advanced, etc.) does **not** expose:
  - Symbol source (screener vs file, scan limits, etc.)
  - Price/volume/volatility filters
  - Sentiment or ML filter toggles/thresholds

- To change what the bot trades, edit `.env` (or set env vars) and **restart the process** so the bot reloads them.

- `BOT_MAX_OPEN_POSITIONS` is the only “what”‑related limit in Settings; it caps how many symbols you hold, not which symbols are eligible.

---

## 7. Quick reference

- **Symbol list:** screener (default) vs `scan_symbols.txt` vs dynamic API → `ENABLE_STOCK_SCREENER`, `SCAN_SYMBOLS_FILE`, `DYNAMIC_SCAN_API_URL`.
- **Size of universe:** `MAX_STOCKS_TO_SCAN`, `MAX_DISCOVERED_STOCKS`, `TOP_STOCKS_TO_TRADE`.
- **Eligibility filters:** `MIN_STOCK_PRICE`, `MAX_STOCK_PRICE`, `MIN_DAILY_VOLUME`, `MAX_STOCK_VOLATILITY` (and internal trend/volatility rules in `filter_stock`).
- **Extra filters:** `ENABLE_SENTIMENT_FILTER`, `ENABLE_ML_SIGNAL_FILTER` + ML params.

---

*See `main.py`, `stock_screener.py`, and `docs/TRADING_SETTINGS_AND_CONTROLS.md` for how these interact with execution and risk settings.*
