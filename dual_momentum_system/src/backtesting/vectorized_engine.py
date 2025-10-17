"""
Vectorized backtesting engine using vectorbt for high-performance multi-asset backtesting.

This module provides a vectorized backtesting framework that can efficiently handle
multi-asset portfolios with complex rebalancing logic and comprehensive analytics.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable

import pandas as pd
import numpy as np
import vectorbt as vbt
from loguru import logger

try:
    from ..core.types import BacktestResult, PriceData
except ImportError:
    from src.core.types import BacktestResult, PriceData


class VectorizedBacktestEngine:
    """
    High-performance vectorized backtesting engine using vectorbt.
    
    This engine leverages vectorized operations for efficient backtesting of
    multi-asset portfolios with support for:
    - Custom signal generation functions
    - Multiple rebalancing strategies
    - Transaction costs and slippage
    - Leverage and shorting
    - Advanced portfolio construction
    
    Example:
        >>> engine = VectorizedBacktestEngine(
        ...     initial_capital=100000,
        ...     commission=0.001,
        ...     freq='D'
        ... )
        >>> results = engine.run_backtest(
        ...     price_data=price_dict,
        ...     signals=signal_matrix
        ... )
        >>> print(results.metrics['sharpe_ratio'])
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        freq: str = 'D',
        risk_free_rate: float = 0.0,
        **kwargs
    ):
        """
        Initialize vectorized backtesting engine.
        
        Args:
            initial_capital: Starting capital
            commission: Commission rate per trade (e.g., 0.001 = 0.1%)
            slippage: Slippage rate (e.g., 0.0005 = 0.05%)
            freq: Data frequency ('D' for daily, 'H' for hourly, etc.)
            risk_free_rate: Annual risk-free rate for Sharpe ratio
            **kwargs: Additional vectorbt portfolio parameters
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.freq = freq
        self.risk_free_rate = risk_free_rate
        self.kwargs = kwargs
        
        logger.info(
            f"Initialized VectorizedBacktestEngine: capital=${initial_capital:,.0f}, "
            f"commission={commission:.2%}, slippage={slippage:.2%}"
        )
    
    def run_backtest(
        self,
        price_data: Union[pd.DataFrame, Dict[str, PriceData]],
        signals: Union[pd.DataFrame, np.ndarray],
        size_type: str = 'percent',
        group_by: Optional[Union[bool, str]] = None,
        cash_sharing: bool = True,
        call_seq: str = 'auto',
        **kwargs
    ) -> BacktestResult:
        """
        Run vectorized backtest on price data with given signals.
        
        Args:
            price_data: DataFrame with close prices (columns=symbols) or
                       dict of PriceData objects
            signals: DataFrame/array with position sizes or directions
                    Same shape as price_data. Values represent:
                    - For size_type='percent': percentage of capital (0-1)
                    - For size_type='shares': number of shares
                    - For size_type='value': dollar amount
            size_type: How to interpret signals ('percent', 'shares', 'value')
            group_by: Group assets for cash sharing
            cash_sharing: Whether to share cash across assets
            call_seq: Order of signal execution ('auto', 'random', array)
            **kwargs: Additional portfolio parameters
        
        Returns:
            BacktestResult with comprehensive metrics and analytics
        """
        logger.info("Starting vectorized backtest")
        
        # Convert price data to DataFrame if needed
        close_prices = self._prepare_price_data(price_data)
        
        # Ensure signals match price data shape
        if isinstance(signals, np.ndarray):
            signals = pd.DataFrame(
                signals,
                index=close_prices.index,
                columns=close_prices.columns
            )
        
        # Validate data alignment
        if not signals.index.equals(close_prices.index):
            logger.warning("Aligning signals with price data")
            signals = signals.reindex(close_prices.index, fill_value=0)
        
        if not signals.columns.equals(close_prices.columns):
            logger.warning("Aligning signal columns with price columns")
            signals = signals.reindex(columns=close_prices.columns, fill_value=0)
        
        logger.info(
            f"Running backtest: {len(close_prices)} periods, "
            f"{len(close_prices.columns)} assets"
        )
        
        # Create portfolio using vectorbt
        portfolio = vbt.Portfolio.from_orders(
            close=close_prices,
            size=signals,
            size_type=size_type,
            init_cash=self.initial_capital,
            fees=self.commission,
            slippage=self.slippage,
            freq=self.freq,
            group_by=group_by,
            cash_sharing=cash_sharing,
            call_seq=call_seq,
            **{**self.kwargs, **kwargs}
        )
        
        # Extract results
        results = self._extract_results(
            portfolio,
            close_prices,
            signals,
            'VectorizedStrategy'
        )
        
        logger.info(
            f"Backtest complete: Return={results.total_return:.2%}, "
            f"Sharpe={results.metrics.get('sharpe_ratio', 0):.2f}"
        )
        
        return results
    
    def run_signal_strategy(
        self,
        price_data: Union[pd.DataFrame, Dict[str, PriceData]],
        entries: pd.DataFrame,
        exits: pd.DataFrame,
        size: Union[float, pd.DataFrame] = 1.0,
        direction: Union[str, pd.DataFrame] = 'longonly',
        **kwargs
    ) -> BacktestResult:
        """
        Run backtest with explicit entry/exit signals.
        
        Args:
            price_data: Close prices
            entries: Boolean DataFrame indicating entry points
            exits: Boolean DataFrame indicating exit points
            size: Position size (percent of capital or shares)
            direction: Trading direction ('longonly', 'shortonly', 'both', or DataFrame)
            **kwargs: Additional portfolio parameters
        
        Returns:
            BacktestResult with metrics
        """
        logger.info("Running signal-based strategy")
        
        close_prices = self._prepare_price_data(price_data)
        
        # Create portfolio from signals
        portfolio = vbt.Portfolio.from_signals(
            close=close_prices,
            entries=entries,
            exits=exits,
            size=size,
            direction=direction,
            init_cash=self.initial_capital,
            fees=self.commission,
            slippage=self.slippage,
            freq=self.freq,
            **{**self.kwargs, **kwargs}
        )
        
        results = self._extract_results(
            portfolio,
            close_prices,
            None,
            'SignalStrategy'
        )
        
        logger.info(f"Signal strategy complete: Return={results.total_return:.2%}")
        
        return results
    
    def run_custom_strategy(
        self,
        price_data: Union[pd.DataFrame, Dict[str, PriceData]],
        signal_func: Callable,
        signal_func_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> BacktestResult:
        """
        Run backtest with custom signal generation function.
        
        Args:
            price_data: Close prices
            signal_func: Function that takes close prices and returns signals
            signal_func_kwargs: Arguments to pass to signal_func
            **kwargs: Additional portfolio parameters
        
        Returns:
            BacktestResult with metrics
        """
        logger.info("Running custom strategy")
        
        close_prices = self._prepare_price_data(price_data)
        
        # Generate signals using custom function
        signal_func_kwargs = signal_func_kwargs or {}
        signals = signal_func(close_prices, **signal_func_kwargs)
        
        return self.run_backtest(
            price_data=close_prices,
            signals=signals,
            **kwargs
        )
    
    def run_multi_strategy_comparison(
        self,
        price_data: Union[pd.DataFrame, Dict[str, PriceData]],
        strategies: Dict[str, pd.DataFrame],
        **kwargs
    ) -> Dict[str, BacktestResult]:
        """
        Run and compare multiple strategies.
        
        Args:
            price_data: Close prices
            strategies: Dict mapping strategy names to signal DataFrames
            **kwargs: Additional portfolio parameters
        
        Returns:
            Dictionary mapping strategy names to BacktestResults
        """
        logger.info(f"Comparing {len(strategies)} strategies")
        
        results = {}
        for name, signals in strategies.items():
            logger.info(f"Running strategy: {name}")
            results[name] = self.run_backtest(
                price_data=price_data,
                signals=signals,
                **kwargs
            )
        
        return results
    
    def optimize_strategy(
        self,
        price_data: Union[pd.DataFrame, Dict[str, PriceData]],
        signal_func: Callable,
        param_grid: Dict[str, List[Any]],
        metric: str = 'sharpe_ratio',
        maximize: bool = True,
        **kwargs
    ) -> tuple[Dict[str, Any], BacktestResult]:
        """
        Optimize strategy parameters using grid search.
        
        Args:
            price_data: Close prices
            signal_func: Signal generation function
            param_grid: Dictionary of parameter names to lists of values
            metric: Metric to optimize (e.g., 'sharpe_ratio', 'annual_return')
            maximize: Whether to maximize (True) or minimize (False) metric
            **kwargs: Additional portfolio parameters
        
        Returns:
            Tuple of (best_params, best_result)
        """
        logger.info(f"Optimizing strategy on {metric}")
        
        close_prices = self._prepare_price_data(price_data)
        
        # Generate all parameter combinations
        import itertools
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))
        
        best_metric_value = float('-inf') if maximize else float('inf')
        best_params = None
        best_result = None
        
        logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        for i, param_combo in enumerate(param_combinations):
            params = dict(zip(param_names, param_combo))
            
            try:
                # Generate signals with these parameters
                signals = signal_func(close_prices, **params)
                
                # Run backtest
                result = self.run_backtest(
                    price_data=close_prices,
                    signals=signals,
                    **kwargs
                )
                
                metric_value = result.metrics.get(metric, 0)
                
                # Check if this is better
                is_better = (
                    (maximize and metric_value > best_metric_value) or
                    (not maximize and metric_value < best_metric_value)
                )
                
                if is_better:
                    best_metric_value = metric_value
                    best_params = params
                    best_result = result
                    logger.info(
                        f"New best: {params} -> {metric}={metric_value:.4f}"
                    )
            
            except Exception as e:
                logger.warning(f"Failed for params {params}: {e}")
                continue
        
        logger.info(
            f"Optimization complete. Best {metric}: {best_metric_value:.4f}"
        )
        
        return best_params, best_result
    
    def _prepare_price_data(
        self,
        price_data: Union[pd.DataFrame, Dict[str, PriceData]]
    ) -> pd.DataFrame:
        """
        Convert price data to DataFrame format.
        
        Args:
            price_data: Price data in various formats
        
        Returns:
            DataFrame with close prices (columns=symbols)
        """
        if isinstance(price_data, pd.DataFrame):
            return price_data
        
        # Convert dict of PriceData to DataFrame
        close_dict = {}
        for symbol, pdata in price_data.items():
            if isinstance(pdata, PriceData):
                close_dict[symbol] = pdata.data['close']
            elif isinstance(pdata, pd.DataFrame):
                close_dict[symbol] = pdata['close']
            else:
                close_dict[symbol] = pdata
        
        close_df = pd.DataFrame(close_dict)
        
        # Align to common dates
        close_df = close_df.dropna(how='all')
        
        return close_df
    
    def _extract_results(
        self,
        portfolio: vbt.Portfolio,
        close_prices: pd.DataFrame,
        signals: Optional[pd.DataFrame],
        strategy_name: str
    ) -> BacktestResult:
        """
        Extract results from vectorbt portfolio.
        
        Args:
            portfolio: Vectorbt Portfolio object
            close_prices: Close price DataFrame
            signals: Signal DataFrame (optional)
            strategy_name: Name of strategy
        
        Returns:
            BacktestResult object
        """
        # Extract key series
        equity_curve = portfolio.value()
        returns = portfolio.returns()
        
        # Extract trades
        trades_df = portfolio.trades.records_readable
        
        # Normalize column names to match standard engine format
        # VectorBT uses capitalized column names (e.g., "Exit Timestamp", "Entry Price")
        # but the rest of the codebase expects lowercase with underscores (e.g., "exit_timestamp", "entry_price")
        # This ensures consistency between vectorized and standard engines
        column_mapping = {
            'Entry Timestamp': 'entry_timestamp',
            'Exit Timestamp': 'exit_timestamp',
            'Entry Price': 'entry_price',
            'Exit Price': 'exit_price',
            'Entry Fees': 'entry_fees',
            'Exit Fees': 'exit_fees',
            'PnL': 'pnl',
            'Return': 'pnl_pct',
            'Direction': 'direction',
            'Status': 'status',
            'Size': 'quantity',
            'Duration': 'duration',
            'Column': 'symbol'
        }
        
        # Rename columns if they exist
        trades_df = trades_df.rename(columns={k: v for k, v in column_mapping.items() if k in trades_df.columns})
        
        # Ensure pnl_pct is in percentage format (0-100) if it's in decimal format (0-1)
        if 'pnl_pct' in trades_df.columns and not trades_df.empty:
            # Check if values are likely in decimal format (between -1 and 1)
            if trades_df['pnl_pct'].abs().max() <= 1:
                trades_df['pnl_pct'] = trades_df['pnl_pct'] * 100
        
        # Calculate comprehensive metrics
        try:
            from .vectorized_metrics import VectorizedMetricsCalculator
        except ImportError:
            from src.backtesting.vectorized_metrics import VectorizedMetricsCalculator
        metrics_calc = VectorizedMetricsCalculator(freq=self.freq)
        metrics = metrics_calc.calculate_all_metrics(
            returns=returns,
            equity_curve=equity_curve,
            trades=trades_df,
            risk_free_rate=self.risk_free_rate
        )
        
        # Get positions
        positions_df = portfolio.positions.records_readable
        
        # Create result
        result = BacktestResult(
            strategy_name=strategy_name,
            start_date=close_prices.index[0],
            end_date=close_prices.index[-1],
            initial_capital=self.initial_capital,
            final_capital=float(equity_curve.iloc[-1]) if len(equity_curve) > 0 else self.initial_capital,
            returns=returns,
            positions=positions_df,
            trades=trades_df,
            metrics=metrics,
            equity_curve=equity_curve,
            metadata={
                'commission': self.commission,
                'slippage': self.slippage,
                'risk_free_rate': self.risk_free_rate,
                'freq': self.freq,
                'vectorbt_stats': portfolio.stats().to_dict()
            }
        )
        
        return result


class SignalGenerator:
    """
    Utility class for generating common trading signals in vectorized form.
    """
    
    @staticmethod
    def momentum_signals(
        prices: pd.DataFrame,
        lookback: int = 252,
        top_n: Optional[int] = None,
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Generate momentum-based signals.
        
        Args:
            prices: Close prices DataFrame
            lookback: Lookback period for momentum calculation
            top_n: Select top N assets by momentum (None for all)
            normalize: Normalize signals to sum to 1
        
        Returns:
            Signal DataFrame with same shape as prices
        """
        # Calculate momentum (returns over lookback)
        momentum = prices.pct_change(lookback)
        
        # Create signals matrix
        signals = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
        
        # For each date, select assets with positive momentum
        for date in momentum.index[lookback:]:
            mom_scores = momentum.loc[date]
            
            # Filter positive momentum
            positive_mom = mom_scores[mom_scores > 0]
            
            if len(positive_mom) > 0:
                if top_n:
                    # Select top N
                    selected = positive_mom.nlargest(top_n)
                else:
                    selected = positive_mom
                
                # Assign weights
                if normalize:
                    weights = selected / selected.sum()
                else:
                    weights = pd.Series(1.0 / len(selected), index=selected.index)
                
                signals.loc[date, weights.index] = weights.values
        
        return signals
    
    @staticmethod
    def sma_crossover_signals(
        prices: pd.DataFrame,
        fast_window: int = 50,
        slow_window: int = 200
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate SMA crossover entry/exit signals.
        
        Args:
            prices: Close prices DataFrame
            fast_window: Fast SMA window
            slow_window: Slow SMA window
        
        Returns:
            Tuple of (entries, exits) as boolean DataFrames
        """
        # Calculate SMAs
        fast_sma = prices.rolling(window=fast_window).mean()
        slow_sma = prices.rolling(window=slow_window).mean()
        
        # Generate signals
        entries = (fast_sma > slow_sma) & (fast_sma.shift(1) <= slow_sma.shift(1))
        exits = (fast_sma < slow_sma) & (fast_sma.shift(1) >= slow_sma.shift(1))
        
        return entries, exits
    
    @staticmethod
    def mean_reversion_signals(
        prices: pd.DataFrame,
        window: int = 20,
        entry_std: float = 2.0,
        exit_std: float = 0.5
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate mean reversion entry/exit signals.
        
        Args:
            prices: Close prices DataFrame
            window: Rolling window for mean/std calculation
            entry_std: Standard deviations from mean for entry
            exit_std: Standard deviations from mean for exit
        
        Returns:
            Tuple of (entries, exits) as boolean DataFrames
        """
        # Calculate z-scores
        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()
        z_scores = (prices - rolling_mean) / rolling_std
        
        # Generate signals (buy when oversold, exit when normalized)
        entries = z_scores < -entry_std
        exits = z_scores > -exit_std
        
        return entries, exits
    
    @staticmethod
    def equal_weight_signals(
        prices: pd.DataFrame,
        rebalance_freq: str = 'M'
    ) -> pd.DataFrame:
        """
        Generate equal-weight rebalancing signals.
        
        Args:
            prices: Close prices DataFrame
            rebalance_freq: Rebalancing frequency ('D', 'W', 'M', 'Q', 'Y')
        
        Returns:
            Signal DataFrame with equal weights at rebalance dates
        """
        n_assets = len(prices.columns)
        weight = 1.0 / n_assets
        
        # Create signals
        signals = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
        
        # Determine rebalance dates
        if rebalance_freq == 'M':
            rebalance_mask = prices.index.to_series().dt.is_month_end
        elif rebalance_freq == 'Q':
            rebalance_mask = prices.index.to_series().dt.is_quarter_end
        elif rebalance_freq == 'Y':
            rebalance_mask = prices.index.to_series().dt.is_year_end
        elif rebalance_freq == 'W':
            rebalance_mask = prices.index.to_series().dt.dayofweek == 4  # Friday
        else:  # Daily
            rebalance_mask = pd.Series(True, index=prices.index)
        
        # Set equal weights on rebalance dates
        signals.loc[rebalance_mask] = weight
        
        return signals
