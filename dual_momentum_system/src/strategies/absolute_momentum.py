"""
Absolute Momentum strategy plugin.

Implements time-series momentum / trend-following approach.
Only invests when asset shows positive momentum vs historical baseline.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np
from loguru import logger

from ..core.base_strategy import BaseStrategy
from ..core.types import MomentumType, PriceData, Signal


class AbsoluteMomentumStrategy(BaseStrategy):
    """
    Absolute Momentum (Time-Series Momentum) Strategy.
    
    Invests in assets when they show positive trend (momentum > threshold).
    Exits to cash/safe asset when trend turns negative.
    
    This is a pure trend-following approach without relative comparison.
    
    Configuration:
        - lookback_period: Momentum calculation period (default: 252)
        - threshold: Minimum momentum to invest (default: 0.0)
        - rebalance_frequency: Rebalancing frequency (default: 'monthly')
        - safe_asset: Asset to hold when momentum negative (default: None)
        - use_moving_average: Use MA crossover instead of raw momentum (default: False)
        - fast_ma: Fast moving average period if using MA (default: 50)
        - slow_ma: Slow moving average period if using MA (default: 200)
        - strength_method: How to calculate signal strength (default: 'binary')
            * 'binary': All passing signals get strength=1.0 (equal weight)
            * 'linear': Linear scaling from threshold to threshold+scale_range
            * 'proportional': Strength proportional to momentum value
            * 'momentum_ratio': Strength = momentum / max(abs(momentum))
        - strength_scale_range: For 'linear' method, range over which to scale (default: 0.10)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Absolute Momentum strategy.
        
        Args:
            config: Strategy configuration
        """
        default_config = {
            'lookback_period': 252,
            'threshold': 0.0,
            'rebalance_frequency': 'monthly',
            'safe_asset': None,
            'use_moving_average': False,
            'fast_ma': 50,
            'slow_ma': 200,
            'signal_threshold': 0.0,
            'strength_method': 'binary',
            'strength_scale_range': 0.10,
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(default_config)
        
        self.lookback_period = self.config['lookback_period']
        self.threshold = self.config['threshold']
        self.safe_asset = self.config['safe_asset']
        self.use_ma = self.config['use_moving_average']
        self.fast_ma = self.config['fast_ma']
        self.slow_ma = self.config['slow_ma']
        self.strength_method = self.config['strength_method']
        self.strength_scale_range = self.config['strength_scale_range']
    
    def calculate_momentum(
        self,
        price_data: Union[PriceData, Dict[str, PriceData]]
    ) -> Union[pd.Series, Dict[str, pd.Series]]:
        """
        Calculate absolute momentum.
        
        If use_moving_average is True, calculates MA crossover signal.
        Otherwise, calculates simple total return over lookback period.
        
        Args:
            price_data: Price data for assets
        
        Returns:
            Momentum scores
        """
        if isinstance(price_data, PriceData):
            return self._calculate_single_momentum(price_data)
        
        # Multiple assets
        momentum_dict = {}
        for symbol, data in price_data.items():
            momentum_dict[symbol] = self._calculate_single_momentum(data)
        
        return momentum_dict
    
    def _calculate_single_momentum(self, price_data: PriceData) -> pd.Series:
        """
        Calculate momentum for single asset.
        
        Args:
            price_data: Price data
        
        Returns:
            Momentum series
        """
        closes = price_data.data['close']
        
        if self.use_ma:
            # Moving average crossover
            fast = closes.rolling(window=self.fast_ma).mean()
            slow = closes.rolling(window=self.slow_ma).mean()
            
            # Momentum = (fast - slow) / slow
            # Positive when fast MA > slow MA (uptrend)
            momentum = (fast - slow) / slow
            
        else:
            # Simple total return momentum
            momentum = closes.pct_change(self.lookback_period)
        
        return momentum
    
    def generate_signals(
        self,
        price_data: Union[PriceData, Dict[str, PriceData]]
    ) -> List[Signal]:
        """
        Generate trading signals based on absolute momentum.
        
        Process:
        1. Calculate momentum for each asset
        2. Generate long signal if momentum > threshold
        3. Generate safe asset signal if momentum <= threshold
        
        Args:
            price_data: Price data
        
        Returns:
            List of signals
        """
        signals = []
        
        # Handle single asset
        if isinstance(price_data, PriceData):
            return self._generate_single_asset_signals(price_data)
        
        # Handle multiple assets
        momentum_dict = self.calculate_momentum(price_data)
        
        # Get latest momentum for each asset
        latest_signals = {}
        latest_timestamp = None
        
        for symbol, momentum_series in momentum_dict.items():
            if len(momentum_series) > 0:
                latest_mom = momentum_series.iloc[-1]
                if not pd.isna(latest_mom):
                    latest_signals[symbol] = latest_mom
                    if latest_timestamp is None:
                        latest_timestamp = momentum_series.index[-1]
        
        if not latest_signals or latest_timestamp is None:
            return signals
        
        # Generate signals for assets with positive momentum
        assets_with_signal = []
        
        # First pass: collect assets that pass threshold
        passing_assets = {}
        for symbol, momentum in latest_signals.items():
            if momentum > self.threshold:
                passing_assets[symbol] = momentum
        
        # Calculate strengths based on chosen method
        if passing_assets:
            strengths = self._calculate_signal_strengths(passing_assets)
            
            for symbol, momentum in passing_assets.items():
                strength = strengths.get(symbol, 1.0)
                
                signal = Signal(
                    timestamp=latest_timestamp,
                    symbol=symbol,
                    direction=1,
                    strength=strength,
                    metadata={
                        'momentum_score': momentum,
                        'strategy': 'absolute_momentum',
                        'lookback_period': self.lookback_period,
                        'threshold': self.threshold,
                        'strength_method': self.strength_method
                    }
                )
                signals.append(signal)
                assets_with_signal.append(symbol)
        
        # If no assets have positive momentum and safe asset configured
        if len(signals) == 0 and self.safe_asset:
            signal = Signal(
                timestamp=latest_timestamp,
                symbol=self.safe_asset,
                direction=1,
                strength=1.0,
                metadata={
                    'momentum_score': 0.0,
                    'strategy': 'absolute_momentum',
                    'reason': 'safe_asset',
                    'threshold': self.threshold
                }
            )
            signals.append(signal)
            logger.info(f"No positive momentum. Switching to safe asset: {self.safe_asset}")
        
        if assets_with_signal:
            logger.info(f"Generated signals for: {assets_with_signal}")
        
        return signals
    
    def _generate_single_asset_signals(self, price_data: PriceData) -> List[Signal]:
        """
        Generate signals for single asset.
        
        Args:
            price_data: Price data
        
        Returns:
            List of signals
        """
        momentum = self.calculate_momentum(price_data)
        
        if len(momentum) == 0:
            return []
        
        latest_momentum = momentum.iloc[-1]
        latest_timestamp = momentum.index[-1]
        
        if pd.isna(latest_momentum):
            return []
        
        if latest_momentum > self.threshold:
            # Positive momentum - long signal
            # Calculate strength for single asset
            strengths = self._calculate_signal_strengths({price_data.symbol: latest_momentum})
            strength = strengths.get(price_data.symbol, 1.0)
            
            signal = Signal(
                timestamp=latest_timestamp,
                symbol=price_data.symbol,
                direction=1,
                strength=strength,
                metadata={
                    'momentum_score': latest_momentum,
                    'strategy': 'absolute_momentum',
                    'lookback_period': self.lookback_period,
                    'strength_method': self.strength_method
                }
            )
            return [signal]
        
        elif self.safe_asset:
            # Negative momentum - safe asset
            signal = Signal(
                timestamp=latest_timestamp,
                symbol=self.safe_asset,
                direction=1,
                strength=1.0,
                metadata={
                    'momentum_score': latest_momentum,
                    'strategy': 'absolute_momentum',
                    'reason': 'safe_asset'
                }
            )
            return [signal]
        
        return []
    
    def _calculate_signal_strengths(self, momentum_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate signal strengths for assets based on configured method.
        
        Args:
            momentum_dict: Dictionary mapping symbols to momentum scores
                          (only includes assets that passed threshold filter)
        
        Returns:
            Dictionary mapping symbols to strength values (0.0 to 1.0)
        
        Strength Calculation Methods:
        
        1. 'binary': All assets get equal strength=1.0
           - Simplest approach
           - Best for equal-weighting strategies
           - Example: SPY (10% mom) → 1.0, QQQ (20% mom) → 1.0
        
        2. 'linear': Linear scaling from threshold to threshold + scale_range
           - Smooth scaling over a fixed range
           - Scale range independent of threshold value
           - Example (threshold=0, range=0.1):
             * SPY (5% mom) → 0.5, QQQ (10% mom) → 1.0, DIA (15% mom) → 1.0
        
        3. 'proportional': Strength proportional to momentum magnitude
           - Normalized by sum of all momentums
           - Higher momentum gets more weight
           - Example: SPY (10% mom) → 0.33, QQQ (20% mom) → 0.67
        
        4. 'momentum_ratio': Strength = momentum / max_momentum
           - Normalized by the highest momentum asset
           - Leader gets strength=1.0, others scaled proportionally
           - Example: SPY (10% mom) → 0.5, QQQ (20% mom) → 1.0
        """
        if not momentum_dict:
            return {}
        
        method = self.strength_method.lower()
        strengths = {}
        
        if method == 'binary':
            # All passing assets get equal strength
            for symbol in momentum_dict:
                strengths[symbol] = 1.0
        
        elif method == 'linear':
            # Linear scaling from threshold to threshold + scale_range
            scale_range = self.strength_scale_range
            
            for symbol, momentum in momentum_dict.items():
                # How far above threshold (as fraction of scale_range)
                excess_momentum = momentum - self.threshold
                strength = excess_momentum / scale_range
                # Clamp to [0.0, 1.0]
                strengths[symbol] = min(1.0, max(0.0, strength))
        
        elif method == 'proportional':
            # Strength proportional to momentum, normalized by sum
            # Use absolute values to handle negative thresholds
            total_momentum = sum(abs(m) for m in momentum_dict.values())
            
            if total_momentum > 0:
                for symbol, momentum in momentum_dict.items():
                    strengths[symbol] = abs(momentum) / total_momentum
            else:
                # Fallback to equal weighting
                for symbol in momentum_dict:
                    strengths[symbol] = 1.0 / len(momentum_dict)
        
        elif method == 'momentum_ratio':
            # Normalize by the maximum momentum
            max_momentum = max(abs(m) for m in momentum_dict.values())
            
            if max_momentum > 0:
                for symbol, momentum in momentum_dict.items():
                    strengths[symbol] = abs(momentum) / max_momentum
            else:
                # Fallback to equal weighting
                for symbol in momentum_dict:
                    strengths[symbol] = 1.0
        
        else:
            # Unknown method - log warning and use binary
            logger.warning(
                f"Unknown strength_method '{method}'. "
                f"Using 'binary' instead. Valid options: binary, linear, proportional, momentum_ratio"
            )
            for symbol in momentum_dict:
                strengths[symbol] = 1.0
        
        return strengths
    
    def get_momentum_type(self) -> MomentumType:
        """Return absolute momentum type."""
        return MomentumType.ABSOLUTE
    
    def get_required_history(self) -> int:
        """Return required history."""
        if self.use_ma:
            return max(self.slow_ma, self.lookback_period)
        return self.lookback_period
    
    @classmethod
    def get_version(cls) -> str:
        """Return strategy version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return strategy description."""
        return (
            "Absolute Momentum (Time-Series Momentum) strategy. "
            "Invests when assets show positive trend, exits to cash/safe asset "
            "when trend turns negative. Can use either simple momentum or "
            "moving average crossover for signal generation. Pure trend-following "
            "without relative comparison to other assets."
        )
