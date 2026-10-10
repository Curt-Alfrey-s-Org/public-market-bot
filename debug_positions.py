#!/usr/bin/env python3
import subprocess

print("Checking logs for position loading...")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'grep -i "position\\|open position" /tmp/bot_output.log | head -20'],
    capture_output=True, text=True, timeout=10
)
print(result.stdout if result.stdout.strip() else "(No position logs found)")

print("\nChecking for execution flow...")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'grep -E "Processing trade for|execute_trade|trade failed|Cycle Summary" /tmp/bot_output.log | tail -20'],
    capture_output=True, text=True, timeout=10
)
print(result.stdout if result.stdout.strip() else "(No execution logs found)")

print("\nChecking bot.positions...")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'grep -i "self.positions\\|positions =" /tmp/bot_output.log | head -5'],
    capture_output=True, text=True, timeout=10
)
print(result.stdout if result.stdout.strip() else "(No position initialization logs)")
