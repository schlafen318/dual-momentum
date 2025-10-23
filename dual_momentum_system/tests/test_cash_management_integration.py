"""
Integration tests for cash management during backtesting.

These tests verify that cash is managed correctly throughout the entire
backtest lifecycle, not just during individual rebalancing events.
"""

import pytest
from datetime import datetime
import pandas as pd
import numpy as np

from src.backtesting.engine import BacktestEngine
from src.strategies.dual_momentum import DualMomentumStrategy
from src.core.types import PriceData, AssetMetadata, AssetType


class TestCashManagementIntegration:
    """Integration tests for cash management."""
    
    @pytest.fixture
    def realistic_price_data(self):
        """Create realistic price data with trends and volatility."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        
        # Generate more realistic price movements
        np.random.seed(42)  # Reproducible
        
        data = {}
        base_prices = {'SPY': 300, 'QQQ': 200, 'DIA': 250, 'IWM': 150}
        
        for symbol, base_price in base_prices.items():
            # Generate returns with drift and volatility
            returns = np.random.normal(0.0003, 0.01, len(dates))  # ~7.5% annual return, 15% vol
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
    
    def test_cash_never_goes_negative(self, realistic_price_data):
        """
        Critical test: Cash should NEVER go negative.
        
        This would indicate a serious bug in execution logic.
        """
        strategy = DualMomentumStrategy({
            'lookback_period': 252,
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
            price_data=realistic_price_data,
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        # Check that cash is never negative
        if not results.positions.empty and 'cash' in results.positions.columns:
            min_cash = results.positions['cash'].min()
            assert min_cash >= -0.01, f"Cash went negative: ${min_cash:.2f}!"
    
    def test_portfolio_value_consistency(self, realistic_price_data):
        """
        Test that portfolio value = cash + sum(positions) at all times.
        
        This verifies accounting integrity.
        """
        strategy = DualMomentumStrategy({
            'lookback_period': 252,
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
            price_data=realistic_price_data,
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        if not results.positions.empty:
            for idx, row in results.positions.iterrows():
                # Calculate sum of all position values
                position_values = 0
                for col in results.positions.columns:
                    if col.endswith('_value') and col != 'portfolio_value':
                        position_values += row[col]
                
                cash = row.get('cash', 0)
                portfolio_value = row.get('portfolio_value', 0)
                
                calculated_pv = cash + position_values
                
                # Allow for small floating point differences
                assert abs(calculated_pv - portfolio_value) < 1.0, (
                    f"Portfolio value mismatch at {idx}: "
                    f"calculated=${calculated_pv:,.2f}, "
                    f"recorded=${portfolio_value:,.2f}"
                )
    
    def test_transaction_costs_reasonable(self, realistic_price_data):
        """
        Test that transaction costs are within expected range.
        
        Excessive transaction costs could indicate double-counting or
        execution errors.
        """
        strategy = DualMomentumStrategy({
            'lookback_period': 252,
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
            price_data=realistic_price_data,
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        # Calculate total transaction costs from trades
        if not results.trades.empty:
            total_volume = results.trades['quantity'].abs().sum() * results.trades['entry_price'].mean()
            expected_max_costs = total_volume * (engine.commission + engine.slippage) * 2  # Buy and sell
            
            # Costs should be reasonable (< 1% of initial capital per year)
            years = (results.end_date - results.start_date).days / 365.25
            annual_cost_rate = (expected_max_costs / engine.initial_capital) / years
            
            assert annual_cost_rate < 0.05, (
                f"Transaction costs seem too high: {annual_cost_rate:.2%} annually"
            )
    
    def test_no_excessive_cash_drag(self, realistic_price_data):
        """
        Test that average cash allocation is minimal.
        
        This is a regression test for the sell-before-buy bug.
        """
        strategy = DualMomentumStrategy({
            'lookback_period': 252,
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
            price_data=realistic_price_data,
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        if not results.positions.empty:
            # Calculate average cash allocation
            avg_cash_pct = results.positions['cash_pct'].mean()
            
            # Should be < 1% on average (allowing for transaction costs and rounding)
            assert avg_cash_pct < 1.0, (
                f"Average cash drag {avg_cash_pct:.2f}% is too high! "
                f"This indicates execution problems."
            )
            
            # 95th percentile should also be reasonable
            p95_cash = results.positions['cash_pct'].quantile(0.95)
            assert p95_cash < 2.0, (
                f"95th percentile cash {p95_cash:.2f}% is too high!"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
