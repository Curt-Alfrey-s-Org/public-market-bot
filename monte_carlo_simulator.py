#!/usr/bin/env python3
"""
Monte Carlo Simulation Module for market-pie5-bot

Provides probabilistic analysis for:
- Portfolio risk simulation (VaR, CVaR, drawdown)
- Strategy robustness testing (price path scenarios)
- Parameter sensitivity analysis
- Trade outcome forecasting
- Tail risk analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MonteCarloResults:
    """Container for Monte Carlo simulation results"""
    simulations: np.ndarray  # Array of simulation outcomes
    mean: float
    median: float
    std_dev: float
    percentiles: Dict[str, float]  # {5, 25, 50, 75, 95}
    var_95: float  # Value at Risk at 95% confidence
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    max_value: float
    min_value: float
    success_rate: float  # Percentage of positive outcomes


class MonteCarloSimulator:
    """
    Monte Carlo simulation framework for trading analysis
    
    Provides probabilistic analysis to complement backtesting
    with scenario-based risk assessment.
    """
    
    def __init__(self, num_simulations: int = 10000, random_seed: Optional[int] = None):
        """
        Initialize Monte Carlo simulator
        
        Args:
            num_simulations: Number of Monte Carlo paths to generate
            random_seed: Random seed for reproducibility (optional)
        """
        self.num_simulations = num_simulations
        self.random_seed = random_seed
        
        # Use per-instance RNG instead of global seed
        self.rng = np.random.default_rng(random_seed)
        
        logger.info(f"Initialized MonteCarloSimulator (simulations={num_simulations}, seed={random_seed})")
    
    def simulate_price_paths(
        self,
        initial_price: float,
        days: int,
        drift: float,
        volatility: float,
        num_paths: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate price paths using Geometric Brownian Motion (GBM)
        
        Models stock prices as: dS = μS dt + σS dW
        where μ is drift, σ is volatility, W is Wiener process
        
        Args:
            initial_price: Starting price
            days: Number of trading days to simulate
            drift: Expected daily return (annualized / 252)
            volatility: Daily volatility (annualized / sqrt(252))
            num_paths: Number of paths (defaults to num_simulations)
            
        Returns:
            Array of shape (num_paths, days + 1) with simulated prices, where:
                - column 0 is the initial price (time 0)
                - columns 1..days are the simulated prices for each subsequent day
        """
        if num_paths is None:
            num_paths = self.num_simulations
        
        # Time step
        dt = 1.0
        
        # Generate random returns using GBM
        # S(t+dt) = S(t) * exp((μ - σ²/2)dt + σ√dt * Z)
        # where Z ~ N(0,1)
        
        random_shocks = self.rng.standard_normal((num_paths, days))
        
        # Calculate returns for each time step
        returns = (drift - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * random_shocks
        
        # Calculate cumulative returns and apply to initial price
        cumulative_returns = np.cumsum(returns, axis=1)
        price_paths = initial_price * np.exp(cumulative_returns)
        
        # Add initial price as first column
        price_paths = np.column_stack([np.full(num_paths, initial_price), price_paths])
        
        logger.debug(f"Generated {num_paths} price paths over {days} days")
        return price_paths
    
    def simulate_portfolio_returns(
        self,
        initial_capital: float,
        positions: List[Dict],
        drift: float = 0.0005,
        volatility: float = 0.02,
        days: int = 252,
        num_simulations: Optional[int] = None
    ) -> MonteCarloResults:
        """
        Simulate portfolio returns using Monte Carlo
        
        Args:
            initial_capital: Starting capital
            positions: List of positions with 'symbol', 'shares', 'current_price'
            drift: Expected daily return (default: 0.05% or ~13% annualized)
            volatility: Daily volatility (default: 2% or ~32% annualized)
            days: Trading days to simulate (default: 252 = 1 year)
            num_simulations: Number of simulations (defaults to self.num_simulations)
            
        Returns:
            MonteCarloResults object with portfolio outcome statistics
        """
        if num_simulations is None:
            num_simulations = self.num_simulations
        
        if not positions:
            # Empty portfolio - return cash only
            simulations = np.full(num_simulations, initial_capital)
            return self._create_results(simulations)
        
        # Calculate current portfolio value
        position_values = []
        for pos in positions:
            shares = pos.get('shares', 0)
            price = pos.get('current_price', 0)
            position_values.append(shares * price)
        
        total_position_value = sum(position_values)
        cash = initial_capital - total_position_value
        
        # Simulate each position independently
        final_values = np.zeros(num_simulations)
        
        for i, pos in enumerate(positions):
            initial_price = pos.get('current_price', 100.0)
            shares = pos.get('shares', 0)
            
            # Simulate price paths for this position
            price_paths = self.simulate_price_paths(
                initial_price=initial_price,
                days=days,
                drift=drift,
                volatility=volatility,
                num_paths=num_simulations
            )
            
            # Get final prices (last column)
            final_prices = price_paths[:, -1]
            
            # Add position value to total
            final_values += shares * final_prices
        
        # Add cash to final values
        final_values += cash
        
        logger.info(f"Simulated portfolio returns: mean=${np.mean(final_values):.2f}, "
                   f"std=${np.std(final_values):.2f}")
        
        return self._create_results(final_values)
    
    def simulate_var_cvar(
        self,
        initial_capital: float,
        expected_return: float,
        volatility: float,
        days: int = 1,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate Value at Risk (VaR) and Conditional VaR (CVaR) using Monte Carlo
        
        VaR: Maximum expected loss at given confidence level (positive number)
        CVaR: Expected loss beyond VaR threshold (tail risk, positive number)
        
        Args:
            initial_capital: Starting capital
            expected_return: Expected daily return
            volatility: Daily volatility
            days: Time horizon in days (default: 1 day)
            confidence_level: Confidence level (default: 0.95 = 95%)
            
        Returns:
            Tuple of (VaR, CVaR) as positive loss amounts in dollars
        """
        # Generate random terminal values using GBM / lognormal returns
        # Under GBM, log-return over `days` is normally distributed:
        #   log(S_T / S_0) ~ N((μ - 0.5 * σ^2) * days, (σ * sqrt(days))^2)
        # where μ is expected daily return and σ is daily volatility.
        drift = (expected_return - 0.5 * volatility ** 2) * days
        diffusion = volatility * np.sqrt(days)
        log_returns = self.rng.normal(drift, diffusion, self.num_simulations)

        # Calculate portfolio values (always positive under GBM)
        final_values = initial_capital * np.exp(log_returns)
        losses = initial_capital - final_values
        
        # VaR: percentile of losses (positive number representing potential loss)
        loss_quantile = np.percentile(losses, confidence_level * 100)
        var = max(float(loss_quantile), 0.0)
        
        # CVaR: mean of losses exceeding VaR threshold (tail risk)
        tail_losses = losses[losses >= loss_quantile]
        cvar_raw = np.mean(tail_losses) if len(tail_losses) > 0 else loss_quantile
        cvar = max(float(cvar_raw), 0.0)
        
        logger.debug(f"VaR {confidence_level:.0%}: ${var:.2f}, CVaR: ${cvar:.2f}")
        
        return var, cvar
    
    def simulate_strategy_robustness(
        self,
        strategy_func: Callable,
        initial_price: float,
        days: int,
        drift_range: Tuple[float, float],
        volatility_range: Tuple[float, float],
        num_scenarios: Optional[int] = None
    ) -> Dict:
        """
        Test strategy performance across various market scenarios
        
        Args:
            strategy_func: Trading strategy function that takes price_path and returns P&L
            initial_price: Starting price
            days: Number of days to simulate
            drift_range: (min_drift, max_drift) for sampling
            volatility_range: (min_vol, max_vol) for sampling
            num_scenarios: Number of scenarios to test (defaults to num_simulations)
            
        Returns:
            Dictionary with robustness metrics
        """
        if num_scenarios is None:
            num_scenarios = self.num_simulations
        
        # Sample market parameters
        drifts = self.rng.uniform(drift_range[0], drift_range[1], num_scenarios)
        volatilities = self.rng.uniform(volatility_range[0], volatility_range[1], num_scenarios)
        
        pnl_results = []
        
        for drift, volatility in zip(drifts, volatilities):
            # Generate price path
            price_path = self.simulate_price_paths(
                initial_price=initial_price,
                days=days,
                drift=drift,
                volatility=volatility,
                num_paths=1
            )[0]
            
            # Apply strategy and record P&L
            try:
                pnl = strategy_func(price_path)
                pnl_results.append(pnl)
            except Exception as e:
                logger.warning(f"Strategy failed on scenario: {e}")
                pnl_results.append(0)
        
        pnl_array = np.array(pnl_results)
        
        return {
            'mean_pnl': np.mean(pnl_array),
            'median_pnl': np.median(pnl_array),
            'std_pnl': np.std(pnl_array),
            'positive_scenarios': np.sum(pnl_array > 0) / len(pnl_array),
            'max_pnl': np.max(pnl_array),
            'min_pnl': np.min(pnl_array),
            'sharpe_ratio': np.mean(pnl_array) / np.std(pnl_array) if np.std(pnl_array) > 0 else 0,
            'scenarios_tested': num_scenarios
        }
    
    def simulate_drawdown_distribution(
        self,
        initial_capital: float,
        expected_return: float,
        volatility: float,
        days: int = 252
    ) -> Dict:
        """
        Simulate maximum drawdown distribution
        
        Args:
            initial_capital: Starting capital
            expected_return: Expected daily return
            volatility: Daily volatility
            days: Trading days to simulate (default: 252 = 1 year)
            
        Returns:
            Dictionary with drawdown statistics
        """
        # Vectorized simulation over all paths to avoid Python loop overhead
        returns = self.rng.normal(
            loc=expected_return,
            scale=volatility,
            size=(self.num_simulations, days),
        )

        # Calculate cumulative portfolio value for each simulation
        portfolio_values = initial_capital * np.cumprod(1 + returns, axis=1)

        # Calculate drawdown at each point for each simulation
        running_max = np.maximum.accumulate(portfolio_values, axis=1)
        drawdowns = (portfolio_values - running_max) / running_max

        # Record maximum drawdown per simulation (most negative value)
        dd_array = np.min(drawdowns, axis=1)
        
        return {
            'mean_max_drawdown': np.mean(dd_array),
            'median_max_drawdown': np.median(dd_array),
            'worst_drawdown_95': np.percentile(dd_array, 5),  # Worst 5%
            'worst_drawdown_99': np.percentile(dd_array, 1),  # Worst 1%
            'best_drawdown': np.max(dd_array),
            'prob_drawdown_over_20pct': np.sum(dd_array < -0.20) / len(dd_array)
        }
    
    def simulate_trade_outcomes(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        num_trades: int
    ) -> MonteCarloResults:
        """
        Simulate sequence of trades based on historical statistics
        
        Args:
            win_rate: Historical win rate (e.g., 0.55 for 55%)
            avg_win: Average winning trade P&L
            avg_loss: Average losing trade P&L (negative value)
            num_trades: Number of trades to simulate
            
        Returns:
            MonteCarloResults with cumulative P&L distribution
        """
        cumulative_pnl = []
        
        for _ in range(self.num_simulations):
            pnl = 0
            for _ in range(num_trades):
                if self.rng.random() < win_rate:
                    pnl += avg_win
                else:
                    pnl += avg_loss
            cumulative_pnl.append(pnl)
        
        return self._create_results(np.array(cumulative_pnl))
    
    def parameter_sensitivity_analysis(
        self,
        base_params: Dict,
        param_ranges: Dict[str, Tuple[float, float]],
        evaluation_func: Callable,
        num_samples: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Analyze strategy sensitivity to parameter variations
        
        Args:
            base_params: Base parameter values
            param_ranges: Dict of {param_name: (min, max)}
            evaluation_func: Function that takes params dict and returns performance metric
            num_samples: Number of parameter combinations to test
            
        Returns:
            DataFrame with parameter values and performance metrics
        """
        if num_samples is None:
            num_samples = min(self.num_simulations, 1000)  # Cap at 1000 for efficiency
        
        results = []
        
        for _ in range(num_samples):
            # Sample parameters
            sampled_params = base_params.copy()
            for param_name, (min_val, max_val) in param_ranges.items():
                sampled_params[param_name] = self.rng.uniform(min_val, max_val)
            
            # Evaluate
            try:
                performance = evaluation_func(sampled_params)
                result = sampled_params.copy()
                result['performance'] = performance
                results.append(result)
            except Exception as e:
                logger.warning(f"Evaluation failed: {e}")
        
        df = pd.DataFrame(results)
        
        logger.info(f"Completed parameter sensitivity analysis: {len(df)} samples")
        return df
    
    def _create_results(self, simulations: np.ndarray) -> MonteCarloResults:
        """
        Create MonteCarloResults from simulation array
        
        Args:
            simulations: Array of simulation outcomes
            
        Returns:
            MonteCarloResults object
        """
        return MonteCarloResults(
            simulations=simulations,
            mean=np.mean(simulations),
            median=np.median(simulations),
            std_dev=np.std(simulations),
            percentiles={
                'p5': np.percentile(simulations, 5),
                'p25': np.percentile(simulations, 25),
                'p50': np.percentile(simulations, 50),
                'p75': np.percentile(simulations, 75),
                'p95': np.percentile(simulations, 95)
            },
            var_95=np.percentile(simulations, 5),  # 5th percentile is VaR at 95% confidence
            cvar_95=np.mean(simulations[simulations <= np.percentile(simulations, 5)]),
            max_value=np.max(simulations),
            min_value=np.min(simulations),
            success_rate=np.sum(simulations > 0) / len(simulations)
        )
    
    def generate_report(self, results: MonteCarloResults, title: str = "Monte Carlo Simulation") -> str:
        """
        Generate human-readable report from simulation results
        
        Args:
            results: MonteCarloResults object
            title: Report title
            
        Returns:
            Formatted string report
        """
        report = f"\n{'='*60}\n"
        report += f"{title}\n"
        report += f"{'='*60}\n\n"
        report += f"Number of Simulations: {len(results.simulations):,}\n\n"
        report += f"Expected Value (Mean):  ${results.mean:,.2f}\n"
        report += f"Median Outcome:         ${results.median:,.2f}\n"
        report += f"Standard Deviation:     ${results.std_dev:,.2f}\n\n"
        report += f"Percentile Distribution:\n"
        report += f"  5th percentile (VaR):  ${results.percentiles['p5']:,.2f}\n"
        report += f"  25th percentile:       ${results.percentiles['p25']:,.2f}\n"
        report += f"  50th percentile:       ${results.percentiles['p50']:,.2f}\n"
        report += f"  75th percentile:       ${results.percentiles['p75']:,.2f}\n"
        report += f"  95th percentile:       ${results.percentiles['p95']:,.2f}\n\n"
        report += f"Risk Metrics:\n"
        report += f"  Value at Risk (95%):   ${results.var_95:,.2f}\n"
        report += f"  CVaR (95%):            ${results.cvar_95:,.2f}\n\n"
        report += f"Range:\n"
        report += f"  Best case:             ${results.max_value:,.2f}\n"
        report += f"  Worst case:            ${results.min_value:,.2f}\n"
        report += f"  Range:                 ${results.max_value - results.min_value:,.2f}\n\n"
        report += f"Success Rate:            {results.success_rate:.2%}\n"
        report += f"{'='*60}\n"
        
        return report


# Example usage demonstration
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("Monte Carlo Simulator Demo\n")
    
    # Initialize simulator
    mc = MonteCarloSimulator(num_simulations=10000, random_seed=42)
    
    # Example 1: Portfolio returns simulation
    print("\n[EXAMPLE 1] Portfolio Returns Simulation")
    print("-" * 60)
    
    positions = [
        {'symbol': 'AAPL', 'shares': 10, 'current_price': 150.0},
        {'symbol': 'GOOGL', 'shares': 5, 'current_price': 140.0}
    ]
    
    results = mc.simulate_portfolio_returns(
        initial_capital=10000.0,
        positions=positions,
        drift=0.0005,  # 0.05% daily return
        volatility=0.02,  # 2% daily volatility
        days=252  # 1 year
    )
    
    print(mc.generate_report(results, "1-Year Portfolio Projection"))
    
    # Example 2: VaR and CVaR
    print("\n[EXAMPLE 2] Value at Risk (VaR) and CVaR")
    print("-" * 60)
    
    var_95, cvar_95 = mc.simulate_var_cvar(
        initial_capital=10000.0,
        expected_return=0.0005,
        volatility=0.02,
        days=1,
        confidence_level=0.95
    )
    
    print(f"1-Day VaR (95% confidence): ${var_95:.2f}")
    print(f"1-Day CVaR (Expected Shortfall): ${cvar_95:.2f}")
    print(f"Interpretation: 95% of days, losses will not exceed ${var_95:.2f}")
    print(f"               If losses exceed VaR, expect ${cvar_95:.2f} average loss")
    
    # Example 3: Drawdown distribution
    print("\n[EXAMPLE 3] Maximum Drawdown Distribution")
    print("-" * 60)
    
    dd_results = mc.simulate_drawdown_distribution(
        initial_capital=10000.0,
        expected_return=0.0005,
        volatility=0.02,
        days=252
    )
    
    print(f"Mean Maximum Drawdown:      {dd_results['mean_max_drawdown']:.2%}")
    print(f"Median Maximum Drawdown:    {dd_results['median_max_drawdown']:.2%}")
    print(f"Worst Drawdown (95th):      {dd_results['worst_drawdown_95']:.2%}")
    print(f"Worst Drawdown (99th):      {dd_results['worst_drawdown_99']:.2%}")
    print(f"Prob(Drawdown > 20%):       {dd_results['prob_drawdown_over_20pct']:.2%}")
    
    # Example 4: Trade outcome simulation
    print("\n[EXAMPLE 4] Trade Outcome Simulation")
    print("-" * 60)
    
    trade_results = mc.simulate_trade_outcomes(
        win_rate=0.55,
        avg_win=200.0,
        avg_loss=-150.0,
        num_trades=100,
        risk_per_trade=0.02
    )
    
    print(mc.generate_report(trade_results, "100-Trade Sequence Projection"))
    
    print("\n✅ Monte Carlo simulation demo complete!")
