#!/usr/bin/env python3
import subprocess
import time

print("=" * 60)
print("COMPREHENSIVE BOT DEBUGGING")
print("=" * 60)

# 1. Check if API is running
print("\n1. API Health Check:")
import requests
try:
    r = requests.get('http://192.0.2.21:8004/api/health', timeout=5)
    print(f"   ✓ API: {r.status_code}")
except Exception as e:
    print(f"   ✗ API: {e}")
    exit(1)

# 2. Check if bot process exists
print("\n2. Bot Process Check:")
result = subprocess.run(['ssh', 'operator@192.0.2.21', 
                        'ps aux | grep main.py | grep -v grep'],
                       capture_output=True, text=True, timeout=10)
if result.stdout:
    print(f"   ✓ Bot running: {result.stdout[:80]}...")
else:
    print("   ✗ No bot process found")

# 3. Check trade count
print("\n3. Trade Count:")
try:
    r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
    total = r.json().get('total', 0)
    print(f"   Trades: {total}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 4. Check settings (ML filter)
print("\n4. ML Filter Settings:")
try:
    r = requests.get('http://192.0.2.21:8004/api/settings/ml-filter', timeout=5)
    settings = r.json()
    print(f"   Enabled: {settings.get('enabled')}")
    print(f"   Available: {settings.get('filter_available')}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
