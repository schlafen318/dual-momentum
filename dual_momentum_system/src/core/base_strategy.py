"""
Base class for momentum strategy plugins.

This module defines the abstract interface for momentum strategy implementations.
Strategies calculate momentum scores and generate trading signals.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

from .types import MomentumType, PriceData, Signal


class BaseStrategy(ABC):
    """
    Abstract base class for momentum strategy plugins.
    
    Strategy plugins implement different momentum calculation methods:
    - Absolute momentum: Trend-following based on asset's own history
    - Relative momentum: Cross-sectional comparison across assets
    - Dual momentum: Combination of absolute and relative
    
    Example:
        >>> class DualMomentumStrategy(BaseStrategy):
        ...     def calculate_momentum(self, price_data):
        ...         # Calculate 12-month momentum
        ...         returns_12m = price_data.data['close'].pct_change(252)
        ...         return returns_12m
        ...     
        ...     def generate_signals(self, price_data):
        ...         momentum = self.calculate_momentum(price_data)
        ...         # Generate signals based on momentum
        ...         # ...
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the strategy.
        
        Args:
            config: Strategy configuration dictionary. May include:
                   - lookback_period: Period for momentum calculation
                   - threshold: Signal generation threshold
                   - rebalance_frequency: How often to rebalance
                   - universe: Asset universe to trade
        
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config or {}
        self._validate_config()
        self.name = self.get_name()
        self._initialized = True
    
    @abstractmethod
    def calculate_momentum(
        self,
        price_data: Union[PriceData, Dict[str, PriceData]]
    ) -> Union[pd.Series, Dict[str, pd.Series]]:
        """
        Calculate momentum score(s) for asset(s).
        
        For absolute momentum, typically calculates trend strength.
        For relative momentum, ranks assets by performance.
        For dual momentum, combines both approaches.
        
        Args:
            price_data: Price data for one asset (PriceData) or 
                       multiple assets (Dict[symbol, PriceData])
        
        Returns:
            Momentum scores:
            - For single asset: pd.Series with momentum over time
            - For multiple assets: Dict[symbol, pd.Series]
        
        Example:
            >>> momentum = strategy.calculate_momentum(price_data)
            >>> print(momentum.iloc[-1])
            0.15  # 15% momentum
        """
        pass
    
    @abstractmethod
    def generate_signals(
        self,
        price_data: Union[PriceData, Dict[str, PriceData]]
    ) -> List[Signal]:
        """
        Generate trading signals based on momentum.
        
        Signals indicate when to enter, exit, or adjust positions.
        Each signal includes direction (long/short/exit) and strength.
        
        Args:
            price_data: Price data for one or more assets
        
        Returns:
            List of Signal objects
        
        Example:
            >>> signals = strategy.generate_signals(price_data)
            >>> for signal in signals:
            ...     print(f"{signal.symbol}: {signal.direction} ({signal.strength})")
            AAPL: 1 (0.85)
            MSFT: 1 (0.72)
        """
        pass
    
    @abstractmethod
    def get_momentum_type(self) -> MomentumType:
        """
        Return the type of momentum strategy.
        
        Returns:
            MomentumType enum value (ABSOLUTE, RELATIVE, DUAL, or CUSTOM)
        
        Example:
            >>> strategy.get_momentum_type()
            MomentumType.DUAL
        """
        pass
    
    def get_required_history(self) -> int:
        """
        Get the number of periods required for momentum calculation.
        
        This helps ensure sufficient data is available before generating signals.
        
        Returns:
            Number of required periods (e.g., 252 for 1 year of daily data)
        
        Example:
            >>> strategy.get_required_history()
            252
        """
        return self.config.get('lookback_period', 252)
    
    def get_rebalance_frequency(self) -> str:
        """
        Get how often the strategy should rebalance.
        
        Returns:
            Rebalance frequency ('daily', 'weekly', 'monthly', 'quarterly', etc.)
        
        Example:
            >>> strategy.get_rebalance_frequency()
            'monthly'
        """
        return self.config.get('rebalance_frequency', 'monthly')
    
    def calculate_absolute_momentum(
        self,
        price_data: PriceData,
        lookback: Optional[int] = None
    ) -> pd.Series:
        """
        Calculate absolute momentum (trend following).
        
        Absolute momentum compares current price to past price to determine trend.
        Commonly uses total return over a lookback period.
        
        Args:
            price_data: Price data for asset
            lookback: Lookback period in bars (uses config default if None)
        
        Returns:
            Series of absolute momentum scores
        
        Example:
            >>> abs_mom = strategy.calculate_absolute_momentum(price_data, lookback=252)
            >>> print(abs_mom.iloc[-1])
            0.23  # 23% return over lookback period
        """
        if lookback is None:
            lookback = self.get_required_history()
        
        closes = price_data.data['close']
        return closes.pct_change(lookback)
    
    def calculate_relative_momentum(
        self,
        price_data_dict: Dict[str, PriceData],
        lookback: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Calculate relative momentum (cross-sectional ranking).
        
        Relative momentum ranks assets by performance to identify leaders.
        
        Args:
            price_data_dict: Dictionary of price data for multiple assets
            lookback: Lookback period in bars (uses config default if None)
        
        Returns:
            DataFrame with momentum scores for each asset over time
        
        Example:
            >>> rel_mom = strategy.calculate_relative_momentum(price_data_dict, lookback=252)
            >>> print(rel_mom.iloc[-1])
            AAPL    0.35
            MSFT    0.28
            GOOGL   0.22
        """
        if lookback is None:
            lookback = self.get_required_history()
        
        momentum_dict = {}
        for symbol, price_data in price_data_dict.items():
            closes = price_data.data['close']
            momentum_dict[symbol] = closes.pct_change(lookback)
        
        return pd.DataFrame(momentum_dict)
    
    def rank_assets(
        self,
        momentum_scores: Union[pd.Series, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Rank assets by momentum scores.
        
        Args:
            momentum_scores: Momentum scores (Series for single timestamp or 
                           DataFrame for time series)
        
        Returns:
            DataFrame with rankings (1 = highest momentum)
        
        Example:
            >>> rankings = strategy.rank_assets(momentum_scores)
            >>> print(rankings.iloc[-1])
            AAPL     1
            MSFT     2
            GOOGL    3
        """
        if isinstance(momentum_scores, pd.Series):
            return momentum_scores.rank(ascending=False)
        else:
            return momentum_scores.rank(axis=1, ascending=False)
    
    def select_top_n(
        self,
        momentum_scores: pd.Series,
        n: int
    ) -> List[str]:
        """
        Select top N assets by momentum.
        
        Args:
            momentum_scores: Latest momentum scores
            n: Number of assets to select
        
        Returns:
            List of top N symbols
        
        Example:
            >>> top_assets = strategy.select_top_n(momentum_scores, n=5)
            >>> print(top_assets)
            ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META']
        """
        return momentum_scores.nlargest(n).index.tolist()
    
    def apply_absolute_filter(
        self,
        momentum_scores: Union[pd.Series, pd.DataFrame],
        threshold: float = 0.0
    ) -> Union[pd.Series, pd.DataFrame]:
        """
        Filter out assets with absolute momentum below threshold.
        
        This implements the absolute momentum filter in dual momentum.
        
        Args:
            momentum_scores: Momentum scores to filter
            threshold: Minimum momentum threshold (e.g., 0.0 for positive momentum)
        
        Returns:
            Filtered momentum scores (below threshold set to NaN)
        
        Example:
            >>> filtered = strategy.apply_absolute_filter(momentum_scores, threshold=0.0)
            >>> # Only assets with positive momentum remain
        """
        return momentum_scores.where(momentum_scores > threshold)
    
    def calculate_volatility_adjusted_momentum(
        self,
        price_data: PriceData,
        lookback: Optional[int] = None,
        vol_window: int = 20
    ) -> pd.Series:
        """
        Calculate volatility-adjusted momentum.
        
        Adjusts momentum by volatility to account for risk.
        
        Args:
            price_data: Price data
            lookback: Lookback period for momentum
            vol_window: Window for volatility calculation
        
        Returns:
            Series of volatility-adjusted momentum scores
        
        Example:
            >>> vol_adj_mom = strategy.calculate_volatility_adjusted_momentum(price_data)
            >>> # Higher scores indicate better risk-adjusted momentum
        """
        if lookback is None:
            lookback = self.get_required_history()
        
        returns = price_data.data['close'].pct_change()
        momentum = price_data.data['close'].pct_change(lookback)
        volatility = returns.rolling(window=vol_window).std()
        
        # Avoid division by zero
        volatility = volatility.replace(0, np.nan)
        
        return momentum / volatility
    
    def should_rebalance(self, current_date: pd.Timestamp, last_rebalance: pd.Timestamp) -> bool:
        """
        Determine if portfolio should be rebalanced.
        
        Args:
            current_date: Current date
            last_rebalance: Date of last rebalance
        
        Returns:
            True if should rebalance, False otherwise
        
        Example:
            >>> should_rebal = strategy.should_rebalance(current_date, last_rebalance_date)
            >>> if should_rebal:
            ...     # Generate new signals
        """
        frequency = self.get_rebalance_frequency()
        
        if frequency == 'daily':
            return True
        elif frequency == 'weekly':
            return current_date.week != last_rebalance.week
        elif frequency == 'monthly':
            return current_date.month != last_rebalance.month
        elif frequency == 'quarterly':
            return current_date.quarter != last_rebalance.quarter
        elif frequency == 'yearly':
            return current_date.year != last_rebalance.year
        else:
            return False
    
    def get_universe(self) -> Optional[List[str]]:
        """
        Get the asset universe for this strategy.
        
        Returns:
            List of symbols in the universe, or None for no restriction
        
        Example:
            >>> universe = strategy.get_universe()
            >>> print(universe)
            ['SPY', 'EFA', 'EEM', 'AGG', 'TLT']
        """
        return self.config.get('universe')
    
    def get_position_count(self) -> int:
        """
        Get maximum number of positions to hold.
        
        Returns:
            Maximum number of positions
        
        Example:
            >>> max_positions = strategy.get_position_count()
            >>> print(max_positions)
            5
        """
        return self.config.get('position_count', 1)
    
    def get_signal_threshold(self) -> float:
        """
        Get minimum signal strength threshold.
        
        Returns:
            Threshold value (0.0 to 1.0)
        
        Example:
            >>> threshold = strategy.get_signal_threshold()
            >>> print(threshold)
            0.5
        """
        return self.config.get('signal_threshold', 0.0)
    
    def validate_signals(self, signals: List[Signal]) -> List[Signal]:
        """
        Validate and filter signals.
        
        Removes invalid signals and applies threshold filtering.
        
        Args:
            signals: List of signals to validate
        
        Returns:
            List of validated signals
        
        Example:
            >>> validated = strategy.validate_signals(raw_signals)
            >>> # Weak signals filtered out
        """
        threshold = self.get_signal_threshold()
        return [s for s in signals if s.strength >= threshold]
    
    def backtest_ready(self, price_data: Union[PriceData, Dict[str, PriceData]]) -> bool:
        """
        Check if there's sufficient data for backtesting.
        
        Args:
            price_data: Price data to check
        
        Returns:
            True if ready, False otherwise
        
        Example:
            >>> if strategy.backtest_ready(price_data):
            ...     results = backtest_engine.run(strategy, price_data)
        """
        required_history = self.get_required_history()
        
        if isinstance(price_data, PriceData):
            return len(price_data.data) >= required_history
        else:
            return all(len(pd.data) >= required_history for pd in price_data.values())
    
    def _validate_config(self) -> None:
        """
        Validate configuration parameters.
        
        Override this method to add custom validation logic.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate lookback period
        if 'lookback_period' in self.config:
            if self.config['lookback_period'] <= 0:
                raise ValueError("lookback_period must be positive")
        
        # Validate position count
        if 'position_count' in self.config:
            if self.config['position_count'] <= 0:
                raise ValueError("position_count must be positive")
        
        # Validate signal threshold
        if 'signal_threshold' in self.config:
            threshold = self.config['signal_threshold']
            if not 0.0 <= threshold <= 1.0:
                raise ValueError("signal_threshold must be between 0.0 and 1.0")
    
    @classmethod
    def get_name(cls) -> str:
        """
        Return the strategy name.
        
        Returns:
            Class name as string
        
        Example:
            >>> DualMomentumStrategy.get_name()
            'DualMomentumStrategy'
        """
        return cls.__name__
    
    @classmethod
    def get_version(cls) -> str:
        """
        Return the plugin version.
        
        Override to provide version information.
        
        Returns:
            Version string
        """
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """
        Return a description of the strategy.
        
        Returns:
            Strategy description
        
        Example:
            >>> print(DualMomentumStrategy.get_description())
            'Dual momentum combines absolute and relative momentum...'
        """
        return cls.__doc__ or "No description available"
    
    def __repr__(self) -> str:
        """String representation of the strategy."""
        return f"{self.get_name()}(type={self.get_momentum_type().value})"
