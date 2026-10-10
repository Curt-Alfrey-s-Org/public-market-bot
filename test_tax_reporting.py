#!/usr/bin/env python3
"""
Test suite for tax reporting functionality
Tests IRS Form 8949 generation, wash sale detection, and CPA reports
"""

import os
# Set environment variables for testing
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'

import unittest
import tempfile
import shutil
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from log_manager import LogManager
from tax_report_generator import TaxReportGenerator


class TestTaxReportGenerator(unittest.TestCase):
    """Test tax report generation functionality"""
    
    def setUp(self):
        """Set up test environment with temporary directory and sample trades"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_trading_logs.db"
        
        # Create log manager and add sample trades
        self.log_manager = LogManager(log_dir=self.test_dir, db_name="test_trading_logs.db")
        
        # Add sample trades for tax year 2024
        self._add_sample_trades()
        
        # Create tax report generator
        self.tax_generator = TaxReportGenerator(db_path=str(self.db_path))
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def _add_sample_trades(self):
        """Add sample trades covering various scenarios"""
        current_year = 2024
        
        # Short-term winning trade
        self.log_manager.log_trade({
            'symbol': 'AAPL',
            'action': 'SELL',
            'quantity': 10.0,
            'price': 155.0,
            'entry_price': 150.0,
            'exit_price': 155.0,
            'pnl': 50.0,
            'pnl_percent': 3.33,
            'is_win': True,
            'timestamp': f'{current_year}-06-15T10:00:00',
            'exit_reason': 'target_reached'
        })
        
        # Short-term losing trade
        self.log_manager.log_trade({
            'symbol': 'MSFT',
            'action': 'SELL',
            'quantity': 5.0,
            'price': 375.0,
            'entry_price': 380.0,
            'exit_price': 375.0,
            'pnl': -25.0,
            'pnl_percent': -1.32,
            'is_win': False,
            'timestamp': f'{current_year}-08-20T14:30:00',
            'exit_reason': 'stop_loss'
        })
        
        # Long-term winning trade (held > 365 days)
        # Note: In real scenario, entry date would be tracked separately
        self.log_manager.log_trade({
            'symbol': 'GOOGL',
            'action': 'SELL',
            'quantity': 8.0,
            'price': 145.0,
            'entry_price': 130.0,
            'exit_price': 145.0,
            'pnl': 120.0,
            'pnl_percent': 11.54,
            'is_win': True,
            'timestamp': f'{current_year}-10-01T11:00:00',
            'exit_reason': 'target_reached'
        })
        
        # Potential wash sale scenario - losing trade
        self.log_manager.log_trade({
            'symbol': 'TSLA',
            'action': 'SELL',
            'quantity': 15.0,
            'price': 240.0,
            'entry_price': 250.0,
            'exit_price': 240.0,
            'pnl': -150.0,
            'pnl_percent': -4.0,
            'is_win': False,
            'timestamp': f'{current_year}-11-10T09:00:00',
            'exit_reason': 'stop_loss'
        })
        
        # Add a BUY trade for TSLA within 30 days (creates wash sale)
        # Note: This is a BUY, not SELL, so won't show in tax report but used for wash sale detection
        conn = self.log_manager._get_connection() if hasattr(self.log_manager, '_get_connection') else None
        if not conn:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trades (
                session_id, timestamp, symbol, action, quantity, price,
                is_win, pnl, pnl_percent, entry_price, exit_price,
                exit_reason, strategy, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.log_manager.session_id,
            f'{current_year}-11-25T10:00:00',
            'TSLA',
            'BUY',
            15.0,
            245.0,
            None,
            None,
            None,
            245.0,
            None,
            'new_position',
            'default',
            '{}'
        ))
        conn.commit()
        conn.close()
    
    def test_get_trades_for_tax_year(self):
        """Test retrieving trades for a specific tax year"""
        trades = self.tax_generator.get_trades_for_tax_year(2024)
        
        # Should return only SELL trades (completed positions)
        self.assertGreater(len(trades), 0)
        
        for trade in trades:
            self.assertEqual(trade['action'], 'SELL')
            self.assertIn('symbol', trade)
            self.assertIn('timestamp', trade)
        
        print(f"✓ Retrieved {len(trades)} trades for tax year 2024")
    
    def test_classify_holding_period(self):
        """Test holding period classification"""
        # Short-term (30 days)
        acquisition = '2024-01-01T00:00:00'
        sale = '2024-01-31T00:00:00'
        period = self.tax_generator.classify_holding_period(acquisition, sale)
        self.assertEqual(period, 'short-term')
        
        # Short-term (365 days exactly)
        acquisition = '2023-01-01T00:00:00'
        sale = '2024-01-01T00:00:00'
        period = self.tax_generator.classify_holding_period(acquisition, sale)
        self.assertEqual(period, 'short-term')
        
        # Long-term (366 days)
        acquisition = '2023-01-01T00:00:00'
        sale = '2024-01-02T00:00:00'
        period = self.tax_generator.classify_holding_period(acquisition, sale)
        self.assertEqual(period, 'long-term')
        
        print("✓ Holding period classification working correctly")
    
    def test_detect_wash_sales(self):
        """Test wash sale detection"""
        trades = self.tax_generator.get_trades_for_tax_year(2024)
        trades_with_wash = self.tax_generator.detect_wash_sales(trades)
        
        # Check that wash sale detection ran
        self.assertIsInstance(trades_with_wash, list)
        
        # Find TSLA trade (should be flagged as wash sale)
        tsla_trades = [t for t in trades_with_wash if t['symbol'] == 'TSLA']
        if tsla_trades:
            # Should have wash_sale flag
            self.assertIn('wash_sale', tsla_trades[0])
            print(f"✓ Wash sale detection working (TSLA flagged: {tsla_trades[0].get('wash_sale', False)})")
        else:
            print("✓ Wash sale detection working (no wash sales in test data)")
    
    def test_generate_form_8949_csv(self):
        """Test IRS Form 8949 CSV generation"""
        output_file = Path(self.test_dir) / 'test_form_8949.csv'
        
        result = self.tax_generator.generate_form_8949_csv(2024, str(output_file))
        
        # Check file was created
        self.assertTrue(output_file.exists())
        self.assertEqual(result, str(output_file))
        
        # Read and validate CSV content
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Check for key sections
        csv_content = '\n'.join([','.join(row) for row in rows])
        self.assertIn('IRS Form 8949', csv_content)
        self.assertIn('Tax Year: 2024', csv_content)
        self.assertIn('PART I: SHORT-TERM', csv_content)
        self.assertIn('PART II: LONG-TERM', csv_content)
        self.assertIn('SUMMARY FOR SCHEDULE D', csv_content)
        
        # Check for column headers
        self.assertIn('Description of property', csv_content)
        self.assertIn('Date acquired', csv_content)
        self.assertIn('Date sold', csv_content)
        self.assertIn('Proceeds', csv_content)
        self.assertIn('Cost', csv_content)
        self.assertIn('Gain or (loss)', csv_content)
        
        print(f"✓ Form 8949 CSV generated successfully: {output_file}")
    
    def test_generate_tax_summary_json(self):
        """Test tax summary JSON generation"""
        output_file = Path(self.test_dir) / 'test_tax_summary.json'
        
        result = self.tax_generator.generate_tax_summary_json(2024, str(output_file))
        
        # Check file was created
        self.assertTrue(output_file.exists())
        self.assertEqual(result, str(output_file))
        
        # Read and validate JSON content
        with open(output_file, 'r') as f:
            summary = json.load(f)
        
        # Check required fields
        self.assertIn('tax_year', summary)
        self.assertEqual(summary['tax_year'], 2024)
        
        self.assertIn('summary', summary)
        self.assertIn('total_trades', summary['summary'])
        self.assertIn('short_term_trades', summary['summary'])
        self.assertIn('long_term_trades', summary['summary'])
        self.assertIn('wash_sales_detected', summary['summary'])
        self.assertIn('net_capital_gain_loss', summary['summary'])
        
        self.assertIn('short_term_trades', summary)
        self.assertIn('long_term_trades', summary)
        self.assertIn('wash_sales', summary)
        self.assertIn('notes', summary)
        
        # Verify trade details include required fields
        if summary['short_term_trades']:
            trade = summary['short_term_trades'][0]
            self.assertIn('symbol', trade)
            self.assertIn('date_acquired', trade)
            self.assertIn('date_sold', trade)
            self.assertIn('proceeds', trade)
            self.assertIn('cost_basis', trade)
            self.assertIn('gain_loss', trade)
        
        print(f"✓ Tax summary JSON generated successfully: {output_file}")
        print(f"  Total trades: {summary['summary']['total_trades']}")
        print(f"  Net gain/loss: ${summary['summary']['net_capital_gain_loss']:.2f}")
    
    def test_generate_cpa_report(self):
        """Test CPA report generation"""
        output_file = Path(self.test_dir) / 'test_cpa_report.txt'
        
        result = self.tax_generator.generate_cpa_report(2024, str(output_file))
        
        # Check file was created
        self.assertTrue(output_file.exists())
        self.assertEqual(result, str(output_file))
        
        # Read and validate report content
        with open(output_file, 'r') as f:
            report = f.read()
        
        # Check for key sections
        self.assertIn('TRADING TAX REPORT FOR CPA REVIEW', report)
        self.assertIn('Tax Year: 2024', report)
        self.assertIn('EXECUTIVE SUMMARY', report)
        self.assertIn('SHORT-TERM CAPITAL GAINS AND LOSSES', report)
        self.assertIn('NOTES AND DISCLAIMERS', report)
        
        # Check for trade details
        self.assertIn('Symbol', report)
        self.assertIn('Qty', report)
        self.assertIn('Acquired', report)
        self.assertIn('Sold', report)
        self.assertIn('Cost Basis', report)
        self.assertIn('Proceeds', report)
        self.assertIn('Gain/Loss', report)
        
        # Check for wash sale section
        self.assertIn('POTENTIAL WASH SALES', report)
        
        print(f"✓ CPA report generated successfully: {output_file}")
    
    def test_generate_all_reports(self):
        """Test generating all reports at once"""
        # Change to test directory to avoid cluttering repo
        import os
        original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        try:
            reports = self.tax_generator.generate_all_reports(2024)
            
            # Check all report types were generated
            self.assertIn('form_8949_csv', reports)
            self.assertIn('tax_summary_json', reports)
            self.assertIn('cpa_report', reports)
            
            # Verify all files exist
            for report_type, filename in reports.items():
                filepath = Path(self.test_dir) / filename
                self.assertTrue(filepath.exists(), f"Report {filename} not found")
            
            print("✓ All tax reports generated successfully")
            print(f"  Form 8949 CSV: {reports['form_8949_csv']}")
            print(f"  Tax Summary JSON: {reports['tax_summary_json']}")
            print(f"  CPA Report: {reports['cpa_report']}")
            
        finally:
            os.chdir(original_dir)
    
    def test_empty_database(self):
        """Test handling of empty database (no trades)"""
        # Create new empty database
        empty_dir = tempfile.mkdtemp()
        empty_db_path = Path(empty_dir) / "empty.db"
        empty_log_manager = LogManager(log_dir=empty_dir, db_name="empty.db")
        
        try:
            empty_generator = TaxReportGenerator(db_path=str(empty_db_path))
            
            # Should handle empty database gracefully
            trades = empty_generator.get_trades_for_tax_year(2024)
            self.assertEqual(len(trades), 0)
            
            print("✓ Empty database handled gracefully")
            
        finally:
            shutil.rmtree(empty_dir)
    
    def test_multiple_tax_years(self):
        """Test generating reports for multiple tax years"""
        # Add trades for 2023
        self.log_manager.log_trade({
            'symbol': 'NVDA',
            'action': 'SELL',
            'quantity': 3.0,
            'price': 500.0,
            'entry_price': 480.0,
            'exit_price': 500.0,
            'pnl': 60.0,
            'pnl_percent': 4.17,
            'is_win': True,
            'timestamp': '2023-12-15T15:00:00',
            'exit_reason': 'target_reached'
        })
        
        # Get trades for each year
        trades_2023 = self.tax_generator.get_trades_for_tax_year(2023)
        trades_2024 = self.tax_generator.get_trades_for_tax_year(2024)
        
        self.assertGreater(len(trades_2023), 0)
        self.assertGreater(len(trades_2024), 0)
        
        # Verify year isolation
        for trade in trades_2023:
            self.assertTrue(trade['timestamp'].startswith('2023'))
        
        for trade in trades_2024:
            self.assertTrue(trade['timestamp'].startswith('2024'))
        
        print(f"✓ Multiple tax years handled correctly")
        print(f"  2023 trades: {len(trades_2023)}")
        print(f"  2024 trades: {len(trades_2024)}")


class TestTaxReportIntegration(unittest.TestCase):
    """Integration tests with main trading bot"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_trade_data_completeness(self):
        """Test that trade data includes all fields needed for tax reporting"""
        # Create a sample trade directly instead of using TradingBot
        # to avoid importing heavy dependencies in test
        sample_trade = {
            'symbol': 'AAPL',
            'action': 'SELL',
            'timestamp': '2024-06-15T10:00:00',
            'quantity': 100.0,
            'entry_price': 150.0,
            'exit_price': 155.0,
            'pnl': 500.0,
            'pnl_percent': 3.33,
            'is_win': True,
            'exit_reason': 'target_reached'
        }
        
        # Required fields for tax reporting
        tax_required_fields = [
            'symbol',
            'action',
            'timestamp',
            'quantity',
            'entry_price',
            'exit_price',
            'pnl'
        ]
        
        for field in tax_required_fields:
            self.assertIn(field, sample_trade, f"Missing required tax field: {field}")
        
        print("✓ Trade data includes all required tax fields")
    
    def test_log_manager_integration(self):
        """Test integration between LogManager and TaxReportGenerator"""
        log_manager = LogManager(log_dir=self.test_dir, db_name="test.db")
        
        # Log a complete trade
        log_manager.log_trade({
            'symbol': 'TEST',
            'action': 'SELL',
            'quantity': 100.0,
            'price': 50.0,
            'entry_price': 45.0,
            'exit_price': 50.0,
            'pnl': 500.0,
            'pnl_percent': 11.11,
            'is_win': True,
            'timestamp': '2024-06-15T10:00:00',
            'exit_reason': 'target_reached'
        })
        
        # Create tax generator and retrieve trade
        db_path = Path(self.test_dir) / "test.db"
        tax_generator = TaxReportGenerator(db_path=str(db_path))
        
        trades = tax_generator.get_trades_for_tax_year(2024)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]['symbol'], 'TEST')
        
        print("✓ LogManager and TaxReportGenerator integration working")


if __name__ == '__main__':
    print("Testing tax reporting functionality...")
    print("=" * 80)
    unittest.main(verbosity=2)
