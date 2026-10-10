import subprocess
import time

print("Starting bot in yfinance mode on operator...")
subprocess.Popen(['ssh', 'operator@192.0.2.21', 
                 'nohup bash -c "cd ~/market-bot/market-pie5-bot && export PAPER_TRADING_MODE=true && export SCHWAB_SANDBOX_MODE=false && source venv/bin/activate && python main.py" > /tmp/bot.log 2>&1 &'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Waiting 8 seconds for bot initialization...")
time.sleep(8)

print("Checking bot status...")
import requests
try:
    r = requests.get('http://192.0.2.21:8004/api/bot/status', timeout=5)
    status = r.json()
    print(f"✓ Bot status: running={status.get('running')}, mode={status.get('mode')}")
except Exception as e:
    print(f"✗ Error: {e}")
