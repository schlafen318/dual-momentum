"""
Optimization Method Comparison for Backtesting.

This module provides functionality to compare different portfolio optimization
methods within the backtesting framework. Instead of using a single position
sizing approach, it runs multiple backtests with different optimization methods
and compares the results.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

import pandas as pd
import numpy as np
from loguru import logger

from ..core.base_strategy import BaseStrategy
from ..core.base_risk import BaseRiskManager
from ..core.types import BacktestResult, PriceData
from ..portfolio_optimization import (
    EqualWeightOptimizer,
    InverseVolatilityOptimizer,
    MinimumVarianceOptimizer,
    MaximumSharpeOptimizer,
    RiskParityOptimizer,
    MaximumDiversificationOptimizer,
    HierarchicalRiskParityOptimizer,
    PortfolioOptimizer,
)
from .engine import BacktestEngine


@dataclass
class OptimizationMethodComparisonResult:
    """
    Results from comparing multiple optimization methods in backtesting.
    
    Attributes:
        method_results: Dictionary mapping optimization method names to backtest results
        comparison_metrics: DataFrame comparing methods on key metrics
        best_sharpe_method: Method with highest Sharpe ratio
        best_return_method: Method with highest total return
        best_risk_adjusted_method: Method with best risk-adjusted performance
        timestamp: When comparison was performed
        metadata: Additional information about the comparison
    """
    method_results: Dict[str, BacktestResult]
    comparison_metrics: pd.DataFrame
    best_sharpe_method: str
    best_return_method: str
    best_risk_adjusted_method: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            'n_methods_compared': len(self.method_results),
            'best_sharpe_method': self.best_sharpe_method,
            'best_sharpe_ratio': self.method_results[self.best_sharpe_method].metrics.get('sharpe_ratio', 0),
            'best_return_method': self.best_return_method,
            'best_return': self.method_results[self.best_return_method].metrics.get('total_return', 0),
            'timestamp': self.timestamp.isoformat(),
        }
    
    def save(self, output_dir: Path, prefix: str = 'optimization_comparison') -> Dict[str, Path]:
        """
        Save comparison results to disk.
        
        Args:
            output_dir: Directory to save results
            prefix: Filename prefix
        
        Returns:
            Dictionary mapping file types to paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = self.timestamp.strftime('%Y%m%d_%H%M%S')
        base_name = f"{prefix}_{timestamp_str}"
        
        saved_files = {}
        
        # Save comparison metrics
        metrics_path = output_dir / f"{base_name}_comparison.csv"
        self.comparison_metrics.to_csv(metrics_path, index=False)
        saved_files['comparison_csv'] = metrics_path
        
        # Save summary as JSON
        summary_path = output_dir / f"{base_name}_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)
        saved_files['summary_json'] = summary_path
        
        # Save individual backtest results
        for method, result in self.method_results.items():
            # Save equity curves
            equity_path = output_dir / f"{base_name}_{method}_equity.csv"
            result.equity_curve.to_csv(equity_path)
            saved_files[f'{method}_equity_csv'] = equity_path
            
            # Save trades
            if hasattr(result, 'trades') and len(result.trades) > 0:
                trades_path = output_dir / f"{base_name}_{method}_trades.csv"
                result.trades.to_csv(trades_path, index=False)
                saved_files[f'{method}_trades_csv'] = trades_path
        
        logger.info(f"Saved optimization comparison results to {output_dir}")
        
        return saved_files


class OptimizationBacktestEngine(BacktestEngine):
    """
    Extended backtest engine that supports portfolio optimization methods.
    
    This engine integrates portfolio optimization into the position sizing logic,
    allowing different optimization methods to determine how capital is allocated
    among assets that pass the momentum filter.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        risk_free_rate: float = 0.0,
        benchmark_include_costs: bool = False,
        optimization_method: Optional[Union[str, PortfolioOptimizer]] = None,
        optimization_lookback: int = 60,
    ):
        """
        Initialize optimization-aware backtesting engine.
        
        Args:
            initial_capital: Starting portfolio value
            commission: Commission rate (e.g., 0.001 = 0.1%)
            slippage: Slippage rate (e.g., 0.0005 = 0.05%)
            risk_free_rate: Annual risk-free rate for Sharpe calculation
            benchmark_include_costs: Whether to apply transaction costs to benchmark
            optimization_method: Portfolio optimization method to use. Can be:
                - String: 'equal_weight', 'inverse_volatility', 'minimum_variance',
                         'maximum_sharpe', 'risk_parity', 'maximum_diversification',
                         'hierarchical_risk_parity'
                - PortfolioOptimizer instance
                - None: Use default momentum-based weighting
            optimization_lookback: Number of periods to use for optimization (default: 60)
        """
        super().__init__(
            initial_capital=initial_capital,
            commission=commission,
            slippage=slippage,
            risk_free_rate=risk_free_rate,
            benchmark_include_costs=benchmark_include_costs,
        )
        
        self.optimization_method = self._initialize_optimizer(optimization_method)
        self.optimization_lookback = optimization_lookback
        
        if self.optimization_method:
            logger.info(f"Using portfolio optimization method: {self.optimization_method.__class__.__name__}")
        else:
            logger.info("Using default momentum-based position sizing")
    
    def _initialize_optimizer(self, method: Optional[Union[str, PortfolioOptimizer]]) -> Optional[PortfolioOptimizer]:
        """Initialize portfolio optimizer from string or instance."""
        if method is None:
            return None
        
        if isinstance(method, PortfolioOptimizer):
            return method
        
        # Method registry
        method_classes = {
            'equal_weight': EqualWeightOptimizer,
            'inverse_volatility': InverseVolatilityOptimizer,
            'minimum_variance': MinimumVarianceOptimizer,
            'maximum_sharpe': MaximumSharpeOptimizer,
            'risk_parity': RiskParityOptimizer,
            'maximum_diversification': MaximumDiversificationOptimizer,
            'hierarchical_risk_parity': HierarchicalRiskParityOptimizer,
        }
        
        if method not in method_classes:
            raise ValueError(
                f"Invalid optimization method '{method}'. "
                f"Must be one of {list(method_classes.keys())}"
            )
        
        optimizer_class = method_classes[method]
        return optimizer_class(risk_free_rate=self.risk_free_rate)
    
    def _execute_signals(
        self,
        signals: List,
        current_date: datetime,
        aligned_data: Dict[str, pd.DataFrame],
        portfolio_value: float,
        risk_manager: Optional[BaseRiskManager],
        strategy: Optional[BaseStrategy] = None
    ) -> None:
        """
        Execute trading signals with optional portfolio optimization.
        
        If an optimization method is configured, it will be used to determine
        position sizes for assets that pass the momentum filter. Otherwise,
        falls back to the default momentum-based weighting.
        """
        if self.optimization_method is None or len(signals) < 2:
            # Fall back to default implementation
            super()._execute_signals(
                signals, current_date, aligned_data, portfolio_value, risk_manager, strategy
            )
            return
        
        # Extract symbols from signals
        signal_symbols = [signal.symbol for signal in signals if signal.direction != 0]
        
        if len(signal_symbols) < 2:
            # Need at least 2 assets for optimization
            super()._execute_signals(
                signals, current_date, aligned_data, portfolio_value, risk_manager, strategy
            )
            return
        
        # Close positions not in signal set
        positions_to_close = [
            symbol for symbol in self.positions.keys() 
            if symbol not in signal_symbols
        ]
        
        for symbol in positions_to_close:
            self._close_position(symbol, current_date, aligned_data)
        
        # Get historical returns for optimization
        returns_df = self._get_returns_for_optimization(
            signal_symbols, aligned_data, current_date
        )
        
        if returns_df is None or len(returns_df) < 10:
            logger.warning("Insufficient return data for optimization, using equal weights")
            # Fall back to equal weights
            weights = {symbol: 1.0 / len(signal_symbols) for symbol in signal_symbols}
        else:
            # Run portfolio optimization
            try:
                opt_result = self.optimization_method.optimize(returns_df)
                weights = opt_result.weights
                
                logger.info(f"Portfolio optimization complete: {self.optimization_method.__class__.__name__}")
                logger.info(f"Optimized weights: {weights}")
            except Exception as e:
                logger.error(f"Portfolio optimization failed: {e}, using equal weights")
                weights = {symbol: 1.0 / len(signal_symbols) for symbol in signal_symbols}
        
        # Execute trades based on optimized weights
        self._execute_optimized_trades(
            weights, signal_symbols, current_date, aligned_data, portfolio_value
        )
    
    def _get_returns_for_optimization(
        self,
        symbols: List[str],
        aligned_data: Dict[str, pd.DataFrame],
        current_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Get historical returns for portfolio optimization.
        
        Args:
            symbols: List of symbols to get returns for
            aligned_data: Price data for all symbols
            current_date: Current date in backtest
        
        Returns:
            DataFrame with returns for each symbol, or None if insufficient data
        """
        returns_dict = {}
        
        for symbol in symbols:
            if symbol not in aligned_data:
                continue
            
            df = aligned_data[symbol]
            
            # Get data up to current date
            historical_data = df[df.index <= current_date]
            
            if len(historical_data) < self.optimization_lookback + 1:
                logger.debug(f"Insufficient data for {symbol}: {len(historical_data)} bars")
                continue
            
            # Get last N periods
            recent_data = historical_data.iloc[-self.optimization_lookback:]
            
            # Calculate returns
            returns = recent_data['close'].pct_change().dropna()
            
            if len(returns) > 0:
                returns_dict[symbol] = returns
        
        if not returns_dict:
            return None
        
        # Align returns to common dates
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()
        
        return returns_df
    
    def _execute_optimized_trades(
        self,
        weights: Dict[str, float],
        symbols: List[str],
        current_date: datetime,
        aligned_data: Dict[str, pd.DataFrame],
        portfolio_value: float
    ) -> None:
        """
        Execute trades based on optimized weights.
        
        Args:
            weights: Dictionary mapping symbols to target weights
            symbols: List of symbols to trade
            current_date: Current date
            aligned_data: Price data
            portfolio_value: Current portfolio value
        """
        logger.info(f"[OPTIMIZED ALLOCATION] Target weights: {weights}")
        
        # Calculate target position values
        target_values = {
            symbol: portfolio_value * weights.get(symbol, 0.0)
            for symbol in symbols
        }
        
        # Execute trades (sells first, then buys)
        sell_trades = []
        buy_trades = []
        
        for symbol in symbols:
            if symbol not in aligned_data:
                continue
            
            current_price = float(aligned_data[symbol].loc[current_date, 'close'])
            target_value = target_values[symbol]
            
            # Apply slippage
            execution_price = current_price * (1 + self.slippage)
            target_shares = target_value / execution_price if execution_price > 0 else 0
            
            if symbol in self.positions:
                # Adjust existing position
                existing_shares = self.positions[symbol].quantity
                if target_shares < existing_shares:
                    sell_trades.append((symbol, target_shares, current_price))
                else:
                    buy_trades.append((symbol, target_shares, current_price))
            else:
                # New position
                buy_trades.append((symbol, target_shares, current_price))
        
        # Execute sells first
        for symbol, target_shares, price in sell_trades:
            self._adjust_position(symbol, target_shares, price, current_date)
        
        # Then execute buys
        for symbol, target_shares, price in buy_trades:
            if symbol in self.positions:
                self._adjust_position(symbol, target_shares, price, current_date)
            else:
                execution_price = price * (1 + self.slippage)
                position_value = target_shares * execution_price
                commission_cost = position_value * self.commission
                total_cost = position_value + commission_cost
                
                if total_cost <= self.cash:
                    self._open_position(symbol, target_shares, execution_price, current_date)
                    self.cash -= total_cost
                else:
                    logger.warning(f"Insufficient cash for {symbol}: need ${total_cost:,.2f}, have ${self.cash:,.2f}")


def compare_optimization_methods_in_backtest(
    strategy: BaseStrategy,
    price_data: Dict[str, PriceData],
    optimization_methods: Optional[List[str]] = None,
    initial_capital: float = 100000.0,
    commission: float = 0.001,
    slippage: float = 0.0005,
    risk_free_rate: float = 0.0,
    risk_manager: Optional[BaseRiskManager] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    benchmark_data: Optional[PriceData] = None,
    optimization_lookback: int = 60,
    verbose: bool = True,
) -> OptimizationMethodComparisonResult:
    """
    Compare multiple portfolio optimization methods in backtesting.
    
    Runs the same strategy with different portfolio optimization methods
    to see how position sizing affects performance.
    
    Args:
        strategy: Trading strategy to backtest
        price_data: Price data for all assets
        optimization_methods: List of optimization methods to compare. Options:
            - 'momentum_based': Default momentum-based weighting (baseline)
            - 'equal_weight': Equal weight allocation
            - 'inverse_volatility': Inverse volatility weighting
            - 'minimum_variance': Minimum variance optimization
            - 'maximum_sharpe': Maximum Sharpe ratio optimization
            - 'risk_parity': Risk parity allocation
            - 'maximum_diversification': Maximum diversification
            - 'hierarchical_risk_parity': HRP allocation
            If None, compares all methods.
        initial_capital: Starting capital for each backtest
        commission: Commission rate
        slippage: Slippage rate
        risk_free_rate: Risk-free rate for calculations
        risk_manager: Optional risk manager
        start_date: Backtest start date
        end_date: Backtest end date
        benchmark_data: Benchmark data for comparison
        optimization_lookback: Periods to use for optimization
        verbose: Print progress messages
    
    Returns:
        OptimizationMethodComparisonResult with results from all methods
    
    Example:
        >>> from src.strategies.dual_momentum import DualMomentumStrategy
        >>> strategy = DualMomentumStrategy({'lookback_period': 252})
        >>> comparison = compare_optimization_methods_in_backtest(
        ...     strategy=strategy,
        ...     price_data=price_data,
        ...     optimization_methods=['momentum_based', 'equal_weight', 'risk_parity']
        ... )
        >>> print(comparison.comparison_metrics)
    """
    # Default methods
    if optimization_methods is None:
        optimization_methods = [
            'momentum_based',
            'equal_weight',
            'inverse_volatility',
            'minimum_variance',
            'maximum_sharpe',
            'risk_parity',
            'maximum_diversification',
            'hierarchical_risk_parity',
        ]
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"OPTIMIZATION METHOD COMPARISON IN BACKTESTING")
        print(f"={'='*80}")
        print(f"Strategy: {strategy.get_name()}")
        print(f"Assets: {list(price_data.keys())}")
        print(f"Methods: {', '.join(optimization_methods)}")
        print(f"{'='*80}\n")
    
    # Validate inputs before running backtests
    if not price_data:
        raise ValueError("price_data is empty")
    
    if len(price_data) < 1:
        raise ValueError(f"Need at least 1 asset for backtesting, got {len(price_data)}")
    
    # Check that all price_data values are PriceData objects
    from ..core.types import PriceData as PriceDataType
    for symbol, data in price_data.items():
        if not isinstance(data, PriceDataType):
            raise TypeError(f"price_data['{symbol}'] must be a PriceData object, got {type(data).__name__}")
        if data.data.empty:
            raise ValueError(f"price_data['{symbol}'] has empty DataFrame")
    
    if verbose:
        print(f"? Validated {len(price_data)} assets")
        if start_date and end_date:
            print(f"? Date range: {start_date.date()} to {end_date.date()}")
        print()
    
    method_results = {}
    
    # Run backtest for each optimization method
    for method in optimization_methods:
        if verbose:
            print(f"Running backtest with {method.replace('_', ' ').title()}...")
        
        try:
            # Create engine with optimization method
            if method == 'momentum_based':
                # Use standard engine (no optimization)
                engine = BacktestEngine(
                    initial_capital=initial_capital,
                    commission=commission,
                    slippage=slippage,
                    risk_free_rate=risk_free_rate,
                )
            else:
                # Use optimization engine
                engine = OptimizationBacktestEngine(
                    initial_capital=initial_capital,
                    commission=commission,
                    slippage=slippage,
                    risk_free_rate=risk_free_rate,
                    optimization_method=method,
                    optimization_lookback=optimization_lookback,
                )
            
            # Run backtest
            result = engine.run(
                strategy=strategy,
                price_data=price_data,
                risk_manager=risk_manager,
                start_date=start_date,
                end_date=end_date,
                benchmark_data=benchmark_data,
            )
            
            method_results[method] = result
            
            if verbose:
                print(f"  ? Total Return: {result.total_return*100:.2f}%, "
                      f"Sharpe: {result.metrics.get('sharpe_ratio', 0):.2f}, "
                      f"Max DD: {result.metrics.get('max_drawdown', 0)*100:.2f}%")
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Error running backtest with {method}: {e}\n{error_trace}")
            if verbose:
                print(f"  ? Failed: {e}")
                print(f"  Error details: {error_trace}")
    
    if not method_results:
        error_msg = (
            f"All {len(optimization_methods)} backtest methods failed!\n"
            f"Methods attempted: {', '.join(optimization_methods)}\n"
            f"Check logs above for specific error details for each method.\n"
            f"Common issues:\n"
            f"  - Insufficient price data\n"
            f"  - Data not in PriceData format\n"
            f"  - Strategy configuration errors\n"
            f"  - Start/end date issues"
        )
        logger.error(error_msg)
        if verbose:
            print(f"\n{'='*80}")
            print("ERROR SUMMARY")
            print(f"{'='*80}")
            print(error_msg)
            print(f"{'='*80}\n")
        raise RuntimeError(error_msg)
    
    # Create comparison metrics DataFrame
    comparison_data = []
    for method, result in method_results.items():
        comparison_data.append({
            'method': method.replace('_', ' ').title(),
            'total_return': result.total_return,
            'annualized_return': result.metrics.get('annualized_return', 0),
            'volatility': result.metrics.get('volatility', 0),
            'sharpe_ratio': result.metrics.get('sharpe_ratio', 0),
            'sortino_ratio': result.metrics.get('sortino_ratio', 0),
            'max_drawdown': result.metrics.get('max_drawdown', 0),
            'calmar_ratio': result.metrics.get('calmar_ratio', 0),
            'win_rate': result.win_rate,
            'num_trades': result.num_trades,
            'final_capital': result.final_capital,
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Identify best methods
    best_sharpe_method = max(
        method_results.items(),
        key=lambda x: x[1].metrics.get('sharpe_ratio', -np.inf)
    )[0]
    
    best_return_method = max(
        method_results.items(),
        key=lambda x: x[1].total_return
    )[0]
    
    # Best risk-adjusted: combination of Sharpe and Sortino
    best_risk_adjusted_method = max(
        method_results.items(),
        key=lambda x: (x[1].metrics.get('sharpe_ratio', 0) + x[1].metrics.get('sortino_ratio', 0)) / 2
    )[0]
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"COMPARISON COMPLETE")
        print(f"={'='*80}")
        print(f"Best Sharpe Ratio: {best_sharpe_method.replace('_', ' ').title()}")
        print(f"Best Total Return: {best_return_method.replace('_', ' ').title()}")
        print(f"Best Risk-Adjusted: {best_risk_adjusted_method.replace('_', ' ').title()}")
        print(f"\nComparison Metrics:")
        print(comparison_df.to_string(index=False))
        print(f"{'='*80}\n")
    
    return OptimizationMethodComparisonResult(
        method_results=method_results,
        comparison_metrics=comparison_df,
        best_sharpe_method=best_sharpe_method,
        best_return_method=best_return_method,
        best_risk_adjusted_method=best_risk_adjusted_method,
        metadata={
            'initial_capital': initial_capital,
            'commission': commission,
            'slippage': slippage,
            'risk_free_rate': risk_free_rate,
            'optimization_lookback': optimization_lookback,
        }
    )
