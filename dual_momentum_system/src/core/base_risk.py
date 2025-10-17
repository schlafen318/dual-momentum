"""
Base class for risk management plugins.

This module defines the abstract interface for risk management implementations.
Risk managers handle position sizing, risk limits, and portfolio constraints.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from .types import Position, Signal, PortfolioState


class BaseRiskManager(ABC):
    """
    Abstract base class for risk management plugins.
    
    Risk managers implement:
    - Position sizing based on risk parameters
    - Portfolio-level risk constraints
    - Drawdown limits
    - Volatility targeting
    - Leverage limits
    
    Example:
        >>> class VolatilityTargetingRisk(BaseRiskManager):
        ...     def calculate_position_size(self, signal, portfolio_value, positions):
        ...         target_vol = self.config['target_volatility']
        ...         asset_vol = self.estimate_volatility(signal.symbol)
        ...         size = (portfolio_value * target_vol) / asset_vol
        ...         return size
        ...     # ... implement other methods
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the risk manager.
        
        Args:
            config: Risk management configuration. May include:
                   - max_position_size: Maximum position as % of portfolio
                   - max_leverage: Maximum portfolio leverage
                   - max_drawdown: Maximum allowed drawdown
                   - target_volatility: Target portfolio volatility
                   - position_limit: Maximum number of positions
        
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config or {}
        self._validate_config()
        self._initialized = True
    
    @abstractmethod
    def calculate_position_size(
        self,
        signal: Signal,
        portfolio_value: float,
        current_positions: Dict[str, Position],
        price_data: Optional[Any] = None
    ) -> float:
        """
        Calculate position size based on risk parameters.
        
        This is the core method that determines how much capital to allocate
        to a new or existing position.
        
        Args:
            signal: Trading signal with direction and strength
            portfolio_value: Current total portfolio value
            current_positions: Dictionary of currently held positions
            price_data: Optional price data for volatility/risk calculations
        
        Returns:
            Position size (number of units/shares to trade)
            Returns 0 if position should not be taken
        
        Example:
            >>> size = risk_manager.calculate_position_size(
            ...     signal=Signal(...),
            ...     portfolio_value=100000,
            ...     current_positions={},
            ...     price_data=price_data
            ... )
            >>> print(size)
            50.0  # Buy 50 shares
        """
        pass
    
    @abstractmethod
    def check_risk_limits(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: Optional[Signal] = None
    ) -> bool:
        """
        Check if risk limits are satisfied.
        
        Validates that the portfolio (and any proposed trade) stays within
        defined risk parameters.
        
        Args:
            portfolio_state: Current portfolio state
            proposed_trade: Proposed trade signal (if any)
        
        Returns:
            True if within risk limits, False otherwise
        
        Example:
            >>> if risk_manager.check_risk_limits(portfolio_state, signal):
            ...     # Execute trade
            ...     pass
        """
        pass
    
    @abstractmethod
    def get_max_leverage(self) -> float:
        """
        Get maximum allowed leverage.
        
        Returns:
            Maximum leverage ratio (e.g., 1.0 = no leverage, 2.0 = 2x leverage)
        
        Example:
            >>> max_lev = risk_manager.get_max_leverage()
            >>> print(max_lev)
            1.0  # No leverage allowed
        """
        pass
    
    def get_max_position_size(self) -> float:
        """
        Get maximum position size as fraction of portfolio.
        
        Returns:
            Maximum position size (0.0 to 1.0)
        
        Example:
            >>> max_pos = risk_manager.get_max_position_size()
            >>> print(max_pos)
            0.20  # Max 20% per position
        """
        return self.config.get('max_position_size', 1.0)
    
    def get_max_drawdown_limit(self) -> float:
        """
        Get maximum allowed drawdown.
        
        Returns:
            Maximum drawdown as fraction (e.g., 0.20 for 20% max drawdown)
        
        Example:
            >>> max_dd = risk_manager.get_max_drawdown_limit()
            >>> print(max_dd)
            0.20  # Stop trading if down 20%
        """
        return self.config.get('max_drawdown', 1.0)
    
    def get_target_volatility(self) -> Optional[float]:
        """
        Get target portfolio volatility for volatility targeting.
        
        Returns:
            Target annualized volatility, or None if not using vol targeting
        
        Example:
            >>> target_vol = risk_manager.get_target_volatility()
            >>> print(target_vol)
            0.15  # Target 15% annualized volatility
        """
        return self.config.get('target_volatility')
    
    def get_position_limit(self) -> Optional[int]:
        """
        Get maximum number of simultaneous positions.
        
        Returns:
            Maximum position count, or None for no limit
        
        Example:
            >>> limit = risk_manager.get_position_limit()
            >>> print(limit)
            10  # Max 10 positions at once
        """
        return self.config.get('position_limit')
    
    def adjust_for_volatility(
        self,
        base_size: float,
        asset_volatility: float,
        target_volatility: Optional[float] = None
    ) -> float:
        """
        Adjust position size based on volatility targeting.
        
        Scales position size inversely with volatility to achieve
        consistent risk across assets.
        
        Args:
            base_size: Base position size
            asset_volatility: Estimated asset volatility
            target_volatility: Target volatility (uses config if None)
        
        Returns:
            Volatility-adjusted position size
        
        Example:
            >>> adjusted = risk_manager.adjust_for_volatility(
            ...     base_size=100,
            ...     asset_volatility=0.30,
            ...     target_volatility=0.15
            ... )
            >>> print(adjusted)
            50.0  # Halved because asset is 2x more volatile than target
        """
        if target_volatility is None:
            target_volatility = self.get_target_volatility()
        
        if target_volatility is None or asset_volatility == 0:
            return base_size
        
        return base_size * (target_volatility / asset_volatility)
    
    def adjust_for_correlation(
        self,
        base_size: float,
        asset_symbol: str,
        current_positions: Dict[str, Position],
        correlation_matrix: pd.DataFrame
    ) -> float:
        """
        Adjust position size based on correlation with existing positions.
        
        Reduces size if highly correlated with existing holdings.
        
        Args:
            base_size: Base position size
            asset_symbol: Symbol of new asset
            current_positions: Current positions
            correlation_matrix: Asset correlation matrix
        
        Returns:
            Correlation-adjusted position size
        
        Example:
            >>> adjusted = risk_manager.adjust_for_correlation(
            ...     base_size=100,
            ...     asset_symbol='MSFT',
            ...     current_positions={'AAPL': position},
            ...     correlation_matrix=corr_matrix
            ... )
        """
        if asset_symbol not in correlation_matrix.index:
            return base_size
        
        # Calculate average correlation with existing positions
        held_symbols = list(current_positions.keys())
        if not held_symbols:
            return base_size
        
        correlations = []
        for symbol in held_symbols:
            if symbol in correlation_matrix.columns:
                corr = correlation_matrix.loc[asset_symbol, symbol]
                correlations.append(abs(corr))
        
        if not correlations:
            return base_size
        
        avg_correlation = np.mean(correlations)
        
        # Reduce size based on correlation (simple linear adjustment)
        adjustment_factor = 1.0 - (avg_correlation * 0.5)  # Max 50% reduction
        return base_size * max(adjustment_factor, 0.5)  # Min 50% of base size
    
    def check_concentration_limits(
        self,
        asset_symbol: str,
        position_size: float,
        asset_price: float,
        portfolio_value: float,
        current_positions: Dict[str, Position]
    ) -> bool:
        """
        Check if position would violate concentration limits.
        
        Args:
            asset_symbol: Symbol to check
            position_size: Proposed position size
            asset_price: Current asset price
            portfolio_value: Total portfolio value
            current_positions: Current positions
        
        Returns:
            True if within limits, False otherwise
        
        Example:
            >>> ok = risk_manager.check_concentration_limits(
            ...     asset_symbol='AAPL',
            ...     position_size=100,
            ...     asset_price=150,
            ...     portfolio_value=100000,
            ...     current_positions={}
            ... )
            >>> print(ok)
            True
        """
        position_value = position_size * asset_price
        position_pct = position_value / portfolio_value
        
        max_position = self.get_max_position_size()
        return position_pct <= max_position
    
    def check_leverage_limit(
        self,
        portfolio_state: PortfolioState,
        additional_exposure: float = 0.0
    ) -> bool:
        """
        Check if leverage is within limits.
        
        Args:
            portfolio_state: Current portfolio state
            additional_exposure: Additional exposure from proposed trade
        
        Returns:
            True if within leverage limit, False otherwise
        
        Example:
            >>> ok = risk_manager.check_leverage_limit(portfolio_state)
            >>> if not ok:
            ...     # Reduce position size or reject trade
        """
        total_exposure = portfolio_state.invested_value + additional_exposure
        leverage = total_exposure / portfolio_state.portfolio_value
        
        return leverage <= self.get_max_leverage()
    
    def check_drawdown_limit(
        self,
        current_value: float,
        peak_value: float
    ) -> bool:
        """
        Check if drawdown is within acceptable limits.
        
        Args:
            current_value: Current portfolio value
            peak_value: Historical peak portfolio value
        
        Returns:
            True if drawdown acceptable, False if limit breached
        
        Example:
            >>> ok = risk_manager.check_drawdown_limit(
            ...     current_value=80000,
            ...     peak_value=100000
            ... )
            >>> print(ok)
            False  # 20% drawdown may exceed limit
        """
        if peak_value == 0:
            return True
        
        drawdown = (peak_value - current_value) / peak_value
        max_drawdown = self.get_max_drawdown_limit()
        
        return drawdown <= max_drawdown
    
    def estimate_portfolio_volatility(
        self,
        positions: Dict[str, Position],
        returns_data: Dict[str, pd.Series],
        window: int = 20
    ) -> float:
        """
        Estimate current portfolio volatility.
        
        Args:
            positions: Current positions
            returns_data: Historical returns for each asset
            window: Lookback window for volatility calculation
        
        Returns:
            Estimated annualized portfolio volatility
        
        Example:
            >>> vol = risk_manager.estimate_portfolio_volatility(
            ...     positions=current_positions,
            ...     returns_data=returns_dict
            ... )
            >>> print(vol)
            0.18  # 18% annualized volatility
        """
        if not positions:
            return 0.0
        
        # Calculate position weights
        total_value = sum(pos.market_value for pos in positions.values())
        weights = {sym: pos.market_value / total_value for sym, pos in positions.items()}
        
        # Get recent returns
        recent_returns = {}
        for symbol in positions.keys():
            if symbol in returns_data:
                recent_returns[symbol] = returns_data[symbol].tail(window)
        
        if not recent_returns:
            return 0.0
        
        # Create returns DataFrame
        returns_df = pd.DataFrame(recent_returns)
        
        # Calculate weighted portfolio returns
        weight_series = pd.Series(weights)
        portfolio_returns = (returns_df * weight_series).sum(axis=1)
        
        # Annualize volatility (assuming daily data)
        return portfolio_returns.std() * np.sqrt(252)
    
    def calculate_kelly_size(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        portfolio_value: float,
        kelly_fraction: float = 0.5
    ) -> float:
        """
        Calculate position size using Kelly Criterion.
        
        Args:
            win_rate: Historical win rate (0.0 to 1.0)
            avg_win: Average winning trade size
            avg_loss: Average losing trade size (positive number)
            portfolio_value: Total portfolio value
            kelly_fraction: Fraction of Kelly to use (for safety)
        
        Returns:
            Position size in dollars
        
        Example:
            >>> size = risk_manager.calculate_kelly_size(
            ...     win_rate=0.55,
            ...     avg_win=100,
            ...     avg_loss=80,
            ...     portfolio_value=100000,
            ...     kelly_fraction=0.5
            ... )
        """
        if avg_loss == 0 or win_rate >= 1.0 or win_rate <= 0.0:
            return 0.0
        
        win_loss_ratio = avg_win / avg_loss
        kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Apply safety fraction and ensure non-negative
        kelly_pct = max(kelly_pct * kelly_fraction, 0.0)
        
        return portfolio_value * kelly_pct
    
    def get_emergency_stop_threshold(self) -> Optional[float]:
        """
        Get threshold for emergency stop (halt all trading).
        
        Returns:
            Drawdown threshold for emergency stop, or None
        
        Example:
            >>> threshold = risk_manager.get_emergency_stop_threshold()
            >>> print(threshold)
            0.25  # Stop all trading if down 25%
        """
        return self.config.get('emergency_stop_threshold')
    
    def should_halt_trading(
        self,
        current_value: float,
        peak_value: float
    ) -> bool:
        """
        Determine if trading should be halted due to losses.
        
        Args:
            current_value: Current portfolio value
            peak_value: Historical peak value
        
        Returns:
            True if trading should stop, False otherwise
        
        Example:
            >>> halt = risk_manager.should_halt_trading(75000, 100000)
            >>> if halt:
            ...     # Close all positions and stop trading
        """
        threshold = self.get_emergency_stop_threshold()
        if threshold is None:
            return False
        
        if peak_value == 0:
            return False
        
        drawdown = (peak_value - current_value) / peak_value
        return drawdown >= threshold
    
    def _validate_config(self) -> None:
        """
        Validate configuration parameters.
        
        Override this method to add custom validation logic.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate max_position_size
        if 'max_position_size' in self.config:
            max_pos = self.config['max_position_size']
            if not 0.0 < max_pos <= 1.0:
                raise ValueError("max_position_size must be between 0.0 and 1.0")
        
        # Validate max_leverage
        if 'max_leverage' in self.config:
            max_lev = self.config['max_leverage']
            if max_lev < 1.0:
                raise ValueError("max_leverage must be >= 1.0")
        
        # Validate max_drawdown
        if 'max_drawdown' in self.config:
            max_dd = self.config['max_drawdown']
            if not 0.0 < max_dd <= 1.0:
                raise ValueError("max_drawdown must be between 0.0 and 1.0")
        
        # Validate target_volatility
        if 'target_volatility' in self.config:
            target_vol = self.config['target_volatility']
            if target_vol <= 0.0:
                raise ValueError("target_volatility must be positive")
    
    @classmethod
    def get_name(cls) -> str:
        """
        Return the risk manager name.
        
        Returns:
            Class name as string
        
        Example:
            >>> VolatilityTargetingRisk.get_name()
            'VolatilityTargetingRisk'
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
    
    def __repr__(self) -> str:
        """String representation of the risk manager."""
        return f"{self.get_name()}(max_leverage={self.get_max_leverage()})"
