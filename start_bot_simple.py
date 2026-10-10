import subprocess
import time

print("Killing any existing bot processes...")
subprocess.Popen(['ssh', 'operator@192.0.2.21', 'pkill -9 -f "python main.py"'],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)

print("Starting bot with yfinance mode...")
# Use Popen with no timeout to avoid hanging
subprocess.Popen(['ssh', 'operator@192.0.2.21',
                 'cd ~/market-bot/market-pie5-bot && PAPER_TRADING_MODE=true SCHWAB_SANDBOX_MODE=false nohup python main.py &'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Bot started in background. Waiting 15 seconds for initialization...")
time.sleep(15)

print("\nChecking if bot is trading...")
import requests
try:
    r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
    trades = r.json()
    print(f"✓ API responds. Total trades: {trades.get('total', 0)}")
except Exception as e:
    print(f"✗ API error: {e}")
