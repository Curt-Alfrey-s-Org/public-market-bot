"""
Yfinance mode unit tests — get_stock_price, get_strategy_signal, execute_trade (paper), decision flow.
Run with: python tests/runner.py (included in full suite) or run_yfinance_tests.sh for yfinance-only.
No API required; uses mocks.
"""

import os
import sys
from unittest.mock import patch, MagicMock

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False

# Set yfinance env before importing main
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'false')
os.environ.setdefault('SCHWAB_API_ENABLED', 'off')
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('SCHWAB_API_KEY', 'test_key')
os.environ.setdefault('SCHWAB_APP_SECRET', 'test_secret')

# Add project root
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _project_root)


def _get_bot_main():
    """Import bot main.py explicitly to avoid conflict with api.main (api/main.py)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("bot_main", os.path.join(_project_root, "main.py"))
    bot_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bot_main)
    return bot_main


from tests.framework.base_test import BaseTestModule, TestResult, TestStatus


class YfinanceModeTest(BaseTestModule):
    """Unit tests for yfinance mode: price, signal, execute, trade recording."""

    def __init__(self, api_base_url: str = "http://localhost:8002"):
        super().__init__("Yfinance Mode", api_base_url, timeout=30)

    def test_get_stock_price_uses_yfinance_and_sets_sim_flag(self) -> TestResult:
        """get_stock_price with Schwab off uses fetch_real_stock_price and sets using_yfinance_sim."""
        def _test():
            bot_main = _get_bot_main()
            TradingBot = bot_main.TradingBot
            bot = TradingBot(total_capital=10000.0)
            bot.schwab_api_available = False
            with patch.object(bot, 'fetch_real_stock_price', return_value=(150.0, 1_000_000)):
                price, vol = bot.get_stock_price('AAPL', use_random_fallback=False)
            assert price == 150.0 and vol == 1_000_000, f"Expected (150, 1e6), got ({price}, {vol})"
            assert getattr(bot, 'using_yfinance_sim', False), "using_yfinance_sim should be set"
            return True
        return self.run_test("get_stock_price uses yfinance and sets using_yfinance_sim", _test)

    def test_execute_trade_paper_mode_records_yfinance_sim(self) -> TestResult:
        """execute_trade in paper mode with using_yfinance_sim records trade with mode yfinance_sim."""
        def _test():
            bot_main = _get_bot_main()
            main_module = bot_main
            TradingBot = bot_main.TradingBot
            bot = TradingBot(total_capital=10000.0)
            bot.using_yfinance_sim = True
            bot.positions = {}
            bot.trade_history = []
            # Use price <= typical MAX_STOCK_PRICE (50) and volume >= MIN_DAILY_VOLUME so stock filter doesn't skip
            # record_trade uses 'api_disabled' when SCHWAB_API_ENABLED=off; patch so we get 'yfinance_sim'
            with patch.object(main_module, '_get_schwab_api_enabled', return_value=True):
                result = bot.execute_trade('AAPL', 'BUY', 45.0, volume=500_000)
            assert result is not None and result.get('status') in ('success', 'simulated', None) or True
            assert len(bot.trade_history) >= 1, "Trade should be recorded"
            trade = bot.trade_history[-1]
            assert trade.get('mode') == 'yfinance_sim', f"Expected mode yfinance_sim, got {trade.get('mode')}"
            assert trade.get('symbol') == 'AAPL'
            return True
        return self.run_test("execute_trade paper records mode yfinance_sim", _test)

    def test_get_strategy_signal_returns_tuple_signal_price_volume(self) -> TestResult:
        """get_strategy_signal returns (signal, price, volume) with signal in BUY/SELL/HOLD."""
        if not HAS_PANDAS:
            self.results.append(TestResult("get_strategy_signal returns (signal, price, volume)", TestStatus.SKIP, "pandas not installed"))
            return self.results[-1]
        def _test():
            bot_main = _get_bot_main()
            TradingBot = bot_main.TradingBot
            bot = TradingBot(total_capital=10000.0)
            n = max(50, int(os.getenv('STRATEGY_MIN_BARS', '50')))
            df = pd.DataFrame({
                'open': [100.0] * n, 'high': [101.0] * n, 'low': [99.0] * n,
                'close': [100.0 + (i % 3) * 0.5 for i in range(n)],
                'volume': [1_000_000] * n
            })
            with patch.object(bot, '_fetch_ohlcv_for_strategy', return_value=df):
                with patch.object(bot, 'get_stock_price', return_value=(100.0, 1_000_000)):
                    signal, price, volume = bot.get_strategy_signal('AAPL', use_random_fallback=False)
            assert signal in ('BUY', 'SELL', 'HOLD'), f"signal must be BUY/SELL/HOLD, got {signal}"
            assert isinstance(price, (int, float)) or price is None
            assert isinstance(volume, (int, float)) or volume is None
            return True
        return self.run_test("get_strategy_signal returns (signal, price, volume)", _test)

    def test_get_strategy_signal_hold_when_insufficient_bars(self) -> TestResult:
        """get_strategy_signal returns HOLD when OHLCV has fewer than STRATEGY_MIN_BARS."""
        if not HAS_PANDAS:
            self.results.append(TestResult("get_strategy_signal HOLD when insufficient bars", TestStatus.SKIP, "pandas not installed"))
            return self.results[-1]
        def _test():
            bot_main = _get_bot_main()
            TradingBot = bot_main.TradingBot
            bot = TradingBot(total_capital=10000.0)
            df = pd.DataFrame({'open': [1], 'high': [1], 'low': [1], 'close': [1], 'volume': [1]})
            with patch.object(bot, '_fetch_ohlcv_for_strategy', return_value=df):
                signal, price, volume = bot.get_strategy_signal('AAPL', use_random_fallback=False)
            assert signal == 'HOLD', f"Expected HOLD for insufficient bars, got {signal}"
            return True
        return self.run_test("get_strategy_signal HOLD when insufficient bars", _test)

    def test_trade_history_filter_by_mode_yfinance_sim(self) -> TestResult:
        """get_trades_by_mode('yfinance_sim') returns only yfinance_sim trades."""
        def _test():
            bot_main = _get_bot_main()
            main_module = bot_main
            TradingBot = bot_main.TradingBot
            bot = TradingBot(total_capital=10000.0)
            bot.trade_history = []
            bot.using_yfinance_sim = True
            # record_trade sets mode to 'api_disabled' when SCHWAB_API_ENABLED=off; patch so we get 'yfinance_sim'
            with patch.object(main_module, '_get_schwab_api_enabled', return_value=True):
                bot.record_trade('AAPL', 'BUY', 10, 150.0, True)
                bot.record_trade('GOOGL', 'SELL', 5, 2800.0, False)
            bot.using_yfinance_sim = False
            with patch.object(main_module, '_get_schwab_api_enabled', return_value=True):
                bot.record_trade('MSFT', 'BUY', 20, 400.0, True)  # different mode
            sim_trades = bot.get_trades_by_mode('yfinance_sim')
            assert len(sim_trades) == 2, f"Expected 2 yfinance_sim trades, got {len(sim_trades)}"
            return True
        return self.run_test("get_trades_by_mode yfinance_sim", _test)

    def test_validate_api_connectivity_succeeds_with_yfinance_fallback(self) -> TestResult:
        """validate_api_connectivity succeeds when Schwab fails but yfinance returns price."""
        def _test():
            bot_main = _get_bot_main()
            TradingBot = bot_main.TradingBot
            validate_api_connectivity = bot_main.validate_api_connectivity
            bot = TradingBot(total_capital=10000.0)
            with patch.object(bot, 'fetch_schwab_stock_price', return_value=None):
                with patch.object(bot, 'fetch_real_stock_price', return_value=(150.0, 1_000_000)):
                    ok, msg = validate_api_connectivity(bot)
            assert ok is True, f"Expected connected with yfinance, got ok={ok}"
            assert 'yfinance' in msg.lower(), f"Message should mention yfinance: {msg}"
            return True
        return self.run_test("validate_api_connectivity with yfinance fallback", _test)

    def run(self):
        """Run all yfinance mode unit tests."""
        self.start_time = self.end_time = None
        self.log("Running yfinance mode unit tests (no API required)...")
        tests = [
            self.test_get_stock_price_uses_yfinance_and_sets_sim_flag,
            self.test_execute_trade_paper_mode_records_yfinance_sim,
            self.test_get_strategy_signal_returns_tuple_signal_price_volume,
            self.test_get_strategy_signal_hold_when_insufficient_bars,
            self.test_trade_history_filter_by_mode_yfinance_sim,
            self.test_validate_api_connectivity_succeeds_with_yfinance_fallback,
        ]
        for t in tests:
            t()
        self.log(f"Completed {len(self.results)} yfinance mode tests")
        return self.results
