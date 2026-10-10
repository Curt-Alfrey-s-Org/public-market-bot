#!/usr/bin/env python3
"""
Portfolio Optimization Module for market-pie5-bot
Implements Modern Portfolio Theory (Markowitz optimization) and risk parity
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Check if scipy is available
try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available - portfolio optimization will use simple methods")

# Minimum data points required for reliable optimization
MIN_DATA_POINTS_FOR_OPTIMIZATION = 20


class PortfolioOptimizer:
    """
    Portfolio optimization using Modern Portfolio Theory
    Provides optimal asset allocation based on risk-return tradeoffs
    """
    
    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize portfolio optimizer
        
        Args:
            risk_free_rate: Risk-free rate for Sharpe ratio calculation (default: 0.0)
        """
        self.risk_free_rate = risk_free_rate
        self.price_history = {}  # {symbol: [prices]}
        
        # Caching for optimization results
        self._allocation_cache = {}  # {(symbols_tuple, total_capital, method): allocations}
        self._cache_timestamp = {}  # Track when cache was created
        self._cache_ttl_seconds = 300  # Cache TTL: 5 minutes
        
        logger.info(f"Initialized PortfolioOptimizer (risk_free_rate={risk_free_rate:.2%})")
    
    def add_price_data(self, symbol: str, prices: List[float]):
        """
        Add price history for a symbol
        
        Args:
            symbol: Stock symbol
            prices: List of historical prices
        """
        self.price_history[symbol] = prices
        logger.debug(f"Added {len(prices)} price points for {symbol}")
    
    def calculate_returns(self, prices: List[float]) -> np.ndarray:
        """
        Calculate daily returns from price data
        
        Args:
            prices: List of prices
            
        Returns:
            Array of daily returns
        """
        if len(prices) < 2:
            return np.array([])
        
        prices_array = np.array(prices)
        returns = np.diff(prices_array) / prices_array[:-1]
        return returns
    
    def calculate_covariance_matrix(self, symbols: List[str]) -> Optional[np.ndarray]:
        """
        Calculate covariance matrix for given symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Covariance matrix or None if insufficient data
        """
        # Collect returns for all symbols
        returns_dict = {}
        min_length = float('inf')
        
        for symbol in symbols:
            if symbol not in self.price_history:
                logger.warning(f"No price history for {symbol}")
                return None
            
            returns = self.calculate_returns(self.price_history[symbol])
            if len(returns) == 0:
                logger.warning(f"Insufficient price data for {symbol}")
                return None
            
            returns_dict[symbol] = returns
            min_length = min(min_length, len(returns))
        
        if min_length < MIN_DATA_POINTS_FOR_OPTIMIZATION:
            logger.warning(f"Insufficient data points ({min_length} < {MIN_DATA_POINTS_FOR_OPTIMIZATION})")
            return None
        
        # Truncate all returns to same length
        returns_matrix = np.array([returns_dict[s][-min_length:] for s in symbols])
        
        # Calculate covariance matrix
        cov_matrix = np.cov(returns_matrix)
        
        return cov_matrix
    
    def calculate_correlation_matrix(self, symbols: List[str]) -> Optional[np.ndarray]:
        """
        Calculate correlation matrix for given symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Correlation matrix or None if insufficient data
        """
        cov_matrix = self.calculate_covariance_matrix(symbols)
        if cov_matrix is None:
            return None
        
        # Convert covariance to correlation
        std_devs = np.sqrt(np.diag(cov_matrix))
        corr_matrix = cov_matrix / np.outer(std_devs, std_devs)
        
        return corr_matrix
    
    def calculate_expected_returns(self, symbols: List[str]) -> Optional[np.ndarray]:
        """
        Calculate expected returns for given symbols
        Uses simple mean of historical returns
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Array of expected returns or None if insufficient data
        """
        expected_returns = []
        
        for symbol in symbols:
            if symbol not in self.price_history:
                return None
            
            returns = self.calculate_returns(self.price_history[symbol])
            if len(returns) == 0:
                return None
            
            # Use mean return as expected return
            expected_returns.append(np.mean(returns))
        
        return np.array(expected_returns)
    
    def portfolio_performance(self, weights: np.ndarray, 
                             expected_returns: np.ndarray,
                             cov_matrix: np.ndarray) -> Tuple[float, float, float]:
        """
        Calculate portfolio performance metrics
        
        Args:
            weights: Asset weights
            expected_returns: Expected returns for each asset
            cov_matrix: Covariance matrix
            
        Returns:
            Tuple of (return, volatility, sharpe_ratio)
        """
        # Portfolio return
        portfolio_return = np.dot(weights, expected_returns)
        
        # Portfolio volatility
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Sharpe ratio
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        return portfolio_return, portfolio_volatility, sharpe_ratio
    
    def optimize_sharpe_ratio(self, expected_returns: np.ndarray,
                             cov_matrix: np.ndarray) -> Optional[np.ndarray]:
        """
        Find portfolio with maximum Sharpe ratio
        
        Args:
            expected_returns: Expected returns for each asset
            cov_matrix: Covariance matrix
            
        Returns:
            Optimal weights or None if optimization fails
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available - using equal weights")
            n = len(expected_returns)
            return np.array([1.0 / n] * n)
        
        n = len(expected_returns)
        
        # Objective function: negative Sharpe ratio (to minimize)
        def objective(weights):
            ret, vol, sharpe = self.portfolio_performance(weights, expected_returns, cov_matrix)
            return -sharpe  # Negative because we minimize
        
        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        
        # Bounds: 0 <= weight <= 1 for each asset
        bounds = tuple((0, 1) for _ in range(n))
        
        # Initial guess: equal weights
        initial_weights = np.array([1.0 / n] * n)
        
        try:
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )
            
            if result.success:
                return result.x
            else:
                logger.warning(f"Optimization failed: {result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return None
    
    def optimize_minimum_variance(self, cov_matrix: np.ndarray) -> Optional[np.ndarray]:
        """
        Find minimum variance portfolio
        
        Args:
            cov_matrix: Covariance matrix
            
        Returns:
            Optimal weights or None if optimization fails
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available - using equal weights")
            n = cov_matrix.shape[0]
            return np.array([1.0 / n] * n)
        
        n = cov_matrix.shape[0]
        
        # Objective function: portfolio variance
        def objective(weights):
            return np.dot(weights, np.dot(cov_matrix, weights))
        
        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        
        # Bounds: 0 <= weight <= 1 for each asset
        bounds = tuple((0, 1) for _ in range(n))
        
        # Initial guess: equal weights
        initial_weights = np.array([1.0 / n] * n)
        
        try:
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )
            
            if result.success:
                return result.x
            else:
                logger.warning(f"Optimization failed: {result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return None
    
    def calculate_risk_parity_weights(self, cov_matrix: np.ndarray) -> Optional[np.ndarray]:
        """
        Calculate risk parity (equal risk contribution) weights
        
        Args:
            cov_matrix: Covariance matrix
            
        Returns:
            Risk parity weights or None if calculation fails
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available - using equal weights")
            n = cov_matrix.shape[0]
            return np.array([1.0 / n] * n)
        
        n = cov_matrix.shape[0]
        
        # Objective: minimize difference in risk contributions
        def objective(weights):
            portfolio_var = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_vol = np.sqrt(portfolio_var)
            
            # Marginal contribution to risk
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            
            # Risk contribution
            risk_contrib = weights * marginal_contrib
            
            # Target: equal risk contribution
            target = portfolio_vol / n
            
            # Sum of squared deviations from target
            return np.sum((risk_contrib - target) ** 2)
        
        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        
        # Bounds: 0 < weight <= 1 for each asset (avoid zero weights)
        bounds = tuple((0.01, 1) for _ in range(n))
        
        # Initial guess: equal weights
        initial_weights = np.array([1.0 / n] * n)
        
        try:
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )
            
            if result.success:
                # Normalize weights to sum to 1
                weights = result.x
                return weights / np.sum(weights)
            else:
                logger.warning(f"Risk parity optimization failed: {result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Risk parity optimization error: {e}")
            return None
    
    def calculate_efficient_frontier(self, expected_returns: np.ndarray,
                                    cov_matrix: np.ndarray,
                                    num_points: int = 50) -> Optional[pd.DataFrame]:
        """
        Calculate efficient frontier
        
        Args:
            expected_returns: Expected returns for each asset
            cov_matrix: Covariance matrix
            num_points: Number of points on frontier
            
        Returns:
            DataFrame with columns: return, volatility, sharpe_ratio, weights
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available - cannot calculate efficient frontier")
            return None
        
        n = len(expected_returns)
        
        # Find range of returns
        min_return = np.min(expected_returns)
        max_return = np.max(expected_returns)
        target_returns = np.linspace(min_return, max_return, num_points)
        
        results = []
        
        for target_return in target_returns:
            # Objective: minimize variance
            def objective(weights):
                return np.dot(weights, np.dot(cov_matrix, weights))
            
            # Constraints
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Weights sum to 1
                {'type': 'eq', 'fun': lambda w: np.dot(w, expected_returns) - target_return}  # Target return
            ]
            
            # Bounds
            bounds = tuple((0, 1) for _ in range(n))
            
            # Initial guess
            initial_weights = np.array([1.0 / n] * n)
            
            try:
                result = minimize(
                    objective,
                    initial_weights,
                    method='SLSQP',
                    bounds=bounds,
                    constraints=constraints,
                    options={'maxiter': 1000}
                )
                
                if result.success:
                    weights = result.x
                    ret, vol, sharpe = self.portfolio_performance(weights, expected_returns, cov_matrix)
                    results.append({
                        'return': ret,
                        'volatility': vol,
                        'sharpe_ratio': sharpe,
                        'weights': weights
                    })
            except Exception as e:
                logger.debug(f"Could not optimize for target return {target_return:.4f}: {e}")
                continue
        
        if not results:
            logger.warning("No points calculated for efficient frontier")
            return None
        
        return pd.DataFrame(results)
    
    def get_optimal_allocation(self, symbols: List[str], 
                              total_capital: float,
                              method: str = 'sharpe') -> Optional[Dict[str, float]]:
        """
        Get optimal capital allocation for given symbols
        
        Uses caching to avoid redundant computation.
        
        Args:
            symbols: List of stock symbols
            total_capital: Total capital to allocate
            method: Optimization method ('sharpe', 'min_variance', 'risk_parity', 'equal')
            
        Returns:
            Dictionary mapping symbols to dollar amounts
        """
        # Check cache first
        cache_key = (tuple(sorted(symbols)), total_capital, method)
        if cache_key in self._allocation_cache:
            cache_time = self._cache_timestamp.get(cache_key)
            if cache_time:
                age = (datetime.now() - cache_time).total_seconds()
                if age < self._cache_ttl_seconds:
                    logger.debug(f"Using cached portfolio allocation (age: {age:.1f}s)")
                    return self._allocation_cache[cache_key].copy()
        
        if method == 'equal':
            # Simple equal allocation
            allocation = total_capital / len(symbols)
            result = {symbol: allocation for symbol in symbols}
            # Cache result
            self._allocation_cache[cache_key] = result.copy()
            self._cache_timestamp[cache_key] = datetime.now()
            return result
        
        # Calculate covariance matrix
        cov_matrix = self.calculate_covariance_matrix(symbols)
        if cov_matrix is None:
            logger.warning("Cannot calculate covariance matrix - using equal weights")
            allocation = total_capital / len(symbols)
            return {symbol: allocation for symbol in symbols}
        
        # Get optimal weights based on method
        if method == 'sharpe':
            expected_returns = self.calculate_expected_returns(symbols)
            if expected_returns is None:
                logger.warning("Cannot calculate expected returns - using equal weights")
                allocation = total_capital / len(symbols)
                return {symbol: allocation for symbol in symbols}
            
            weights = self.optimize_sharpe_ratio(expected_returns, cov_matrix)
        elif method == 'min_variance':
            weights = self.optimize_minimum_variance(cov_matrix)
        elif method == 'risk_parity':
            weights = self.calculate_risk_parity_weights(cov_matrix)
        else:
            logger.error(f"Unknown optimization method: {method}")
            return None
        
        if weights is None:
            logger.warning("Optimization failed - using equal weights")
            allocation = total_capital / len(symbols)
            return {symbol: allocation for symbol in symbols}
        
        # Convert weights to dollar amounts
        allocations = {}
        for i, symbol in enumerate(symbols):
            allocations[symbol] = weights[i] * total_capital
        
        logger.info(f"Optimal allocation ({method}):")
        for symbol, amount in allocations.items():
            logger.info(f"  {symbol}: ${amount:.2f} ({weights[symbols.index(symbol)]:.2%})")
        
        # Cache result
        cache_key = (tuple(sorted(symbols)), total_capital, method)
        self._allocation_cache[cache_key] = allocations.copy()
        self._cache_timestamp[cache_key] = datetime.now()
        
        return allocations
    
    def clear_cache(self):
        """Clear optimization cache (useful when price data changes significantly)"""
        self._allocation_cache.clear()
        self._cache_timestamp.clear()
        logger.debug("Portfolio optimization cache cleared")
    
    def calculate_diversification_score(self, symbols: List[str]) -> float:
        """
        Calculate diversification score for portfolio
        Based on average correlation between assets
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Diversification score (0 to 1, higher is more diversified)
        """
        if len(symbols) < 2:
            return 0.0
        
        corr_matrix = self.calculate_correlation_matrix(symbols)
        if corr_matrix is None:
            return 0.0
        
        # Get upper triangle of correlation matrix (excluding diagonal)
        n = len(symbols)
        correlations = []
        for i in range(n):
            for j in range(i + 1, n):
                correlations.append(abs(corr_matrix[i, j]))
        
        if not correlations:
            return 0.0
        
        # Average absolute correlation
        avg_correlation = np.mean(correlations)
        
        # Convert to diversification score (lower correlation = higher diversification)
        diversification_score = 1.0 - avg_correlation
        
        logger.info(f"Portfolio diversification score: {diversification_score:.2f}")
        return diversification_score
    
    def suggest_rebalancing(self, current_positions: Dict[str, float],
                           target_allocations: Dict[str, float],
                           threshold: float = 0.05) -> Dict[str, float]:
        """
        Suggest rebalancing trades to reach target allocations
        
        Args:
            current_positions: Current holdings {symbol: dollar_amount}
            target_allocations: Target allocations {symbol: dollar_amount}
            threshold: Minimum deviation to trigger rebalancing (default: 5%)
            
        Returns:
            Dictionary of rebalancing trades {symbol: dollar_amount_to_buy_or_sell}
        """
        rebalancing_trades = {}
        
        for symbol in target_allocations:
            current = current_positions.get(symbol, 0)
            target = target_allocations[symbol]
            
            deviation = abs(current - target) / target if target > 0 else 0
            
            if deviation > threshold:
                trade_amount = target - current
                rebalancing_trades[symbol] = trade_amount
                
                action = "BUY" if trade_amount > 0 else "SELL"
                logger.info(f"Rebalancing {symbol}: {action} ${abs(trade_amount):.2f}")
        
        return rebalancing_trades
