#!/usr/bin/env bash
# Run all yfinance-related tests. No API required for unit tests.
# Uses project venv if present (same as start_api.sh).
set -e
cd "$(dirname "$0")"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
python3 tests/runner.py --yfinance-only "$@"
