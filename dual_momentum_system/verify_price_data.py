#!/usr/bin/env python3
"""
Verification script for price data download and backtesting integration.

This script verifies that:
1. Price data downloads correctly from Yahoo Finance
2. Data is properly normalized
3. Backtesting engine correctly uses the downloaded data
4. Bug fixes are working (variable shadowing, timezone handling)

Run: python verify_price_data.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backtesting.engine import BacktestEngine
from src.data_sources.yahoo_finance import YahooFinanceSource
from src.asset_classes.equity import EquityAsset
from src.strategies.dual_momentum import DualMomentumStrategy


def print_header(title):
    """Print formatted header."""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_section(title):
    """Print formatted section."""
    print()
    print("-" * 80)
    print(f"  {title}")
    print("-" * 80)


def verify_data_download():
    """Verify price data download."""
    print_section("TEST 1: Data Download")
    
    ds = YahooFinanceSource({'cache_enabled': True})
    asset = EquityAsset()
    
    end = datetime.now()
    start = end - timedelta(days=90)
    
    # Test single symbol
    symbol = 'SPY'
    raw_data = ds.fetch_data(symbol, start, end, '1d')
    
    print(f"✓ Downloaded {len(raw_data)} bars for {symbol}")
    print(f"  Columns: {list(raw_data.columns)}")
    print(f"  Index type: {type(raw_data.index).__name__}")
    print(f"  Timezone: {raw_data.index.tz}")
    
    # Verify required columns
    required = ['open', 'high', 'low', 'close', 'volume']
    has_required = all(col in [c.lower() for c in raw_data.columns] for col in required)
    
    if not has_required:
        print(f"✗ FAILED: Missing required columns")
        return False
    
    print(f"✓ All required columns present")
    return True


def verify_data_normalization():
    """Verify data normalization."""
    print_section("TEST 2: Data Normalization")
    
    ds = YahooFinanceSource({'cache_enabled': True})
    asset = EquityAsset()
    
    end = datetime.now()
    start = end - timedelta(days=90)
    
    symbol = 'SPY'
    raw_data = ds.fetch_data(symbol, start, end, '1d')
    price_data = asset.normalize_data(raw_data, symbol)
    
    print(f"✓ Normalized to PriceData structure")
    print(f"  Symbol: {price_data.symbol}")
    print(f"  Shape: {price_data.data.shape}")
    print(f"  Columns: {list(price_data.data.columns)}")
    
    # Verify PriceData structure
    required = ['open', 'high', 'low', 'close', 'volume']
    has_cols = all(col in price_data.data.columns for col in required)
    
    if not has_cols:
        print(f"✗ FAILED: Missing required columns after normalization")
        return False
    
    print(f"✓ PriceData structure validated")
    return True


def verify_data_integrity():
    """Verify data integrity."""
    print_section("TEST 3: Data Integrity")
    
    ds = YahooFinanceSource({'cache_enabled': True})
    asset = EquityAsset()
    
    end = datetime.now()
    start = end - timedelta(days=90)
    
    symbol = 'SPY'
    raw_data = ds.fetch_data(symbol, start, end, '1d')
    price_data = asset.normalize_data(raw_data, symbol)
    
    checks = []
    
    # Check 1: No NaN in close
    no_nans = not price_data.data['close'].isna().any()
    checks.append(("No NaN in close prices", no_nans))
    
    # Check 2: Positive prices
    positive = (price_data.data['close'] > 0).all()
    checks.append(("All prices positive", positive))
    
    # Check 3: High >= Low
    high_gte_low = (price_data.data['high'] >= price_data.data['low']).all()
    checks.append(("High >= Low", high_gte_low))
    
    # Check 4: Close in range
    close_valid = (
        (price_data.data['close'] >= price_data.data['low']) &
        (price_data.data['close'] <= price_data.data['high'])
    ).all()
    checks.append(("Close within [Low, High]", close_valid))
    
    # Check 5: Sorted dates
    sorted_dates = price_data.data.index.is_monotonic_increasing
    checks.append(("Dates sorted", sorted_dates))
    
    # Check 6: No duplicates
    no_dupes = not price_data.data.index.has_duplicates
    checks.append(("No duplicate dates", no_dupes))
    
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def verify_backtesting_integration():
    """Verify backtesting integration with bug fixes."""
    print_section("TEST 4: Backtesting Integration (Bug Fixes)")
    
    ds = YahooFinanceSource({'cache_enabled': True})
    asset = EquityAsset()
    
    end = datetime.now()
    start = end - timedelta(days=365)
    
    # Load multiple symbols
    symbols = ['SPY', 'AGG']
    price_data = {}
    
    for symbol in symbols:
        raw_data = ds.fetch_data(symbol, start, end, '1d')
        price_data[symbol] = asset.normalize_data(raw_data, symbol)
        print(f"✓ Loaded {symbol}: {len(price_data[symbol].data)} bars")
    
    # Create strategy
    strategy = DualMomentumStrategy({
        'lookback_period': 63,
        'rebalance_frequency': 'monthly',
        'position_count': 1,
        'absolute_threshold': 0.0,
        'safe_asset': 'AGG'
    })
    
    # Create engine
    engine = BacktestEngine(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005
    )
    
    print("\n  Testing Bug Fixes:")
    print("  - Bug #1: Variable shadowing (pd.data -> pdata.data)")
    print("  - Bug #2: Timezone handling in date filtering")
    print()
    
    try:
        # This will fail if bugs are not fixed
        results = engine.run(
            strategy=strategy,
            price_data=price_data,
            risk_manager=None,
            start_date=start,
            end_date=end
        )
        
        print(f"✓ Backtest completed successfully")
        print(f"  Final capital: ${results.final_capital:,.2f}")
        print(f"  Total return: {results.total_return:.2%}")
        print(f"  Number of periods: {len(results.equity_curve)}")
        
        print("\n✓ Both bug fixes verified:")
        print("  ✓ Data extraction works (Bug #1 fixed)")
        print("  ✓ Timezone handling works (Bug #2 fixed)")
        
        return True
        
    except TypeError as e:
        if "Invalid comparison between dtype=datetime64" in str(e):
            print(f"✗ FAILED: Timezone bug not fixed")
            print(f"  Error: {e}")
            return False
        raise
    
    except AttributeError as e:
        if "'module' object has no attribute 'data'" in str(e):
            print(f"✗ FAILED: Variable shadowing bug not fixed")
            print(f"  Error: {e}")
            return False
        raise


def main():
    """Run all verification tests."""
    print_header("PRICE DATA VERIFICATION FOR BACKTESTING")
    
    print("This script verifies:")
    print("  1. Price data downloads correctly from Yahoo Finance")
    print("  2. Data is properly normalized and validated")
    print("  3. Data integrity checks pass")
    print("  4. Backtesting engine works with the data")
    print("  5. Bug fixes are working correctly")
    
    tests = [
        ("Data Download", verify_data_download),
        ("Data Normalization", verify_data_normalization),
        ("Data Integrity", verify_data_integrity),
        ("Backtesting Integration", verify_backtesting_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED with exception:")
            print(f"  {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print_section("SUMMARY")
    
    all_passed = all(passed for _, passed in results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    
    if all_passed:
        print("=" * 80)
        print("  ✓ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("Price data is correctly downloaded and used in backtesting.")
        print("Both bug fixes are working correctly.")
        return 0
    else:
        print("=" * 80)
        print("  ✗ SOME TESTS FAILED")
        print("=" * 80)
        print()
        print("Please review the failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
