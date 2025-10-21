"""
Complete end-to-end backtesting example.

This script demonstrates the full workflow:
1. Load plugins
2. Fetch data
3. Configure strategy and risk management
4. Run backtest
5. Analyze results
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
import warnings
warnings.filterwarnings('ignore')

from src.core import get_plugin_manager
from src.config.config_manager import get_config_manager
from src.backtesting.engine import BacktestEngine
from src.backtesting.performance import PerformanceCalculator


def main():
    """Run complete backtesting example."""
    
    print("=" * 80)
    print("DUAL MOMENTUM FRAMEWORK - COMPLETE BACKTESTING EXAMPLE")
    print("=" * 80)
    print()
    
    # =========================================================================
    # STEP 1: Initialize Plugin Manager
    # =========================================================================
    print("[STEP 1] Initializing Plugin Manager...")
    print("-" * 80)
    
    plugin_manager = get_plugin_manager()
    
    print(f"✓ Discovered {len(plugin_manager.list_strategies())} strategies")
    print(f"✓ Discovered {len(plugin_manager.list_data_sources())} data sources")
    print(f"✓ Discovered {len(plugin_manager.list_asset_classes())} asset classes")
    print(f"✓ Discovered {len(plugin_manager.list_risk_managers())} risk managers")
    print()
    
    # =========================================================================
    # STEP 2: Configure Components
    # =========================================================================
    print("[STEP 2] Configuring Components...")
    print("-" * 80)
    
    # Define asset universe
    universe = ['SPY', 'EFA', 'EEM', 'AGG', 'TLT']
    print(f"Asset Universe: {universe}")
    print()
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 3)  # 3 years of data
    print(f"Date Range: {start_date.date()} to {end_date.date()}")
    print()
    
    # =========================================================================
    # STEP 3: Load Data
    # =========================================================================
    print("[STEP 3] Loading Data...")
    print("-" * 80)
    
    # Get multi-source data provider with automatic failover
    from src.data_sources import get_default_data_source
    data_source = get_default_data_source()
    print(f"✓ Using multi-source data provider with {len(data_source.sources)} source(s)")
    
    # Show source status
    source_status = data_source.get_source_status()
    for source_name, is_available in source_status.items():
        status = "✓ Available" if is_available else "✗ Unavailable"
        print(f"  - {source_name}: {status}")
    
    # Get asset class
    EquityAsset = plugin_manager.get_asset_class('EquityAsset')
    if not EquityAsset:
        print("✗ Equity asset class not available")
        return
    
    asset_class = EquityAsset()
    print(f"✓ Using asset class: {asset_class.get_name()}")
    print()
    
    # Fetch data for all assets
    print("Fetching historical data...")
    price_data = {}
    
    for symbol in universe:
        try:
            print(f"  - Fetching {symbol}...", end=" ")
            raw_data = data_source.fetch_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe='1d'
            )
            
            if not raw_data.empty:
                normalized = asset_class.normalize_data(raw_data, symbol)
                price_data[symbol] = normalized
                print(f"✓ ({len(normalized.data)} bars)")
            else:
                print("✗ No data")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    if not price_data:
        print("\n✗ No data loaded. Cannot proceed with backtest.")
        return
    
    print(f"\n✓ Loaded data for {len(price_data)} assets")
    print()
    
    # =========================================================================
    # STEP 4: Configure Strategy
    # =========================================================================
    print("[STEP 4] Configuring Strategy...")
    print("-" * 80)
    
    # Get strategy class
    DualMomentum = plugin_manager.get_strategy('DualMomentumStrategy')
    if not DualMomentum:
        print("✗ Dual Momentum strategy not available")
        return
    
    # Configure strategy
    strategy_config = {
        'lookback_period': 126,  # 6 months
        'rebalance_frequency': 'monthly',
        'position_count': 1,
        'absolute_threshold': 0.0,
        'safe_asset': 'AGG',  # Bonds as safe asset
    }
    
    strategy = DualMomentum(config=strategy_config)
    
    # AUTOMATIC SAFE ASSET FETCHING
    # If the safe asset is not in the universe, it will be automatically fetched
    # This prevents the common issue of safe asset signals being silently skipped
    from src.backtesting.utils import ensure_safe_asset_data
    
    price_data = ensure_safe_asset_data(
        strategy=strategy,
        price_data=price_data,
        data_source=data_source,
        start_date=start_date,
        end_date=end_date,
        asset_class=asset_class
    )
    
    print(f"Strategy: {strategy.get_name()}")
    print(f"  - Momentum Type: {strategy.get_momentum_type().value}")
    print(f"  - Lookback Period: {strategy.get_required_history()} days")
    print(f"  - Rebalance: {strategy.get_rebalance_frequency()}")
    print(f"  - Positions: {strategy.get_position_count()}")
    print(f"  - Safe Asset: {strategy_config['safe_asset']}")
    print()
    
    # =========================================================================
    # STEP 5: Configure Risk Management
    # =========================================================================
    print("[STEP 5] Configuring Risk Management...")
    print("-" * 80)
    
    # Get risk manager class
    BasicRisk = plugin_manager.get_risk_manager('BasicRiskManager')
    if not BasicRisk:
        print("✗ Basic risk manager not available")
        return
    
    # Configure risk management
    risk_config = {
        'max_position_size': 1.0,  # 100% in single position (dual momentum typical)
        'max_leverage': 1.0,
        'equal_weight': True,
    }
    
    risk_manager = BasicRisk(config=risk_config)
    
    print(f"Risk Manager: {risk_manager.get_name()}")
    print(f"  - Max Position Size: {risk_manager.get_max_position_size():.0%}")
    print(f"  - Max Leverage: {risk_manager.get_max_leverage()}x")
    print()
    
    # =========================================================================
    # STEP 6: Run Backtest
    # =========================================================================
    print("[STEP 6] Running Backtest...")
    print("-" * 80)
    
    # Create backtest engine
    engine = BacktestEngine(
        initial_capital=100000,
        commission=0.001,  # 0.1%
        slippage=0.0005,   # 0.05%
    )
    
    print(f"Initial Capital: ${engine.initial_capital:,.2f}")
    print(f"Commission: {engine.commission:.3%}")
    print(f"Slippage: {engine.slippage:.3%}")
    print()
    
    print("Executing backtest...")
    
    try:
        results = engine.run(
            strategy=strategy,
            price_data=price_data,
            risk_manager=risk_manager,
            start_date=start_date,
            end_date=end_date
        )
        
        print("✓ Backtest completed successfully")
        print()
        
    except Exception as e:
        print(f"✗ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # =========================================================================
    # STEP 7: Analyze Results
    # =========================================================================
    print("[STEP 7] Analyzing Results...")
    print("-" * 80)
    print()
    
    # Print performance metrics
    calculator = PerformanceCalculator()
    calculator.print_metrics(results.metrics)
    
    # Print trade summary
    print("\n" + "=" * 80)
    print("TRADE SUMMARY")
    print("=" * 80)
    
    if not results.trades.empty:
        print(f"\nTotal Trades: {len(results.trades)}")
        print(f"Winning Trades: {results.winning_trades}")
        print(f"Losing Trades: {results.num_trades - results.winning_trades}")
        print(f"Win Rate: {results.win_rate:.2%}")
        
        print("\nTop 5 Trades by P&L:")
        top_trades = results.trades.nlargest(5, 'pnl')[['symbol', 'entry_timestamp', 'exit_timestamp', 'pnl', 'pnl_pct']]
        print(top_trades.to_string(index=False))
        
        print("\nWorst 5 Trades by P&L:")
        worst_trades = results.trades.nsmallest(5, 'pnl')[['symbol', 'entry_timestamp', 'exit_timestamp', 'pnl', 'pnl_pct']]
        print(worst_trades.to_string(index=False))
    else:
        print("\nNo trades executed")
    
    # =========================================================================
    # STEP 8: Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("BACKTEST SUMMARY")
    print("=" * 80)
    
    print(f"\nStrategy: {results.strategy_name}")
    print(f"Period: {results.start_date.date()} to {results.end_date.date()}")
    print(f"Initial Capital: ${results.initial_capital:,.2f}")
    print(f"Final Capital: ${results.final_capital:,.2f}")
    print(f"Total Return: {results.total_return:,.2%}")
    print(f"Sharpe Ratio: {results.metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results.metrics['max_drawdown']:.2%}")
    
    # Benchmark comparison (SPY) - use the benchmark data from results
    if 'benchmark_return' in results.metrics:
        benchmark_total = results.metrics['benchmark_return']
        outperformance = results.total_return - benchmark_total
        
        print(f"\nBenchmark: {benchmark_total:.2%}")
        print(f"Outperformance: {outperformance:+.2%}")
        
        # Additional benchmark metrics if available
        if 'alpha' in results.metrics:
            print(f"Alpha: {results.metrics['alpha']:.2%}")
        if 'beta' in results.metrics:
            print(f"Beta: {results.metrics['beta']:.2f}")
        if 'information_ratio' in results.metrics:
            print(f"Information Ratio: {results.metrics['information_ratio']:.2f}")
    else:
        print("\nNo benchmark data available for comparison")
    
    print("\n" + "=" * 80)
    print("✓ Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    main()
