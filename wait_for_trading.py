import subprocess
import time
import requests

print("Starting bot with full venv path...")
subprocess.Popen(['ssh', 'operator@192.0.2.21',
                 'cd ~/market-bot/market-pie5-bot && nohup ./venv/bin/python main.py > nohup_bot.log 2>&1 &'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Waiting 40 seconds for bot initialization + first trading cycle...")
for i in range(40):
    time.sleep(1)
    if i % 10 == 0:
        try:
            r = requests.get('http://192.0.2.21:8004/api/trades', timeout=2)
            trades = r.json().get('total', 0)
            print(f"  [{i}s] Trades: {trades}")
        except:
            print(f"  [{i}s] API not ready")

print("\nFinal check:")
try:
    r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
    total = r.json().get('total', 0)
    print(f"✓ Total trades: {total}")
    
    if total > 0:
        print("✓ SUCCESS - BOT IS TRADING!")
    else:
        print("✗ No trades yet. Bot might be initializing or stuck.")
        print("  Check bot log on operator: tail nohup_bot.log")
except Exception as e:
    print(f"✗ Error: {e}")
