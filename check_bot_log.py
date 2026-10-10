import subprocess

print("Checking bot log on operator...")
result = subprocess.run(['ssh', 'operator@192.0.2.21', 'tail -100 nohup_bot.log 2>&1 || tail -100 /tmp/bot.log 2>&1 || echo "No log found"'],
                       capture_output=True, text=True, timeout=10)

print(result.stdout[-3000:])  # Last 3000 chars
