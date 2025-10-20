"""
Test script for Yahoo Finance Direct data source.

This script verifies that the new direct HTTP-based Yahoo Finance
data source works correctly without the yfinance library.
"""

from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_sources.yahoo_finance_direct import YahooFinanceDirectSource
from loguru import logger


def test_availability():
    """Test if the data source is available."""
    print("\n" + "="*60)
    print("Testing Yahoo Finance Direct Availability")
    print("="*60)
    
    source = YahooFinanceDirectSource()
    is_available = source.is_available()
    
    print(f"✓ Service available: {is_available}")
    assert is_available, "Yahoo Finance should be available"
    print("PASSED: Availability check")


def test_fetch_single_symbol():
    """Test fetching data for a single symbol."""
    print("\n" + "="*60)
    print("Testing Single Symbol Fetch")
    print("="*60)
    
    source = YahooFinanceDirectSource()
    
    # Fetch SPY data for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"Fetching SPY from {start_date.date()} to {end_date.date()}")
    data = source.fetch_data('SPY', start_date, end_date, timeframe='1d')
    
    print(f"✓ Received {len(data)} rows")
    print(f"✓ Columns: {list(data.columns)}")
    print(f"\nFirst 3 rows:")
    print(data.head(3))
    print(f"\nLast 3 rows:")
    print(data.tail(3))
    
    # Validate data
    assert len(data) > 0, "Should have received data"
    assert 'close' in data.columns, "Should have close column"
    assert 'volume' in data.columns, "Should have volume column"
    
    print("\nPASSED: Single symbol fetch")


def test_fetch_multiple_symbols():
    """Test fetching data for multiple symbols."""
    print("\n" + "="*60)
    print("Testing Multiple Symbols Fetch")
    print("="*60)
    
    source = YahooFinanceDirectSource()
    
    symbols = ['SPY', 'TLT', 'GLD']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"Fetching {symbols} from {start_date.date()} to {end_date.date()}")
    data_dict = source.fetch_multiple(symbols, start_date, end_date, timeframe='1d')
    
    print(f"✓ Received data for {len(data_dict)} symbols")
    
    for symbol, data in data_dict.items():
        print(f"\n{symbol}:")
        print(f"  - {len(data)} rows")
        print(f"  - Latest close: ${data['close'].iloc[-1]:.2f}")
    
    # Validate data
    assert len(data_dict) > 0, "Should have received data for at least one symbol"
    for symbol in symbols:
        if symbol in data_dict:
            assert len(data_dict[symbol]) > 0, f"Should have data for {symbol}"
    
    print("\nPASSED: Multiple symbols fetch")


def test_latest_price():
    """Test getting latest price."""
    print("\n" + "="*60)
    print("Testing Latest Price")
    print("="*60)
    
    source = YahooFinanceDirectSource()
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in symbols:
        price = source.get_latest_price(symbol)
        print(f"✓ {symbol}: ${price:.2f}" if price else f"✗ {symbol}: No price available")
        assert price is not None, f"Should have price for {symbol}"
        assert price > 0, f"Price should be positive for {symbol}"
    
    print("\nPASSED: Latest price fetch")


def test_asset_info():
    """Test getting asset information."""
    print("\n" + "="*60)
    print("Testing Asset Info")
    print("="*60)
    
    source = YahooFinanceDirectSource()
    
    info = source.get_asset_info('AAPL')
    
    if info:
        print(f"✓ Symbol: {info.get('symbol')}")
        print(f"✓ Name: {info.get('name')}")
        print(f"✓ Sector: {info.get('sector')}")
        print(f"✓ Exchange: {info.get('exchange')}")
        print(f"✓ Currency: {info.get('currency')}")
        
        print("\nPASSED: Asset info fetch")
    else:
        print("Note: Asset info not available (this is optional)")


def test_caching():
    """Test caching functionality."""
    print("\n" + "="*60)
    print("Testing Caching")
    print("="*60)
    
    source = YahooFinanceDirectSource({'cache_enabled': True})
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # First fetch (from API)
    print("First fetch (should hit API)...")
    import time
    t1 = time.time()
    data1 = source.fetch_data('SPY', start_date, end_date, timeframe='1d')
    t1_elapsed = time.time() - t1
    
    # Second fetch (from cache)
    print("Second fetch (should use cache)...")
    t2 = time.time()
    data2 = source.fetch_data('SPY', start_date, end_date, timeframe='1d')
    t2_elapsed = time.time() - t2
    
    print(f"✓ First fetch: {t1_elapsed:.3f}s ({len(data1)} rows)")
    print(f"✓ Second fetch: {t2_elapsed:.3f}s ({len(data2)} rows)")
    print(f"✓ Cache speedup: {t1_elapsed/t2_elapsed:.1f}x faster")
    
    assert len(data1) == len(data2), "Cached data should match"
    assert t2_elapsed < t1_elapsed, "Cached fetch should be faster"
    
    print("\nPASSED: Caching")


def test_supported_features():
    """Test supported features."""
    print("\n" + "="*60)
    print("Testing Supported Features")
    print("="*60)
    
    source = YahooFinanceDirectSource()
    
    timeframes = source.get_supported_timeframes()
    print(f"✓ Supported timeframes: {timeframes}")
    assert '1d' in timeframes, "Should support daily timeframe"
    assert '1h' in timeframes, "Should support hourly timeframe"
    
    asset_types = source.get_supported_asset_types()
    print(f"✓ Supported asset types: {asset_types}")
    assert len(asset_types) > 0, "Should support at least one asset type"
    
    requires_auth = source.requires_authentication()
    print(f"✓ Requires authentication: {requires_auth}")
    assert not requires_auth, "Should not require authentication"
    
    print("\nPASSED: Supported features")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("Yahoo Finance Direct Data Source Test Suite")
    print("="*70)
    
    tests = [
        test_availability,
        test_fetch_single_symbol,
        test_fetch_multiple_symbols,
        test_latest_price,
        test_asset_info,
        test_caching,
        test_supported_features,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ FAILED: {test.__name__}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n✓ All tests passed! Yahoo Finance Direct is working correctly.")
        print("\nThis data source works without the yfinance library and is")
        print("compatible with Streamlit Cloud and other restricted environments.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
