#!/usr/bin/env python3
"""
Latency & Freshness Probe

Measures HTTP response latency for key endpoints and estimates data freshness
(e.g., how recent decisions updates are) to identify lag sources (network vs data fetch).

Outputs JSON to logs/latency_probe.json and prints a concise summary.

Usage:
  python scripts/latency_probe.py --alias operator --samples 5
  python scripts/latency_probe.py --target 127.0.0.1:8000 --samples 5

Auth: every /api/* endpoint except health needs a JWT. Set MARKET_BOT_ADMIN_TOKEN,
or MARKET_BOT_ADMIN_USERNAME / MARKET_BOT_ADMIN_PASSWORD (one login at startup).
The token is only sent as an Authorization header and is never printed
(see scripts/market_bot_auth.py).
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_bot_auth import MISSING_TOKEN_HELP, auth_headers, resolve_admin_token  # noqa: E402

WORKSPACE_ROOT = Path(__file__).parent.parent
OUT_PATH = WORKSPACE_ROOT / "logs" / "latency_probe.json"
TARGETS_CONFIG = WORKSPACE_ROOT / "config" / "monitor_targets.json"

ENDPOINTS = [
    ("health", "/api/health"),
    ("bot_status", "/api/bot/status"),
    ("stats", "/api/stats"),
    ("trades", "/api/trades?limit=50"),
    ("reports_decisions", "/api/reports/decisions"),
    ("messages", "/api/messages"),
]


def resolve_base_url(alias_or_url: str) -> str:
    base = alias_or_url
    try:
        if not alias_or_url.startswith("http") and TARGETS_CONFIG.exists():
            data = json.loads(TARGETS_CONFIG.read_text(encoding="utf-8"))
            # Array format: {"targets": [{"name": "operator", "url": "http://..."}, ...]}
            mapping = {t.get("name"): t.get("url") for t in data.get("targets", [])}
            # Dict format: {"operator": {"api_url": "http://..."}}
            if not mapping:
                mapping = {k: (v.get("url") or v.get("api_url")) for k, v in data.items() if isinstance(v, dict)}
            if alias_or_url in mapping and mapping[alias_or_url]:
                base = mapping[alias_or_url]
    except Exception:
        pass
    if not base.startswith("http"):
        base = f"http://{base}"
    return base.rstrip('/')


def measure_latency(
    url: str, samples: int = 5, timeout: int = 5, headers: Optional[Dict[str, str]] = None
) -> Tuple[float, float, float]:
    times: List[float] = []
    for _ in range(samples):
        start = time.perf_counter()
        try:
            r = requests.get(url, timeout=timeout, headers=headers)
            r.raise_for_status()
        except Exception:
            # Record as timeout/failed with large sentinel
            times.append(timeout)
            continue
        times.append(time.perf_counter() - start)
        time.sleep(0.2)
    if not times:
        return (float("inf"), float("inf"), float("inf"))
    return (min(times), sum(times) / len(times), max(times))


def iso_to_epoch(s: str) -> float:
    try:
        dt = datetime.fromisoformat(s)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


def get_reports_decisions(base_url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    try:
        r = requests.get(f"{base_url}/api/reports/decisions", timeout=5, headers=headers)
        if r.status_code == 200:
            return r.json() or {}
    except Exception:
        pass
    return {}


def summarize_freshness(decisions_payload: Dict[str, Any]) -> Dict[str, Any]:
    now = time.time()
    rows = decisions_payload.get("decisions", []) or []
    ages = []
    for row in rows:
        ts = row.get("updated_at")
        if ts:
            ages.append(max(0.0, now - iso_to_epoch(ts)))
    cycle_number = decisions_payload.get("cycle_number", 0)
    total_candidates = decisions_payload.get("total_candidates", 0)
    evaluated_count = decisions_payload.get("evaluated_count", 0)
    cycle_in_progress_no_data = decisions_payload.get("cycle_in_progress_no_data", False)
    timings = decisions_payload.get("last_cycle_timings")
    return {
        "rows": len(rows),
        "age_min_s": min(ages) if ages else None,
        "age_avg_s": (sum(ages) / len(ages)) if ages else None,
        "age_max_s": max(ages) if ages else None,
        "cycle_number": cycle_number,
        "total_candidates": total_candidates,
        "evaluated_count": evaluated_count,
        "cycle_in_progress_no_data": cycle_in_progress_no_data,
        "last_cycle_timings": timings,
    }


def main():
    ap = argparse.ArgumentParser(description="Latency & Freshness Probe")
    ap.add_argument("--alias", help="Alias name from config/monitor_targets.json")
    ap.add_argument("--target", help="Raw URL host:port or http URL", default="http://127.0.0.1:8000")
    ap.add_argument("--samples", type=int, default=5, help="Number of latency samples per endpoint")
    args = ap.parse_args()

    base_url = resolve_base_url(args.alias or args.target)
    token = resolve_admin_token(base_url)
    if not token:
        print(MISSING_TOKEN_HELP, file=sys.stderr)
        sys.exit(2)
    headers = auth_headers(token)
    results: Dict[str, Any] = {
        "target": base_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "samples_per_endpoint": args.samples,
        "endpoints": {},
    }

    print(f"Probing {base_url} with {args.samples} samples per endpoint…")
    for name, path in ENDPOINTS:
        url = f"{base_url}{path}"
        mn, avg, mx = measure_latency(url, samples=args.samples, headers=headers)
        results["endpoints"][name] = {
            "url": url,
            "latency_min_s": round(mn, 4),
            "latency_avg_s": round(avg, 4),
            "latency_max_s": round(mx, 4),
        }
        print(f"- {name}: avg={round(avg, 4)}s (min={round(mn, 4)}s, max={round(mx, 4)}s)")

    # Freshness from decisions
    dec_payload = get_reports_decisions(base_url, headers=headers)
    freshness = summarize_freshness(dec_payload)
    results["decisions_freshness"] = freshness

    # Save
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\nFreshness summary:")
    print(json.dumps(freshness, indent=2))
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
