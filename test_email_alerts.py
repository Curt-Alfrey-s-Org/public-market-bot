#!/usr/bin/env python3
"""
Test Email Alert System
Tests email alerts with different severity levels and configurations.

Usage:
    python3 test_email_alerts.py [--test-all] [--severity INFO|WARNING|CRITICAL]
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_email_alerts(test_all: bool = False, severity: str = None):
    """Test email alert system"""
    logger.info("="*60)
    logger.info("Email Alert System Test")
    logger.info("="*60)
    
    try:
        from main import TradingBot, AlertSystem, ENABLE_ALERTS, ALERT_EMAIL
        
        # Check configuration
        logger.info("\n[1] Checking Configuration...")
        if not ENABLE_ALERTS:
            logger.warning("⚠️  Alerts are disabled (ENABLE_ALERTS=false)")
            logger.info("   Set ENABLE_ALERTS=true in .env to enable")
            return False
        
        if not ALERT_EMAIL:
            logger.warning("⚠️  No alert email configured (ALERT_EMAIL not set)")
            logger.info("   Set ALERT_EMAIL=operator@example.com in .env")
            return False
        
        logger.info(f"✓ Alerts enabled: {ENABLE_ALERTS}")
        logger.info(f"✓ Alert email: {ALERT_EMAIL}")
        
        # Check SMTP configuration
        from main import SMTP_USERNAME, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
        logger.info("\n[2] Checking SMTP Configuration...")
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("⚠️  SMTP credentials not configured")
            logger.info("   Set SMTP_USERNAME and SMTP_PASSWORD in .env")
            logger.info("   For Gmail: Use app-specific password")
            logger.info("   For Outlook: Use regular password or app password")
            return False
        
        logger.info(f"✓ SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
        logger.info(f"✓ SMTP Username: {SMTP_USERNAME}")
        logger.info("✓ SMTP Password: [configured]")
        
        # Test severity levels
        logger.info("\n[3] Testing Alert Severity Levels...")
        
        test_cases = []
        if test_all:
            test_cases = [
                ('INFO', 'Test Info Alert', 'This is a test INFO alert. Used for informational messages.'),
                ('WARNING', 'Test Warning Alert', 'This is a test WARNING alert. Used for important warnings.'),
                ('CRITICAL', 'Test Critical Alert', 'This is a test CRITICAL alert. Used for urgent issues.'),
            ]
        elif severity:
            test_cases = [
                (severity.upper(), f'Test {severity} Alert', f'This is a test {severity} alert.'),
            ]
        else:
            # Default: test CRITICAL (most important)
            test_cases = [
                ('CRITICAL', 'Test Critical Alert', 'This is a test CRITICAL alert. Used for urgent issues.'),
            ]
        
        results = []
        for sev, subject, message in test_cases:
            logger.info(f"\n  Testing {sev} severity...")
            try:
                AlertSystem.send_alert(subject, message, severity=sev)
                logger.info(f"  ✓ {sev} alert sent successfully")
                results.append((sev, True, None))
            except Exception as e:
                logger.error(f"  ✗ {sev} alert failed: {e}")
                results.append((sev, False, str(e)))
        
        # Test rate limiting
        logger.info("\n[4] Testing Rate Limiting...")
        from main import EMAIL_RATE_LIMIT_ENABLED, EMAIL_MAX_PER_HOUR, EMAIL_MIN_INTERVAL_SECONDS
        logger.info(f"  Rate limiting enabled: {EMAIL_RATE_LIMIT_ENABLED}")
        if EMAIL_RATE_LIMIT_ENABLED:
            logger.info(f"  Max per hour: {EMAIL_MAX_PER_HOUR}")
            logger.info(f"  Min interval: {EMAIL_MIN_INTERVAL_SECONDS} seconds")
            
            # Try sending multiple alerts quickly (should be rate limited)
            logger.info("  Sending 3 rapid alerts (should trigger rate limiting)...")
            for i in range(3):
                try:
                    AlertSystem.send_alert(
                        f"Rate Limit Test {i+1}",
                        f"This is test alert #{i+1} to test rate limiting.",
                        severity='INFO'
                    )
                    logger.info(f"    Alert {i+1}: Sent")
                except Exception as e:
                    logger.warning(f"    Alert {i+1}: {e}")
        
        # Test severity filtering
        logger.info("\n[5] Testing Severity Filtering...")
        from main import ALERT_MIN_SEVERITY
        logger.info(f"  Minimum severity: {ALERT_MIN_SEVERITY}")
        logger.info(f"  Only {ALERT_MIN_SEVERITY} and above will be emailed")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Test Summary")
        logger.info("="*60)
        
        passed = sum(1 for _, success, _ in results if success)
        failed = len(results) - passed
        
        logger.info(f"\nSeverity Tests: {passed} passed, {failed} failed")
        for sev, success, error in results:
            status = "✓ PASS" if success else "✗ FAIL"
            logger.info(f"  {sev}: {status}")
            if error:
                logger.info(f"    Error: {error}")
        
        if passed == len(results):
            logger.info("\n✅ All email alert tests passed!")
            logger.info("\n📧 Check your email inbox for test alerts")
            logger.info(f"   Recipient: {ALERT_EMAIL}")
        else:
            logger.warning(f"\n⚠️  {failed} test(s) failed")
            logger.info("   Check SMTP configuration and credentials")
        
        return passed == len(results)
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test Email Alert System')
    parser.add_argument('--test-all', action='store_true',
                       help='Test all severity levels (INFO, WARNING, CRITICAL)')
    parser.add_argument('--severity', type=str, choices=['INFO', 'WARNING', 'CRITICAL'],
                       help='Test specific severity level')
    
    args = parser.parse_args()
    
    success = test_email_alerts(test_all=args.test_all, severity=args.severity)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
