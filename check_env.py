import subprocess

print("Checking bot process...")
result = subprocess.run(['ssh', 'operator@192.0.2.21',
                        'ps aux | grep main.py | grep -v grep'],
                       capture_output=True, text=True, timeout=10)
if result.stdout:
    lines = result.stdout.strip().split('\n')
    for line in lines:
        print(f"Process: {line[:100]}...")
else:
    print("✗ No bot process found!")

print("\nChecking environment variables...")
result = subprocess.run(['ssh', 'operator@192.0.2.21',
                        'env | grep -E "PAPER|SCHWAB|TRADING"'],
                       capture_output=True, text=True, timeout=10)
print("Environment:")
print(result.stdout)

print("\nChecking .env file on operator...")
result = subprocess.run(['ssh', 'operator@192.0.2.21',
                        'grep -E "PAPER|SCHWAB|ML" ~/market-bot/market-pie5-bot/.env | head -20'],
                       capture_output=True, text=True, timeout=10)
print(result.stdout)
