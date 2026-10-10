import subprocess
import time
import requests

print("Pulling latest code on operator...")
subprocess.Popen(['ssh', 'operator@192.0.2.21', 
                 'cd ~/market-bot/market-pie5-bot && git pull origin copilot/integrate-batch-pricing'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)

print("Killing port 8004...")
subprocess.Popen(['ssh', 'operator@192.0.2.21', 'sudo fuser -k 8004/tcp || true'],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)

print("Starting uvicorn...")
subprocess.Popen(['ssh', 'operator@192.0.2.21', 
                 'nohup bash -c "cd ~/market-bot/market-pie5-bot && source venv/bin/activate && uvicorn api.main:app --host 0.0.0.0 --port 8004" > /tmp/uvicorn.log 2>&1 &'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Waiting 10 seconds for API startup...")
time.sleep(10)

print("\nTesting ML filter endpoints...")
try:
    # Get ML settings
    r = requests.get('http://192.0.2.21:8004/api/settings/ml-filter', timeout=5)
    print(f"✓ GET /api/settings/ml-filter: {r.status_code}")
    print(f"  Current settings: {r.json()}")
    
    # Toggle ML filter
    print("\nToggling ML filter OFF...")
    r = requests.put('http://192.0.2.21:8004/api/settings/ml-filter', 
                     json={'enabled': False}, timeout=5)
    print(f"✓ PUT /api/settings/ml-filter: {r.status_code}")
    print(f"  Updated: {r.json()}")
    
    # Verify it changed
    r = requests.get('http://192.0.2.21:8004/api/settings/ml-filter', timeout=5)
    print(f"\n✓ Verification GET: enabled={r.json()['enabled']}")
    
except Exception as e:
    print(f"✗ Error: {e}")
