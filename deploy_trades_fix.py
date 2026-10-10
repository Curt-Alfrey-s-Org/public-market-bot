import subprocess
import time

print("Pulling latest code on operator...")
subprocess.run(['ssh', 'operator@192.0.2.21', 
               'cd ~/market-bot/market-pie5-bot && git pull origin copilot/integrate-batch-pricing'],
              timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Restarting API on new host...")
subprocess.run(['ssh', 'operator@192.0.2.21', 'sudo fuser -k 8004/tcp || true'],
              timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)

subprocess.Popen(['ssh', 'operator@192.0.2.21',
                 'cd ~/market-bot/market-pie5-bot && nohup ./venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8004 &'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Waiting 8 seconds for API startup on new host...")
time.sleep(8)

print("Checking trades...")
import requests
try:
    r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
    print(f"✓ GET /api/trades: {r.status_code}")
    total = r.json().get('total', 0)
    print(f"  Trades in database: {total}")
except Exception as e:
    print(f"✗ Error: {e}")
