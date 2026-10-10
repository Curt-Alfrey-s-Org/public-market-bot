import os
import unittest

from main import TradingBot


class TestShortCoverExitPriceTracking(unittest.TestCase):
    def setUp(self):
        # Configure environment for API-disabled paper/sandbox mode
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        # Allow immediate closes for tests
        os.environ['SWING_MIN_HOLD_DAYS'] = '0'

        self.bot = TradingBot(total_capital=10000.0)
        # Restart recovery derives open positions from trades that other
        # tests persisted in the shared test DB; start from a clean slate.
        self.bot.positions.clear()
        self.bot.trade_history.clear()

    def tearDown(self):
        self.bot.positions.clear()
        self.bot.trade_history.clear()

    def test_short_records_entry_exit_and_pnl(self):
        symbol = 'TSLA'
        # Use price within MAX_STOCK_PRICE filter (default $55) so the
        # opening trade is not skipped by the stock filter
        entry_price = 50.0

        result = self.bot.execute_trade_paper_mode(symbol, 'SHORT', entry_price)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('status'), 'simulated')

        self.assertGreaterEqual(len(self.bot.trade_history), 1)
        trade = self.bot.trade_history[-1]

        # Validate core fields
        self.assertEqual(trade['symbol'], symbol)
        self.assertEqual(trade['action'], 'SHORT')
        self.assertIn('entry_price', trade)
        self.assertIn('exit_price', trade)
        self.assertIn('quantity', trade)
        self.assertIn('pnl', trade)
        self.assertIn('pnl_percent', trade)
        self.assertEqual(trade.get('mode'), 'api_disabled')

        # Entry price equals the SHORT price
        self.assertAlmostEqual(trade['entry_price'], entry_price, places=6)

        # For shorts, pnl = (entry - exit) * qty
        qty = trade['quantity']
        exit_price = trade['exit_price']
        expected_pnl = (entry_price - exit_price) * qty
        expected_pnl_percent = ((entry_price - exit_price) / entry_price) * 100

        self.assertAlmostEqual(trade['pnl'], expected_pnl, places=6)
        self.assertAlmostEqual(trade['pnl_percent'], expected_pnl_percent, places=6)

    def test_cover_records_exit_price_and_pnl_on_open_short(self):
        symbol = 'NVDA'
        entry_price = 300.0
        quantity = 5.0
        exit_price = 290.0

        # Open a short position, then COVER to close
        self.bot.open_position(symbol, entry_price, quantity, stop_percent=self.bot.trailing_stop_percent, side='short')

        result = self.bot.execute_trade_paper_mode(symbol, 'COVER', exit_price)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('status'), 'simulated')

        self.assertGreaterEqual(len(self.bot.trade_history), 1)
        trade = self.bot.trade_history[-1]

        self.assertEqual(trade['symbol'], symbol)
        self.assertEqual(trade['action'], 'COVER')
        self.assertIn('entry_price', trade)
        self.assertIn('exit_price', trade)
        self.assertIn('quantity', trade)
        self.assertIn('pnl', trade)
        self.assertIn('pnl_percent', trade)
        self.assertEqual(trade.get('mode'), 'api_disabled')

        # Entry/Exit prices match expected
        self.assertAlmostEqual(trade['entry_price'], entry_price, places=6)
        self.assertAlmostEqual(trade['exit_price'], exit_price, places=6)
        self.assertAlmostEqual(trade['quantity'], quantity, places=6)

        expected_pnl = (entry_price - exit_price) * quantity
        expected_pnl_percent = ((entry_price - exit_price) / entry_price) * 100

        self.assertAlmostEqual(trade['pnl'], expected_pnl, places=6)
        self.assertAlmostEqual(trade['pnl_percent'], expected_pnl_percent, places=6)


if __name__ == '__main__':
    unittest.main()
