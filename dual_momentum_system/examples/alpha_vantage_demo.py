#!/usr/bin/env python3
"""
Alpha Vantage Data Download Demo

This script demonstrates how to use Alpha Vantage for downloading market data
in the dual momentum system. Alpha Vantage provides reliable stock, forex, and
crypto data with a free tier (500 requests/day, 5 requests/minute).

Usage:
    # Set API key via environment variable
    export ALPHAVANTAGE_API_KEY=VT0RO0SAME6YV9PC
    python examples/alpha_vantage_demo.py
    
    # Or run directly (API key is in the script)
    python examples/alpha_vantage_demo.py
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_sources import AlphaVantageSource, get_default_data_source


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
    print("-" * 70)
    print(f"  {title}")
    print("-" * 70)


def demo_basic_usage():
    """Demonstrate basic Alpha Vantage usage."""
    print_section("Demo 1: Basic Alpha Vantage Data Download")
    
    # Your API key
    api_key = "VT0RO0SAME6YV9PC"
    
    # Create Alpha Vantage data source
    source = AlphaVantageSource({
        'api_key': api_key,
        'cache_enabled': True
    })
    
    print(f"✓ Alpha Vantage source initialized")
    print(f"  Name: {source.get_name()}")
    print(f"  Version: {source.get_version()}")
    print(f"  Description: {source.get_description()}")
    
    # Check availability
    print(f"\n✓ Checking API availability...")
    is_available = source.is_available()
    print(f"  Available: {'✓ Yes' if is_available else '✗ No'}")
    
    if not is_available:
        print("\n⚠️  API is not available. Please check:")
        print("     - API key is correct")
        print("     - Internet connection is working")
        print("     - You haven't exceeded rate limits")
        return False
    
    # Download data for a popular stock
    print(f"\n✓ Downloading data for SPY (S&P 500 ETF)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 3 months
    
    try:
        data = source.fetch_data('SPY', start_date, end_date, timeframe='1d')
        
        print(f"\n✓ Successfully downloaded {len(data)} days of data")
        print(f"\n  Data range: {data.index[0].date()} to {data.index[-1].date()}")
        print(f"\n  Latest prices:")
        print(f"    Open:   ${data['open'].iloc[-1]:.2f}")
        print(f"    High:   ${data['high'].iloc[-1]:.2f}")
        print(f"    Low:    ${data['low'].iloc[-1]:.2f}")
        print(f"    Close:  ${data['close'].iloc[-1]:.2f}")
        print(f"    Volume: {int(data['volume'].iloc[-1]):,}")
        
        # Show sample of data
        print(f"\n  Sample data (last 5 days):")
        print(data[['open', 'high', 'low', 'close', 'volume']].tail().to_string())
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error downloading data: {e}")
        return False


def demo_multiple_symbols():
    """Demonstrate downloading multiple symbols."""
    print_section("Demo 2: Download Multiple Symbols")
    
    api_key = "VT0RO0SAME6YV9PC"
    source = AlphaVantageSource({
        'api_key': api_key,
        'cache_enabled': True
    })
    
    # Common dual momentum universe
    symbols = ['SPY', 'QQQ', 'TLT']  # US Stocks, Tech, Bonds
    
    print(f"✓ Downloading data for {len(symbols)} symbols: {', '.join(symbols)}")
    print(f"  (Note: Free tier limit is 5 requests/minute)")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # 1 month
    
    results = {}
    
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"\n  [{i}/{len(symbols)}] Fetching {symbol}...", end=' ')
            data = source.fetch_data(symbol, start_date, end_date, timeframe='1d')
            results[symbol] = data
            print(f"✓ Got {len(data)} days")
            
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    # Summary
    print(f"\n✓ Successfully downloaded {len(results)}/{len(symbols)} symbols")
    
    if results:
        print(f"\n  Summary:")
        for symbol, data in results.items():
            latest_close = data['close'].iloc[-1]
            change_pct = ((data['close'].iloc[-1] / data['close'].iloc[0]) - 1) * 100
            print(f"    {symbol:5s}: ${latest_close:8.2f}  ({change_pct:+.2f}% over period)")
    
    return len(results) > 0


def demo_with_multi_source():
    """Demonstrate using Alpha Vantage with multi-source failover."""
    print_section("Demo 3: Multi-Source Setup (Recommended)")
    
    print("This is the recommended way to use Alpha Vantage in production.")
    print("It sets up automatic failover from Yahoo Finance to Alpha Vantage.\n")
    
    # Configure multi-source with Alpha Vantage as backup
    config = {
        'alphavantage_api_key': 'VT0RO0SAME6YV9PC'
    }
    
    source = get_default_data_source(config)
    
    print(f"✓ Multi-source provider initialized with {len(source.sources)} sources:")
    for i, src in enumerate(source.sources, 1):
        print(f"    {i}. {src.get_name()}")
    
    # Check status
    status = source.get_source_status()
    print(f"\n✓ Source availability:")
    for name, available in status.items():
        print(f"    - {name}: {'✓ Available' if available else '✗ Unavailable'}")
    
    # Fetch data - will automatically use Yahoo first, then Alpha Vantage if needed
    print(f"\n✓ Fetching data with automatic failover...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        data = source.fetch_data('AAPL', start_date, end_date)
        
        print(f"\n✓ Successfully fetched {len(data)} days of data for AAPL")
        print(f"  Latest close: ${data['close'].iloc[-1]:.2f}")
        print(f"\n  This data was fetched from the first available source.")
        print(f"  If Yahoo Finance fails, it will automatically try Alpha Vantage!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def demo_backtest_integration():
    """Show how to use Alpha Vantage in a backtest."""
    print_section("Demo 4: Integration with Backtesting")
    
    print("Here's how to use Alpha Vantage in your backtests:\n")
    
    code = '''
# Example: Using Alpha Vantage in a backtest
from datetime import datetime, timedelta
from src.data_sources import get_default_data_source
from src.backtesting.engine import BacktestEngine
from src.strategies.dual_momentum import DualMomentumStrategy

# 1. Setup data source with Alpha Vantage
config = {
    'alphavantage_api_key': 'VT0RO0SAME6YV9PC'
}
data_source = get_default_data_source(config)

# 2. Define your universe
universe = ['SPY', 'QQQ', 'TLT', 'GLD']
safe_asset = 'SHY'

# 3. Download data
end_date = datetime.now()
start_date = end_date - timedelta(days=365)  # 1 year

price_data = {}
for symbol in universe + [safe_asset]:
    try:
        data = data_source.fetch_data(symbol, start_date, end_date)
        price_data[symbol] = data
        print(f"✓ Downloaded {symbol}: {len(data)} days")
    except Exception as e:
        print(f"✗ Failed to download {symbol}: {e}")

# 4. Run backtest
strategy = DualMomentumStrategy({
    'lookback_period': 120,  # 6 months
    'rebalance_frequency': 'monthly'
})

engine = BacktestEngine(
    strategy=strategy,
    universe=universe,
    safe_asset=safe_asset,
    initial_capital=10000
)

results = engine.run(price_data, start_date, end_date)
print(f"\\nBacktest Results:")
print(f"  Total Return: {results.total_return:.2%}")
print(f"  Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"  Max Drawdown: {results.max_drawdown:.2%}")
'''
    
    print(code)
    
    print("\n✓ This pattern ensures reliable data download with automatic failover!")


def main():
    """Run all demos."""
    print_header("Alpha Vantage Data Download Demo")
    
    print("This demo shows how to use Alpha Vantage for market data in the")
    print("dual momentum trading system.\n")
    print("API Key: VT0RO0SAME6YV9PC")
    print("Free Tier: 500 requests/day, 5 requests/minute")
    
    demos = [
        ("Basic Usage", demo_basic_usage),
        ("Multiple Symbols", demo_multiple_symbols),
        ("Multi-Source Setup", demo_with_multi_source),
        ("Backtest Integration", demo_backtest_integration),
    ]
    
    results = []
    
    for demo_name, demo_func in demos:
        try:
            result = demo_func()
            results.append((demo_name, result))
        except Exception as e:
            print(f"\n✗ {demo_name} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((demo_name, False))
    
    # Summary
    print_section("SUMMARY")
    
    for demo_name, result in results:
        if result is True:
            status = "✓ SUCCESS"
        elif result is False:
            status = "✗ FAILED"
        else:
            status = "⊘ INFO"
        print(f"{status}: {demo_name}")
    
    success_count = sum(1 for _, r in results if r is True)
    
    if success_count >= 2:
        print()
        print("=" * 80)
        print("  ✓ Alpha Vantage is working correctly!")
        print("=" * 80)
        print()
        print("Next Steps:")
        print("  1. Use get_default_data_source() in your code for automatic failover")
        print("  2. Alpha Vantage will be used as backup when Yahoo Finance is down")
        print("  3. Consider setting ALPHAVANTAGE_API_KEY environment variable")
        print()
        print("Environment Variable Setup:")
        print("  export ALPHAVANTAGE_API_KEY=VT0RO0SAME6YV9PC")
        print("  # Or add to your .env file")
        print()
        return 0
    else:
        print()
        print("Please check the errors above and ensure:")
        print("  - API key is valid")
        print("  - Internet connection is working")
        print("  - You haven't exceeded rate limits")
        return 1


if __name__ == "__main__":
    sys.exit(main())
