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
from ..core.types import MomentumType, PriceData, Signal, SignalReason


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
        - blend_zone_lower: Lower bound for blend zone (default: -0.05)
        - blend_zone_upper: Upper bound for blend zone (default: 0.05)
        - enable_blending: Enable gradual allocation blending (default: True)
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
            'blend_zone_lower': -0.05,
            'blend_zone_upper': 0.05,
            'enable_blending': True,
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
        self.blend_zone_lower = self.config['blend_zone_lower']
        self.blend_zone_upper = self.config['blend_zone_upper']
        self.enable_blending = self.config['enable_blending']
        
        # Validate safe asset configuration
        self._validate_safe_asset_config()
    
    def _validate_safe_asset_config(self) -> None:
        """
        Validate safe asset configuration at initialization.
        
        Raises:
            ValueError: If safe asset configuration is invalid
        """
        if self.safe_asset is not None:
            if not isinstance(self.safe_asset, str):
                raise ValueError(
                    f"safe_asset must be a string symbol, got {type(self.safe_asset)}"
                )
            
            if not self.safe_asset or not self.safe_asset.strip():
                raise ValueError("safe_asset cannot be empty string")
            
            if len(self.safe_asset) > 10:
                logger.warning(
                    f"safe_asset '{self.safe_asset}' is unusually long (>10 chars). "
                    f"Verify this is a valid symbol."
                )
            
            logger.info(f"Safe asset configured: {self.safe_asset}")
        else:
            logger.info(
                "No safe asset configured. Portfolio will hold cash during defensive periods."
            )
    
    def _calculate_blend_ratio(self, momentum: float) -> float:
        """
        Calculate risky:safe blend ratio based on momentum strength.
        
        Args:
            momentum: Momentum score
        
        Returns:
            Blend ratio (0.0 = 100% safe, 1.0 = 100% risky)
        """
        if momentum >= self.blend_zone_upper:
            return 1.0
        elif momentum <= self.blend_zone_lower:
            return 0.0
        else:
            range_size = self.blend_zone_upper - self.blend_zone_lower
            return (momentum - self.blend_zone_lower) / range_size
    
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
        assets_in_blend_zone = []
        
        for symbol, momentum in latest_signals.items():
            if momentum > self.threshold:
                # Positive momentum - go long
                # Strength based on how far above threshold
                strength = min(1.0, max(0.0, momentum / (self.threshold + 0.1)))
                
                signal = Signal(
                    timestamp=latest_timestamp,
                    symbol=symbol,
                    direction=1,
                    strength=strength,
                    reason=SignalReason.MOMENTUM_POSITIVE,
                    confidence=min(1.0, strength),
                    metadata={
                        'momentum_score': momentum,
                        'strategy': 'absolute_momentum',
                        'lookback_period': self.lookback_period,
                        'threshold': self.threshold
                    }
                )
                signals.append(signal)
                assets_with_signal.append(symbol)
            
            elif self.enable_blending and self.safe_asset:
                # Check if in blend zone
                if self.blend_zone_lower <= momentum <= self.blend_zone_upper:
                    assets_in_blend_zone.append((symbol, momentum))
        
        # If no clear positive signals but have assets in blend zone
        if len(signals) == 0 and assets_in_blend_zone and self.safe_asset:
            # Use the asset with highest momentum in blend zone
            best_symbol, best_momentum = max(assets_in_blend_zone, key=lambda x: x[1])
            blend_ratio = self._calculate_blend_ratio(best_momentum)
            
            if blend_ratio > 0:
                signal = Signal(
                    timestamp=latest_timestamp,
                    symbol=best_symbol,
                    direction=1,
                    strength=blend_ratio,
                    reason=SignalReason.BLEND_ALLOCATION,
                    confidence=0.6,
                    blend_ratio=blend_ratio,
                    metadata={
                        'momentum_score': best_momentum,
                        'strategy': 'absolute_momentum',
                        'blend_mode': 'risky_component',
                        'lookback_period': self.lookback_period
                    }
                )
                signals.append(signal)
            
            if blend_ratio < 1.0:
                signal = Signal(
                    timestamp=latest_timestamp,
                    symbol=self.safe_asset,
                    direction=1,
                    strength=1.0 - blend_ratio,
                    reason=SignalReason.BLEND_ALLOCATION,
                    confidence=0.6,
                    blend_ratio=blend_ratio,
                    metadata={
                        'momentum_score': best_momentum,
                        'strategy': 'absolute_momentum',
                        'blend_mode': 'safe_component',
                        'lookback_period': self.lookback_period
                    }
                )
                signals.append(signal)
            
            logger.info(
                f"Blended allocation: {blend_ratio:.1%} {best_symbol}, "
                f"{(1-blend_ratio):.1%} {self.safe_asset}"
            )
        
        # If still no signals and safe asset configured, full defensive
        elif len(signals) == 0 and self.safe_asset:
            signal = Signal(
                timestamp=latest_timestamp,
                symbol=self.safe_asset,
                direction=1,
                strength=1.0,
                reason=SignalReason.DEFENSIVE_ROTATION,
                confidence=1.0,
                metadata={
                    'momentum_score': 0.0,
                    'strategy': 'absolute_momentum',
                    'threshold': self.threshold
                }
            )
            signals.append(signal)
            logger.info(f"No positive momentum. Defensive rotation to: {self.safe_asset}")
        
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
        signals = []
        momentum = self.calculate_momentum(price_data)
        
        if len(momentum) == 0:
            return []
        
        latest_momentum = momentum.iloc[-1]
        latest_timestamp = momentum.index[-1]
        
        if pd.isna(latest_momentum):
            return []
        
        if latest_momentum > self.threshold:
            # Positive momentum - long signal
            strength = min(1.0, max(0.0, latest_momentum / (self.threshold + 0.1)))
            
            signal = Signal(
                timestamp=latest_timestamp,
                symbol=price_data.symbol,
                direction=1,
                strength=strength,
                reason=SignalReason.MOMENTUM_POSITIVE,
                confidence=min(1.0, strength),
                metadata={
                    'momentum_score': latest_momentum,
                    'strategy': 'absolute_momentum',
                    'lookback_period': self.lookback_period
                }
            )
            return [signal]
        
        # Check for blended allocation
        elif self.enable_blending and self.safe_asset:
            if self.blend_zone_lower <= latest_momentum <= self.blend_zone_upper:
                blend_ratio = self._calculate_blend_ratio(latest_momentum)
                
                if blend_ratio > 0:
                    signal = Signal(
                        timestamp=latest_timestamp,
                        symbol=price_data.symbol,
                        direction=1,
                        strength=blend_ratio,
                        reason=SignalReason.BLEND_ALLOCATION,
                        confidence=0.6,
                        blend_ratio=blend_ratio,
                        metadata={
                            'momentum_score': latest_momentum,
                            'strategy': 'absolute_momentum',
                            'blend_mode': 'risky_component',
                            'lookback_period': self.lookback_period
                        }
                    )
                    signals.append(signal)
                
                if blend_ratio < 1.0:
                    signal = Signal(
                        timestamp=latest_timestamp,
                        symbol=self.safe_asset,
                        direction=1,
                        strength=1.0 - blend_ratio,
                        reason=SignalReason.BLEND_ALLOCATION,
                        confidence=0.6,
                        blend_ratio=blend_ratio,
                        metadata={
                            'momentum_score': latest_momentum,
                            'strategy': 'absolute_momentum',
                            'blend_mode': 'safe_component',
                            'lookback_period': self.lookback_period
                        }
                    )
                    signals.append(signal)
                
                return signals
        
        # Full defensive
        if self.safe_asset:
            signal = Signal(
                timestamp=latest_timestamp,
                symbol=self.safe_asset,
                direction=1,
                strength=1.0,
                reason=SignalReason.DEFENSIVE_ROTATION,
                confidence=1.0,
                metadata={
                    'momentum_score': latest_momentum,
                    'strategy': 'absolute_momentum'
                }
            )
            return [signal]
        
        return []
    
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
