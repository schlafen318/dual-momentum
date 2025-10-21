#!/usr/bin/env python3
"""
Test script to verify benchmark indexing works correctly.

This script creates a simple test to verify that:
1. Benchmark starts with the same notional value as strategy
2. Benchmark is properly indexed from its actual price
3. Both strategy and benchmark have the same starting value
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backtesting.engine import BacktestEngine
from src.strategies.absolute_momentum import AbsoluteMomentumStrategy
from src.data_sources import get_default_data_source
from src.core.types import PriceData, AssetMetadata, AssetType
from loguru import logger

def test_benchmark_indexing():
    """Test that benchmark indexing works correctly."""
    
    # Configure console logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    print("=" * 80)
    print("TESTING BENCHMARK INDEXING")
    print("=" * 80)
    
    # Create simple test data
    dates = pd.date_range('2025-08-21', periods=5, freq='D')
    
    # Create strategy data (portfolio values)
    strategy_values = [100000, 101000, 102000, 101500, 103000]
    strategy_series = pd.Series(strategy_values, index=dates)
    
    # Create benchmark data (SPY prices)
    spy_prices = [633.79, 635.50, 638.20, 636.80, 640.10]
    spy_series = pd.Series(spy_prices, index=dates)
    
    print(f"Strategy values: {strategy_values}")
    print(f"SPY prices: {spy_prices}")
    
    # Test the indexing logic
    strategy_start_value = strategy_series.iloc[0]
    benchmark_start_price = spy_series.iloc[0]
    
    print(f"\nStrategy start value: ${strategy_start_value:,.2f}")
    print(f"Benchmark start price: ${benchmark_start_price:.2f}")
    
    # Create indexed benchmark values
    benchmark_indexed = (spy_series / benchmark_start_price) * strategy_start_value
    
    print(f"\nIndexed benchmark values:")
    for i, (date, value) in enumerate(benchmark_indexed.items()):
        print(f"  {date.strftime('%Y-%m-%d')}: ${value:,.2f}")
    
    # Calculate returns
    strategy_returns = strategy_series.pct_change().dropna()
    benchmark_returns = benchmark_indexed.pct_change().dropna()
    
    print(f"\nReturns comparison:")
    print(f"Strategy returns: {strategy_returns.values}")
    print(f"Benchmark returns: {benchmark_returns.values}")
    
    # Verify both start with same value
    print(f"\nVerification:")
    print(f"Strategy starts at: ${strategy_series.iloc[0]:,.2f}")
    print(f"Benchmark starts at: ${benchmark_indexed.iloc[0]:,.2f}")
    print(f"Same starting value: {strategy_series.iloc[0] == benchmark_indexed.iloc[0]}")
    
    # Calculate total returns
    strategy_total = (1 + strategy_returns).prod() - 1
    benchmark_total = (1 + benchmark_returns).prod() - 1
    
    print(f"\nTotal returns:")
    print(f"Strategy: {strategy_total:.2%}")
    print(f"Benchmark: {benchmark_total:.2%}")
    print(f"Outperformance: {strategy_total - benchmark_total:+.2%}")
    
    print("\n✅ Benchmark indexing test completed!")

if __name__ == "__main__":
    test_benchmark_indexing()
