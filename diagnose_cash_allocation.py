"""
Diagnostic script to understand the 7.52% cash allocation issue.

Run this with your exact backtest setup to see what's happening.
"""

from datetime import datetime
from loguru import logger

# Set up logging to console
logger.remove()
logger.add(lambda msg: print(msg, end=''), colorize=True, level="INFO")

print("="*80)
print("CASH ALLOCATION DIAGNOSTIC")
print("="*80)

# TODO: Replace these with your actual setup
YOUR_4_SYMBOLS = ['SPY', 'QQQ', 'DIA', 'IWM']  # Replace with your actual 4 symbols
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2023, 12, 31)

print(f"\nYour setup:")
print(f"  Symbols: {YOUR_4_SYMBOLS}")
print(f"  Period: {START_DATE} to {END_DATE}")

# Import necessary components
try:
    from dual_momentum_system.src.data import YahooFinanceSource
    from dual_momentum_system.src.strategies import DualMomentumStrategy
    from dual_momentum_system.src.backtesting import BacktestEngine
    from dual_momentum_system.src.core.types import AssetClass
    
    print("\n✓ Imports successful")
    
    # Fetch data
    print("\n[1/4] Fetching price data...")
    data_source = YahooFinanceSource()
    price_data = {}
    
    for symbol in YOUR_4_SYMBOLS:
        try:
            data = data_source.fetch_data(
                symbol=symbol,
                start_date=START_DATE,
                end_date=END_DATE,
                asset_class=AssetClass.EQUITY
            )
            price_data[symbol] = data
            print(f"  ✓ {symbol}: {len(data.data)} bars")
        except Exception as e:
            print(f"  ✗ {symbol}: {e}")
    
    if len(price_data) != len(YOUR_4_SYMBOLS):
        print(f"\n⚠️ Warning: Only got {len(price_data)}/{len(YOUR_4_SYMBOLS)} symbols")
    
    # Create strategy with default settings
    print("\n[2/4] Creating strategy with 'default' settings...")
    strategy_config = {
        'lookback_period': 252,
        'rebalance_frequency': 'monthly',
        'position_count': min(3, len(price_data)),  # UI default
        'absolute_threshold': 0.0,
        'safe_asset': None,  # You said no safe asset
    }
    
    print(f"  Strategy config: {strategy_config}")
    strategy = DualMomentumStrategy(strategy_config)
    
    # Create backtest engine
    print("\n[3/4] Creating backtest engine...")
    engine = BacktestEngine(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005
    )
    
    # Run backtest with detailed logging
    print("\n[4/4] Running backtest (check logs for [ORDER SIZING] lines)...")
    print("-"*80)
    
    results = engine.run(
        strategy=strategy,
        price_data=price_data,
        start_date=START_DATE,
        end_date=END_DATE
    )
    
    print("-"*80)
    print("\n✓ Backtest complete!")
    
    # Analyze first rebalance allocation
    print("\n" + "="*80)
    print("FIRST REBALANCE ANALYSIS")
    print("="*80)
    
    if not results.positions.empty:
        first_date = results.positions.index[0]
        first_row = results.positions.iloc[0]
        
        print(f"\nDate: {first_date}")
        print(f"Portfolio value: ${first_row.get('portfolio_value', 0):,.2f}")
        print(f"Cash: ${first_row.get('cash', 0):,.2f} ({first_row.get('cash_pct', 0):.2f}%)")
        
        print("\nPositions:")
        for col in results.positions.columns:
            if col.endswith('_pct') and col not in ['cash_pct']:
                symbol = col.replace('_pct', '')
                pct = first_row[col]
                if pct > 0:
                    value = first_row.get(f'{symbol}_value', 0)
                    print(f"  {symbol}: ${value:,.2f} ({pct:.2f}%)")
        
        # Calculate total allocation
        total_pct = sum(first_row[col] for col in results.positions.columns 
                       if col.endswith('_pct') and col not in ['cash_pct'])
        cash_pct = first_row.get('cash_pct', 0)
        
        print(f"\nTotal risky asset allocation: {total_pct:.2f}%")
        print(f"Cash allocation: {cash_pct:.2f}%")
        print(f"Sum: {total_pct + cash_pct:.2f}%")
        
        if cash_pct > 1.0:  # More than 1% cash
            print(f"\n⚠️ ISSUE CONFIRMED: {cash_pct:.2f}% cash remaining!")
            print("\nPossible causes based on logs above:")
            print("  1. Check [ORDER SIZING] Scale factor - if < 1.0, ran out of cash")
            print("  2. Check if signal strengths are < expected")
            print("  3. Check if one position was skipped due to insufficient cash")
    else:
        print("\n⚠️ No position data available")
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)
    print("\nPlease share:")
    print("  1. The [ORDER SIZING] log lines above")
    print("  2. The first rebalance allocation percentages")
    print("  3. Any warnings or errors during execution")

except ImportError as e:
    print(f"\n✗ Import error: {e}")
    print("\nMake sure you're running from the project root:")
    print("  cd /workspace")
    print("  python3 diagnose_cash_allocation.py")
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
