#!/usr/bin/env python3
"""
Diagnose Bot Status
Checks if bot is running, if API can access it, and shows recent activity
"""

import os
import sys
import requests
import json
from datetime import datetime

def check_api_health():
    """Check if API is responding"""
    try:
        response = requests.get('http://localhost:8000/api/health', timeout=2)
        if response.status_code == 200:
            print("✓ API is responding")
            return True
        else:
            print(f"✗ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ API is not responding (connection refused)")
        return False
    except Exception as e:
        print(f"✗ API check failed: {e}")
        return False

def check_bot_status():
    """Check bot status via API"""
    try:
        response = requests.get('http://localhost:8000/api/bot/status', timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Bot Status: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"✗ Bot status returned {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Bot status check failed: {e}")
        return None

def check_trades():
    """Check recent trades"""
    try:
        response = requests.get('http://localhost:8000/api/trades?limit=10', timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Trades: {data.get('total', 0)} total")
            if data.get('trades'):
                print("  Recent trades:")
                for trade in data['trades'][:5]:
                    print(f"    - {trade.get('symbol')} {trade.get('side')} @ ${trade.get('entry_price')}")
            else:
                print("  No trades found")
            return data
        else:
            print(f"✗ Trades returned {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Trades check failed: {e}")
        return None

def check_stats():
    """Check bot stats"""
    try:
        response = requests.get('http://localhost:8000/api/stats', timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Stats:")
            print(f"  Capital: ${data.get('capital', 0):.2f}")
            print(f"  Total Trades: {data.get('total_trades', 0)}")
            print(f"  Open Positions: {data.get('open_positions', 0)}")
            return data
        else:
            print(f"✗ Stats returned {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Stats check failed: {e}")
        return None

def main():
    print("=" * 60)
    print("Bot Status Diagnostic")
    print("=" * 60)
    print()
    
    # Check API
    print("1. Checking API Health...")
    api_ok = check_api_health()
    print()
    
    if not api_ok:
        print("⚠ API is not responding. Please start the API:")
        print("   ./start_api.sh")
        return
    
    # Check bot status
    print("2. Checking Bot Status...")
    bot_status = check_bot_status()
    print()
    
    # Check trades
    print("3. Checking Recent Trades...")
    trades = check_trades()
    print()
    
    # Check stats
    print("4. Checking Bot Stats...")
    stats = check_stats()
    print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if bot_status:
        running = bot_status.get('running', False)
        mode = bot_status.get('mode', 'unknown')
        print(f"Bot Running: {'Yes' if running else 'No'}")
        print(f"Bot Mode: {mode}")
    
    if stats:
        print(f"Total Trades: {stats.get('total_trades', 0)}")
        print(f"Open Positions: {stats.get('open_positions', 0)}")
    
    if trades:
        print(f"Trade History Count: {trades.get('total', 0)}")
    
    print()
    print("If bot is running but no trades appear:")
    print("  1. Bot may be waiting for market signals")
    print("  2. Bot may be paused due to T+1 settlement")
    print("  3. Bot may need to be restarted via API")

if __name__ == '__main__':
    main()
