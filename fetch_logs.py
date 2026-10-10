import subprocess

# Fetch bot log
print("=== BOT LOG (last 100 lines) ===")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'tail -100 /tmp/bot.log 2>/dev/null || echo "Log file not found or empty"'],
    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15
)
print(result.stdout if result.stdout else "(no output)")

# Fetch uvicorn API log
print("\n=== API LOG (last 50 lines) ===")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'tail -50 /tmp/uvicorn.log 2>/dev/null || echo "Log file not found"'],
    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15
)
print(result.stdout if result.stdout else "(no output)")

# Check if bot is still running
print("\n=== BOT PROCESS STATUS ===")
result = subprocess.run(
    ['ssh', 'operator@192.0.2.21', 'ps aux | grep python | grep main.py | grep -v grep'],
    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10
)
print(result.stdout if result.stdout else "(bot not running)")
