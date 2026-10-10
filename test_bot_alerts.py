#!/usr/bin/env python3
"""
Test script for bot-integrated alert system

Tests:
1. Alert system initialization in TradingBot
2. Sizzle detection during paper trading
3. Trade execution alerts
4. Filter block alerts (news, earnings, macro, sentiment, options)
"""
import os
import sys

# Set environment variables for paper trading
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'  # Use yfinance simulation

# Import after setting env vars
from main import TradingBot

def test_alert_initialization():
    """Test that alert system initializes correctly in TradingBot"""
    print("\n" + "="*70)
    print("TEST 1: Alert System Initialization")
    print("="*70)
    
    bot = TradingBot(total_capital=10000.0)
    
    # Check alert manager
    has_alert_manager = bot.alert_manager is not None
    print(f"✓ AlertManager initialized: {has_alert_manager}")
    
    # Check sizzle detector
    has_sizzle_detector = bot.sizzle_detector is not None
    print(f"✓ SizzleDetector initialized: {has_sizzle_detector}")
    
    if has_sizzle_detector:
        print(f"  - Volume threshold: {bot.sizzle_detector.volume_threshold}x")
        print(f"  - Price change threshold: {bot.sizzle_detector.price_change_threshold}%")
        print(f"  - Momentum threshold: {bot.sizzle_detector.momentum_threshold}")
    
    return bot, has_alert_manager, has_sizzle_detector

def test_trade_execution_alert(bot):
    """Test trade execution alert"""
    print("\n" + "="*70)
    print("TEST 2: Trade Execution Alert")
    print("="*70)
    
    # Execute a paper trade
    result = bot.execute_trade_paper_mode('AAPL', 'BUY', 150.0, volume=1000000)
    
    print(f"Trade status: {result.get('status')}")
    print(f"Expected: Desktop notification for AAPL BUY trade")
    print("  Check for popup: '✅ Trade Executed: AAPL'")
    
    return result

def test_sizzle_detection(bot):
    """Test sizzle detection for volume spike"""
    print("\n" + "="*70)
    print("TEST 3: Sizzle Detection (Volume Spike)")
    print("="*70)
    
    # Execute trade with high volume (5x normal)
    result = bot.execute_trade_paper_mode('GME', 'BUY', 25.0, volume=5000000)
    
    print(f"Trade status: {result.get('status')}")
    print(f"Expected: Volume spike alert if 5M > 3x average")
    print("  Check for popup: '📊 SIZZLE ALERT: GME'")
    
    return result

def test_news_filter_alert(bot):
    """Test news filter block alert"""
    print("\n" + "="*70)
    print("TEST 4: News Filter Block Alert")
    print("="*70)
    
    # Note: This requires news_monitor to be initialized and have data
    if bot.news_monitor:
        print("News monitor available - filter may trigger if M&A/IPO/Regulatory events exist")
        print("Expected: Filter block alert if high-impact news detected")
        print("  Check for popup: '📰 Trade Blocked: [SYMBOL]'")
    else:
        print("⚠️  News monitor not available - skipping news filter test")
    
    return None

def test_earnings_filter_alert(bot):
    """Test earnings filter block alert"""
    print("\n" + "="*70)
    print("TEST 5: Earnings Filter Block Alert")
    print("="*70)
    
    # Note: This requires earnings_calendar to be initialized
    if bot.earnings_calendar:
        print("Earnings calendar available - filter may trigger if earnings upcoming")
        print("Expected: Filter block alert if earnings within 3 days")
        print("  Check for popup: '📊 Trade Blocked: [SYMBOL]'")
    else:
        print("⚠️  Earnings calendar not available - skipping earnings filter test")
    
    return None

def main():
    """Run all alert integration tests"""
    print("\n" + "="*70)
    print("TRADING BOT ALERT SYSTEM INTEGRATION TESTS")
    print("="*70)
    print("\nThis script tests the alert system integrated into main trading bot.")
    print("Desktop notifications should appear for:")
    print("  - Trade executions (BUY/SELL/SHORT/COVER)")
    print("  - Sizzle stocks (unusual volume/price)")
    print("  - Filter blocks (news/earnings/macro/sentiment/options)")
    print("\nNote: Alerts may not trigger if filters or data sources are unavailable.")
    
    try:
        # Test 1: Initialization
        bot, has_alerts, has_sizzle = test_alert_initialization()
        
        if not has_alerts:
            print("\n⚠️  WARNING: Alert system not initialized!")
            print("Possible causes:")
            print("  1. alert_manager.py not found")
            print("  2. plyer not installed (run: pip install plyer)")
            print("  3. Import error in main.py")
            return
        
        # Test 2: Trade execution alert
        test_trade_execution_alert(bot)
        
        # Test 3: Sizzle detection
        if has_sizzle:
            test_sizzle_detection(bot)
        
        # Test 4: News filter alert
        test_news_filter_alert(bot)
        
        # Test 5: Earnings filter alert
        test_earnings_filter_alert(bot)
        
        print("\n" + "="*70)
        print("ALERT HISTORY (from AlertManager)")
        print("="*70)
        
        if bot.alert_manager:
            recent_alerts = bot.alert_manager.get_recent_alerts(10)
            if recent_alerts:
                for i, alert in enumerate(recent_alerts, 1):
                    timestamp = alert.get('timestamp', 'N/A')
                    title = alert.get('title', 'N/A')
                    message = alert.get('message', 'N/A')[:80]
                    print(f"\n{i}. [{timestamp}] {title}")
                    print(f"   {message}")
            else:
                print("No alerts in history (may need to check notification permissions)")
        
        print("\n" + "="*70)
        print("✅ Alert integration tests complete!")
        print("="*70)
        print("\nIf no popups appeared, check:")
        print("  1. Notification permissions in OS settings")
        print("  2. plyer installation: pip list | grep plyer")
        print("  3. Alert manager logs in bot output above")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
