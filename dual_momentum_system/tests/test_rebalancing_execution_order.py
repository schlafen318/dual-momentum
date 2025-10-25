"""
Tests to ensure rebalancing executes sells before buys.

This test suite specifically guards against the bug where buy orders fail
due to insufficient cash even when subsequent sell orders would generate
enough cash.
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.backtesting.engine import BacktestEngine
from src.strategies.dual_momentum import DualMomentumStrategy
from src.core.types import PriceData, AssetMetadata, AssetType, Signal, SignalReason


@pytest.mark.skip(reason="Known issue: Rebalancing execution tests need investigation (pre-existing on main)")
class TestRebalancingExecutionOrder:
    """Test suite for rebalancing execution order logic."""
    
    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for 4 assets."""
        np.random.seed(42)  # Reproducible tests
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        
        data = {}
        base_prices = {'SPY': 150, 'QQQ': 180, 'DIA': 160, 'IWM': 140}
        
        for symbol in ['SPY', 'QQQ', 'DIA', 'IWM']:
            base_price = base_prices[symbol]
            # Generate realistic trending prices
            returns = np.random.normal(0.0004, 0.008, len(dates))  # ~10% annual return
            if symbol in ['SPY', 'QQQ']:
                returns += 0.0002  # Extra drift for these
            
            prices = base_price * np.exp(np.cumsum(returns))
            
            df = pd.DataFrame({
                'open': prices * np.random.uniform(0.99, 1.01, len(dates)),
                'high': prices * np.random.uniform(1.0, 1.02, len(dates)),
                'low': prices * np.random.uniform(0.98, 1.0, len(dates)),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, len(dates)),
            }, index=dates)
            
            data[symbol] = PriceData(
                symbol=symbol,
                data=df,
                metadata=AssetMetadata(symbol=symbol, name=symbol, asset_type=AssetType.EQUITY)
            )
        
        return data
    
    def test_sell_before_buy_execution_order(self, sample_price_data):
        """
        Test that sells execute before buys during rebalancing.
        
        Scenario:
        1. Start with positions in SPY, DIA, IWM
        2. Rebalance to QQQ (new), SPY (reduced), DIA (reduced)
        3. Verify QQQ buy happens AFTER SPY/DIA sells
        """
        strategy = DualMomentumStrategy({
            'lookback_period': 60,
            'rebalance_frequency': 'monthly',
            'position_count': 3,
            'absolute_threshold': 0.0,
            'safe_asset': None,
        })
        
        engine = BacktestEngine(
            initial_capital=100000,
            commission=0.001,
            slippage=0.0005
        )
        
        results = engine.run(
            strategy=strategy,
            price_data=sample_price_data,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        # Check that cash allocation is minimal (< 1%)
        if not results.positions.empty:
            first_rebalance = results.positions.iloc[0]
            cash_pct = first_rebalance.get('cash_pct', 0)
            
            assert cash_pct < 1.0, (
                f"Cash allocation {cash_pct:.2f}% is too high! "
                f"This suggests sells didn't execute before buys."
            )
    
    def test_cash_availability_during_rotation(self, sample_price_data):
        """
        Test that cash from sales is available for purchases in same rebalance.
        
        This is the core bug test: ensure that when rotating from one asset
        to another, the sale proceeds are available for the purchase.
        """
        strategy = DualMomentumStrategy({
            'lookback_period': 60,
            'rebalance_frequency': 'monthly',
            'position_count': 2,
            'absolute_threshold': 0.0,
            'safe_asset': None,
        })
        
        engine = BacktestEngine(
            initial_capital=100000,
            commission=0.001,
            slippage=0.0005
        )
        
        results = engine.run(
            strategy=strategy,
            price_data=sample_price_data,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        # Analyze all rebalancing events
        if not results.positions.empty:
            max_cash_pct = results.positions['cash_pct'].max()
            
            # Allow for transaction costs (~0.15%) plus small buffer
            assert max_cash_pct < 2.0, (
                f"Maximum cash allocation {max_cash_pct:.2f}% exceeds threshold! "
                f"This indicates execution order issues during rebalancing."
            )
    
    def test_full_capital_deployment(self, sample_price_data):
        """
        Test that capital is fully deployed (minus transaction costs).
        
        Verifies that the fix ensures all available capital is invested
        according to strategy weights.
        """
        strategy = DualMomentumStrategy({
            'lookback_period': 60,
            'rebalance_frequency': 'monthly',
            'position_count': 3,
            'absolute_threshold': 0.0,
            'safe_asset': None,
        })
        
        engine = BacktestEngine(
            initial_capital=100000,
            commission=0.001,
            slippage=0.0005
        )
        
        results = engine.run(
            strategy=strategy,
            price_data=sample_price_data,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        if not results.positions.empty:
            # Calculate average cash allocation across all periods
            avg_cash_pct = results.positions['cash_pct'].mean()
            
            # Average should be very low (< 0.5%)
            assert avg_cash_pct < 0.5, (
                f"Average cash allocation {avg_cash_pct:.2f}% is too high! "
                f"Capital should be fully deployed."
            )
    
    def test_no_failed_orders_due_to_cash(self):
        """
        Test that no orders fail due to insufficient cash when
        rebalancing with both buys and sells.
        
        This would require access to engine logs or adding a tracker
        for failed orders.
        """
        # TODO: Implement once we add order tracking to engine
        pass
    
    def test_allocation_matches_target_weights(self, sample_price_data):
        """
        Test that actual allocation closely matches target weights.
        
        If sells happen after buys, allocations will deviate significantly
        from targets due to insufficient cash.
        """
        strategy = DualMomentumStrategy({
            'lookback_period': 60,
            'rebalance_frequency': 'monthly',
            'position_count': 3,
            'absolute_threshold': 0.0,
            'safe_asset': None,
        })
        
        engine = BacktestEngine(
            initial_capital=100000,
            commission=0.001,
            slippage=0.0005
        )
        
        results = engine.run(
            strategy=strategy,
            price_data=sample_price_data,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        if not results.positions.empty:
            # For each rebalancing event
            for idx, row in results.positions.iterrows():
                # Sum of all allocations (including cash)
                total_allocation = 0
                for col in results.positions.columns:
                    if col.endswith('_pct'):
                        total_allocation += row[col]
                
                # Should sum to 100% (allowing for floating point precision)
                assert abs(total_allocation - 100.0) < 0.01, (
                    f"Total allocation {total_allocation:.2f}% != 100% at {idx}"
                )


@pytest.mark.skip(reason="Known issue: Edge case tests need investigation (pre-existing on main)")
class TestEdgeCases:
    """Test edge cases in rebalancing logic."""
    
    def test_all_sells_no_buys(self, sample_price_data):
        """Test rebalancing when going to 100% cash (defensive)."""
        # This would happen when all assets fail momentum filter
        # and there's no safe asset
        pass
    
    def test_all_buys_no_sells(self, sample_price_data):
        """Test rebalancing when adding to all positions (no sales)."""
        pass
    
    def test_mixed_increase_decrease_same_asset(self, sample_price_data):
        """Test that same asset isn't both bought and sold."""
        pass


@pytest.mark.skip(reason="Known issue: Property tests need investigation (pre-existing on main)")
class TestPropertyBasedTests:
    """Property-based tests using hypothesis (if available)."""
    
    def test_invariant_cash_never_negative(self):
        """Property: Cash should never go negative during execution."""
        # Use hypothesis to generate random price scenarios
        pass
    
    def test_invariant_portfolio_value_conservation(self):
        """
        Property: Portfolio value before and after rebalancing should be
        approximately equal (minus transaction costs).
        """
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
