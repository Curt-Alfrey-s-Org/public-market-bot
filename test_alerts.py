#!/usr/bin/env python3
"""
Test desktop alert system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alert_manager import get_alert_manager, alert_news, alert_sizzle, alert_trade_blocked, alert_trade

print("\n" + "=" * 80)
print("Testing Desktop Alert System")
print("=" * 80 + "\n")

# Initialize
manager = get_alert_manager(enabled=True)
print(f"Alert manager initialized: {manager.enabled}")
print(f"Notification available: {'Yes' if manager.enabled else 'No'}\n")

if not manager.enabled:
    print("⚠️  Notification library not available")
    print("Install: pip install plyer (or win10toast on Windows)\n")
    sys.exit(1)

# Test 1: High-impact news alert
print("[TEST 1] High-impact news alert (M&A)")
alert_news(
    symbol='TSLA',
    event_type='M&A',
    description='Tesla considering acquisition of battery startup - $2.5B deal',
    impact='high'
)
print("✅ Sent M&A alert\n")

import time
time.sleep(3)

# Test 2: Sizzle stock alert (volume)
print("[TEST 2] Sizzle stock alert (volume spike)")
alert_sizzle(
    symbol='GME',
    metric='volume',
    value=8.5,
    threshold=3.0
)
print("✅ Sent volume spike alert\n")

time.sleep(3)

# Test 3: Sizzle stock alert (price change)
print("[TEST 3] Sizzle stock alert (price change)")
alert_sizzle(
    symbol='NVDA',
    metric='price_change',
    value=7.8,
    threshold=5.0
)
print("✅ Sent price change alert\n")

time.sleep(3)

# Test 4: Trade block alert
print("[TEST 4] Trade block alert")
alert_trade_blocked(
    symbol='AAPL',
    reason='Earnings report tomorrow - high volatility expected',
    filter_type='earnings'
)
print("✅ Sent trade block alert\n")

time.sleep(3)

# Test 5: Trade execution alert
print("[TEST 5] Trade execution alert")
alert_trade(
    symbol='GOOGL',
    action='BUY',
    price=142.35,
    quantity=50
)
print("✅ Sent trade execution alert\n")

time.sleep(2)

# Show alert history
print("=" * 80)
print("Alert History (Last 10)")
print("=" * 80 + "\n")

recent = manager.get_recent_alerts(count=10)
for i, alert in enumerate(recent, 1):
    print(f"{i}. [{alert['timestamp']}]")
    print(f"   {alert['title']}")
    print(f"   {alert['message']}\n")

print("=" * 80)
print("✅ All tests complete!")
print("=" * 80 + "\n")

print("Note: If notifications didn't appear:")
print("  1. Check notification permissions (system settings)")
print("  2. Verify plyer/win10toast installed")
print("  3. Try running in foreground (not nohup)")
print("  4. Check /tmp/news_daemon.log for errors\n")
