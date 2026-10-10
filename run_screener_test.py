#!/usr/bin/env python3
"""
Run stock screener test and emit logs + timing to stdout for capture/analysis.

  python3 run_screener_test.py
  python3 run_screener_test.py 2>&1 | tee screener_results.txt

Configure logging *before* importing stock_screener so INFO (including timing
breakdown) is visible. Suppresses Pandas4Warning so output stays readable.
"""

from __future__ import annotations

import logging
import os
import sys
import warnings

# Suppress pandas/yfinance Timestamp.utcnow warnings before any yfinance use
warnings.filterwarnings("ignore", message=r".*Timestamp\.utcnow.*", module="yfinance.*")

# Configure logging so screener INFO (including timing) goes to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True,
)

# Ensure screener timing is enabled for this run
os.environ.setdefault("ENABLE_SCREENER_TIMING", "true")

from stock_screener import screen_for_trades

if __name__ == "__main__":
    max_stocks = int(os.environ.get("SCREENER_TEST_MAX_STOCKS", "10"))
    print("=" * 60)
    print(f"Stock screener test (max_stocks={max_stocks})")
    print("=" * 60)
    symbols = screen_for_trades(max_stocks=max_stocks)
    print("=" * 60)
    print(f"Stocks returned: {symbols}")
    print("=" * 60)
