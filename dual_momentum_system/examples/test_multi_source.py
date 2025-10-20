#!/usr/bin/env python3
"""
Test script for multi-source data provider with failover.

This script demonstrates and tests the new multi-source data provider
that can automatically failover to alternative data sources when
Yahoo Finance is unavailable.

Usage:
    python examples/test_multi_source.py
    
    # With API keys for full testing
    export ALPHAVANTAGE_API_KEY=your_key
    export TWELVEDATA_API_KEY=your_key
    python examples/test_multi_source.py
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_sources import (
    YahooFinanceDirectSource,
    AlphaVantageSource,
    TwelveDataSource,
    MultiSourceDataProvider,
    get_default_data_source
)


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
    print("-" * 60)
    print(f"  {title}")
    print("-" * 60)


def test_yahoo_direct():
    """Test Yahoo Finance Direct source."""
    print_section("Test 1: Yahoo Finance Direct")
    
    try:
        source = YahooFinanceDirectSource({'cache_enabled': True})
        
        print(f"✓ Source initialized: {source.get_name()}")
        print(f"✓ Available: {source.is_available()}")
        
        # Fetch data
        end = datetime.now()
        start = end - timedelta(days=30)
        data = source.fetch_data('SPY', start, end)
        
        print(f"✓ Fetched {len(data)} rows for SPY")
        print(f"✓ Latest close: ${data['close'].iloc[-1]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_alpha_vantage():
    """Test Alpha Vantage source (if API key available)."""
    print_section("Test 2: Alpha Vantage (Optional)")
    
    api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    
    if not api_key:
        print("⊘ Skipped: No API key (set ALPHAVANTAGE_API_KEY env var)")
        print("  Get free key at: https://www.alphavantage.co/support/#api-key")
        return None
    
    try:
        source = AlphaVantageSource({
            'api_key': api_key,
            'cache_enabled': True
        })
        
        print(f"✓ Source initialized: {source.get_name()}")
        print(f"✓ Available: {source.is_available()}")
        
        # Fetch data
        end = datetime.now()
        start = end - timedelta(days=30)
        data = source.fetch_data('AAPL', start, end)
        
        print(f"✓ Fetched {len(data)} rows for AAPL")
        if len(data) > 0:
            print(f"✓ Latest close: ${data['close'].iloc[-1]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_twelve_data():
    """Test Twelve Data source (if API key available)."""
    print_section("Test 3: Twelve Data (Optional)")
    
    api_key = os.environ.get('TWELVEDATA_API_KEY')
    
    if not api_key:
        print("⊘ Skipped: No API key (set TWELVEDATA_API_KEY env var)")
        print("  Get free key at: https://twelvedata.com/pricing")
        return None
    
    try:
        source = TwelveDataSource({
            'api_key': api_key,
            'cache_enabled': True
        })
        
        print(f"✓ Source initialized: {source.get_name()}")
        print(f"✓ Available: {source.is_available()}")
        
        # Fetch data
        end = datetime.now()
        start = end - timedelta(days=30)
        data = source.fetch_data('MSFT', start, end)
        
        print(f"✓ Fetched {len(data)} rows for MSFT")
        if len(data) > 0:
            print(f"✓ Latest close: ${data['close'].iloc[-1]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_multi_source_basic():
    """Test basic multi-source functionality."""
    print_section("Test 4: Multi-Source Provider (Basic)")
    
    try:
        # Create multi-source with just Yahoo
        yahoo = YahooFinanceDirectSource({'cache_enabled': True})
        multi = MultiSourceDataProvider({
            'sources': [yahoo],
            'cache_enabled': True
        })
        
        print(f"✓ Multi-source initialized with {len(multi.sources)} source(s)")
        print(f"✓ Available: {multi.is_available()}")
        
        # Check status
        status = multi.get_source_status()
        print(f"✓ Source status:")
        for name, available in status.items():
            print(f"    - {name}: {'✓ Available' if available else '✗ Unavailable'}")
        
        # Fetch data
        end = datetime.now()
        start = end - timedelta(days=30)
        data = multi.fetch_data('SPY', start, end)
        
        print(f"✓ Fetched {len(data)} rows for SPY")
        print(f"✓ Latest close: ${data['close'].iloc[-1]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_source_with_alternatives():
    """Test multi-source with all available alternatives."""
    print_section("Test 5: Multi-Source with All Alternatives")
    
    try:
        sources = []
        
        # Always add Yahoo
        sources.append(YahooFinanceDirectSource({'cache_enabled': True}))
        
        # Add Alpha Vantage if available
        av_key = os.environ.get('ALPHAVANTAGE_API_KEY')
        if av_key:
            sources.append(AlphaVantageSource({
                'api_key': av_key,
                'cache_enabled': True
            }))
        
        # Add Twelve Data if available
        td_key = os.environ.get('TWELVEDATA_API_KEY')
        if td_key:
            sources.append(TwelveDataSource({
                'api_key': td_key,
                'cache_enabled': True
            }))
        
        multi = MultiSourceDataProvider({
            'sources': sources,
            'cache_enabled': True
        })
        
        print(f"✓ Multi-source initialized with {len(multi.sources)} source(s):")
        for i, source in enumerate(multi.sources):
            print(f"    {i+1}. {source.get_name()}")
        
        # Check status
        status = multi.get_source_status()
        print(f"\n✓ Source availability:")
        for name, available in status.items():
            print(f"    - {name}: {'✓ Available' if available else '✗ Unavailable'}")
        
        # Fetch multiple symbols
        end = datetime.now()
        start = end - timedelta(days=30)
        symbols = ['SPY', 'TLT', 'GLD']
        
        print(f"\n✓ Fetching {len(symbols)} symbols...")
        data = multi.fetch_multiple(symbols, start, end)
        
        print(f"✓ Successfully fetched {len(data)}/{len(symbols)} symbols:")
        for symbol, df in data.items():
            print(f"    - {symbol}: {len(df)} rows, latest close: ${df['close'].iloc[-1]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_default_data_source():
    """Test the convenience get_default_data_source function."""
    print_section("Test 6: Default Data Source (Convenience Function)")
    
    try:
        # Get API keys if available
        config = {}
        if os.environ.get('ALPHAVANTAGE_API_KEY'):
            config['alphavantage_api_key'] = os.environ['ALPHAVANTAGE_API_KEY']
        if os.environ.get('TWELVEDATA_API_KEY'):
            config['twelvedata_api_key'] = os.environ['TWELVEDATA_API_KEY']
        
        # Get default source
        source = get_default_data_source(config)
        
        print(f"✓ Default source initialized with {len(source.sources)} provider(s)")
        
        # Check status
        status = source.get_source_status()
        print(f"✓ Provider status:")
        for name, available in status.items():
            print(f"    - {name}: {'✓ Available' if available else '✗ Unavailable'}")
        
        # Fetch data
        end = datetime.now()
        start = end - timedelta(days=7)
        data = source.fetch_data('AAPL', start, end)
        
        print(f"✓ Fetched {len(data)} rows for AAPL")
        if len(data) > 0:
            print(f"✓ Latest close: ${data['close'].iloc[-1]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print_header("Multi-Source Data Provider Test Suite")
    
    print("This test suite verifies:")
    print("  1. Yahoo Finance Direct (primary, always available)")
    print("  2. Alpha Vantage (optional, requires API key)")
    print("  3. Twelve Data (optional, requires API key)")
    print("  4. Multi-source failover functionality")
    print("  5. Convenience functions")
    print()
    print("Note: Tests 2-3 will be skipped if API keys are not configured.")
    print("      Set ALPHAVANTAGE_API_KEY and TWELVEDATA_API_KEY env vars to enable.")
    
    tests = [
        ("Yahoo Finance Direct", test_yahoo_direct),
        ("Alpha Vantage", test_alpha_vantage),
        ("Twelve Data", test_twelve_data),
        ("Multi-Source Basic", test_multi_source_basic),
        ("Multi-Source with Alternatives", test_multi_source_with_alternatives),
        ("Default Data Source", test_default_data_source),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED with exception:")
            print(f"  {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print_section("SUMMARY")
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    
    for test_name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print()
        print("=" * 80)
        print("  ✓ ALL TESTS PASSED (or skipped)")
        print("=" * 80)
        print()
        print("Multi-source data provider is working correctly!")
        print()
        print("Usage in your code:")
        print("  from src.data_sources import get_default_data_source")
        print("  source = get_default_data_source()")
        print("  data = source.fetch_data('SPY', start_date, end_date)")
        print()
        return 0
    else:
        print()
        print("=" * 80)
        print("  ✗ SOME TESTS FAILED")
        print("=" * 80)
        print()
        print("Please review the failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
