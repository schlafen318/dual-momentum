"""
Tests for signal strength calculation methods in Absolute Momentum strategy.

This module tests the various strength calculation methods to ensure:
- Correct normalization and scaling
- Independence from threshold values
- Edge case handling
- Consistency across different momentum values
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.strategies.absolute_momentum import AbsoluteMomentumStrategy
from src.core.types import PriceData, AssetMetadata, AssetType


class TestSignalStrengthCalculation:
    """Test suite for signal strength calculation methods."""
    
    @pytest.fixture
    def create_price_data(self):
        """Helper to create price data with specific returns."""
        def _create(symbol: str, final_return: float, periods: int = 300):
            """
            Create price data that results in specified return over lookback period.
            
            Args:
                symbol: Asset symbol
                final_return: Target return (e.g., 0.10 for 10%)
                periods: Number of data points
            """
            dates = pd.date_range(end=datetime.now(), periods=periods, freq='D')
            # Create prices that result in desired return
            # If final_return = 0.10, price goes from 100 to 110
            prices = np.linspace(100, 100 * (1 + final_return), periods)
            
            data = pd.DataFrame({
                'close': prices,
                'open': prices,
                'high': prices * 1.01,
                'low': prices * 0.99,
                'volume': [1000000] * periods
            }, index=dates)
            
            return PriceData(
                symbol=symbol,
                data=data,
                metadata=AssetMetadata(
                    symbol=symbol,
                    name=symbol,
                    asset_type=AssetType.EQUITY
                )
            )
        return _create
    
    # =========================================================================
    # Test Binary Method
    # =========================================================================
    
    def test_binary_method_equal_strength(self, create_price_data):
        """Binary method should give all passing assets strength=1.0."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'binary'
        })
        
        # Create assets with different momentum values
        price_data = {
            'SPY': create_price_data('SPY', 0.05),   # 5% return
            'QQQ': create_price_data('QQQ', 0.20),   # 20% return
            'DIA': create_price_data('DIA', 0.10),   # 10% return
        }
        
        signals = strategy.generate_signals(price_data)
        
        # All should have strength=1.0
        assert len(signals) == 3
        for signal in signals:
            assert signal.strength == 1.0, \
                f"{signal.symbol} should have strength=1.0, got {signal.strength}"
    
    def test_binary_method_respects_threshold(self, create_price_data):
        """Binary method should only include assets above threshold."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.10,  # 10% threshold
            'strength_method': 'binary'
        })
        
        price_data = {
            'SPY': create_price_data('SPY', 0.05),   # Below threshold
            'QQQ': create_price_data('QQQ', 0.20),   # Above threshold
            'DIA': create_price_data('DIA', 0.08),   # Below threshold
        }
        
        signals = strategy.generate_signals(price_data)
        
        # Only QQQ should pass
        assert len(signals) == 1
        assert signals[0].symbol == 'QQQ'
        assert signals[0].strength == 1.0
    
    # =========================================================================
    # Test Linear Method
    # =========================================================================
    
    def test_linear_method_correct_scaling(self, create_price_data):
        """Linear method should scale correctly over configured range."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'linear',
            'strength_scale_range': 0.10  # Scale from 0% to 10%
        })
        
        price_data = {
            'LOW': create_price_data('LOW', 0.05),   # 5% = 0.5 strength
            'MID': create_price_data('MID', 0.075),  # 7.5% = 0.75 strength
            'HIGH': create_price_data('HIGH', 0.15), # 15% = 1.0 strength (clamped)
        }
        
        signals = strategy.generate_signals(price_data)
        signal_dict = {s.symbol: s.strength for s in signals}
        
        # Check scaling
        assert abs(signal_dict['LOW'] - 0.5) < 0.01, \
            f"Expected 0.5, got {signal_dict['LOW']}"
        assert abs(signal_dict['MID'] - 0.75) < 0.01, \
            f"Expected 0.75, got {signal_dict['MID']}"
        assert signal_dict['HIGH'] == 1.0, \
            f"Expected 1.0, got {signal_dict['HIGH']}"
    
    def test_linear_method_threshold_independence(self, create_price_data):
        """
        Linear scaling should be independent of threshold value.
        
        This is the key fix - scaling range should not change with threshold!
        """
        # Test with threshold = 0.0
        strategy1 = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'linear',
            'strength_scale_range': 0.10
        })
        
        price_data1 = {
            'ASSET': create_price_data('ASSET', 0.05),  # 5% return
        }
        signals1 = strategy1.generate_signals(price_data1)
        strength1 = signals1[0].strength
        
        # Test with threshold = 0.05
        strategy2 = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.05,
            'strength_method': 'linear',
            'strength_scale_range': 0.10  # Same scale range!
        })
        
        # Asset now needs 10% return to have same excess above threshold
        price_data2 = {
            'ASSET': create_price_data('ASSET', 0.10),  # 10% return
        }
        signals2 = strategy2.generate_signals(price_data2)
        strength2 = signals2[0].strength
        
        # Both should have same strength (0.5) because:
        # Case 1: (0.05 - 0.0) / 0.10 = 0.5
        # Case 2: (0.10 - 0.05) / 0.10 = 0.5
        assert abs(strength1 - 0.5) < 0.01
        assert abs(strength2 - 0.5) < 0.01
        assert abs(strength1 - strength2) < 0.01, \
            f"Strengths should be equal: {strength1} vs {strength2}"
    
    def test_linear_method_custom_scale_range(self, create_price_data):
        """Test that custom scale ranges work correctly."""
        # Tight scale range (5%)
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'linear',
            'strength_scale_range': 0.05  # Only 5% range
        })
        
        price_data = {
            'ASSET': create_price_data('ASSET', 0.05),  # 5% return
        }
        
        signals = strategy.generate_signals(price_data)
        
        # Should reach full strength at 5%
        assert signals[0].strength == 1.0
    
    # =========================================================================
    # Test Proportional Method
    # =========================================================================
    
    def test_proportional_method_correct_weighting(self, create_price_data):
        """Proportional method should weight by momentum magnitude."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'proportional'
        })
        
        price_data = {
            'SPY': create_price_data('SPY', 0.10),   # 10%
            'QQQ': create_price_data('QQQ', 0.20),   # 20%
            'DIA': create_price_data('DIA', 0.30),   # 30%
        }
        # Total momentum = 60%, so weights should be:
        # SPY: 10/60 = 0.167
        # QQQ: 20/60 = 0.333
        # DIA: 30/60 = 0.500
        
        signals = strategy.generate_signals(price_data)
        signal_dict = {s.symbol: s.strength for s in signals}
        
        # Check proportional weighting
        assert abs(signal_dict['SPY'] - 0.167) < 0.01
        assert abs(signal_dict['QQQ'] - 0.333) < 0.01
        assert abs(signal_dict['DIA'] - 0.500) < 0.01
        
        # Check they sum to 1.0
        total = sum(signal_dict.values())
        assert abs(total - 1.0) < 0.001
    
    def test_proportional_method_equal_momentum(self, create_price_data):
        """Equal momentum should result in equal weights."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'proportional'
        })
        
        price_data = {
            'SPY': create_price_data('SPY', 0.15),
            'QQQ': create_price_data('QQQ', 0.15),
            'DIA': create_price_data('DIA', 0.15),
        }
        
        signals = strategy.generate_signals(price_data)
        
        # All should have equal strength = 1/3
        for signal in signals:
            assert abs(signal.strength - 0.333) < 0.01
    
    # =========================================================================
    # Test Momentum Ratio Method
    # =========================================================================
    
    def test_momentum_ratio_method_leader_gets_one(self, create_price_data):
        """Momentum ratio should give leader strength=1.0."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'momentum_ratio'
        })
        
        price_data = {
            'SPY': create_price_data('SPY', 0.10),
            'QQQ': create_price_data('QQQ', 0.30),  # Leader
            'DIA': create_price_data('DIA', 0.15),
        }
        
        signals = strategy.generate_signals(price_data)
        signal_dict = {s.symbol: s.strength for s in signals}
        
        # QQQ should have strength=1.0
        assert signal_dict['QQQ'] == 1.0
        
        # Others should be relative to QQQ
        # SPY: 0.10/0.30 = 0.333
        # DIA: 0.15/0.30 = 0.500
        assert abs(signal_dict['SPY'] - 0.333) < 0.01
        assert abs(signal_dict['DIA'] - 0.500) < 0.01
    
    # =========================================================================
    # Test Edge Cases
    # =========================================================================
    
    def test_single_asset(self, create_price_data):
        """Test all methods work with single asset."""
        methods = ['binary', 'linear', 'proportional', 'momentum_ratio']
        
        for method in methods:
            strategy = AbsoluteMomentumStrategy({
                'lookback_period': 252,
                'threshold': 0.0,
                'strength_method': method,
                'strength_scale_range': 0.10
            })
            
            price_data = create_price_data('SPY', 0.15)
            signals = strategy.generate_signals(price_data)
            
            assert len(signals) == 1, f"Method {method} failed with single asset"
            assert 0.0 <= signals[0].strength <= 1.0, \
                f"Method {method} produced invalid strength: {signals[0].strength}"
    
    def test_all_assets_filtered_out(self, create_price_data):
        """Test when no assets pass threshold."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.20,  # Very high threshold
            'strength_method': 'binary',
            'safe_asset': 'SHY'
        })
        
        price_data = {
            'SPY': create_price_data('SPY', 0.05),
            'QQQ': create_price_data('QQQ', 0.10),
        }
        
        signals = strategy.generate_signals(price_data)
        
        # Should switch to safe asset
        assert len(signals) == 1
        assert signals[0].symbol == 'SHY'
        assert signals[0].strength == 1.0
    
    def test_negative_momentum_filtered(self, create_price_data):
        """Negative momentum assets should be filtered out."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'binary'
        })
        
        price_data = {
            'SPY': create_price_data('SPY', 0.10),   # Positive
            'QQQ': create_price_data('QQQ', -0.05),  # Negative
        }
        
        signals = strategy.generate_signals(price_data)
        
        # Only SPY should pass
        assert len(signals) == 1
        assert signals[0].symbol == 'SPY'
    
    def test_unknown_method_fallback(self, create_price_data):
        """Unknown method should fallback to binary with warning."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'invalid_method'
        })
        
        price_data = {
            'SPY': create_price_data('SPY', 0.10),
            'QQQ': create_price_data('QQQ', 0.20),
        }
        
        signals = strategy.generate_signals(price_data)
        
        # Should fallback to binary (all strength=1.0)
        assert len(signals) == 2
        for signal in signals:
            assert signal.strength == 1.0
    
    # =========================================================================
    # Test Metadata
    # =========================================================================
    
    def test_strength_method_in_metadata(self, create_price_data):
        """Signals should include strength_method in metadata."""
        strategy = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'proportional'
        })
        
        price_data = create_price_data('SPY', 0.15)
        signals = strategy.generate_signals(price_data)
        
        assert 'strength_method' in signals[0].metadata
        assert signals[0].metadata['strength_method'] == 'proportional'
    
    # =========================================================================
    # Integration Test: Compare Old vs New Behavior
    # =========================================================================
    
    def test_linear_fixes_old_bug(self, create_price_data):
        """
        Test that new linear method fixes the old bug.
        
        Old behavior: strength = momentum / (threshold + 0.1)
        New behavior: strength = (momentum - threshold) / scale_range
        
        The key difference: scaling range is now independent of threshold!
        """
        # Test case that would fail with old implementation
        
        # Scenario 1: threshold=0.0, momentum=0.05
        strategy1 = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.0,
            'strength_method': 'linear',
            'strength_scale_range': 0.10
        })
        
        price_data1 = create_price_data('ASSET', 0.05)
        signals1 = strategy1.generate_signals(price_data1)
        strength1 = signals1[0].strength
        
        # Scenario 2: threshold=0.05, momentum=0.10
        # Same "excess" above threshold (0.05)
        strategy2 = AbsoluteMomentumStrategy({
            'lookback_period': 252,
            'threshold': 0.05,
            'strength_method': 'linear',
            'strength_scale_range': 0.10
        })
        
        price_data2 = create_price_data('ASSET', 0.10)
        signals2 = strategy2.generate_signals(price_data2)
        strength2 = signals2[0].strength
        
        # NEW BEHAVIOR: Should be equal (both 0.5)
        assert abs(strength1 - 0.5) < 0.01
        assert abs(strength2 - 0.5) < 0.01
        
        # OLD BEHAVIOR would have given:
        # strength1 = 0.05 / (0.0 + 0.1) = 0.5
        # strength2 = 0.10 / (0.05 + 0.1) = 0.667  <- WRONG!
        
        print(f"\n✓ Fixed bug verified:")
        print(f"  Old formula would give: 0.5 and 0.667 (inconsistent)")
        print(f"  New formula gives: {strength1:.3f} and {strength2:.3f} (consistent)")


class TestStrengthCalculationRecommendations:
    """Test recommendations for when to use each method."""
    
    def test_binary_for_equal_weight(self):
        """Binary is best for equal-weight portfolios."""
        # When you want to give equal weight to all passing assets
        pass
    
    def test_linear_for_gradual_scaling(self):
        """Linear is best for gradually increasing position with momentum."""
        # When you want smooth scaling over a momentum range
        pass
    
    def test_proportional_for_momentum_weighting(self):
        """Proportional is best for weighting by momentum strength."""
        # When you want to allocate more to higher momentum assets
        pass
    
    def test_momentum_ratio_for_leader_emphasis(self):
        """Momentum ratio emphasizes the leader while keeping others."""
        # When you want to identify and emphasize the strongest asset
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
