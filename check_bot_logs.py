import subprocess

print("Checking bot process status...")
result = subprocess.run(['ssh', 'operator@192.0.2.21', 'pgrep -a "python main.py"'],
                       capture_output=True, text=True, timeout=10)
print("Processes:")
print(result.stdout)

print("\nChecking main log file...")
result = subprocess.run(['ssh', 'operator@192.0.2.21', 'tail -100 market-pie5-bot.log 2>/dev/null || echo "Log not found"'],
                       capture_output=True, text=True, timeout=10)
print(result.stdout)

print("\nChecking syslog for bot output...")
result = subprocess.run(['ssh', 'operator@192.0.2.21', r'journalctl -n 50 2>/dev/null | grep -i "bot\|trading" || echo "No entries"'],
                       capture_output=True, text=True, timeout=10)
print(result.stdout[:500])
