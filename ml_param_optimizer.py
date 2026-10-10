#!/usr/bin/env python3
"""
Parameter optimizer for the trading bot — backtest-driven heuristics.

Optimizes numeric bot settings from aggregated backtest metrics using
rule-based adjustments within documented parameter ranges. This replaces the
legacy path that asked a general-purpose LLM for JSON parameter suggestions
(no proven OOS edge for LLM param tuning).

Optional plain-English explanation of suggested changes is available via
api.services.trading_insights_llm (narrative only; never auto-applied).
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def get_decrypted_env(key: str, default: str = "") -> str:
    try:
        import main

        decrypt_func = getattr(main, "get_decrypted_env", None)
        if callable(decrypt_func):
            return decrypt_func(key, default)
    except Exception:
        pass
    return os.getenv(key, default)


class MLParameterOptimizer:
    """
    Optimize trading bot parameters from backtest aggregates (heuristic / grid-lite).
    Supports win_rate and profit_factor targets.
    """

    def __init__(
        self,
        target_win_rate: float = 0.70,
        target_metric: str = "win_rate",
        target_value: float = None,
    ):
        if target_value is None:
            self.target_metric = "win_rate"
            self.target_value = target_win_rate
        else:
            self.target_metric = target_metric
            self.target_value = target_value

        self.target_win_rate = self.target_value if self.target_metric == "win_rate" else 0.70

        self.param_ranges = {
            "BOT_RISK_THRESHOLD": (0.01, 0.05),
            "BOT_TRAILING_STOP_PERCENT": (0.02, 0.10),
            "BOT_STOP_LOSS_PERCENT": (0.03, 0.08),
            "BOT_TAKE_PROFIT_PERCENT": (0.05, 0.15),
            "BOT_MAX_CONSECUTIVE_LOSSES": (2, 5),
            "BOT_MIN_ALLOCATION": (50, 200),
            "BOT_MAX_ALLOCATION": (300, 1000),
            "TRADING_FREQUENCY": (1, 5),
            "MIN_TRAILING_STOP": (0.01, 0.05),
            "MAX_TRAILING_STOP": (0.05, 0.15),
        }

        logger.info(
            "Parameter optimizer initialized (%s target=%s, method=backtest_heuristic)",
            self.target_metric,
            self.target_value,
        )

    def is_api_configured(self) -> bool:
        """Always true — optimization does not require the LLM brain."""
        return True

    def optimize_parameters(
        self,
        backtest_results: List[Dict[str, Any]],
        current_params: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], float]:
        """
        Suggest parameters from backtest analysis (heuristic adjustments).
        """
        analysis = self._analyze_backtest_results(backtest_results)
        if analysis["num_backtests"] == 0:
            logger.warning("No backtest results — returning current parameters")
            return dict(current_params), 0.0

        optimized, predicted = self._optimize_from_backtest_analysis(analysis, current_params)
        optimized = self._validate_parameters(optimized)
        logger.info(
            "Backtest heuristic optimization complete (predicted %s=%.4f)",
            self.target_metric,
            predicted,
        )
        return optimized, predicted

    def _optimize_from_backtest_analysis(
        self,
        analysis: Dict[str, Any],
        current_params: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], float]:
        """Rule-based nudges from aggregate backtest metrics."""
        params = {k: float(v) if k != "BOT_MAX_CONSECUTIVE_LOSSES" else int(v) for k, v in current_params.items()}

        wr = analysis["avg_win_rate"]
        roi = analysis["avg_roi"]
        pf = analysis["avg_profit_factor"]
        dd = analysis["avg_max_drawdown"]
        target = self.target_value

        if self.target_metric == "profit_factor":
            if pf < target:
                params = self._nudge(params, "BOT_RISK_THRESHOLD", -0.003)
                params = self._nudge(params, "BOT_TRAILING_STOP_PERCENT", -0.005)
                params = self._nudge(params, "BOT_TAKE_PROFIT_PERCENT", 0.01)
            predicted = min(target, pf + 0.15) if pf > 0 else target * 0.5
        else:
            if wr < target:
                params = self._nudge(params, "BOT_TRAILING_STOP_PERCENT", -0.005)
                params = self._nudge(params, "BOT_STOP_LOSS_PERCENT", -0.005)
                params = self._nudge(params, "BOT_RISK_THRESHOLD", -0.002)
                params = self._nudge_int(params, "BOT_MAX_CONSECUTIVE_LOSSES", -1)
            elif wr >= target and roi < 0.03:
                params = self._nudge(params, "BOT_TAKE_PROFIT_PERCENT", 0.01)
                params = self._nudge(params, "BOT_MAX_ALLOCATION", 50.0)
            predicted = min(target, wr + min(0.08, (target - wr) * 0.5))

        if dd > 0.12:
            params = self._nudge(params, "BOT_RISK_THRESHOLD", -0.003)
            params = self._nudge(params, "BOT_STOP_LOSS_PERCENT", -0.005)

        if analysis.get("win_rate_std", 0) > 0.15:
            params = self._nudge_int(params, "TRADING_FREQUENCY", 1)

        if analysis.get("avg_sharpe", 0) < 0.5 and wr > 0:
            params = self._nudge(params, "MIN_TRAILING_STOP", 0.005)

        return params, float(predicted)

    def _nudge(self, params: Dict[str, Any], key: str, delta: float) -> Dict[str, Any]:
        if key not in self.param_ranges:
            return params
        lo, hi = self.param_ranges[key]
        cur = float(params.get(key, (lo + hi) / 2))
        params[key] = max(lo, min(hi, cur + delta))
        return params

    def _nudge_int(self, params: Dict[str, Any], key: str, delta: int) -> Dict[str, Any]:
        if key not in self.param_ranges:
            return params
        lo, hi = self.param_ranges[key]
        cur = int(params.get(key, lo))
        params[key] = max(int(lo), min(int(hi), cur + delta))
        return params

    def _analyze_backtest_results(self, backtest_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not backtest_results:
            return {
                "avg_win_rate": 0.0,
                "avg_roi": 0.0,
                "avg_profit_factor": 0.0,
                "avg_sharpe": 0.0,
                "avg_max_drawdown": 0.0,
                "num_backtests": 0,
            }

        win_rates, rois, profit_factors, sharpe_ratios, max_drawdowns = [], [], [], [], []

        for result in backtest_results:
            if "win_rate" in result:
                win_rates.append(result["win_rate"])
            elif "analyzers" in result and "win_rate" in result["analyzers"]:
                win_rates.append(result["analyzers"]["win_rate"])

            if "roi" in result:
                rois.append(result["roi"])
            elif "analyzers" in result and "total_return" in result["analyzers"]:
                rois.append(result["analyzers"]["total_return"])

            if "profit_factor" in result:
                profit_factors.append(result["profit_factor"])
            elif "analyzers" in result and "profit_factor" in result["analyzers"]:
                profit_factors.append(result["analyzers"]["profit_factor"])
            elif "trades" in result and isinstance(result["trades"], list):
                gross_profit = sum(t.get("pnl", 0) for t in result["trades"] if t.get("pnl", 0) > 0)
                gross_loss = abs(sum(t.get("pnl", 0) for t in result["trades"] if t.get("pnl", 0) < 0))
                if gross_loss > 0:
                    profit_factors.append(gross_profit / gross_loss)
                elif gross_profit > 0:
                    profit_factors.append(gross_profit)

            if "sharpe_ratio" in result:
                sharpe_ratios.append(result["sharpe_ratio"])
            elif "analyzers" in result and "sharpe_ratio" in result["analyzers"]:
                sharpe_ratios.append(result["analyzers"]["sharpe_ratio"])

            if "max_drawdown" in result:
                max_drawdowns.append(abs(result["max_drawdown"]))
            elif "analyzers" in result and "max_drawdown_pct" in result["analyzers"]:
                max_drawdowns.append(abs(result["analyzers"]["max_drawdown_pct"]))

        return {
            "avg_win_rate": float(np.mean(win_rates)) if win_rates else 0.0,
            "avg_roi": float(np.mean(rois)) if rois else 0.0,
            "avg_profit_factor": float(np.mean(profit_factors)) if profit_factors else 0.0,
            "avg_sharpe": float(np.mean(sharpe_ratios)) if sharpe_ratios else 0.0,
            "avg_max_drawdown": float(np.mean(max_drawdowns)) if max_drawdowns else 0.0,
            "num_backtests": len(backtest_results),
            "win_rate_std": float(np.std(win_rates)) if win_rates else 0.0,
            "roi_std": float(np.std(rois)) if rois else 0.0,
            "profit_factor_std": float(np.std(profit_factors)) if profit_factors else 0.0,
        }

    def _validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        validated = {}
        for key, value in params.items():
            if key not in self.param_ranges:
                continue
            lo, hi = self.param_ranges[key]
            try:
                if key in ("BOT_MAX_CONSECUTIVE_LOSSES", "TRADING_FREQUENCY", "BOT_MIN_ALLOCATION", "BOT_MAX_ALLOCATION"):
                    value = int(round(float(value)))
                else:
                    value = float(value)
            except (ValueError, TypeError):
                continue
            validated[key] = max(lo, min(hi, value)) if not isinstance(lo, int) else max(int(lo), min(int(hi), int(value)))
        return validated

    def save_optimization_result(
        self,
        params: Dict[str, Any],
        predicted_value: float,
        filename: Optional[str] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        if filename is None:
            filename = f"param_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        result: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "method": "backtest_heuristic",
            "target_metric": self.target_metric,
            "target_value": self.target_value,
            "optimized_parameters": params,
        }
        if analysis:
            result["backtest_analysis"] = analysis
        if self.target_metric == "profit_factor":
            result["predicted_profit_factor"] = predicted_value
        else:
            result["predicted_win_rate"] = predicted_value

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            logger.info("Optimization results saved to %s", filename)
            return filename
        except Exception as e:
            logger.error("Failed to save optimization results: %s", e)
            return ""
