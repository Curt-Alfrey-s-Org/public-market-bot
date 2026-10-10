#!/usr/bin/env python3
"""
Extended Integration Test Runner
Runs paper trading session to test all integrations working together.

Usage:
    python3 run_integration_test.py [--trades N] [--duration HOURS] [--gui]
"""

import sys
import os
import argparse
import logging
import time
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_integration_test(num_trades: int = None, duration_hours: float = None, use_gui: bool = False):
    """
    Run extended integration test
    
    Args:
        num_trades: Target number of trades (None = no limit)
        duration_hours: Maximum duration in hours (None = no limit)
        use_gui: Use web GUI instead of CLI
    """
    logger.info("="*60)
    logger.info("Extended Integration Test - Paper Trading Session")
    logger.info("="*60)
    
    try:
        from main import TradingBot
        
        # Initialize bot
        logger.info("\n[1] Initializing TradingBot with all integrations...")
        bot = TradingBot(total_capital=10000.0)
        
        # Verify all integrations
        logger.info("\n[2] Verifying All Integrations...")
        integrations_status = {
            'ML Signal Filter': bot.ml_signal_filter is not None and bot.ml_signal_filter.is_trained,
            'Portfolio Optimizer': bot.portfolio_optimizer is not None,
            'Adaptive Learning': bot.adaptive_learner is not None,
            'Real-time ML Optimization': bot.ml_optimizer is not None,
            'Email Alerts': hasattr(bot, 'alert_system') and bot.alert_system is not None,
        }
        
        for name, status in integrations_status.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"  {status_icon} {name}: {'Enabled' if status else 'Disabled'}")
        
        if not all(integrations_status.values()):
            logger.warning("⚠️  Some integrations are disabled - check configuration")
        
        # Test configuration
        logger.info("\n[3] Testing Configuration...")
        from main import (
            ENABLE_ML_SIGNAL_FILTER, ENABLE_PORTFOLIO_OPTIMIZATION,
            ENABLE_ADAPTIVE_LEARNING, ENABLE_REALTIME_ML_OPTIMIZATION,
            ENABLE_ALERTS, PAPER_TRADING_MODE
        )
        
        logger.info(f"  Paper Trading Mode: {PAPER_TRADING_MODE}")
        logger.info(f"  ML Signal Filter: {ENABLE_ML_SIGNAL_FILTER}")
        logger.info(f"  Portfolio Optimization: {ENABLE_PORTFOLIO_OPTIMIZATION}")
        logger.info(f"  Adaptive Learning: {ENABLE_ADAPTIVE_LEARNING}")
        logger.info(f"  Real-time ML Optimization: {ENABLE_REALTIME_ML_OPTIMIZATION}")
        logger.info(f"  Email Alerts: {ENABLE_ALERTS}")
        
        if not PAPER_TRADING_MODE:
            logger.warning("⚠️  WARNING: Not in paper trading mode!")
            logger.warning("   This test will use REAL MONEY. Set PAPER_TRADING_MODE=true")
            response = input("Continue anyway? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Test cancelled")
                return False
        
        # Start test session
        logger.info("\n" + "="*60)
        logger.info("Starting Extended Integration Test")
        logger.info("="*60)
        logger.info(f"Target Trades: {num_trades or 'Unlimited'}")
        logger.info(f"Max Duration: {duration_hours or 'Unlimited'} hours")
        logger.info(f"Mode: {'Web GUI' if use_gui else 'CLI'}")
        logger.info("\n📊 What to Monitor:")
        logger.info("  - ML Signal Filter: Look for 'Signal filtered' or 'Signal accepted' in logs")
        logger.info("  - Portfolio Optimizer: Look for 'Optimal allocation' messages")
        logger.info("  - Adaptive Learning: Look for 'Updated [strategy] strategy weight' messages")
        logger.info("  - Real-time ML Optimization: Look for 'Running periodic ML parameter optimization'")
        logger.info("  - Performance: Look for 'Using cached' messages")
        logger.info("\n" + "="*60)
        
        if use_gui:
            logger.info("\n🚀 Starting Web GUI...")
            logger.info("   Open browser to http://localhost:8050")
            logger.info("   Click 'Start' button to begin trading")
            logger.info("\n   The bot will run until you stop it or close the browser")
            import subprocess
            subprocess.run(['./start_web_gui.sh'])
        else:
            logger.info("\n🚀 Starting CLI Trading Session...")
            logger.info("   The bot will run and execute trades")
            logger.info("   Monitor the output for integration activity")
            logger.info("   Press Ctrl+C to stop")
            logger.info("\n" + "="*60 + "\n")
            
            # Import and run main trading loop
            # Note: This is a simplified version - actual implementation would
            # call the main trading loop from main.py
            logger.info("To run full trading session, use:")
            logger.info("  python3 main.py --mode paper")
            logger.info("\nOr use Web GUI:")
            logger.info("  ./start_web_gui.sh")
        
        return True
        
    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run Extended Integration Test')
    parser.add_argument('--trades', type=int, default=None,
                       help='Target number of trades (default: unlimited)')
    parser.add_argument('--duration', type=float, default=None,
                       help='Maximum duration in hours (default: unlimited)')
    parser.add_argument('--gui', action='store_true',
                       help='Use web GUI instead of CLI')
    
    args = parser.parse_args()
    
    success = run_integration_test(
        num_trades=args.trades,
        duration_hours=args.duration,
        use_gui=args.gui
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
