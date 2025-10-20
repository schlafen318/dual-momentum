#!/usr/bin/env python3
"""
Quick Alpha Vantage Test Script

Simple script to verify Alpha Vantage API is working.
This is a minimal test - use alpha_vantage_demo.py for full examples.

Usage:
    python examples/quick_alpha_vantage_test.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_sources import AlphaVantageSource


def main():
    print("=" * 60)
    print("  Quick Alpha Vantage API Test")
    print("=" * 60)
    print()
    
    # Your API key
    api_key = "VT0RO0SAME6YV9PC"
    
    # Create source
    print("1. Initializing Alpha Vantage source...")
    source = AlphaVantageSource({'api_key': api_key})
    print(f"   ✓ {source.get_name()} initialized")
    
    # Check availability
    print("\n2. Checking API availability...")
    if not source.is_available():
        print("   ✗ API not available!")
        print("   Check your internet connection and API key.")
        return 1
    print("   ✓ API is available")
    
    # Download sample data
    print("\n3. Downloading sample data (SPY)...")
    try:
        end = datetime.now()
        start = end - timedelta(days=30)
        
        data = source.fetch_data('SPY', start, end)
        
        if len(data) == 0:
            print("   ✗ No data returned")
            return 1
        
        print(f"   ✓ Downloaded {len(data)} days of data")
        print(f"   ✓ Latest close: ${data['close'].iloc[-1]:.2f}")
        
        print("\n" + "=" * 60)
        print("  ✓ SUCCESS - Alpha Vantage is working!")
        print("=" * 60)
        print()
        print(f"Data range: {data.index[0].date()} to {data.index[-1].date()}")
        print(f"\nLast 3 days:")
        print(data[['close', 'volume']].tail(3).to_string())
        print()
        return 0
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
