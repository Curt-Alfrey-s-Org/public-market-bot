#!/usr/bin/env python3
"""
Load Test Probe

Applies concurrent HTTP load to key API endpoints and measures latency distribution
(p50/p90/p99), success/error rates, and request throughput. Helps distinguish network/server
pressure effects from upstream data staleness.

Outputs JSON to logs/load_test_probe.json and prints a concise summary.

Usage:
  python scripts/load_test_probe.py --alias operator --concurrency 8 --duration 60
  python scripts/load_test_probe.py --target 127.0.0.1:8000 --concurrency 8 --duration 60

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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_bot_auth import MISSING_TOKEN_HELP, auth_headers, resolve_admin_token  # noqa: E402

WORKSPACE_ROOT = Path(__file__).parent.parent
OUT_PATH = WORKSPACE_ROOT / "logs" / "load_test_probe.json"
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
            # Array format
            mapping = {t.get("name"): t.get("url") for t in data.get("targets", [])}
            # Dict format
            if not mapping:
                mapping = {k: (v.get("url") or v.get("api_url")) for k, v in data.items() if isinstance(v, dict)}
            if alias_or_url in mapping and mapping[alias_or_url]:
                base = mapping[alias_or_url]
    except Exception:
        pass
    if not base.startswith("http"):
        base = f"http://{base}"
    return base.rstrip('/')


def fetch(url: str, timeout: int = 5, headers: Optional[Dict[str, str]] = None) -> Tuple[bool, float, int]:
    start = time.perf_counter()
    try:
        r = requests.get(url, timeout=timeout, headers=headers)
        ok = r.status_code == 200
        return ok, time.perf_counter() - start, r.status_code
    except Exception:
        return False, timeout, 0


def percentile(sorted_values: List[float], pct: float) -> float:
    if not sorted_values:
        return float('inf')
    idx = int(max(0, min(len(sorted_values) - 1, round((pct / 100.0) * (len(sorted_values) - 1)))))
    return sorted_values[idx]


def run_load(
    base_url: str, concurrency: int, duration: int, headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    end_time = time.time() + duration
    metrics: Dict[str, Any] = {name: {"latencies": [], "success": 0, "errors": 0, "statuses": {}} for name, _ in ENDPOINTS}
    total_requests = 0

    with ThreadPoolExecutor(max_workers=concurrency) as exe:
        futures = []
        while time.time() < end_time:
            for name, path in ENDPOINTS:
                url = f"{base_url}{path}"
                futures.append(exe.submit(fetch, url, 5, headers))
            # Drain futures quickly to avoid memory growth
            for f in as_completed(futures):
                ok, latency, status = f.result()
                total_requests += 1
                m = metrics[name] if (name := ENDPOINTS[(total_requests - 1) % len(ENDPOINTS)][0]) else None
                if m is not None:
                    m["latencies"].append(latency)
                    if ok:
                        m["success"] += 1
                    else:
                        m["errors"] += 1
                    m["statuses"][str(status)] = m["statuses"].get(str(status), 0) + 1
            futures.clear()
            time.sleep(0.05)

    # Summarize
    summary: Dict[str, Any] = {}
    for name, _ in ENDPOINTS:
        data = metrics[name]
        lats = sorted(data["latencies"])
        summary[name] = {
            "requests": len(lats),
            "success": data["success"],
            "errors": data["errors"],
            "status_counts": data["statuses"],
            "p50_s": round(percentile(lats, 50), 4) if lats else None,
            "p90_s": round(percentile(lats, 90), 4) if lats else None,
            "p99_s": round(percentile(lats, 99), 4) if lats else None,
            "min_s": round(lats[0], 4) if lats else None,
            "max_s": round(lats[-1], 4) if lats else None,
        }
    summary["total_requests"] = total_requests
    return summary


def main():
    ap = argparse.ArgumentParser(description="Load Test Probe")
    ap.add_argument("--alias", help="Alias name from config/monitor_targets.json")
    ap.add_argument("--target", help="Raw URL host:port or http URL", default="http://127.0.0.1:8000")
    ap.add_argument("--concurrency", type=int, default=8, help="Concurrent workers")
    ap.add_argument("--duration", type=int, default=60, help="Duration seconds")
    args = ap.parse_args()

    base_url = resolve_base_url(args.alias or args.target)
    token = resolve_admin_token(base_url)
    if not token:
        print(MISSING_TOKEN_HELP, file=sys.stderr)
        sys.exit(2)
    headers = auth_headers(token)
    print(f"Load testing {base_url} with concurrency={args.concurrency} for {args.duration}s…")
    summary = run_load(base_url, args.concurrency, args.duration, headers=headers)

    payload = {
        "target": base_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "concurrency": args.concurrency,
        "duration_seconds": args.duration,
        "summary": summary,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Print concise summary
    for name, stats in summary.items():
        if name == "total_requests":
            continue
        print(f"- {name}: p50={stats['p50_s']}s p90={stats['p90_s']}s p99={stats['p99_s']}s errors={stats['errors']} requests={stats['requests']}")
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
