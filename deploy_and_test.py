import subprocess
import time

print("Pulling latest code on operator...")
subprocess.Popen(['ssh', 'operator@192.0.2.21',
                 'cd ~/market-bot/market-pie5-bot && git pull origin copilot/integrate-batch-pricing'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

print("Killing old bot process...")
subprocess.Popen(['ssh', 'operator@192.0.2.21', 'pkill -9 -f "python main.py"'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

print("Starting new bot with continuous loop...")
subprocess.Popen(['ssh', 'operator@192.0.2.21',
                 'cd ~/market-bot/market-pie5-bot && nohup ./venv/bin/python main.py &'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Waiting 30 seconds for bot to initialize and start trading cycle #1...")
time.sleep(30)

# Check trades
import requests
try:
    r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
    total = r.json().get('total', 0)
    print(f"\n✓ Trades generated: {total}")
    if total > 0:
        print("✓✓✓ BOT IS TRADING! ✓✓✓")
    else:
        print("⏳ Waiting for more trades (bot might still be in first cycle)...")
        print("   Checking again in 30 seconds...")
        time.sleep(30)
        r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
        total = r.json().get('total', 0)
        print(f"   Trades now: {total}")
except Exception as e:
    print(f"✗ Error: {e}")
