#!/usr/bin/env python3
"""
Test script to verify all improvements are working correctly.
"""

import sys
from datetime import datetime

def test_signal_reason():
    """Test SignalReason enum and enhanced Signal."""
    try:
        from src.core.types import Signal, SignalReason
        
        # Test basic signal
        s1 = Signal(
            timestamp=datetime(2024, 1, 1),
            symbol='SPY',
            direction=1,
            strength=0.8,
            reason=SignalReason.MOMENTUM_POSITIVE,
            confidence=0.9
        )
        
        assert s1.reason == SignalReason.MOMENTUM_POSITIVE
        assert s1.confidence == 0.9
        assert not s1.is_defensive
        assert not s1.is_blended
        
        # Test defensive signal
        s2 = Signal(
            timestamp=datetime(2024, 1, 1),
            symbol='SHY',
            direction=1,
            strength=1.0,
            reason=SignalReason.DEFENSIVE_ROTATION
        )
        
        assert s2.is_defensive
        
        # Test blended signal
        s3 = Signal(
            timestamp=datetime(2024, 1, 1),
            symbol='SPY',
            direction=1,
            strength=0.6,
            reason=SignalReason.BLEND_ALLOCATION,
            blend_ratio=0.6
        )
        
        assert s3.is_blended
        assert s3.blend_ratio == 0.6
        
        print("✓ SignalReason and enhanced Signal tests passed")
        return True
    except Exception as e:
        print(f"✗ SignalReason test failed: {e}")
        return False

def test_cash_manager():
    """Test CashManager functionality."""
    try:
        from src.core.cash_manager import CashManager
        
        # Create cash manager
        cm = CashManager(strategic_cash_pct=0.05, operational_buffer_pct=0.02)
        
        # Test allocation calculation
        allocation = cm.calculate_allocation(total_value=100000, current_cash=10000)
        
        assert allocation.strategic_cash == 5000  # 5% of 100k
        assert allocation.operational_buffer >= 2000  # 2% of 100k (or min)
        assert allocation.total_cash == 10000
        assert allocation.available_cash >= 0
        
        # Test available for investment
        available = cm.available_for_investment(100000, 10000)
        assert available >= 0
        
        print("✓ CashManager tests passed")
        return True
    except Exception as e:
        print(f"✗ CashManager test failed: {e}")
        return False

def test_strategy_validation():
    """Test strategy safe asset validation."""
    try:
        from src.strategies.dual_momentum import DualMomentumStrategy
        
        # Test valid configuration
        config1 = {'safe_asset': 'SHY'}
        strategy1 = DualMomentumStrategy(config1)
        assert strategy1.safe_asset == 'SHY'
        
        # Test no safe asset
        config2 = {'safe_asset': None}
        strategy2 = DualMomentumStrategy(config2)
        assert strategy2.safe_asset is None
        
        # Test blend zone configuration
        assert hasattr(strategy1, 'blend_zone_lower')
        assert hasattr(strategy1, 'blend_zone_upper')
        assert hasattr(strategy1, 'enable_blending')
        
        print("✓ Strategy validation tests passed")
        return True
    except Exception as e:
        print(f"✗ Strategy validation test failed: {e}")
        return False

def test_blend_ratio_calculation():
    """Test blend ratio calculation logic."""
    try:
        from src.strategies.dual_momentum import DualMomentumStrategy
        
        strategy = DualMomentumStrategy({
            'blend_zone_lower': -0.05,
            'blend_zone_upper': 0.05
        })
        
        # Test above blend zone - should be 100% risky
        ratio1 = strategy._calculate_blend_ratio(0.10)
        assert ratio1 == 1.0, f"Expected 1.0, got {ratio1}"
        
        # Test below blend zone - should be 100% safe
        ratio2 = strategy._calculate_blend_ratio(-0.10)
        assert ratio2 == 0.0, f"Expected 0.0, got {ratio2}"
        
        # Test in middle of blend zone - should be 50/50
        ratio3 = strategy._calculate_blend_ratio(0.00)
        assert abs(ratio3 - 0.5) < 0.01, f"Expected ~0.5, got {ratio3}"
        
        # Test near upper bound
        ratio4 = strategy._calculate_blend_ratio(0.025)
        assert 0.5 < ratio4 < 1.0, f"Expected between 0.5 and 1.0, got {ratio4}"
        
        print("✓ Blend ratio calculation tests passed")
        return True
    except Exception as e:
        print(f"✗ Blend ratio test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_manager_integration():
    """Test risk manager integration with CashManager."""
    try:
        from src.backtesting.basic_risk import BasicRiskManager
        
        # Create risk manager with cash settings
        rm = BasicRiskManager({
            'strategic_cash_pct': 0.05,
            'operational_buffer_pct': 0.02
        })
        
        assert hasattr(rm, 'cash_manager')
        assert rm.cash_manager.strategic_cash_pct == 0.05
        
        # Test cash allocation method
        allocation = rm.get_cash_allocation(100000, 10000)
        assert allocation.strategic_cash == 5000
        
        print("✓ Risk manager integration tests passed")
        return True
    except Exception as e:
        print(f"✗ Risk manager integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING IMPROVEMENTS")
    print("=" * 60)
    print()
    
    tests = [
        test_signal_reason,
        test_cash_manager,
        test_strategy_validation,
        test_blend_ratio_calculation,
        test_risk_manager_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
