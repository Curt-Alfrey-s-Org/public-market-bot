#!/usr/bin/env python3
"""
Benchmark yfinance throughput using DataFetcher + RateLimiter.
- Disables DataFetcher cache to force real calls
- Loops over a set of symbols for a fixed duration
- Reports calls attempted, successes, rate-limit hits, and avg latency
"""
import os
import time
import logging
from datetime import datetime, timedelta

# Ensure workspace path is importable
import sys
sys.path.append(os.getcwd())

from data_fetcher import DataFetcher, YFINANCE_AVAILABLE  # type: ignore

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger("bench")

SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "NVDA", "TSLA", "AMD", "NFLX", "INTC"
]

DURATION_SEC = int(os.getenv("BENCH_DURATION_SEC", "30"))
PERIOD = os.getenv("BENCH_PERIOD", "1d")
INTERVAL = os.getenv("BENCH_INTERVAL", "1m")


def main():
    if not YFINANCE_AVAILABLE:
        logger.error("yfinance not available in environment. Install it and retry.")
        return 1

    fetcher = DataFetcher()
    # Disable DataFetcher cache to force real API calls
    fetcher.cache_duration = 0

    start = time.time()
    end = start + DURATION_SEC
    attempted = 0
    successes = 0
    rate_limited = 0
    errors = 0
    latencies = []

    logger.info(
        f"Starting yfinance throughput benchmark: duration={DURATION_SEC}s, period={PERIOD}, interval={INTERVAL}"
    )

    # Report configured rate-limiter settings
    yfl = fetcher.yfinance_limiter
    logger.info(
        f"Limiter: max_calls={yfl.max_calls}, window={getattr(yfl, 'time_window', '60')}s"
    )

    while time.time() < end:
        for sym in SYMBOLS:
            if time.time() >= end:
                break
            attempted += 1
            t0 = time.time()
            try:
                data = fetcher.fetch_historical_data_yfinance(sym, period=PERIOD, interval=INTERVAL)
                t1 = time.time()
                latencies.append(t1 - t0)
                if data is not None:
                    successes += 1
                else:
                    # Distinguish rate-limit skip vs. other None
                    # When rate-limited, DataFetcher logs warning and returns None before calling.
                    # Heuristically check remaining calls; if 0, likely rate-limit.
                    remaining = yfl.get_remaining_calls()
                    if remaining == 0 and not yfl.can_make_call():
                        rate_limited += 1
                    else:
                        errors += 1
            except Exception as e:
                t1 = time.time()
                latencies.append(t1 - t0)
                logger.debug(f"Error fetching {sym}: {e}")
                errors += 1

    dur = time.time() - start
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    remaining = yfl.get_remaining_calls()
    wait_time = getattr(yfl, 'get_wait_time', lambda: 0.0)()

    logger.info("=== Benchmark Summary ===")
    logger.info(f"Duration: {dur:.2f}s | Attempts: {attempted} | Successes: {successes}")
    logger.info(f"Rate-limited skips: {rate_limited} | Errors: {errors}")
    logger.info(f"Avg latency per call: {avg_latency*1000:.1f} ms")
    logger.info(f"Limiter remaining calls in window: {remaining} | next call in ~{wait_time:.1f}s")

    # Simple guidance based on outcomes
    if rate_limited > 0 and successes > 0:
        logger.info("Guidance: Consider increasing YFINANCE_MAX_CALLS_PER_MINUTE or spreading requests.")
    elif errors > 0 and rate_limited == 0:
        logger.info("Guidance: Errors occurred without rate-limit; inspect network stability or intervals.")
    else:
        logger.info("Guidance: Settings look healthy at current throughput.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
