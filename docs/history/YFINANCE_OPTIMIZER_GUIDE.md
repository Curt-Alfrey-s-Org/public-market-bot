# Yfinance Mode Optimizer

This guide explains how to tune yfinance-mode settings using the optimizer harness that runs short, repeatable samples and scores each configuration by Win Rate and Profit Factor (PF).

## Summary
- Script: `scripts/yfinance_mode_optimizer.py`
- Presets: `config/yfinance_optimizer_presets.json`
- Output: `logs/yfinance_optimizer_results.json`

The optimizer applies settings via the API (`/api/settings`), runs a timed sample, gathers `/api/trades` during the window, and computes:
- Win%: closed winning trades / closed trades
- PF: sum(positive PnL) / abs(sum(negative PnL))

## Quick Start

Local (bot/API running on 127.0.0.1:8000):

```bash
# 3 combos x 180s each
python scripts/yfinance_mode_optimizer.py --target 127.0.0.1:8000 --grid-limit 3
```

Remote (alias `operator` defined in `config/monitor_targets.json`):

```bash
# 6 combos x 300s each, require at least 6 closed trades per run
python scripts/yfinance_mode_optimizer.py --alias operator --duration 300 --min-trades 6 --grid-limit 6
```

## Tuning Dimensions
The default presets explore three axes:
- Risk & Sizing: `BOT_RISK_THRESHOLD`, `BOT_POSITION_SIZE`, `BOT_STOP_LOSS_PERCENT`, `BOT_TAKE_PROFIT_PERCENT`
- ML Filter: `ENABLE_ML_SIGNAL_FILTER`, `ML_SIGNAL_FILTER_MIN_CONFIDENCE`, `ML_SIGNAL_FILTER_MIN_WIN_PROB`
- Minimum Bars: `STRATEGY_MIN_BARS`

You can edit `config/yfinance_optimizer_presets.json` to adjust grids, base overrides, duration, and minimum trade requirements.

## Selecting the Best
After a run, the script prints the best configuration by PF among samples that meet:
- `closed_trades >= min_trades_required`
- Win% in [35%, 75%] (to avoid degenerate or overly conservative results)

The full payload is saved to `logs/yfinance_optimizer_results.json` for deeper analysis.

## Notes & Tips
- Ensure the bot is running in yfinance/simulation mode (`PAPER_TRADING_MODE=true`, `SCHWAB_SANDBOX_MODE=false`).
- The script filters trades by timestamp window; historical trades are not included in metrics.
- If PF is `inf`, it indicates no losses observed in the window; prefer configurations with sufficient losing samples for realistic PF.
- For reproducibility, keep `TRADING_FREQUENCY` and throttling consistent across runs.

## Next Steps
- Expand grids for weekend/overnight runs (longer durations, more combinations).
- Persist top N configs and re-validate across multiple sessions.
- Add optional exits sizing threshold to reduce sub-minimum SELL allocations (if needed).
