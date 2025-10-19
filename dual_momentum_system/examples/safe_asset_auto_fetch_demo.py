"""
Demonstration of automatic safe asset fetching.

This example shows how the system automatically fetches safe asset data
when it's configured but not included in the universe. This prevents the
common issue of safe asset signals being silently skipped during bearish periods.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
import warnings
warnings.filterwarnings('ignore')

from src.data_sources.yahoo_finance import YahooFinanceSource
from src.asset_classes.equity import EquityAsset
from src.strategies.dual_momentum import DualMomentumStrategy
from src.backtesting.engine import BacktestEngine
from src.backtesting.utils import prepare_backtest_data, ensure_safe_asset_data


def demo_manual_approach():
    """Demonstrates the manual approach to ensure safe asset is included."""
    
    print("=" * 80)
    print("APPROACH 1: Manual Safe Asset Handling")
    print("=" * 80)
    print()
    
    # Setup
    data_source = YahooFinanceSource({'cache_enabled': True})
    asset_class = EquityAsset()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=400)  # ~16 months
    
    # Universe WITHOUT safe asset
    universe = ['SPY', 'QQQ', 'IWM']  # Note: No SHY!
    print(f"Universe: {universe}")
    
    # Strategy with SHY as safe asset (not in universe)
    strategy = DualMomentumStrategy({
        'safe_asset': 'SHY',  # ← Safe asset NOT in universe above
        'position_count': 1,
        'absolute_threshold': 0.0,
        'lookback_period': 126
    })
    print(f"Safe Asset: {strategy.config['safe_asset']}")
    print(f"Problem: SHY not in universe → signals will be skipped!\n")
    
    # Fetch universe data
    print("Fetching universe data...")
    price_data = {}
    for symbol in universe:
        try:
            raw_data = data_source.fetch_data(symbol, start_date, end_date)
            price_data[symbol] = asset_class.normalize_data(raw_data, symbol)
            print(f"  ✓ {symbol}: {len(price_data[symbol].data)} bars")
        except Exception as e:
            print(f"  ✗ {symbol}: {e}")
    
    print(f"\nBefore auto-fetch: {list(price_data.keys())}")
    
    # Use ensure_safe_asset_data to automatically fetch SHY
    print("\nCalling ensure_safe_asset_data()...")
    price_data = ensure_safe_asset_data(
        strategy=strategy,
        price_data=price_data,
        data_source=data_source,
        start_date=start_date,
        end_date=end_date,
        asset_class=asset_class
    )
    
    print(f"After auto-fetch: {list(price_data.keys())}")
    print(f"✓ SHY automatically added!\n")
    
    # Run backtest
    print("Running backtest...")
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, price_data)
    
    print(f"✓ Backtest complete")
    print(f"  Final Capital: ${results.final_capital:,.2f}")
    print(f"  Total Return: {results.total_return:.2%}")
    print(f"  Number of Trades: {len(results.trades)}")
    print()


def demo_convenience_function():
    """Demonstrates using the convenience function for one-step data prep."""
    
    print("=" * 80)
    print("APPROACH 2: Using prepare_backtest_data() Convenience Function")
    print("=" * 80)
    print()
    
    # Setup
    data_source = YahooFinanceSource({'cache_enabled': True})
    asset_class = EquityAsset()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=400)
    
    # Universe WITHOUT safe asset
    universe = ['SPY', 'EFA', 'EEM']  # No AGG!
    print(f"Universe: {universe}")
    
    # Strategy with AGG as safe asset
    strategy = DualMomentumStrategy({
        'safe_asset': 'AGG',  # ← Not in universe
        'position_count': 1,
        'absolute_threshold': 0.0,
        'lookback_period': 126
    })
    print(f"Safe Asset: {strategy.config['safe_asset']}")
    print()
    
    # ONE-STEP data preparation (automatically includes safe asset)
    print("Calling prepare_backtest_data()...")
    print("(Automatically fetches universe + safe asset)")
    print()
    
    price_data = prepare_backtest_data(
        strategy=strategy,
        symbols=universe,
        data_source=data_source,
        start_date=start_date,
        end_date=end_date,
        asset_class=asset_class,
        include_safe_asset=True  # ← This is the default
    )
    
    print(f"\nData loaded for: {list(price_data.keys())}")
    print(f"✓ AGG automatically included!\n")
    
    # Run backtest
    print("Running backtest...")
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, price_data)
    
    print(f"✓ Backtest complete")
    print(f"  Final Capital: ${results.final_capital:,.2f}")
    print(f"  Total Return: {results.total_return:.2%}")
    print(f"  Number of Trades: {len(results.trades)}")
    print()


def demo_safe_asset_already_in_universe():
    """Demonstrates what happens when safe asset is already in universe."""
    
    print("=" * 80)
    print("SCENARIO: Safe Asset Already in Universe (No Auto-Fetch Needed)")
    print("=" * 80)
    print()
    
    # Setup
    data_source = YahooFinanceSource({'cache_enabled': True})
    asset_class = EquityAsset()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=400)
    
    # Universe WITH safe asset
    universe = ['SPY', 'AGG', 'GLD']  # AGG included
    print(f"Universe: {universe}")
    
    # Strategy with AGG as safe asset (already in universe)
    strategy = DualMomentumStrategy({
        'safe_asset': 'AGG',  # ← Already in universe
        'position_count': 1,
        'absolute_threshold': 0.0,
        'lookback_period': 126
    })
    print(f"Safe Asset: {strategy.config['safe_asset']}")
    print()
    
    # Use prepare_backtest_data
    print("Calling prepare_backtest_data()...")
    
    price_data = prepare_backtest_data(
        strategy=strategy,
        symbols=universe,
        data_source=data_source,
        start_date=start_date,
        end_date=end_date,
        asset_class=asset_class
    )
    
    print(f"\nData loaded for: {list(price_data.keys())}")
    print(f"✓ AGG already in universe - no additional fetch needed\n")
    
    # Run backtest
    print("Running backtest...")
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, price_data)
    
    print(f"✓ Backtest complete")
    print(f"  Final Capital: ${results.final_capital:,.2f}")
    print(f"  Total Return: {results.total_return:.2%}")
    print(f"  Number of Trades: {len(results.trades)}")
    print()


def main():
    """Run all demos."""
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  SAFE ASSET AUTO-FETCH DEMONSTRATION".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Shows how to automatically fetch safe asset data when it's".center(78) + "║")
    print("║" + "  configured but not included in the universe.".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    try:
        # Demo 1: Manual approach with ensure_safe_asset_data()
        demo_manual_approach()
        
        # Demo 2: Convenience function
        demo_convenience_function()
        
        # Demo 3: Safe asset already in universe
        demo_safe_asset_already_in_universe()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print("✓ Demonstrated 3 approaches to handling safe assets:")
        print()
        print("  1. Manual: Use ensure_safe_asset_data() after fetching universe")
        print("     → Most control, useful when you already have a data dict")
        print()
        print("  2. Convenience: Use prepare_backtest_data() for one-step setup")
        print("     → Simplest, recommended for new code")
        print()
        print("  3. Universe Inclusion: Add safe asset to universe upfront")
        print("     → Traditional approach, still works fine")
        print()
        print("Key Takeaway:")
        print("  If your safe_asset is outside your universe, the system now")
        print("  automatically fetches it, preventing the silent skip bug that")
        print("  caused high cash allocation during bearish periods.")
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
