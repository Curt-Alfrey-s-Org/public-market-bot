#!/usr/bin/env python3
import requests
import json

print("Checking API /trades endpoint...")
try:
    r = requests.get('http://192.0.2.21:8004/api/trades', timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    total = data.get('total', 0)
    print(f"Total trades: {total}")
    
    if total > 0:
        trades = data.get('trades', [])[:3]
        print(f"\nFirst 3 trades:")
        for trade in trades:
            print(f"  {trade.get('symbol')}: {trade.get('action')} @ ${trade.get('price'):.2f}")
    
    print(f"\nRaw response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
