"""
Dual Momentum strategy plugin.

Implements the dual momentum approach combining absolute and relative momentum,
popularized by Gary Antonacci.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np
from loguru import logger

from ..core.base_strategy import BaseStrategy
from ..core.types import MomentumType, PriceData, Signal


class DualMomentumStrategy(BaseStrategy):
    """
    Dual Momentum Strategy.
    
    Combines:
    1. Absolute Momentum: Only holds assets with positive trend (vs cash/bonds)
    2. Relative Momentum: Ranks assets and selects top performers
    
    This approach aims to capture trend-following benefits while avoiding
    drawdowns through the absolute momentum filter.
    
    Configuration:
        - lookback_period: Momentum calculation period (default: 252 trading days)
        - rebalance_frequency: How often to rebalance (default: 'monthly')
        - position_count: Number of top assets to hold (default: 1)
        - absolute_threshold: Minimum momentum to be invested (default: 0.0)
        - use_volatility_adjustment: Adjust for volatility (default: False)
        - safe_asset: Symbol for safe asset (bonds/cash) when momentum negative (default: None)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Dual Momentum strategy.
        
        Args:
            config: Strategy configuration dictionary
        """
        # Set defaults
        default_config = {
            'lookback_period': 252,
            'rebalance_frequency': 'monthly',
            'position_count': 1,
            'absolute_threshold': 0.0,
            'use_volatility_adjustment': False,
            'safe_asset': None,
            'signal_threshold': 0.0,
        }
        
        # Merge with provided config
        if config:
            default_config.update(config)
        
        super().__init__(default_config)
        
        self.lookback_period = self.config['lookback_period']
        self.use_vol_adj = self.config['use_volatility_adjustment']
        self.safe_asset = self.config['safe_asset']
        self.absolute_threshold = self.config['absolute_threshold']
    
    def calculate_momentum(
        self,
        price_data: Union[PriceData, Dict[str, PriceData]]
    ) -> Union[pd.Series, Dict[str, pd.Series]]:
        """
        Calculate momentum scores.
        
        For dual momentum:
        1. Calculate total return over lookback period
        2. Optionally adjust for volatility
        
        Args:
            price_data: Price data for one or more assets
        
        Returns:
            Momentum scores (Series for single asset, Dict for multiple)
        """
        # Handle single asset
        if isinstance(price_data, PriceData):
            return self._calculate_single_momentum(price_data)
        
        # Handle multiple assets
        momentum_dict = {}
        for symbol, data in price_data.items():
            momentum_dict[symbol] = self._calculate_single_momentum(data)
        
        return momentum_dict
    
    def _calculate_single_momentum(self, price_data: PriceData) -> pd.Series:
        """
        Calculate momentum for a single asset.
        
        Args:
            price_data: Price data for asset
        
        Returns:
            Momentum score series
        """
        closes = price_data.data['close']
        
        if self.use_vol_adj:
            # Volatility-adjusted momentum
            returns = closes.pct_change()
            momentum = closes.pct_change(self.lookback_period)
            volatility = returns.rolling(window=min(20, self.lookback_period)).std()
            
            # Avoid division by zero
            volatility = volatility.replace(0, np.nan)
            vol_adj_momentum = momentum / volatility
            
            return vol_adj_momentum
        else:
            # Simple total return momentum
            momentum = closes.pct_change(self.lookback_period)
            return momentum
    
    def generate_signals(
        self,
        price_data: Union[PriceData, Dict[str, PriceData]]
    ) -> List[Signal]:
        """
        Generate trading signals based on dual momentum.
        
        Process:
        1. Calculate momentum for all assets
        2. Apply absolute momentum filter (must be > threshold)
        3. Rank remaining assets by relative momentum
        4. Generate signals for top N assets
        5. If no assets pass filter, signal safe asset (if configured)
        
        Args:
            price_data: Price data for assets
        
        Returns:
            List of trading signals
        """
        signals = []
        
        # Ensure we have multiple assets for comparison
        if isinstance(price_data, PriceData):
            logger.warning("Dual momentum requires multiple assets for comparison")
            return self._generate_single_asset_signals(price_data)
        
        # Calculate momentum for all assets
        momentum_dict = self.calculate_momentum(price_data)
        
        # Get latest momentum scores
        latest_momentum = {}
        latest_timestamp = None
        
        for symbol, momentum_series in momentum_dict.items():
            if len(momentum_series) > 0:
                latest_momentum[symbol] = momentum_series.iloc[-1]
                if latest_timestamp is None:
                    latest_timestamp = momentum_series.index[-1]
        
        if not latest_momentum or latest_timestamp is None:
            logger.warning("No valid momentum scores available")
            return signals
        
        # Step 1: Apply absolute momentum filter
        filtered_momentum = {
            symbol: score
            for symbol, score in latest_momentum.items()
            if not pd.isna(score) and score > self.absolute_threshold
        }
        
        # Step 2: Rank by relative momentum
        if filtered_momentum:
            sorted_assets = sorted(
                filtered_momentum.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Step 3: Select top N assets
            position_count = self.get_position_count()
            top_assets = sorted_assets[:position_count]
            
            # Generate long signals for top assets
            for symbol, momentum_score in top_assets:
                # Normalize strength (0 to 1 based on relative ranking)
                max_momentum = sorted_assets[0][1]
                if max_momentum > 0:
                    strength = momentum_score / max_momentum
                else:
                    strength = 0.5
                
                strength = max(0.0, min(1.0, strength))
                
                signal = Signal(
                    timestamp=latest_timestamp,
                    symbol=symbol,
                    direction=1,  # Long
                    strength=strength,
                    metadata={
                        'momentum_score': momentum_score,
                        'rank': top_assets.index((symbol, momentum_score)) + 1,
                        'strategy': 'dual_momentum',
                        'lookback_period': self.lookback_period
                    }
                )
                signals.append(signal)
            
            logger.info(f"Generated {len(signals)} long signals for: {[s.symbol for s in signals]}")
        
        else:
            # No assets pass absolute momentum filter
            logger.info("No assets pass absolute momentum filter")
            
            # If safe asset configured, signal it
            if self.safe_asset:
                signal = Signal(
                    timestamp=latest_timestamp,
                    symbol=self.safe_asset,
                    direction=1,  # Long
                    strength=1.0,
                    metadata={
                        'momentum_score': 0.0,
                        'rank': 1,
                        'strategy': 'dual_momentum',
                        'reason': 'safe_asset',
                        'lookback_period': self.lookback_period
                    }
                )
                signals.append(signal)
                logger.info(f"Switched to safe asset: {self.safe_asset}")
        
        return signals
    
    def _generate_single_asset_signals(self, price_data: PriceData) -> List[Signal]:
        """
        Generate signals for single asset (absolute momentum only).
        
        Args:
            price_data: Price data for single asset
        
        Returns:
            List of signals
        """
        momentum = self.calculate_momentum(price_data)
        
        if len(momentum) == 0:
            return []
        
        latest_momentum = momentum.iloc[-1]
        latest_timestamp = momentum.index[-1]
        
        # Check absolute momentum
        if not pd.isna(latest_momentum) and latest_momentum > self.absolute_threshold:
            # Long signal
            signal = Signal(
                timestamp=latest_timestamp,
                symbol=price_data.symbol,
                direction=1,
                strength=min(1.0, abs(latest_momentum)),
                metadata={
                    'momentum_score': latest_momentum,
                    'strategy': 'dual_momentum',
                    'lookback_period': self.lookback_period
                }
            )
            return [signal]
        
        elif self.safe_asset:
            # Safe asset signal
            signal = Signal(
                timestamp=latest_timestamp,
                symbol=self.safe_asset,
                direction=1,
                strength=1.0,
                metadata={
                    'momentum_score': latest_momentum,
                    'strategy': 'dual_momentum',
                    'reason': 'safe_asset',
                    'lookback_period': self.lookback_period
                }
            )
            return [signal]
        
        return []
    
    def get_momentum_type(self) -> MomentumType:
        """Return dual momentum type."""
        return MomentumType.DUAL
    
    def get_required_history(self) -> int:
        """Return required history length."""
        # Need extra data for volatility calculation if enabled
        if self.use_vol_adj:
            return self.lookback_period + 20
        return self.lookback_period
    
    @classmethod
    def get_version(cls) -> str:
        """Return strategy version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return strategy description."""
        return (
            "Dual Momentum Strategy combining absolute and relative momentum. "
            "Ranks assets by performance (relative momentum) but only invests "
            "when trend is positive (absolute momentum). Can rotate to a safe "
            "asset when all risky assets show negative momentum. "
            "Based on research by Gary Antonacci."
        )
