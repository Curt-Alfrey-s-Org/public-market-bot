#!/usr/bin/env python3
"""
Tests for strategy-based trading (Phase 1 per MISSION.md).

Covers: get_strategy_signal, CLI/GUI use of BUY/SELL/HOLD (not hardcoded BUY).
"""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'false')
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ['RESTART_RECOVERY_ENABLED'] = 'false'

from main import TradingBot, STRATEGIES_AVAILABLE


class TestGetStrategySignal(unittest.TestCase):
    def setUp(self):
        self.bot = TradingBot(total_capital=10000.0)

    def test_returns_tuple_of_three(self):
        """get_strategy_signal returns (signal, price, volume)."""
        with patch.object(TradingBot, '_fetch_ohlcv_for_strategy', return_value=None):
            out = self.bot.get_strategy_signal('AAPL', use_random_fallback=True)
        self.assertIsInstance(out, tuple)
        self.assertEqual(len(out), 3)
        signal, price, volume = out
        self.assertIn(signal, ('BUY', 'SELL', 'HOLD'))

    def test_hold_when_strategies_unavailable(self):
        """When strategies module unavailable, returns HOLD and no price/volume."""
        with patch('main.STRATEGIES_AVAILABLE', False):
            with patch.object(TradingBot, '_ensure_strategy_manager'):
                bot = TradingBot(total_capital=10000.0)
                bot._strategy_manager = None
                signal, price, volume = bot.get_strategy_signal('AAPL', use_random_fallback=True)
        self.assertEqual(signal, 'HOLD')
        self.assertIsNone(price)
        self.assertIsNone(volume)

    def test_hold_when_insufficient_ohlcv(self):
        """When OHLCV missing or < 50 bars, returns HOLD."""
        with patch.object(TradingBot, '_fetch_ohlcv_for_strategy', return_value=None):
            signal, price, volume = self.bot.get_strategy_signal('AAPL', use_random_fallback=True)
        self.assertEqual(signal, 'HOLD')
        self.assertIsNone(price)
        self.assertIsNone(volume)

    @unittest.skipUnless(STRATEGIES_AVAILABLE, "strategies module required")
    def test_signal_in_valid_set_with_mock_ohlcv(self):
        """When strategies available and OHLCV provided, signal is BUY, SELL, or HOLD."""
        import pandas as pd
        import numpy as np
        n = 60
        df = pd.DataFrame({
            'close': 100.0 + np.cumsum(np.random.randn(n) * 0.5),
            'open': 99.0,
            'high': 101.0,
            'low': 98.0,
            'volume': 1_000_000,
        })
        with patch.object(TradingBot, '_fetch_ohlcv_for_strategy', return_value=df):
            with patch.object(TradingBot, 'get_stock_price', return_value=(100.0, 1_000_000)):
                signal, price, volume = self.bot.get_strategy_signal('AAPL', use_random_fallback=True)
        self.assertIn(signal, ('BUY', 'SELL', 'HOLD'),
                      f"signal must be BUY/SELL/HOLD, got {signal!r}")
        self.assertIsNotNone(price)
        self.assertIsNotNone(volume)

    @unittest.skipUnless(STRATEGIES_AVAILABLE, "strategies module required")
    def test_price_source_last_close_uses_ohlcv_not_get_stock_price(self):
        """When PRICE_SOURCE=last_close, use last close/volume from OHLCV; skip get_stock_price."""
        import pandas as pd
        import numpy as np
        n = 60
        last_close = 123.45
        last_vol = 500_000
        df = pd.DataFrame({
            'close': np.linspace(100.0, last_close, n),
            'open': 99.0,
            'high': 101.0,
            'low': 98.0,
            'volume': last_vol,
        })
        with patch('main.PRICE_SOURCE', 'last_close'):
            with patch.object(TradingBot, '_fetch_ohlcv_for_strategy', return_value=df):
                with patch.object(TradingBot, 'get_stock_price', return_value=(999.0, 999)) as mock_get:
                    signal, price, volume = self.bot.get_strategy_signal(
                        'AAPL', use_random_fallback=True
                    )
                    self.assertEqual(price, last_close)
                    self.assertEqual(volume, last_vol)
                    mock_get.assert_not_called()


class TestSignalToAction(unittest.TestCase):
    """Phase B: (signal, position) → action mapping (SELL+flat→SHORT, BUY+short→COVER)."""

    def setUp(self):
        self.bot = TradingBot(total_capital=10000.0)

    def test_buy_flat_returns_buy(self):
        self.assertEqual(self.bot._signal_to_action('AAPL', 'BUY'), 'BUY')

    def test_buy_long_returns_none(self):
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='long')
        self.assertIsNone(self.bot._signal_to_action('AAPL', 'BUY'))

    def test_buy_short_returns_cover(self):
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='short')
        self.assertEqual(self.bot._signal_to_action('AAPL', 'BUY'), 'COVER')

    def test_sell_long_returns_sell(self):
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='long')
        self.assertEqual(self.bot._signal_to_action('AAPL', 'SELL'), 'SELL')

    def test_sell_flat_returns_short(self):
        self.assertEqual(self.bot._signal_to_action('AAPL', 'SELL'), 'SHORT')

    def test_sell_short_returns_none(self):
        self.bot.open_position('AAPL', 100.0, 10.0, 0.03, side='short')
        self.assertIsNone(self.bot._signal_to_action('AAPL', 'SELL'))

    def test_hold_returns_none(self):
        self.assertIsNone(self.bot._signal_to_action('AAPL', 'HOLD'))
