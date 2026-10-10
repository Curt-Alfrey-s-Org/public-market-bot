"""
Yfinance regression tests — catch recently found problems so they don't recur.
No API required; uses mocks and main.py directly.
Run with: python tests/runner.py (included in full suite) or run_yfinance_tests.sh.
"""

import json
import os
import sys
import tempfile
from unittest.mock import patch

# Set env before importing main
os.environ.setdefault("PAPER_TRADING_MODE", "true")
os.environ.setdefault("SCHWAB_SANDBOX_MODE", "false")
os.environ.setdefault("SCHWAB_API_ENABLED", "off")

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


class YfinanceRegressionTest(BaseTestModule):
    """Regression tests for yfinance-mode issues found during development."""

    def __init__(self, api_base_url: str = "http://localhost:8002"):
        super().__init__("Yfinance Regression", api_base_url, timeout=30)

    def test_record_trade_mode_api_disabled_when_schwab_off(self) -> TestResult:
        """
        Regression: When SCHWAB_API_ENABLED=off, record_trade sets mode to 'api_disabled', not 'yfinance_sim'.
        Problem found: Tests expected trade['mode'] == 'yfinance_sim' but got 'api_disabled' when env was off.
        Fix: Tests that need 'yfinance_sim' must patch SCHWAB_API_ENABLED=on; this test documents the contract.
        """
        def _test():
            bot_main = _get_bot_main()
            TradingBot = bot_main.TradingBot
            bot = TradingBot(total_capital=10000.0)
            bot.trade_history = []
            bot.using_yfinance_sim = True
            # Do NOT patch SCHWAB_API_ENABLED — leave it off (default in many envs)
            bot.record_trade("AAPL", "BUY", 10, 150.0, True)
            assert len(bot.trade_history) == 1
            trade = bot.trade_history[0]
            # Contract: when api_enabled is False, record_trade uses 'api_disabled'
            assert trade.get("mode") == "api_disabled", "When SCHWAB_API_ENABLED=off, mode must be 'api_disabled'"
            assert trade.get("symbol") == "AAPL"
            return True
        return self.run_test("record_trade mode api_disabled when SCHWAB off", _test)

    def test_save_trade_history_metadata_mode_in_allowed_set(self) -> TestResult:
        """
        Regression: save_trade_history metadata['mode'] is env-derived, not per-trade; must be in allowed set.
        Problem found: Test asserted metadata['mode'] == 'yfinance_sim' but code sets api_disabled/sandbox/simulation/live.
        """
        def _test():
            bot_main = _get_bot_main()
            TradingBot = bot_main.TradingBot
            bot = TradingBot(total_capital=10000.0)
            bot.trade_history = []
            with patch.dict(os.environ, {"SCHWAB_API_ENABLED": "on"}):
                bot.using_yfinance_sim = True
                bot.record_trade("AAPL", "BUY", 10, 150.0, True)
            allowed = ("api_disabled", "sandbox", "simulation", "live")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                tmp = f.name
            try:
                bot.save_trade_history(tmp)
                with open(tmp) as f:
                    data = json.load(f)
                meta_mode = data.get("metadata", {}).get("mode")
                assert meta_mode in allowed, f"metadata['mode'] must be one of {allowed}, got {meta_mode!r}"
                assert len(data.get("trades", [])) == 1
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
            return True
        return self.run_test("save_trade_history metadata mode in allowed set", _test)

    def test_trade_filter_count_requires_isolated_history(self) -> TestResult:
        """
        Regression: When asserting get_trades_by_mode counts, bot.trade_history must be cleared first.
        Problem found: Bot loads trades from DB on init; tests that assert exact count (e.g. 2) failed with 6+.
        Fix: Tests that assert trade count or filter by mode must set bot.trade_history = [] before adding test trades.
        """
        def _test():
            bot_main = _get_bot_main()
            TradingBot = bot_main.TradingBot
            bot = TradingBot(total_capital=10000.0)
            # Isolate: clear so only our test trades are present
            bot.trade_history = []
            with patch.dict(os.environ, {"SCHWAB_API_ENABLED": "on", "PAPER_TRADING_MODE": "true", "SCHWAB_SANDBOX_MODE": "true"}):
                bot.using_yfinance_sim = True
                bot.record_trade("A", "BUY", 1, 100.0, True)
                bot.record_trade("B", "SELL", 1, 200.0, False)
            sim_trades = bot.get_trades_by_mode("yfinance_sim")
            assert len(sim_trades) == 2, "After isolating trade_history and adding 2 yfinance_sim trades, count must be 2"
            return True
        return self.run_test("trade filter count requires isolated trade_history", _test)

    def run(self):
        """Run all yfinance regression tests."""
        self.log("Running yfinance regression tests (no API required)...")
        for test_func in [
            self.test_record_trade_mode_api_disabled_when_schwab_off,
            self.test_save_trade_history_metadata_mode_in_allowed_set,
            self.test_trade_filter_count_requires_isolated_history,
        ]:
            test_func()
        self.log(f"Completed {len(self.results)} yfinance regression tests")
        return self.results
