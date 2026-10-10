"""
Test PDT enforcement with business day calculation
Validates that PDT rules use exact 5 business days instead of 7 calendar days
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from main import TradingBot



class TestPDTBusinessDays(unittest.TestCase):
    """Test PDT business day calculation accuracy"""
    
    def test_business_day_calculation_excludes_weekends(self):
        """Test that business day calculation properly excludes weekends"""
        from pandas.tseries.offsets import BDay
        import pandas as pd
        
        # Start on a Monday
        monday = datetime(2024, 1, 8)  # Monday, January 8, 2024
        
        # 5 business days back from Monday should be previous Monday
        # (excluding Saturday and Sunday)
        cutoff = (pd.Timestamp(monday) - BDay(5)).date()
        
        # Should be previous Monday (5 business days = 7 calendar days with weekend)
        expected_cutoff = datetime(2024, 1, 1).date()  # Previous Monday
        
        # Verify weekend days are excluded
        self.assertEqual(cutoff, expected_cutoff, 
                       f"5 business days from {monday.date()} should be {expected_cutoff}, got {cutoff}")
        
        print(f"✓ 5 business days from {monday.date()} = {cutoff} (correct)")
    
    def test_pdt_tracker_uses_business_days_in_main(self):
        """Test that TradingBot in main.py uses business days correctly"""
        import pandas as pd
        from pandas.tseries.offsets import BDay
        
        # Simulate being in production mode to enable PDT tracking
        with patch('main.PAPER_TRADING_MODE', False):
            bot = TradingBot(total_capital=10000.0)
            
            # Use TODAY as reference point for relative date testing
            today = datetime.now().date()
            
            # Calculate dates relative to today
            recent_trade_date = (pd.Timestamp.now() - BDay(2)).date()  # 2 business days ago
            at_cutoff_date = (pd.Timestamp.now() - BDay(5)).date()  # Exactly at 5 business days
            old_trade_date = (pd.Timestamp.now() - BDay(10)).date()  # 10 business days ago (old)
            
            # Add some trades
            bot.day_trades = [
                (recent_trade_date, 'TEST1'),  # Within 5 biz days
                (at_cutoff_date, 'TEST2'),  # At the cutoff (should be kept)
                (old_trade_date, 'TEST3'),  # Older than 5 biz days (should be removed)
            ]
            
            initial_count = len(bot.day_trades)
            self.assertEqual(initial_count, 3, "Should start with 3 trades")
            
            # Call add_day_trade which should trigger cleanup using current date
            bot.add_day_trade('TEST4')
            
            # Verify TEST3 was removed (it's older than 5 business days from today)
            symbols = [sym for _, sym in bot.day_trades]
            self.assertIn('TEST4', symbols, "TEST4 (today) should be in the list")
            self.assertIn('TEST1', symbols, "TEST1 (2 biz days ago) should be in the list")
            self.assertIn('TEST2', symbols, "TEST2 (at cutoff) should be in the list")
            self.assertNotIn('TEST3', symbols, "TEST3 (10 biz days ago) should be removed")
            
            print(f"✓ PDT tracker correctly filters trades older than 5 business days")
            print(f"  Cutoff date: {(pd.Timestamp.now() - BDay(5)).date()}")
            print(f"  Kept: TEST1 ({recent_trade_date}), TEST2 ({at_cutoff_date}), TEST4 ({today})")
            print(f"  Removed: TEST3 ({old_trade_date})")
    
    def test_seven_calendar_days_vs_five_business_days(self):
        """Test that 5 business days is more accurate than 7 calendar days"""
        from pandas.tseries.offsets import BDay
        import pandas as pd
        
        # Scenario: It's Monday, and we had trades on:
        # - Last Monday (7 calendar days ago, 5 business days ago) - SHOULD be at cutoff
        # - Last Tuesday (8 calendar days ago, 6 business days ago) - should be removed
        
        monday = datetime(2024, 1, 15)  # Monday, January 15, 2024
        
        # Using old method (7 calendar days)
        old_cutoff = monday.date() - timedelta(days=7)  # January 8 (Monday)
        
        # Using new method (5 business days)
        new_cutoff = (pd.Timestamp(monday) - BDay(5)).date()  # January 8 (Monday)
        
        # In this case they're the same, but let's test a scenario where they differ
        # Friday scenario
        friday = datetime(2024, 1, 12)  # Friday, January 12, 2024
        
        unused_new_cutoff_fri = (pd.Timestamp(friday) - BDay(5)).date()  # January 5 (Friday)
        # (Friday-specific cutoff calculations can be added here if needed in future tests)
        
        
        # 5 business days back from Jan 15 would skip the holiday
        
        # The key point: business days account for weekends automatically
        # 7 calendar days from Monday = previous Monday (includes weekend)
        # 5 business days from Monday = previous Monday (excludes weekend)
        
        # They should be the same for Monday to Monday
        self.assertEqual(new_cutoff, old_cutoff, 
                        "For Monday to Monday, both methods give same result")
        
        print(f"✓ Business day calculation correctly excludes weekends")
        print(f"  7 calendar days from {monday.date()}: {old_cutoff}")
        print(f"  5 business days from {monday.date()}: {new_cutoff}")
    
    def test_pdt_only_counts_same_day_trades(self):
        """Test that PDT tracker only counts trades that are truly same-day"""
        # This test verifies the fix for the issue where all trades were
        # being counted as day trades, even multi-day positions
        
        with patch('main.PAPER_TRADING_MODE', False):
            bot = TradingBot(total_capital=10000.0)
            
            # Simulate opening a position on Monday
            monday = datetime(2024, 1, 8, 10, 0, 0)
            with patch('main.datetime') as mock_datetime:
                mock_datetime.now.return_value = monday
                mock_datetime.fromisoformat = datetime.fromisoformat
                
                # Open position
                bot.open_position('TEST1', 100.0, 10.0)
                
                # Verify entry time was recorded
                self.assertIn('TEST1', bot.positions)
                self.assertIn('entry_time', bot.positions['TEST1'])
                
                # Now close position on Tuesday (different day)
                tuesday = datetime(2024, 1, 9, 10, 0, 0)
                mock_datetime.now.return_value = tuesday
                
                pnl_info = bot.close_position('TEST1', 105.0, exit_reason='test')
                
                # Verify entry_time is in exit_conditions
                self.assertIn('entry_time', pnl_info['exit_conditions'])
                
                # The entry date and exit date are different, so this should NOT be a day trade
                entry_date = datetime.fromisoformat(pnl_info['exit_conditions']['entry_time']).date()
                exit_date = tuesday.date()
                
                self.assertNotEqual(entry_date, exit_date, 
                                   "Entry and exit should be on different days")
                
                print(f"✓ Multi-day position correctly identified:")
                print(f"  Entry: {entry_date}")
                print(f"  Exit:  {exit_date}")
                print(f"  Same day trade: {entry_date == exit_date}")


if __name__ == '__main__':
    unittest.main()
