#!/usr/bin/env python3
"""
Tests for short selling (Phase 1 mission per MISSION.md).

Covers: SHORT/COVER actions, position side (long/short), P&L, trailing stops,
execute_trade paper/live validation, invalid action handling,
can_open_short (margin/availability, concentration limits).
"""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'false')
os.environ.setdefault('ENABLE_PDT_RULES', 'false')

from main import (
    TradingBot,
    VALID_ACTIONS,
    ACTIONS_OPEN_POSITION,
    ACTIONS_CLOSE_POSITION,
    SCHWAB_INSTRUCTION_MAP,
)


class TestShortSellingConstants(unittest.TestCase):
    def test_valid_actions_includes_short_cover(self):
        self.assertIn('BUY', VALID_ACTIONS)
        self.assertIn('SELL', VALID_ACTIONS)
        self.assertIn('SHORT', VALID_ACTIONS)
        self.assertIn('COVER', VALID_ACTIONS)

    def test_actions_open_position(self):
        self.assertIn('BUY', ACTIONS_OPEN_POSITION)
        self.assertIn('SHORT', ACTIONS_OPEN_POSITION)

    def test_actions_close_position(self):
        self.assertIn('SELL', ACTIONS_CLOSE_POSITION)
        self.assertIn('COVER', ACTIONS_CLOSE_POSITION)

    def test_schwab_instruction_map(self):
        self.assertEqual(SCHWAB_INSTRUCTION_MAP['BUY'], 'BUY')
        self.assertEqual(SCHWAB_INSTRUCTION_MAP['SELL'], 'SELL')
        self.assertEqual(SCHWAB_INSTRUCTION_MAP['SHORT'], 'SELL_SHORT')
        self.assertEqual(SCHWAB_INSTRUCTION_MAP['COVER'], 'BUY_TO_COVER')


class TestPositionSideAndPnL(unittest.TestCase):
    def setUp(self):
        self.bot = TradingBot(total_capital=10000.0)

    def test_open_position_long_default(self):
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='long')
        self.assertIn('AAPL', self.bot.positions)
        pos = self.bot.positions['AAPL']
        self.assertEqual(pos['side'], 'long')
        self.assertEqual(pos['high_price'], 100.0)
        self.assertIsNone(pos.get('low_price'))

    def test_open_position_short(self):
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='short')
        self.assertIn('AAPL', self.bot.positions)
        pos = self.bot.positions['AAPL']
        self.assertEqual(pos['side'], 'short')
        self.assertEqual(pos['low_price'], 100.0)
        self.assertIsNone(pos.get('high_price'))

    def test_close_position_long_pnl(self):
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='long')
        info = self.bot.close_position('AAPL', 110.0, 'test')
        self.assertIsNotNone(info)
        self.assertEqual(info['side'], 'long')
        self.assertAlmostEqual(info['pnl'], 100.0)
        self.assertAlmostEqual(info['pnl_percent'], 10.0)
        self.assertTrue(info['is_win'])
        self.assertNotIn('AAPL', self.bot.positions)

    def test_close_position_short_pnl(self):
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='short')
        info = self.bot.close_position('AAPL', 90.0, 'test')
        self.assertIsNotNone(info)
        self.assertEqual(info['side'], 'short')
        self.assertAlmostEqual(info['pnl'], 100.0)
        self.assertAlmostEqual(info['pnl_percent'], 10.0)
        self.assertTrue(info['is_win'])
        self.assertNotIn('AAPL', self.bot.positions)

    def test_close_position_short_loss(self):
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='short')
        info = self.bot.close_position('AAPL', 110.0, 'test')
        self.assertIsNotNone(info)
        self.assertAlmostEqual(info['pnl'], -100.0)
        self.assertFalse(info['is_win'])


class TestExecuteTradePaperShortCover(unittest.TestCase):
    def setUp(self):
        self.bot = TradingBot(total_capital=10000.0)

    def test_invalid_action_returns_error(self):
        r = self.bot.execute_trade_paper_mode('AAPL', 'INVALID', 100.0, volume=1_000_000)
        self.assertEqual(r.get('status'), 'error')
        self.assertEqual(r.get('reason'), 'invalid_action')

    def test_short_opens_position_and_simulates(self):
        r = self.bot.execute_trade_paper_mode('AAPL', 'SHORT', 100.0, volume=1_000_000)
        self.assertIn(r.get('status'), ('simulated', 'skipped'))
        if r.get('status') == 'simulated':
            self.assertEqual(r.get('action'), 'SHORT')
            self.assertIn('quantity', r)
            self.assertIn('price', r)

    def test_cover_without_short_skipped(self):
        r = self.bot.execute_trade_paper_mode('AAPL', 'COVER', 100.0, volume=1_000_000)
        self.assertEqual(r.get('status'), 'skipped')
        self.assertEqual(r.get('reason'), 'no_short_position')

    def test_short_round_trip_closes_position(self):
        self.bot.execute_trade_paper_mode('AAPL', 'SHORT', 100.0, volume=1_000_000)
        self.assertNotIn('AAPL', self.bot.positions)

    def test_cover_closes_open_short(self):
        from datetime import datetime, timedelta
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='short')
        past = (datetime.now() - timedelta(days=2)).isoformat()
        self.bot.positions['AAPL']['entry_time'] = past
        r = self.bot.execute_trade_paper_mode('AAPL', 'COVER', 95.0, volume=1_000_000)
        self.assertEqual(r.get('status'), 'simulated')
        self.assertEqual(r.get('action'), 'COVER')
        self.assertNotIn('AAPL', self.bot.positions)


class TestTrailingStopShort(unittest.TestCase):
    def setUp(self):
        self.bot = TradingBot(total_capital=10000.0)
        self.bot.open_position('AAPL', 100.0, 10.0, 0.05, side='short')

    def test_short_trailing_stop_trigger_when_price_rises(self):
        triggered = self.bot.check_trailing_stop('AAPL', 106.0)
        self.assertTrue(triggered is True or triggered == 'partial_exit')

    def test_short_trailing_stop_not_triggered_when_price_falls(self):
        triggered = self.bot.check_trailing_stop('AAPL', 95.0)
        self.assertFalse(triggered)


class TestCanOpenShort(unittest.TestCase):
    """Margin/short-availability and concentration limits (can_open_short)."""

    def setUp(self):
        self.bot = TradingBot(total_capital=10000.0)
        # Clear positions loaded from DB so tests have deterministic state
        self.bot.positions = {}

    def test_can_open_short_when_allowed(self):
        ok, msg = self.bot.can_open_short(500.0, for_live=False)
        self.assertTrue(ok, msg)
        self.assertIn("allowed", msg.lower())

    def test_can_open_short_blocked_when_disabled_paper(self):
        with patch('main.ALLOW_SHORTS_IN_PAPER', False):
            ok, msg = self.bot.can_open_short(500.0, for_live=False)
        self.assertFalse(ok)
        self.assertIn("ALLOW_SHORTS_IN_PAPER", msg)

    def test_can_open_short_blocked_when_disabled_live(self):
        with patch('main.SCHWAB_SHORT_SELLING_ENABLED', False):
            ok, msg = self.bot.can_open_short(500.0, for_live=True)
        self.assertFalse(ok)
        self.assertIn("SCHWAB_SHORT_SELLING_ENABLED", msg)

    def test_can_open_short_blocked_at_max_positions(self):
        with patch('main.MAX_SHORT_POSITIONS', 2):
            self.bot.open_position('A', 100.0, 10.0, 0.03, side='short')
            self.bot.open_position('B', 100.0, 10.0, 0.03, side='short')
            ok, msg = self.bot.can_open_short(500.0, for_live=False)
        self.assertFalse(ok)
        self.assertIn("Maximum short positions", msg)

    def test_can_open_short_blocked_when_exposure_exceeded(self):
        with patch('main.MAX_SHORT_EXPOSURE_PCT', 0.10):
            self.bot.open_position('A', 100.0, 100.0, 0.03, side='short')
            ok, msg = self.bot.can_open_short(500.0, for_live=False)
        self.assertFalse(ok)
        self.assertIn("exceed", msg.lower())


if __name__ == '__main__':
    unittest.main()
