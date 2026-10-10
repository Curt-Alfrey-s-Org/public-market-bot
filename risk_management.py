#!/usr/bin/env python3
"""
Risk Management Module for market-pie5-bot
Provides position sizing, risk/reward calculations, and portfolio risk management
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Try to import Monte Carlo simulator for advanced risk analysis
try:
    from monte_carlo_simulator import MonteCarloSimulator
    MONTE_CARLO_AVAILABLE = True
except ImportError:
    MONTE_CARLO_AVAILABLE = False
    logger.warning("monte_carlo_simulator not available - advanced risk simulation disabled")


class RiskManager:
    """
    Risk management system for trading decisions
    Handles position sizing, risk/reward analysis, and portfolio risk
    """
    
    def __init__(self, total_capital: float, risk_per_trade: float = 0.02):
        """
        Initialize Risk Manager
        
        Args:
            total_capital: Total available capital
            risk_per_trade: Maximum risk per trade as decimal (default: 0.02 = 2%)
        """
        self.total_capital = total_capital
        self.risk_per_trade = risk_per_trade
        self.max_portfolio_risk = 0.06  # Max 6% portfolio risk
        self.max_position_size = 0.20  # Max 20% of capital in single position
        
        # Initialize Monte Carlo simulator if available
        self.mc_simulator = None
        if MONTE_CARLO_AVAILABLE:
            try:
                self.mc_simulator = MonteCarloSimulator(num_simulations=10000, random_seed=None)
                logger.info("Monte Carlo simulator initialized for advanced risk analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize Monte Carlo simulator: {e}")
        
        logger.info(f"Initialized RiskManager (capital=${total_capital:.2f}, risk_per_trade={risk_per_trade:.2%})")
    
    def calculate_position_size_fixed_risk(self, entry_price: float, stop_loss_price: float) -> Dict:
        """
        Calculate position size based on fixed risk amount
        
        Uses the formula: Position Size = (Risk Amount) / (Entry Price - Stop Loss Price)
        
        Args:
            entry_price: Entry price per share
            stop_loss_price: Stop loss price per share
            
        Returns:
            Dictionary with position sizing details
        """
        # Validate inputs
        if entry_price <= 0:
            logger.error(f"Invalid entry_price: {entry_price} (must be positive)")
            return {
                'position_size': 0,
                'shares': 0,
                'position_value': 0,
                'risk_amount': 0,
                'error': 'Entry price must be positive'
            }
        
        if stop_loss_price <= 0:
            logger.error(f"Invalid stop_loss_price: {stop_loss_price} (must be positive)")
            return {
                'position_size': 0,
                'shares': 0,
                'position_value': 0,
                'risk_amount': 0,
                'error': 'Stop loss price must be positive'
            }
        
        # Calculate risk amount per trade
        risk_amount = self.total_capital * self.risk_per_trade
        
        # Calculate risk per share (use absolute value to handle both long and short positions)
        risk_per_share = abs(entry_price - stop_loss_price)
        
        if risk_per_share <= 0:
            logger.warning("Invalid risk per share (must be positive)")
            return {
                'position_size': 0,
                'shares': 0,
                'position_value': 0,
                'risk_amount': risk_amount,
                'error': 'Invalid stop loss price'
            }
        
        # Calculate number of shares
        shares = risk_amount / risk_per_share
        
        # Calculate position value
        position_value = shares * entry_price
        
        # Check if position exceeds max size
        max_position_value = self.total_capital * self.max_position_size
        if position_value > max_position_value:
            # Scale down to max position size
            shares = max_position_value / entry_price
            position_value = max_position_value
            actual_risk = shares * risk_per_share
            logger.warning(f"Position size capped at {self.max_position_size:.0%} of capital")
        else:
            actual_risk = risk_amount
        
        result = {
            'shares': shares,
            'position_value': position_value,
            'position_size_pct': (position_value / self.total_capital) * 100,
            'risk_amount': actual_risk,
            'risk_pct': (actual_risk / self.total_capital) * 100,
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price,
            'risk_per_share': risk_per_share
        }
        
        logger.debug(f"Position size: {shares:.2f} shares (${position_value:.2f}, risk=${actual_risk:.2f})")
        
        return result
    
    def calculate_position_size_pct_capital(self, entry_price: float, 
                                           allocation_pct: float = 0.10) -> Dict:
        """
        Calculate position size as percentage of capital
        
        Args:
            entry_price: Entry price per share
            allocation_pct: Percentage of capital to allocate (default: 0.10 = 10%)
            
        Returns:
            Dictionary with position sizing details
        """
        # Ensure allocation doesn't exceed max
        allocation_pct = min(allocation_pct, self.max_position_size)
        
        # Calculate position value
        position_value = self.total_capital * allocation_pct
        
        # Calculate number of shares
        shares = position_value / entry_price
        
        result = {
            'shares': shares,
            'position_value': position_value,
            'position_size_pct': allocation_pct * 100,
            'entry_price': entry_price
        }
        
        logger.debug(f"Position size: {shares:.2f} shares (${position_value:.2f}, {allocation_pct:.1%} of capital)")
        
        return result
    
    def calculate_risk_reward_ratio(self, entry_price: float, stop_loss_price: float,
                                    target_price: float) -> Dict:
        """
        Calculate risk/reward ratio for a trade
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            target_price: Target/take-profit price
            
        Returns:
            Dictionary with risk/reward analysis
        """
        # Calculate risk (entry to stop loss)
        risk = abs(entry_price - stop_loss_price)
        risk_pct = (risk / entry_price) * 100
        
        # Calculate reward (entry to target)
        reward = abs(target_price - entry_price)
        reward_pct = (reward / entry_price) * 100
        
        # Calculate risk/reward ratio
        if risk > 0:
            rr_ratio = reward / risk
        else:
            rr_ratio = 0
        
        # Determine if trade is favorable (min 1:2 risk/reward)
        is_favorable = rr_ratio >= 2.0
        
        result = {
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price,
            'target_price': target_price,
            'risk': risk,
            'risk_pct': risk_pct,
            'reward': reward,
            'reward_pct': reward_pct,
            'risk_reward_ratio': rr_ratio,
            'is_favorable': is_favorable,
            'recommendation': 'TAKE TRADE' if is_favorable else 'SKIP TRADE'
        }
        
        logger.debug(f"Risk/Reward: 1:{rr_ratio:.2f} ({result['recommendation']})")
        
        return result
    
    def calculate_kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate optimal position size using Kelly Criterion
        
        Formula: f* = (bp - q) / b
        where:
        - f* = optimal fraction of capital
        - b = odds received on the bet (avg_win / avg_loss)
        - p = probability of winning (win_rate)
        - q = probability of losing (1 - win_rate)
        
        Args:
            win_rate: Win rate as decimal (e.g., 0.6 for 60%)
            avg_win: Average win amount
            avg_loss: Average loss amount
            
        Returns:
            Optimal position size as decimal
        """
        if avg_loss <= 0:
            logger.error(f"Kelly Criterion: Invalid average loss ({avg_loss}) - must be positive. Returning 0.")
            return 0.0
        
        # Calculate odds
        b = avg_win / avg_loss
        
        # Calculate Kelly percentage
        kelly_pct = (b * win_rate - (1 - win_rate)) / b
        
        # Apply half-Kelly for more conservative sizing
        kelly_pct = kelly_pct * 0.5
        
        # Ensure within reasonable bounds
        kelly_pct = max(0.0, min(kelly_pct, self.max_position_size))
        
        logger.debug(f"Kelly Criterion: {kelly_pct:.2%} of capital")
        
        return kelly_pct
    
    def calculate_position_size_with_earnings_adjustment(
        self,
        base_position_size: float,
        symbol: str,
        earnings_calendar = None
    ) -> float:
        """
        Adjust position size based on upcoming earnings
        
        Args:
            base_position_size: Base position size in dollars
            symbol: Stock symbol
            earnings_calendar: EarningsCalendar instance (optional)
            
        Returns:
            Adjusted position size in dollars
        """
        if earnings_calendar is None:
            # No earnings calendar, return base size
            return base_position_size
        
        try:
            adjustment_multiplier = earnings_calendar.get_position_size_adjustment(symbol)
            adjusted_size = base_position_size * adjustment_multiplier
            
            if adjustment_multiplier < 1.0:
                logger.info(f"{symbol}: Earnings adjustment {adjustment_multiplier:.0%} (${base_position_size:.2f} → ${adjusted_size:.2f})")
            
            return adjusted_size
        except Exception as e:
            logger.debug(f"Error adjusting position size for earnings: {e}")
            return base_position_size
    
    def assess_portfolio_risk(self, positions: Dict) -> Dict:
        """
        Assess overall portfolio risk from open positions
        
        Args:
            positions: Dictionary of open positions with risk amounts
            
        Returns:
            Dictionary with portfolio risk assessment
        """
        if not positions:
            return {
                'total_positions': 0,
                'total_risk': 0,
                'total_risk_pct': 0,
                'max_risk_exceeded': False,
                'can_open_new': True
            }
        
        # Calculate total risk across all positions
        total_risk = 0
        position_values = []
        
        for symbol, position in positions.items():
            risk_amount = position.get('risk_amount', 0)
            position_value = position.get('position_value', 0)
            
            total_risk += risk_amount
            position_values.append(position_value)
        
        # Calculate portfolio metrics
        total_risk_pct = (total_risk / self.total_capital) * 100
        total_exposure = sum(position_values)
        total_exposure_pct = (total_exposure / self.total_capital) * 100
        
        # Check if max portfolio risk exceeded
        max_risk_exceeded = total_risk_pct > (self.max_portfolio_risk * 100)
        
        # Check if we can open new positions
        can_open_new = not max_risk_exceeded
        
        result = {
            'total_positions': len(positions),
            'total_risk': total_risk,
            'total_risk_pct': total_risk_pct,
            'total_exposure': total_exposure,
            'total_exposure_pct': total_exposure_pct,
            'max_risk_exceeded': max_risk_exceeded,
            'max_risk_pct': self.max_portfolio_risk * 100,
            'can_open_new': can_open_new
        }
        
        if max_risk_exceeded:
            logger.warning(f"Portfolio risk {total_risk_pct:.2f}% exceeds max {self.max_portfolio_risk:.2%}")
        
        return result
    
    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted return)
        
        Sharpe Ratio = (Average Return - Risk Free Rate) / Standard Deviation of Returns
        
        Args:
            returns: Array of returns
            risk_free_rate: Risk-free rate (annualized)
            
        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        sharpe = (avg_return - risk_free_rate) / std_return
        
        logger.debug(f"Sharpe Ratio: {sharpe:.3f}")
        
        return sharpe
    
    def calculate_max_drawdown(self, equity_curve: np.ndarray) -> Dict:
        """
        Calculate maximum drawdown from equity curve
        
        Args:
            equity_curve: Array of equity values over time
            
        Returns:
            Dictionary with drawdown analysis
        """
        if len(equity_curve) < 2:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'drawdown_duration': 0
            }
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_curve)
        
        # Calculate drawdown
        drawdown = running_max - equity_curve
        drawdown_pct = (drawdown / running_max) * 100
        
        # Find maximum drawdown
        max_dd = np.max(drawdown)
        max_dd_pct = np.max(drawdown_pct)
        
        # Find drawdown duration (simplified)
        max_dd_idx = np.argmax(drawdown)
        peak_idx = np.argmax(equity_curve[:max_dd_idx+1])
        duration = max_dd_idx - peak_idx
        
        result = {
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd_pct,
            'drawdown_duration': duration,
            'current_drawdown': drawdown[-1],
            'current_drawdown_pct': drawdown_pct[-1]
        }
        
        logger.debug(f"Max Drawdown: {max_dd_pct:.2f}% over {duration} periods")
        
        return result
    
    def calculate_var(self, returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) at given confidence level
        
        VaR estimates the potential loss at a given confidence level
        
        Args:
            returns: Array of returns
            confidence_level: Confidence level (default: 0.95 = 95%)
            
        Returns:
            VaR value (positive number representing potential loss)
        """
        if len(returns) < 2:
            return 0.0
        
        # Calculate VaR using historical method
        var = np.percentile(returns, (1 - confidence_level) * 100)
        
        logger.debug(f"VaR ({confidence_level:.0%}): {var:.4f}")
        
        # Return as positive number (potential loss)
        return abs(var)
    
    def validate_trade(self, entry_price: float, stop_loss_price: float,
                      target_price: Optional[float] = None,
                      current_positions: Optional[Dict] = None,
                      symbol: Optional[str] = None,
                      action: Optional[str] = 'BUY',
                      pdt_checker: Optional[callable] = None,
                      holding_period_checker: Optional[callable] = None) -> Dict:
        """
        Comprehensive trade validation
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            target_price: Target price (optional)
            current_positions: Dictionary of current positions (optional)
            symbol: Trading symbol (optional, required for PDT/holding checks)
            action: Trade action - 'BUY' or 'SELL' (optional, default 'BUY')
            pdt_checker: Optional callable that returns (can_trade: bool, message: str) for PDT compliance
            holding_period_checker: Optional callable that returns (can_trade: bool, message: str) for holding period
            
        Returns:
            Dictionary with validation results including all reasons and warnings
        """
        validation = {
            'is_valid': True,
            'reasons': [],
            'warnings': []
        }
        
        # 1. Check position sizing
        position_size = self.calculate_position_size_fixed_risk(entry_price, stop_loss_price)
        
        if 'error' in position_size:
            validation['is_valid'] = False
            validation['reasons'].append(position_size['error'])
            # Continue checking other validations instead of returning early
        
        # 2. Check risk per trade
        if 'error' not in position_size and position_size['risk_pct'] > (self.risk_per_trade * 100):
            validation['warnings'].append(f"Risk exceeds {self.risk_per_trade:.1%} per trade limit")
        
        # 3. Check risk/reward if target provided
        if target_price is not None:
            rr = self.calculate_risk_reward_ratio(entry_price, stop_loss_price, target_price)
            
            if not rr['is_favorable']:
                validation['warnings'].append(f"Risk/Reward ratio {rr['risk_reward_ratio']:.2f} is unfavorable (< 2.0)")
        
        # 4. Check portfolio risk if positions provided
        if current_positions is not None:
            portfolio_risk = self.assess_portfolio_risk(current_positions)
            
            if not portfolio_risk['can_open_new']:
                validation['is_valid'] = False
                validation['reasons'].append(f"Portfolio risk {portfolio_risk['total_risk_pct']:.2f}% exceeds max")
        
        # 5. Check PDT compliance if checker provided (for BUY actions)
        if pdt_checker is not None and action and action.upper() == 'BUY':
            try:
                can_trade_pdt, pdt_msg = pdt_checker()
                if not can_trade_pdt:
                    validation['is_valid'] = False
                    validation['reasons'].append(f"PDT violation: {pdt_msg}")
            except Exception as e:
                logger.error(f"Error checking PDT compliance: {e}")
                validation['warnings'].append(f"PDT check failed: {str(e)}")
        
        # 6. Check holding period if checker provided (for SELL actions)
        if holding_period_checker is not None and symbol and action and action.upper() == 'SELL':
            try:
                can_trade_hold, hold_msg = holding_period_checker(symbol, action)
                if not can_trade_hold:
                    validation['is_valid'] = False
                    validation['reasons'].append(f"Holding period not met: {hold_msg}")
            except Exception as e:
                logger.error(f"Error checking holding period: {e}")
                validation['warnings'].append(f"Holding period check failed: {str(e)}")
        
        # Add summary
        if validation['is_valid']:
            if validation['warnings']:
                validation['summary'] = f"Trade passes validation with {len(validation['warnings'])} warning(s)"
            else:
                validation['summary'] = 'Trade passes validation'
        else:
            validation['summary'] = 'Trade failed validation: ' + ', '.join(validation['reasons'])
        
        return validation
    
    def calculate_monte_carlo_var(
        self,
        expected_return: float,
        volatility: float,
        days: int = 1,
        confidence_level: float = 0.95
    ) -> Optional[Tuple[float, float]]:
        """
        Calculate Value at Risk (VaR) and Conditional VaR using Monte Carlo simulation
        
        VaR and CVaR are returned as positive loss amounts (matching RiskManager.calculate_var convention)
        
        Args:
            expected_return: Expected daily return (e.g., 0.0005 for 0.05%)
            volatility: Daily volatility (e.g., 0.02 for 2%)
            days: Time horizon in days (default: 1 day)
            confidence_level: Confidence level (default: 0.95 for 95%)
            
        Returns:
            Tuple of (VaR, CVaR) as positive loss amounts in dollars, or None if unavailable
        """
        if not self.mc_simulator:
            logger.warning("Monte Carlo simulator not available for VaR calculation")
            return None
        
        try:
            var, cvar = self.mc_simulator.simulate_var_cvar(
                initial_capital=self.total_capital,
                expected_return=expected_return,
                volatility=volatility,
                days=days,
                confidence_level=confidence_level
            )
            
            logger.info(f"Monte Carlo VaR ({confidence_level:.0%}, {days}d): ${var:.2f}, CVaR: ${cvar:.2f}")
            return var, cvar
        except Exception as e:
            logger.error(f"Failed to calculate Monte Carlo VaR: {e}")
            return None
    
    def simulate_portfolio_risk(
        self,
        positions: List[Dict],
        drift: float = 0.0005,
        volatility: float = 0.02,
        days: int = 252
    ) -> Optional[Dict]:
        """
        Simulate portfolio returns using Monte Carlo
        
        Args:
            positions: List of positions with 'symbol', 'shares', 'current_price'
            drift: Expected daily return (default: 0.05% or ~13% annualized)
            volatility: Daily volatility (default: 2% or ~32% annualized)
            days: Trading days to simulate (default: 252 = 1 year)
            
        Returns:
            Dictionary with simulation results or None if unavailable
        """
        if not self.mc_simulator:
            logger.warning("Monte Carlo simulator not available for portfolio simulation")
            return None
        
        try:
            results = self.mc_simulator.simulate_portfolio_returns(
                initial_capital=self.total_capital,
                positions=positions,
                drift=drift,
                volatility=volatility,
                days=days
            )
            
            # Compute loss-based VaR and CVaR relative to initial capital
            var_95_loss = max(0.0, self.total_capital - results.var_95)
            cvar_95_loss = max(0.0, self.total_capital - results.cvar_95)
            
            # Convert to dictionary format
            return {
                'mean': results.mean,
                'median': results.median,
                'std_dev': results.std_dev,
                'percentiles': results.percentiles,
                # Loss-based VaR/CVaR (positive numbers represent potential losses)
                'var_95_loss': var_95_loss,
                'cvar_95_loss': cvar_95_loss,
                # Value-based percentiles for reference
                'var_95': results.var_95,  # 5th percentile portfolio value
                'cvar_95': results.cvar_95,  # Mean of worst 5% outcomes
                'max_value': results.max_value,
                'min_value': results.min_value,
                'success_rate': results.success_rate,
                'simulations': len(results.simulations)
            }
        except Exception as e:
            logger.error(f"Failed to simulate portfolio risk: {e}")
            return None
    
    def estimate_drawdown_risk(
        self,
        expected_return: float,
        volatility: float,
        days: int = 252
    ) -> Optional[Dict]:
        """
        Estimate maximum drawdown distribution using Monte Carlo
        
        Args:
            expected_return: Expected daily return
            volatility: Daily volatility
            days: Trading days to simulate (default: 252 = 1 year)
            
        Returns:
            Dictionary with drawdown statistics or None if unavailable
        """
        if not self.mc_simulator:
            logger.warning("Monte Carlo simulator not available for drawdown estimation")
            return None
        
        try:
            dd_results = self.mc_simulator.simulate_drawdown_distribution(
                initial_capital=self.total_capital,
                expected_return=expected_return,
                volatility=volatility,
                days=days
            )
            
            logger.info(f"Monte Carlo Drawdown: Mean={dd_results['mean_max_drawdown']:.2%}, "
                       f"95th={dd_results['worst_drawdown_95']:.2%}")
            
            return dd_results
        except Exception as e:
            logger.error(f"Failed to estimate drawdown risk: {e}")
            return None


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Risk Management Module - Example Usage")
    print("="*60)
    
    # Initialize risk manager
    capital = 10000.0
    risk_pct = 0.02  # 2% risk per trade
    
    risk_mgr = RiskManager(total_capital=capital, risk_per_trade=risk_pct)
    
    print(f"\nInitial Capital: ${capital:.2f}")
    print(f"Risk Per Trade: {risk_pct:.1%}")
    
    # Example trade parameters
    entry_price = 150.0
    stop_loss = 147.0
    target_price = 159.0
    
    print("\n" + "-"*60)
    print("Trade Parameters")
    print("-"*60)
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Stop Loss: ${stop_loss:.2f}")
    print(f"Target Price: ${target_price:.2f}")
    
    # Calculate position size
    print("\n" + "-"*60)
    print("Position Sizing (Fixed Risk)")
    print("-"*60)
    
    pos_size = risk_mgr.calculate_position_size_fixed_risk(entry_price, stop_loss)
    print(f"Shares: {pos_size['shares']:.2f}")
    print(f"Position Value: ${pos_size['position_value']:.2f}")
    print(f"Position Size: {pos_size['position_size_pct']:.2f}%")
    print(f"Risk Amount: ${pos_size['risk_amount']:.2f}")
    print(f"Risk: {pos_size['risk_pct']:.2f}%")
    
    # Calculate risk/reward
    print("\n" + "-"*60)
    print("Risk/Reward Analysis")
    print("-"*60)
    
    rr = risk_mgr.calculate_risk_reward_ratio(entry_price, stop_loss, target_price)
    print(f"Risk: ${rr['risk']:.2f} ({rr['risk_pct']:.2f}%)")
    print(f"Reward: ${rr['reward']:.2f} ({rr['reward_pct']:.2f}%)")
    print(f"Risk/Reward Ratio: 1:{rr['risk_reward_ratio']:.2f}")
    print(f"Favorable: {rr['is_favorable']}")
    print(f"Recommendation: {rr['recommendation']}")
    
    # Kelly Criterion
    print("\n" + "-"*60)
    print("Kelly Criterion")
    print("-"*60)
    
    win_rate = 0.60
    avg_win = 300
    avg_loss = 200
    
    kelly = risk_mgr.calculate_kelly_criterion(win_rate, avg_win, avg_loss)
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Average Win: ${avg_win:.2f}")
    print(f"Average Loss: ${avg_loss:.2f}")
    print(f"Optimal Position Size: {kelly:.2%}")
    
    # Validate trade
    print("\n" + "-"*60)
    print("Trade Validation")
    print("-"*60)
    
    validation = risk_mgr.validate_trade(entry_price, stop_loss, target_price)
    print(f"Valid: {validation['is_valid']}")
    print(f"Summary: {validation['summary']}")
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    print("\n" + "="*60)
    print("Risk Management module initialized successfully")
    print("="*60)
