#!/usr/bin/env python3
import subprocess

print("Clearing trade history to test fresh bot...")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'rm -f ~/market-bot/market-pie5-bot/logs/trading_logs.db && echo "✓ Cleared trades database"'],
    capture_output=True, text=True, timeout=10
)
print(result.stdout)

print("\nRestarting bot...")
subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'pkill -9 -f "python main.py"'],
    capture_output=True, timeout=10
)

import time
time.sleep(2)

subprocess.Popen(
    ['ssh', 'operator@192.0.2.21',
     'cd ~/market-bot/market-pie5-bot && nohup ./venv/bin/python main.py > /tmp/bot_output.log 2>&1 &'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

print("✓ Bot restarting (waiting 60 seconds for first cycle with fresh positions)...")
time.sleep(60)

print("\nChecking for trades now...")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'tail -100 /tmp/bot_output.log | grep -E "Processing trade|execute_trade|Cycle Summary"'],
    capture_output=True, text=True, timeout=10
)
if result.stdout.strip():
    print("✓ Found trade execution logs:")
    print(result.stdout)
else:
    print("Still no trades - checking logs...")
    result = subprocess.run(
        ['ssh', 'operator@192.0.2.21', 'tail -50 /tmp/bot_output.log'],
        capture_output=True, text=True, timeout=10
    )
    print(result.stdout)
