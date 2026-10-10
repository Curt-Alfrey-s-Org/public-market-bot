#!/usr/bin/env python3
"""
Deploy latest bug fixes to operator and test
"""
import subprocess
import time
import requests
import json

print("=" * 80)
print("DEPLOYING BUG FIXES TO operator")
print("=" * 80)
print()

# Step 1: Pull code
print("Step 1: Pulling latest code on operator...")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 
     'cd ~/market-bot/market-pie5-bot && git pull origin copilot/integrate-batch-pricing'],
    capture_output=True, text=True, timeout=15
)
print(result.stdout if result.stdout else result.stderr)

# Step 2: Kill old bot
print("\nStep 2: Killing old bot process...")
subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'pkill -9 -f "python main.py"'],
    capture_output=True, timeout=10
)
time.sleep(2)

# Step 3: Start new bot
print("\nStep 3: Starting new bot with fixes...")
print("Command: nohup ./venv/bin/python main.py > /tmp/bot_output.log 2>&1 &")
subprocess.Popen(
    ['ssh', 'operator@192.0.2.21',
     'cd ~/market-bot/market-pie5-bot && nohup ./venv/bin/python main.py > /tmp/bot_output.log 2>&1 &'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

print("✓ Bot starting...")
print()

# Step 4: Wait and check status
print("Step 4: Waiting 50 seconds for bot to initialize and run first trading cycle...")
for i in range(50, 0, -10):
    time.sleep(10)
    print(f"  ⏳ {i}s remaining...")

print()
print("=" * 80)
print("VERIFICATION CHECKS")
print("=" * 80)
print()

# Check 1: API Status
print("Check 1: API Status Endpoint")
try:
    r = requests.get('http://192.0.2.21:8004/api/bot/status', timeout=5)
    if r.status_code == 200:
        status = r.json()
        print(f"✓ API Response: {json.dumps(status, indent=2)}")
        if status.get('running'):
            print("  ✓✓ Bot is RUNNING (running: true)")
        else:
            print("  ✗ Bot not showing as running (running: false)")
    else:
        print(f"✗ API Error: {r.status_code}")
except Exception as e:
    print(f"✗ Could not reach API: {e}")

print()

# Check 2: Trades
print("Check 2: Trades Generated")
try:
    r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
    if r.status_code == 200:
        data = r.json()
        total = data.get('total', 0)
        print(f"✓ Trades endpoint returned: total={total}")
        if total > 0:
            print(f"  ✓✓ BOT IS TRADING! Generated {total} trades")
            trades = data.get('trades', [])[:3]
            for trade in trades:
                print(f"    - {trade.get('symbol', '?')}: {trade.get('action', '?')}")
        else:
            print(f"  ⏳ No trades yet (might still be initializing)")
    else:
        print(f"✗ API Error: {r.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

print()

# Check 3: Bot logs
print("Check 3: Bot Log Output")
print("-" * 80)
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'tail -60 /tmp/bot_output.log 2>/dev/null || echo "No output yet"'],
    capture_output=True, text=True, timeout=10
)
log_output = result.stdout
if log_output and "No output yet" not in log_output:
    lines = log_output.split('\n')
    # Show last 30 lines
    for line in lines[-30:]:
        if line.strip():
            print(line)
else:
    print("(No bot output captured yet - bot might still be starting)")

print()
print("-" * 80)
print()

# Check 4: Look for cycle logs
print("Check 4: Trading Cycle Logs")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'grep "Trading Cycle" /tmp/bot_output.log 2>/dev/null | tail -5 || echo "No cycles logged"'],
    capture_output=True, text=True, timeout=10
)
cycle_output = result.stdout
if "No cycles logged" not in cycle_output:
    print("✓ Found trading cycles:")
    for line in cycle_output.strip().split('\n'):
        if line.strip():
            print(f"  {line}")
else:
    print("✗ No trading cycles found in logs yet")

print()
print("=" * 80)
print("DEPLOYMENT COMPLETE")
print("=" * 80)
print()
print("Summary:")
print("  1. Code pulled and deployed")
print("  2. Old bot process killed")
print("  3. New bot started with fixes")
print("  4. API status checked")
print("  5. Trades checked")
print("  6. Logs inspected for cycle execution")
print()
print("Next: Monitor logs and check API again in 60 seconds")
print()
print("Command to monitor logs in real-time:")
print("  ssh operator@192.0.2.21 'tail -f /tmp/bot_output.log'")
print()
print("Command to check trades periodically:")
print("  watch -n 5 'curl -s http://192.0.2.21:8004/api/trades | jq .total'")
