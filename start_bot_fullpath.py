import subprocess
import time

print("Starting bot with full path...")
subprocess.Popen(['ssh', 'operator@192.0.2.21',
                 'cd ~/market-bot/market-pie5-bot && nohup ./venv/bin/python main.py &'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Waiting 20 seconds for bot to initialize...")
time.sleep(20)

print("\nChecking if bot is trading...")
import requests
try:
    r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
    trades = r.json()
    total = trades.get('total', 0)
    print(f"✓ Total trades generated: {total}")
    
    if total > 0:
        print("✓ BOT IS TRADING!")
    else:
        print("✗ Bot running but no trades yet (might need more time or initialization)")
        
except Exception as e:
    print(f"✗ Error: {e}")
