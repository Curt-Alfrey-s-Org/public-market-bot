#!/usr/bin/env python3
"""
Test suite for enhanced logging and reporting features
Tests LogManager, LogParser, and ReportGenerator
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')

import unittest
import os
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from log_manager import LogManager
from report_generator import LogParser, ReportGenerator


class TestLogManager(unittest.TestCase):
    """Test LogManager functionality"""
    
    def setUp(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.log_manager = LogManager(log_dir=self.test_dir, db_name="test.db")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_log_trade(self):
        """Test logging a trade"""
        trade = {
            'symbol': 'AAPL',
            'action': 'BUY',
            'quantity': 10.0,
            'price': 150.0,
            'is_win': True,
            'pnl': 50.0,
            'pnl_percent': 3.33
        }
        
        self.log_manager.log_trade(trade)
        
        # Verify trade was logged
        trades = self.log_manager.get_trades()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]['symbol'], 'AAPL')
        self.assertEqual(trades[0]['action'], 'BUY')
    
    def test_log_system_event(self):
        """Test logging a system event"""
        self.log_manager.log_system_event('INFO', 'Test message', {'key': 'value'})
        
        # Check that log file was created
        json_files = list(Path(self.test_dir).glob("system_*.json"))
        self.assertGreater(len(json_files), 0)
    
    def test_log_backtest_result(self):
        """Test logging backtest results"""
        backtest = {
            'initial_capital': 10000.0,
            'final_capital': 11000.0,
            'total_pnl': 1000.0,
            'roi': 0.10,
            'total_trades': 50,
            'winning_trades': 30,
            'losing_trades': 20,
            'win_rate': 0.60
        }
        
        self.log_manager.log_backtest_result(backtest)
        
        # Verify backtest was logged
        results = self.log_manager.get_backtest_results()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['total_trades'], 50)
        self.assertEqual(results[0]['win_rate'], 0.60)
    
    def test_merge_trade_history(self):
        """Test merging existing trade history"""
        trade_history = [
            {'symbol': 'AAPL', 'action': 'BUY', 'price': 150.0, 'is_win': True},
            {'symbol': 'MSFT', 'action': 'BUY', 'price': 300.0, 'is_win': False},
            {'symbol': 'GOOGL', 'action': 'BUY', 'price': 2800.0, 'is_win': True}
        ]
        
        count = self.log_manager.merge_trade_history(trade_history)
        self.assertEqual(count, 3)
        
        # Verify all trades were logged
        trades = self.log_manager.get_trades()
        self.assertEqual(len(trades), 3)
    
    def test_get_trades_with_filters(self):
        """Test retrieving trades with filters"""
        # Log multiple trades
        trades_data = [
            {'symbol': 'AAPL', 'action': 'BUY', 'price': 150.0, 'is_win': True},
            {'symbol': 'MSFT', 'action': 'BUY', 'price': 300.0, 'is_win': False},
            {'symbol': 'AAPL', 'action': 'SELL', 'price': 155.0, 'is_win': True}
        ]
        
        for trade in trades_data:
            self.log_manager.log_trade(trade)
        
        # Filter by symbol
        aapl_trades = self.log_manager.get_trades(symbol='AAPL')
        self.assertEqual(len(aapl_trades), 2)
        
        # Filter by session_id
        session_trades = self.log_manager.get_trades(session_id=self.log_manager.session_id)
        self.assertEqual(len(session_trades), 3)
    
    def test_log_performance_metric(self):
        """Test logging performance metrics"""
        self.log_manager.log_performance_metric('sharpe_ratio', 1.5, {'period': 'monthly'})
        self.log_manager.log_performance_metric('max_drawdown', 0.15)
        
        # Verify metrics were logged (would need to query database)
        # For now, just ensure no errors were raised
        self.assertTrue(True)


class TestLogParser(unittest.TestCase):
    """Test LogParser functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.log_manager = LogManager(log_dir=self.test_dir, db_name="test.db")
        self.log_parser = LogParser(db_path=str(Path(self.test_dir) / "test.db"))
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_calculate_win_rate(self):
        """Test win rate calculation"""
        trades = [
            {'is_win': 1},
            {'is_win': 1},
            {'is_win': 0},
            {'is_win': 1}
        ]
        
        win_rate = self.log_parser.calculate_win_rate(trades)
        self.assertEqual(win_rate, 0.75)  # 3 out of 4
    
    def test_calculate_roi(self):
        """Test ROI calculation"""
        trades = [
            {'pnl': 100.0},
            {'pnl': 50.0},
            {'pnl': -30.0}
        ]
        
        roi = self.log_parser.calculate_roi(trades, initial_capital=1000.0)
        self.assertAlmostEqual(roi, 0.12, places=2)  # (100+50-30)/1000
    
    def test_calculate_pnl_trend(self):
        """Test P&L trend calculation"""
        trades = [
            {'timestamp': '2024-01-01T10:00:00', 'pnl': 100.0},
            {'timestamp': '2024-01-01T11:00:00', 'pnl': 50.0},
            {'timestamp': '2024-01-01T12:00:00', 'pnl': -30.0}
        ]
        
        trend = self.log_parser.calculate_pnl_trend(trades)
        self.assertEqual(len(trend), 3)
        self.assertEqual(trend[0][1], 100.0)
        self.assertEqual(trend[1][1], 150.0)
        self.assertEqual(trend[2][1], 120.0)
    
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        returns = [0.05, 0.03, -0.02, 0.04, 0.06]
        
        sharpe = self.log_parser.calculate_sharpe_ratio(returns)
        self.assertIsInstance(sharpe, float)
        self.assertGreater(sharpe, 0)
    
    def test_calculate_max_drawdown(self):
        """Test max drawdown calculation"""
        pnl_trend = [
            ('2024-01-01', 0),
            ('2024-01-02', 100),
            ('2024-01-03', 150),
            ('2024-01-04', 80),
            ('2024-01-05', 120)
        ]
        
        max_dd = self.log_parser.calculate_max_drawdown(pnl_trend)
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0)
    
    def test_get_kpis_with_data(self):
        """Test KPI extraction with actual data"""
        # Log some trades
        trades_data = [
            {'symbol': 'AAPL', 'action': 'BUY', 'price': 150.0, 'is_win': True, 'pnl': 50.0, 'pnl_percent': 5.0},
            {'symbol': 'MSFT', 'action': 'SELL', 'price': 300.0, 'is_win': False, 'pnl': -30.0, 'pnl_percent': -3.0},
            {'symbol': 'GOOGL', 'action': 'BUY', 'price': 2800.0, 'is_win': True, 'pnl': 100.0, 'pnl_percent': 4.0}
        ]
        
        for trade in trades_data:
            self.log_manager.log_trade(trade)
        
        kpis = self.log_parser.get_kpis()
        
        self.assertEqual(kpis['total_trades'], 3)
        self.assertEqual(kpis['winning_trades'], 2)
        self.assertEqual(kpis['losing_trades'], 1)
        self.assertAlmostEqual(kpis['win_rate'], 2/3, places=2)
        self.assertEqual(kpis['total_pnl'], 120.0)
    
    def test_get_kpis_no_data(self):
        """Test KPI extraction with no data"""
        kpis = self.log_parser.get_kpis()
        
        self.assertIn('error', kpis)
        self.assertEqual(kpis['total_trades'], 0)


class TestReportGenerator(unittest.TestCase):
    """Test ReportGenerator functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.log_manager = LogManager(log_dir=self.test_dir, db_name="test.db")
        self.log_parser = LogParser(db_path=str(Path(self.test_dir) / "test.db"))
        self.report_generator = ReportGenerator(self.log_parser)
        
        # Add some sample data
        trades_data = [
            {'symbol': 'AAPL', 'action': 'BUY', 'price': 150.0, 'is_win': True, 'pnl': 50.0, 'pnl_percent': 5.0},
            {'symbol': 'MSFT', 'action': 'SELL', 'price': 300.0, 'is_win': False, 'pnl': -30.0, 'pnl_percent': -3.0},
            {'symbol': 'GOOGL', 'action': 'BUY', 'price': 2800.0, 'is_win': True, 'pnl': 100.0, 'pnl_percent': 4.0}
        ]
        
        for trade in trades_data:
            self.log_manager.log_trade(trade)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
        
        # Clean up generated report files in current directory
        for file in ['report.txt', 'report.json', 'visualize.py']:
            if os.path.exists(file):
                os.remove(file)
    
    def test_generate_text_report(self):
        """Test text report generation"""
        report_file = os.path.join(self.test_dir, 'test_report.txt')
        report = self.report_generator.generate_text_report(output_file=report_file)
        
        self.assertIsInstance(report, str)
        self.assertIn('TRADING PERFORMANCE REPORT', report)
        self.assertIn('Total Trades:', report)
        self.assertTrue(os.path.exists(report_file))
    
    def test_generate_json_report(self):
        """Test JSON report generation"""
        report_file = os.path.join(self.test_dir, 'test_report.json')
        report = self.report_generator.generate_json_report(output_file=report_file)
        
        self.assertIsInstance(report, dict)
        self.assertIn('kpis', report)
        self.assertIn('generated_at', report)
        self.assertTrue(os.path.exists(report_file))
        
        # Verify JSON is valid
        with open(report_file, 'r') as f:
            loaded_report = json.load(f)
            self.assertEqual(loaded_report['kpis']['total_trades'], 3)
    
    def test_generate_visualization_script(self):
        """Test visualization script generation"""
        script_file = os.path.join(self.test_dir, 'test_visualize.py')
        self.report_generator.generate_visualization_script(output_file=script_file)
        
        self.assertTrue(os.path.exists(script_file))
        
        # Verify script contains expected content
        with open(script_file, 'r') as f:
            content = f.read()
            self.assertIn('matplotlib', content)
            self.assertIn('LogParser', content)
            self.assertIn('plt.show()', content)


class TestEnhancedFilterStock(unittest.TestCase):
    """Test enhanced filter_stock functionality"""
    
    def setUp(self):
        """Set up test bot"""
        from main import TradingBot
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_trend_gradient_calculation(self):
        """Test trend gradient calculation"""
        # Add upward trending prices
        prices = [100, 102, 104, 106, 108]
        for price in prices:
            self.bot.update_price_history('TEST', price)
        
        gradient = self.bot.calculate_trend_gradient('TEST', window=5)
        self.assertIsNotNone(gradient)
        self.assertGreater(gradient, 0)  # Should be positive for uptrend
    
    def test_volatility_pattern_analysis(self):
        """Test volatility pattern analysis"""
        # Add prices with varying volatility
        prices = [100, 101, 99, 100, 102, 98, 103, 97, 104, 96, 105]
        for price in prices:
            self.bot.update_price_history('TEST', price)
        
        analysis = self.bot.analyze_volatility_pattern('TEST')
        self.assertIn('is_stable', analysis)
        self.assertIn('recent_volatility', analysis)
        self.assertIn('volatility_trend', analysis)
    
    def test_filter_stock_with_metadata(self):
        """Test that filter_stock logs validation metadata"""
        # Add sufficient price history
        for i in range(10):
            self.bot.update_price_history('TEST', 100 + i)
        
        is_valid, reason = self.bot.filter_stock('TEST', 100.0, 1000000)
        
        # Check if validation log was created
        self.assertTrue(hasattr(self.bot, 'stock_validation_log'))
        self.assertGreater(len(self.bot.stock_validation_log), 0)
        
        # Check metadata content
        last_log = self.bot.stock_validation_log[-1]
        self.assertIn('metadata', last_log)
        self.assertIn('checks_passed', last_log['metadata'])


if __name__ == '__main__':
    print("Running enhanced logging and reporting tests...")
    print("=" * 70)
    unittest.main(verbosity=2)
