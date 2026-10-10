import os
import unittest

from main import TradingBot


class TestExitPriceTracking(unittest.TestCase):
    def setUp(self):
        # Ensure API is disabled and paper/sandbox modes are set for tests
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        # Disable swing minimum hold period for immediate SELL/COVER in tests
        os.environ['SWING_MIN_HOLD_DAYS'] = '0'

        self.bot = TradingBot(total_capital=10000.0)
        # Restart recovery derives open positions from trades that other
        # tests persisted in the shared test DB; start from a clean slate.
        self.bot.positions.clear()
        self.bot.trade_history.clear()

    def tearDown(self):
        # Clean up any positions and trade history created during tests
        self.bot.positions.clear()
        self.bot.trade_history.clear()

    def test_buy_records_entry_exit_and_pnl(self):
        symbol = 'AAPL'
        # Use price within MAX_STOCK_PRICE filter (default $55) so trade is not skipped
        entry_price = 50.0

        result = self.bot.execute_trade_paper_mode(symbol, 'BUY', entry_price)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('status'), 'simulated')

        self.assertGreaterEqual(len(self.bot.trade_history), 1)
        trade = self.bot.trade_history[-1]

        # Validate recorded fields
        self.assertEqual(trade['symbol'], symbol)
        self.assertEqual(trade['action'], 'BUY')
        self.assertIn('entry_price', trade)
        self.assertIn('exit_price', trade)
        self.assertIn('quantity', trade)
        self.assertIn('pnl', trade)
        self.assertIn('pnl_percent', trade)
        self.assertEqual(trade.get('mode'), 'api_disabled')

        # Entry price equals the BUY price
        self.assertAlmostEqual(trade['entry_price'], entry_price, places=6)

        # Recompute P&L and percent and compare
        qty = trade['quantity']
        exit_price = trade['exit_price']
        expected_pnl = (exit_price - entry_price) * qty
        expected_pnl_percent = ((exit_price - entry_price) / entry_price) * 100

        self.assertAlmostEqual(trade['pnl'], expected_pnl, places=6)
        self.assertAlmostEqual(trade['pnl_percent'], expected_pnl_percent, places=6)

    def test_sell_records_exit_price_and_pnl_on_open_long(self):
        symbol = 'MSFT'
        entry_price = 100.0
        quantity = 10.0
        exit_price = 110.0

        # Manually open a long position, then SELL to close
        self.bot.open_position(symbol, entry_price, quantity, stop_percent=self.bot.trailing_stop_percent, side='long')

        result = self.bot.execute_trade_paper_mode(symbol, 'SELL', exit_price)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('status'), 'simulated')

        self.assertGreaterEqual(len(self.bot.trade_history), 1)
        trade = self.bot.trade_history[-1]

        # Validate recorded fields
        self.assertEqual(trade['symbol'], symbol)
        self.assertEqual(trade['action'], 'SELL')
        self.assertIn('entry_price', trade)
        self.assertIn('exit_price', trade)
        self.assertIn('quantity', trade)
        self.assertIn('pnl', trade)
        self.assertIn('pnl_percent', trade)
        self.assertEqual(trade.get('mode'), 'api_disabled')

        # Entry/Exit prices match expected
        self.assertAlmostEqual(trade['entry_price'], entry_price, places=6)
        self.assertAlmostEqual(trade['exit_price'], exit_price, places=6)

        # Quantity from close should match opened quantity
        self.assertAlmostEqual(trade['quantity'], quantity, places=6)

        expected_pnl = (exit_price - entry_price) * quantity
        expected_pnl_percent = ((exit_price - entry_price) / entry_price) * 100

        self.assertAlmostEqual(trade['pnl'], expected_pnl, places=6)
        self.assertAlmostEqual(trade['pnl_percent'], expected_pnl_percent, places=6)


if __name__ == '__main__':
    unittest.main()
