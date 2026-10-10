#!/usr/bin/env python3
"""
Yfinance Mode Optimizer

Runs a grid of setting combinations against a running API, time-boxes each sample,
collects trades within the window, and computes Win Rate and Profit Factor (PF).
Saves results to logs/yfinance_optimizer_results.json and prints a concise summary.

Usage:
  python scripts/yfinance_mode_optimizer.py --target 127.0.0.1:8000 --duration 180 --min-trades 6 --grid-limit 12
  python scripts/yfinance_mode_optimizer.py --alias operator --duration 300

Notes:
- Assumes the bot is already running in yfinance/simulation mode.
- Uses /api/settings (PUT) to apply configs; only whitelisted keys will persist.
- Computes PF: sum(positive pnls) / abs(sum(negative pnls)); Win% over closed trades.
- Filters trades by timestamps in the run window to avoid historical contamination.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# Auth: /api/* needs a JWT and PUT /api/settings needs an ADMIN JWT. Set
# MARKET_BOT_ADMIN_TOKEN, or MARKET_BOT_ADMIN_USERNAME/MARKET_BOT_ADMIN_PASSWORD
# (see scripts/market_bot_auth.py).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_bot_auth import MISSING_TOKEN_HELP, auth_headers, resolve_admin_token  # noqa: E402

_AUTH_TOKEN: Optional[str] = None

WORKSPACE_ROOT = Path(__file__).parent.parent
DEFAULT_PRESETS_PATH = WORKSPACE_ROOT / "config" / "yfinance_optimizer_presets.json"
RESULTS_PATH = WORKSPACE_ROOT / "logs" / "yfinance_optimizer_results.json"
TARGETS_CONFIG = WORKSPACE_ROOT / "config" / "monitor_targets.json"


def resolve_base_url(alias_or_url: str) -> str:
    """Resolve base URL from alias using config/monitor_targets.json or return raw URL.
    Supports both array and dict formats. Ensures scheme and strips trailing slashes.
    """
    base = alias_or_url
    try:
        if not alias_or_url.startswith("http") and TARGETS_CONFIG.exists():
            data = json.loads(TARGETS_CONFIG.read_text(encoding="utf-8"))
            # Format A: {"targets": [{"name": "operator", "url": "http://..."}, ...]}
            mapping = {t.get("name"): t.get("url") for t in data.get("targets", [])}
            # Format B: {"operator": {"api_url": "http://..."}, ...}
            if not mapping:
                mapping = {k: (v.get("url") or v.get("api_url")) for k, v in data.items() if isinstance(v, dict)}
            if alias_or_url in mapping and mapping[alias_or_url]:
                base = mapping[alias_or_url]
    except Exception:
        pass
    if not base.startswith("http"):
        base = f"http://{base}"
    return base.rstrip('/')


def put_settings(base_url: str, settings: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    url = f"{base_url}/api/settings"
    try:
        resp = requests.put(url, json={"settings": settings}, headers=auth_headers(_AUTH_TOKEN), timeout=10)
        if resp.status_code == 200:
            return True, resp.json()
        return False, {"error": f"HTTP {resp.status_code}", "text": resp.text[:200]}
    except Exception as e:
        return False, {"error": str(e)}


def get_trades(base_url: str, limit: int = 1000) -> List[Dict[str, Any]]:
    url = f"{base_url}/api/trades?limit={limit}"
    try:
        resp = requests.get(url, headers=auth_headers(_AUTH_TOKEN), timeout=10)
        if resp.status_code == 200:
            data = resp.json() or {}
            return data.get("trades", [])
        return []
    except Exception:
        return []


def to_epoch(dt_str: Optional[str]) -> Optional[float]:
    if not dt_str:
        return None
    try:
        # Expect ISO format from API
        dt = datetime.fromisoformat(dt_str)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def windowed_trades(trades: List[Dict[str, Any]], start_ts: float, end_ts: float) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for t in trades:
        entry_ts = None
        exit_ts = None
        # API returns `entry_timestamp` and `exit_timestamp` as ISO; convert to epoch
        try:
            entry_ts = to_epoch(t.get("entry_timestamp"))
        except Exception:
            entry_ts = None
        try:
            exit_ts = to_epoch(t.get("exit_timestamp"))
        except Exception:
            exit_ts = None
        # Include trades whose entry or exit occurred in window
        if entry_ts and start_ts <= entry_ts <= end_ts:
            out.append(t)
        elif exit_ts and start_ts <= exit_ts <= end_ts:
            out.append(t)
    return out


def compute_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    closed = [t for t in trades if (t.get("status") or "").lower() == "closed"]
    wins = 0
    losses = 0
    sum_pos = 0.0
    sum_neg = 0.0
    for t in closed:
        pnl = t.get("pnl")
        if pnl is None:
            # If no pnl, attempt rough inference from entry/exit
            try:
                entry = t.get("entry_price")
                exitp = t.get("exit_price")
                qty = float(t.get("quantity") or 0)
                if entry is not None and exitp is not None and qty > 0:
                    pnl = (exitp - entry) * qty
            except Exception:
                pnl = None
        if pnl is None:
            continue
        if pnl > 0:
            wins += 1
            sum_pos += float(pnl)
        elif pnl < 0:
            losses += 1
            sum_neg += float(pnl)
        else:
            # zero pnl, neither win nor loss
            pass
    total = len(closed)
    win_rate = (wins / total * 100.0) if total > 0 else 0.0
    pf = (sum_pos / abs(sum_neg)) if sum_neg < 0 else float('inf') if sum_pos > 0 else 0.0
    return {
        "closed_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate_percent": round(win_rate, 2),
        "profit_factor": round(pf, 3) if pf != float('inf') else float('inf'),
        "sum_positive_pnl": round(sum_pos, 2),
        "sum_negative_pnl": round(sum_neg, 2)
    }


def grid_combinations(presets: Dict[str, Any], limit: Optional[int]) -> List[Dict[str, Any]]:
    grids = presets.get("grids", {})
    groups = [grids.get("risk_and_sizing", []), grids.get("ml_filter", []), grids.get("min_bars", [])]
    combos = []
    for parts in product(*groups):
        merged = {}
        for p in parts:
            merged.update(p)
        # Base overrides applied after merged
        merged.update(presets.get("base_overrides", {}))
        combos.append(merged)
    if limit and limit > 0:
        combos = combos[:limit]
    return combos


def run_sample(base_url: str, settings: Dict[str, Any], duration_s: int) -> Dict[str, Any]:
    ok, _ = put_settings(base_url, settings)
    if not ok:
        return {"error": "settings_update_failed"}
    # Wait a short stabilization period so the bot picks up new settings
    time.sleep(3)
    start_ts = time.time()
    deadline = start_ts + duration_s
    # Poll trades a few times during the window to capture exits
    all_trades: List[Dict[str, Any]] = []
    while time.time() < deadline:
        trades = get_trades(base_url)
        if trades:
            all_trades = trades  # keep latest snapshot
        time.sleep(5)
    end_ts = time.time()
    windowed = windowed_trades(all_trades, start_ts, end_ts)
    metrics = compute_metrics(windowed)
    return {
        "settings": settings,
        "metrics": metrics,
        "window": {
            "start": datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat(),
            "end": datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat()
        },
        "trade_count_in_window": len(windowed)
    }


def main():
    parser = argparse.ArgumentParser(description="Yfinance Mode Optimizer")
    parser.add_argument("--target", help="Base URL like 127.0.0.1:8000 or http://...", default=os.getenv("API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--alias", help="Alias name from config/monitor_targets.json (e.g., operator)")
    parser.add_argument("--duration", type=int, help="Seconds per sample", default=None)
    parser.add_argument("--min-trades", type=int, help="Minimum closed trades required in window", default=None)
    parser.add_argument("--grid-limit", type=int, help="Limit combinations for quick runs", default=None)
    parser.add_argument("--presets", help="Path to presets JSON", default=str(DEFAULT_PRESETS_PATH))
    args = parser.parse_args()

    base_url = resolve_base_url(args.alias or args.target)
    global _AUTH_TOKEN
    _AUTH_TOKEN = resolve_admin_token(base_url)
    if not _AUTH_TOKEN:
        print(MISSING_TOKEN_HELP)
        sys.exit(2)
    try:
        presets = json.loads(Path(args.presets).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Failed to read presets: {e}")
        sys.exit(1)

    duration_s = args.duration or int(presets.get("duration_seconds", 180))
    min_trades = args.min_trades or int(presets.get("min_trades_required", 6))
    combos = grid_combinations(presets, args.grid_limit)
    results: List[Dict[str, Any]] = []

    print(f"Target: {base_url}; Samples: {len(combos)}; Duration each: {duration_s}s; Min trades: {min_trades}")
    for idx, settings in enumerate(combos, start=1):
        print(f"[{idx}/{len(combos)}] Running sample with settings: {json.dumps(settings)}")
        sample = run_sample(base_url, settings, duration_s)
        metrics = sample.get("metrics", {})
        closed = int(metrics.get("closed_trades", 0))
        # Skip if not enough trades
        if closed < min_trades:
            sample["skipped_reason"] = f"closed_trades({closed}) < min_trades({min_trades})"
        results.append(sample)
        # Short breather between samples
        time.sleep(2)

    # Pick best by PF among non-skipped and with sane win rate (e.g., 35–75%)
    candidates = []
    for r in results:
        m = r.get("metrics", {})
        wr = float(m.get("win_rate_percent") or 0.0)
        pf = m.get("profit_factor")
        closed = int(m.get("closed_trades", 0))
        if r.get("skipped_reason"):
            continue
        if closed >= min_trades and 35.0 <= wr <= 75.0 and pf not in (None, 0):
            candidates.append((pf, wr, r))
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = candidates[0][2] if candidates else None

    # Save results
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "target": base_url,
        "duration_seconds": duration_s,
        "min_trades_required": min_trades,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "best": best
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Print concise summary
    def fmt(m: Dict[str, Any]) -> str:
        return f"closed={m.get('closed_trades')} win%={m.get('win_rate_percent')} pf={m.get('profit_factor')}"

    print("\nOptimization complete.")
    if best:
        bm = best.get("metrics", {})
        print(f"Best config: {fmt(bm)}")
        print(json.dumps(best.get("settings", {}), indent=2))
    else:
        print("No suitable best config found (insufficient trades or metrics). See logs/yfinance_optimizer_results.json.")


if __name__ == "__main__":
    main()
