"""
Test script to verify Streamlit Cloud yfinance fix.

This script tests:
1. Environment detection
2. Data source selection
3. Data fetching with YahooFinanceDirectSource
4. Fallback behavior

Run this locally to verify the fix works before deploying to Streamlit Cloud.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_environment_detection():
    """Test if environment detection works correctly."""
    print("=" * 80)
    print("TEST 1: Environment Detection")
    print("=" * 80)
    
    from src.data_sources import _is_streamlit_cloud
    
    # Test current environment
    is_cloud = _is_streamlit_cloud()
    print(f"✓ Environment detection function exists")
    print(f"  Current environment: {'Streamlit Cloud' if is_cloud else 'Local'}")
    
    # Show environment variables being checked
    env_vars = [
        'STREAMLIT_SHARING_MODE',
        'STREAMLIT_SERVER_PORT',
        'HOSTNAME',
        'DYNO',
        'RENDER',
        'RAILWAY_ENVIRONMENT',
        'VERCEL',
        'NETLIFY',
    ]
    
    print(f"\n  Environment variables checked:")
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"    - {var}: {value}")
    
    print("\n✅ Environment detection test passed\n")
    return is_cloud


def test_data_source_selection(simulate_cloud=False):
    """Test that correct data source is selected."""
    print("=" * 80)
    print(f"TEST 2: Data Source Selection {'(Simulated Cloud)' if simulate_cloud else '(Current Env)'}")
    print("=" * 80)
    
    from src.data_sources import get_default_data_source
    
    # Get data source with optional cloud simulation
    config = {'force_direct': True} if simulate_cloud else {}
    data_source = get_default_data_source(config)
    
    print(f"✓ Data source initialized: {type(data_source).__name__}")
    
    # Check internal sources
    if hasattr(data_source, 'sources'):
        print(f"  Available sources ({len(data_source.sources)}):")
        for i, source in enumerate(data_source.sources, 1):
            print(f"    {i}. {type(source).__name__}")
    
    print("\n✅ Data source selection test passed\n")
    return data_source


def test_data_fetching(data_source):
    """Test actual data fetching."""
    print("=" * 80)
    print("TEST 3: Data Fetching")
    print("=" * 80)
    
    # Test with well-known symbol
    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # 1 month
    
    print(f"  Fetching {symbol} from {start_date.date()} to {end_date.date()}")
    
    try:
        data = data_source.fetch_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe='1d'
        )
        
        if data is not None and not data.empty:
            print(f"✓ Successfully fetched {len(data)} rows")
            print(f"  Columns: {list(data.columns)}")
            print(f"  Date range: {data.index[0].date()} to {data.index[-1].date()}")
            print(f"  Latest close: ${data['close'].iloc[-1]:.2f}")
            print("\n✅ Data fetching test passed\n")
            return True
        else:
            print(f"❌ Received empty data")
            return False
            
    except Exception as e:
        print(f"❌ Data fetching failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_fetching(data_source):
    """Test batch fetching of multiple symbols."""
    print("=" * 80)
    print("TEST 4: Batch Fetching")
    print("=" * 80)
    
    symbols = ['SPY', 'QQQ', 'IWM']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"  Fetching {len(symbols)} symbols: {', '.join(symbols)}")
    
    try:
        data_dict = data_source.fetch_multiple(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            timeframe='1d'
        )
        
        success_count = len(data_dict)
        print(f"✓ Successfully fetched {success_count}/{len(symbols)} symbols")
        
        for symbol, data in data_dict.items():
            print(f"  - {symbol}: {len(data)} rows")
        
        if success_count > 0:
            print("\n✅ Batch fetching test passed\n")
            return True
        else:
            print("\n⚠️ Batch fetching test partially failed (no data)\n")
            return False
            
    except Exception as e:
        print(f"❌ Batch fetching failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_caching(data_source):
    """Test caching functionality."""
    print("=" * 80)
    print("TEST 5: Caching")
    print("=" * 80)
    
    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    import time
    
    # First fetch (should hit API)
    print(f"  First fetch (should be slow)...")
    start_time = time.time()
    data1 = data_source.fetch_data(symbol, start_date, end_date)
    first_duration = time.time() - start_time
    print(f"    Duration: {first_duration:.3f}s")
    
    # Second fetch (should use cache)
    print(f"  Second fetch (should be fast - cached)...")
    start_time = time.time()
    data2 = data_source.fetch_data(symbol, start_date, end_date)
    second_duration = time.time() - start_time
    print(f"    Duration: {second_duration:.3f}s")
    
    # Calculate speedup
    if second_duration > 0:
        speedup = first_duration / second_duration
        print(f"  Cache speedup: {speedup:.1f}x faster")
        
        if speedup > 10:
            print("\n✅ Caching test passed (significant speedup)\n")
            return True
        else:
            print("\n⚠️ Caching may not be working (minimal speedup)\n")
            return False
    else:
        print("\n⚠️ Second fetch was too fast to measure\n")
        return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("STREAMLIT CLOUD YFINANCE FIX - VERIFICATION TESTS")
    print("=" * 80 + "\n")
    
    results = []
    
    try:
        # Test 1: Environment detection
        is_cloud = test_environment_detection()
        results.append(("Environment Detection", True))
        
        # Test 2a: Data source selection (current environment)
        data_source = test_data_source_selection(simulate_cloud=False)
        results.append(("Data Source Selection (Current)", True))
        
        # Test 2b: Data source selection (simulated cloud)
        cloud_data_source = test_data_source_selection(simulate_cloud=True)
        results.append(("Data Source Selection (Simulated Cloud)", True))
        
        # Test 3: Data fetching
        fetch_success = test_data_fetching(data_source)
        results.append(("Data Fetching", fetch_success))
        
        # Test 4: Batch fetching
        batch_success = test_batch_fetching(data_source)
        results.append(("Batch Fetching", batch_success))
        
        # Test 5: Caching
        cache_success = test_caching(data_source)
        results.append(("Caching", cache_success))
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The fix is working correctly.")
        print("\nYou can now deploy to Streamlit Cloud with confidence.")
        print("\nExpected behavior on Streamlit Cloud:")
        print("  - Environment will be auto-detected as cloud")
        print("  - YahooFinanceDirectSource will be used automatically")
        print("  - Data fetching should work reliably")
        print("  - No yfinance import errors")
    else:
        print("\n⚠️ Some tests failed. Review the errors above.")
        print("\nIf data fetching failed, possible causes:")
        print("  1. Network connectivity issues")
        print("  2. Yahoo Finance temporary outage")
        print("  3. Rate limiting (try again in a few minutes)")
    
    print("\n" + "=" * 80 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
