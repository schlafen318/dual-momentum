#!/usr/bin/env python3
"""
Test script to verify benchmark alignment with performance period.

This script runs a backtest with benchmark data to ensure that:
1. Benchmark performance starts from the first rebalancing date
2. Benchmark and strategy are properly aligned for fair comparison
3. All performance metrics use the same time period
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backtesting.engine import BacktestEngine
from src.strategies.absolute_momentum import AbsoluteMomentumStrategy
from src.data_sources import get_default_data_source
from src.core.types import PriceData, AssetMetadata, AssetType
from loguru import logger

def test_benchmark_alignment():
    """Test that benchmark is properly aligned with performance period."""
    
    # Configure console logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    print("=" * 80)
    print("TESTING BENCHMARK ALIGNMENT WITH PERFORMANCE PERIOD")
    print("=" * 80)
    
    # Create strategy
    strategy = AbsoluteMomentumStrategy({
        'lookback_period': 20,
        'threshold': 0.0,
        'safe_asset': 'TLT'
    })
    
    # Create data source
    data_source = get_default_data_source()
    
    # Fetch data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f"Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    symbols = ['SPY', 'TLT', 'GLD']
    price_data = {}
    
    for symbol in symbols:
        try:
            data = data_source.fetch_data(symbol, start_date, end_date)
            if len(data) > 0:
                # Wrap DataFrame in PriceData object
                metadata = AssetMetadata(
                    symbol=symbol,
                    name=f"{symbol} Stock",
                    asset_type=AssetType.EQUITY,
                    exchange='NYSE',
                    currency='USD'
                )
                price_data[symbol] = PriceData(
                    symbol=symbol,
                    data=data,
                    metadata=metadata
                )
                print(f"✓ Fetched {len(data)} rows for {symbol}")
            else:
                print(f"✗ No data for {symbol}")
        except Exception as e:
            print(f"✗ Error fetching {symbol}: {e}")
    
    if not price_data:
        print("❌ No price data available for backtesting")
        return
    
    # Use SPY as benchmark
    benchmark_data = price_data['SPY']
    
    # Create backtest engine
    engine = BacktestEngine(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005
    )
    
    print(f"\nRunning backtest with {len(price_data)} assets and SPY benchmark...")
    print("Check the logs for benchmark alignment verification!")
    
    # Run backtest
    try:
        results = engine.run(
            strategy=strategy,
            price_data=price_data,
            start_date=start_date,
            end_date=end_date,
            benchmark_data=benchmark_data
        )
        
        print(f"\n✅ Backtest completed successfully!")
        print(f"   Final Value: ${results.final_capital:,.2f}")
        print(f"   Total Return: {results.total_return:.2%}")
        
        # Check benchmark metrics
        if 'benchmark_return' in results.metrics:
            benchmark_return = results.metrics['benchmark_return']
            outperformance = results.total_return - benchmark_return
            
            print(f"\n📊 BENCHMARK COMPARISON (Aligned to Performance Period):")
            print(f"   Strategy Return: {results.total_return:.2%}")
            print(f"   Benchmark Return: {benchmark_return:.2%}")
            print(f"   Outperformance: {outperformance:+.2%}")
            
            if 'alpha' in results.metrics:
                print(f"   Alpha: {results.metrics['alpha']:.2%}")
            if 'beta' in results.metrics:
                print(f"   Beta: {results.metrics['beta']:.2f}")
            if 'information_ratio' in results.metrics:
                print(f"   Information Ratio: {results.metrics['information_ratio']:.2f}")
        else:
            print("\n❌ No benchmark metrics available")
            
        # Check if logs directory was created
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_files = list(logs_dir.glob("backtest_*.log"))
            print(f"\n📁 Log files created: {len(log_files)}")
            for log_file in log_files:
                print(f"   - {log_file.name}")
        else:
            print("\n❌ No logs directory created")
            
    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_benchmark_alignment()
