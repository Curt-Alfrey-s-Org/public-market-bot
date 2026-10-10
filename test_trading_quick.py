#!/usr/bin/env python3
"""Quick test: Verify bot trades with ML filter OFF."""

import requests
import json
import time

base_url = "http://192.0.2.21:8004"

# Settings with ML filter OFF to allow trading
settings = {
    "ENABLE_ML_SIGNAL_FILTER": "false",
    "BOT_RISK_THRESHOLD": 0.02,
    "BOT_POSITION_SIZE": 0.01,
    "BOT_STOP_LOSS_PERCENT": 0.03,
    "BOT_TAKE_PROFIT_PERCENT": 0.06,
    "STRATEGY_MIN_BARS": 50,
    "PAPER_TRADING_MODE": "true",
    "SCHWAB_SANDBOX_MODE": "false",
    "DRY_RUN_MODE": "false",
    "BACKTEST_MODE": "false"
}

# Apply settings
print("[1/3] Applying settings (ML OFF)...")
r = requests.put(f"{base_url}/api/settings", json={"settings": settings}, timeout=10)
print(f"  Settings applied: {r.status_code}")

# Let bot run for 3 minutes
duration_s = 180
print(f"[2/3] Running bot for {duration_s}s...")
time.sleep(duration_s)

# Get trades
print("[3/3] Fetching trades...")
r = requests.get(f"{base_url}/api/trades?limit=100", timeout=10)
trades = r.json().get('trades', [])
closed_trades = [t for t in trades if t.get('status') == 'closed']

print(f"\nResults:")
print(f"  Total trades: {len(trades)}")
print(f"  Closed trades: {len(closed_trades)}")
if closed_trades:
    print(f"  First closed trade: {json.dumps(closed_trades[0], indent=2)[:300]}")
else:
    print(f"  ⚠ No closed trades found - bot may not be trading")
    
print(f"\nConclusion: {'✅ Bot is trading' if len(closed_trades) > 0 else '❌ Bot not trading - check logs'}")
