#!/usr/bin/env python3
"""Diagnostic: Check bot state, settings, and cycle progress."""
import requests
import time

base_url = "http://192.0.2.21:8004"

print("=== BOT DIAGNOSTICS ===\n")

# 1. Bot status
r = requests.get(f"{base_url}/api/bot/status", timeout=10)
status = r.json()
print(f"Bot Running: {status.get('running')}")
print(f"Mode: {status.get('mode')}")
print(f"Last Update: {status.get('last_update')}")
print()

# 2. Settings
r = requests.get(f"{base_url}/api/settings", timeout=10)
settings = r.json().get('settings', {})
print(f"ML Filter Enabled: {settings.get('ENABLE_ML_SIGNAL_FILTER')}")
print(f"Trading Frequency: {settings.get('TRADING_FREQUENCY')}")
print(f"Strategy Min Bars: {settings.get('STRATEGY_MIN_BARS')}")
print()

# 3. Trades
r = requests.get(f"{base_url}/api/trades?limit=20", timeout=10)
trades = r.json().get('trades', [])
closed = [t for t in trades if t.get('status') == 'closed']
print(f"Total Trades: {len(trades)}")
print(f"Closed Trades: {len(closed)}")
if closed:
    print(f"Sample closed trade: {closed[0]['symbol']} @ {closed[0].get('entry_price', 'N/A')}")
print()

# 4. Reports (cycles, decisions)
r = requests.get(f"{base_url}/api/reports/cycles?limit=3", timeout=10)
cycles = r.json().get('cycles', [])
print(f"Total Cycles: {len(cycles)}")
if cycles:
    print(f"Latest cycle: {cycles[0]}")
