# Stock Screener Test – Capturing Results for Analysis

## What went wrong with the last capture

The `screener_results.txt` you pulled was **almost entirely Pandas4Warning** lines from yfinance. There were **no screener logs** (e.g. "Screening up to...", "SCREENING TIMING BREAKDOWN", "✓ SYMBOL", "Screening complete").

**Why:** The screener logs via `logger.info()`. When you run:

```bash
python3 -c "from stock_screener import screen_for_trades; screen_for_trades(max_stocks=10)"
```

no logging is configured, so those `INFO` messages never appear. Only yfinance warnings (stderr) were captured. Cursor therefore **cannot** analyze timing or pass/fail from that file.

## How to capture usable output

Use **`run_screener_test.py`**. It configures logging **before** importing the screener, suppresses Pandas4Warning, runs `screen_for_trades`, and prints the returned symbols. All screener logs (including the timing breakdown) go to stdout.

**On Linux (after pull):**

```bash
cd /path/to/market-bot
source venv/bin/activate
python3 run_screener_test.py 2>&1 | tee screener_results.txt
```

**Optional:** use a smaller run for a quicker test:

```bash
SCREENER_TEST_MAX_STOCKS=5 python3 run_screener_test.py 2>&1 | tee screener_results.txt
```

Then commit/push `screener_results.txt`, pull on Windows, and tell Cursor **"screener results are in screener_results.txt"**. The file will contain:

- "Screening up to X stocks from universe of Y..."
- Per-symbol pass/fail (✓ / ✗)
- **SCREENING TIMING BREAKDOWN** (total time, fetch/filter/scoring, avg per call, % of total)
- "Screening complete: M/N stocks passed"
- "Stocks returned: [...]"

Cursor can then analyze **where** the 30+ seconds is spent and suggest concrete optimizations.

## Quick reference

| Step | Command |
|------|--------|
| Run screener test | `python3 run_screener_test.py 2>&1 \| tee screener_results.txt` |
| Shorter test | `SCREENER_TEST_MAX_STOCKS=5 python3 run_screener_test.py 2>&1 \| tee screener_results.txt` |
| Push for analysis | `git add screener_results.txt && git commit -m "screener test results" && git push` |
| **Capture + push (Linux script)** | `bash scripts/run_linux_commands_3.sh` → writes **`debug_logs/run_3_results.txt`** and **`debug_logs/run_3_env_info.txt`**, then `git add debug_logs/` + commit + push. Pull on Windows and open those files for Cursor to analyze. Numbered scripts (_2, _3, …) avoid overwriting. |

---

## Example analysis (2026-01-25 run)

Below is a condensed analysis of a typical `screener_results.txt` from `run_screener_test.py` (max_stocks=10).

### Config

- **Universe:** 158 stocks (from cache).
- **Scan pool:** Up to 50 stocks (capped from universe).
- **Returned:** Up to 10 that fit .env (price $5–$200, vol ≥ 300k).
- **Criteria:** Price $5–$200, min vol 300k, max volatility 20%.

### Pass/fail

- **Fetched:** 50 symbols.
- **Passed filters:** 10.
- **Filtered out:** 21 by basic (price/vol/volatility), 0 by sentiment, 0 by ML.
- **Stocks returned:** SLB, DVN, MS, XOM, QCOM, PM, CHTR, EL, MPC, CVX (top 10 by score).

### Timing breakdown (total **33.15 s**)

| Phase | Total | Calls | Avg/call | % of total |
|-------|-------|-------|----------|------------|
| **Fetch stock info** | **33.15 s** | 50 | **0.66 s** | **100%** |
| Basic filtering | 0.00 s | 49 | 0.00 s | 0% |
| Scoring/ranking | 0.00 s | 28 | 0.00 s | 0% |

### Bottleneck

**100% of runtime is in `fetch_stock_info`** (yfinance API calls). Filter and scoring are negligible. Per-stock fetch averages ~0.66 s; some symbols (e.g. MS, NFLX) take &gt;1–2 s.

### Recommendations

1. **Parallelize fetches** – Use `async_data_fetcher` or `concurrent.futures` to fetch multiple symbols at once instead of one-by-one. Biggest leverage.
2. **Batch yfinance** – Where possible, use `yf.download(symbols, ...)` to fetch many tickers in a single request.
3. **Early exit** – Stop scanning once enough symbols pass (e.g. 10); avoid fetching the full scan pool if not needed.
4. **Reduce scan pool** – Keep `MAX_STOCKS_TO_SCAN` / scan cap close to `TOP_STOCKS_TO_TRADE` so fewer API calls.
5. **Suppress Pandas4Warning in runner** – Ensure `run_screener_test.py` uses `module="yfinance.*"` in its warning filter so output stays readable (see above).

### Screener optimization (implemented)

**Batch mode (Phase 1 + Phase 2):** Goal ~3s to get ~200 filtered (TOS-like), then sort. **No early cutoff** — we fetch the full scan pool in chunks via `yf.download`, filter all, then score and sort. See:

- `SCREENER_USE_BATCH_FETCH` (default true), `SCREENER_BATCH_SIZE`, `SCREENER_TARGET_FILTERED`, `MAX_STOCKS_TO_SCAN` (default 600) in `.env.example`.
- `stock_screener.py`: `_fetch_batch_stock_info`, batch path in `screen_stocks`. Phase 1 = fetch+filter; Phase 2 = sort. Advanced filters (sentiment/ML) are skipped in batch mode; disable `SCREENER_USE_BATCH_FETCH` for full filtering.
