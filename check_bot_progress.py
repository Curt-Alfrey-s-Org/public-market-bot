#!/usr/bin/env python3
import subprocess
import time
import requests
import json

print("Waiting another 60 seconds for more cycles...")
time.sleep(60)

print("\nChecking bot logs for cycle summary...")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'tail -80 /tmp/bot_output.log'],
    capture_output=True, text=True, timeout=10
)

print("LAST 80 LINES OF BOT LOG:")
print("=" * 80)
print(result.stdout)
print("=" * 80)

print("\nChecking for 'Cycle Summary'...")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'grep -i "cycle summary\\|end of trading cycle" /tmp/bot_output.log | tail -5'],
    capture_output=True, text=True, timeout=10
)
if result.stdout.strip():
    print("✓ Found cycle summaries:")
    print(result.stdout)
else:
    print("✗ No cycle summaries yet")

print("\nChecking trades...")
try:
    r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
    data = r.json()
    total = data.get('total', 0)
    print(f"API Trades: {total}")
    if total > 0:
        trades = data.get('trades', [])[:5]
        for t in trades:
            print(f"  - {t.get('symbol')}: {t.get('action')} @ ${t.get('price'):.2f}")
except:
    print("Could not reach API")

print("\nChecking for BUY/SELL actions in logs...")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'grep "Processing trade for\\|Execute trade" /tmp/bot_output.log | wc -l'],
    capture_output=True, text=True, timeout=10
)
print(f"Trade execution lines: {result.stdout.strip()}")
