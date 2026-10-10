import subprocess
import time
import requests

print("Step 1: Kill port 8004...")
subprocess.Popen(['ssh', 'operator@192.0.2.21', 'sudo fuser -k 8004/tcp || true'],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(3)

print("Step 2: Start uvicorn in background...")
subprocess.Popen(['ssh', 'operator@192.0.2.21', 
                 'nohup bash -c "cd ~/market-bot/market-pie5-bot && source venv/bin/activate && uvicorn api.main:app --host 0.0.0.0 --port 8004" > /tmp/uvicorn.log 2>&1 &'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Step 3: Waiting 10 seconds for API startup...")
time.sleep(10)

print("\nStep 4: Testing reset endpoint...")
for attempt in range(3):
    try:
        r = requests.post('http://192.0.2.21:8004/api/trades/reset', 
                         params={'session_only': 'false'}, timeout=5)
        print(f"✓ Reset Status: {r.status_code}")
        print(f"Response: {r.json()}")
        break
    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {str(e)[:100]}")
        if attempt < 2:
            time.sleep(3)
            print("Retrying...")
