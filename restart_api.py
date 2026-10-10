import subprocess
import time

# Kill port 8000
print("Killing port 8004...")
subprocess.run(['ssh', '-o', 'StrictHostKeyChecking=no', 'operator@192.0.2.21', 
                'sudo fuser -k 8004/tcp 2>/dev/null || true'], timeout=10)

time.sleep(2)

# Start uvicorn
print("Starting uvicorn...")
subprocess.run(['ssh', '-o', 'StrictHostKeyChecking=no', 'operator@192.0.2.21', 
                'cd ~/market-bot/market-pie5-bot && source venv/bin/activate && '
                'nohup uvicorn api.main:app --host 0.0.0.0 --port 8004 > /tmp/uvicorn.log 2>&1 &'],
               timeout=10)

print("API restart initiated. Waiting 5 seconds for startup...")
time.sleep(5)

# Test endpoint
print("\nTesting reset endpoint...")
import requests
try:
    r = requests.post('http://192.0.2.21:8004/api/trades/reset', 
                     params={'session_only': 'false'}, timeout=10)
    print(f"✓ Reset Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"✗ Error: {e}")
