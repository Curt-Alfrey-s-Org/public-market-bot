#!/usr/bin/env python3
"""
Bootstrap test runner: set pandas/yfinance warning filter before any other imports,
then run unittest discover. Use for cleaner output (no Pandas4Warning / Timestamp.utcnow).

  python3 run_unittest.py

Runs: discover -s . -p "test_*.py" -v
"""

import warnings

# Must run before any test or app code (including main, data_fetcher, yfinance)
warnings.filterwarnings("ignore", message=r".*Timestamp\.utcnow.*")

import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover(".", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    ok = runner.run(suite).wasSuccessful()
    raise SystemExit(0 if ok else 1)
