"""
Optimization Method Comparison in Backtesting Demo

This example demonstrates how to compare different portfolio optimization methods
directly within backtesting. Instead of using a single position sizing approach,
it runs multiple backtests with different optimization methods and compares results.

This helps answer the question: "Which optimization method works best for my strategy?"
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting import compare_optimization_methods_in_backtest
from src.strategies.dual_momentum import DualMomentumStrategy
from src.data_sources import get_default_data_source


def run_optimization_comparison_demo():
    """
    Demonstrate optimization method comparison in backtesting.
    
    This example:
    1. Sets up a dual momentum strategy
    2. Runs backtests with different optimization methods
    3. Compares which method produces best results
    """
    
    print("="*80)
    print("OPTIMIZATION METHOD COMPARISON IN BACKTESTING")
    print("="*80)
    print()
    
    # Configuration
    universe = ['SPY', 'EFA', 'EEM', 'AGG', 'TLT', 'GLD']
    safe_asset = 'AGG'
    start_date = datetime(2018, 1, 1)
    end_date = datetime(2023, 12, 31)
    initial_capital = 100000
    
    print("Configuration:")
    print(f"  Universe: {', '.join(universe)}")
    print(f"  Safe Asset: {safe_asset}")
    print(f"  Date Range: {start_date.date()} to {end_date.date()}")
    print(f"  Initial Capital: ${initial_capital:,}")
    print()
    
    # Load price data
    print("Loading price data...")
    data_provider = get_default_data_source()
    
    # Add buffer for lookback calculations
    data_start = start_date - timedelta(days=400)
    
    price_data = {}
    for symbol in universe:
        try:
            data = data_provider.fetch_data(
                symbol,
                start_date=data_start,
                end_date=end_date
            )
            price_data[symbol] = data
            print(f"  ✓ Loaded {symbol}")
        except Exception as e:
            print(f"  ✗ Failed to load {symbol}: {e}")
    
    if not price_data:
        print("\nError: No price data loaded!")
        return
    
    print(f"\nLoaded data for {len(price_data)} assets")
    print()
    
    # Create strategy
    print("Creating dual momentum strategy...")
    strategy_config = {
        'lookback_period': 252,
        'rebalance_frequency': 'monthly',
        'position_count': 3,
        'absolute_threshold': 0.0,
        'safe_asset': safe_asset,
    }
    strategy = DualMomentumStrategy(strategy_config)
    print("  ✓ Strategy created")
    print()
    
    # Methods to compare
    optimization_methods = [
        'momentum_based',          # Baseline: default momentum weighting
        'equal_weight',            # Simple 1/N allocation
        'inverse_volatility',      # Lower vol = higher weight
        'risk_parity',             # Equal risk contribution
        'maximum_sharpe',          # Best risk-adjusted returns
    ]
    
    print("="*80)
    print("RUNNING COMPARISON")
    print("="*80)
    print()
    print(f"Comparing {len(optimization_methods)} optimization methods:")
    for method in optimization_methods:
        print(f"  - {method.replace('_', ' ').title()}")
    print()
    print("This will take a few minutes...")
    print()
    
    try:
        # Run comparison
        comparison = compare_optimization_methods_in_backtest(
            strategy=strategy,
            price_data=price_data,
            optimization_methods=optimization_methods,
            initial_capital=initial_capital,
            commission=0.001,  # 0.1%
            slippage=0.0005,   # 0.05%
            risk_free_rate=0.02,  # 2% annual
            start_date=start_date,
            end_date=end_date,
            optimization_lookback=60,  # Use 60 days of history for optimization
            verbose=True,
        )
        
        # Display detailed results
        print("\n" + "="*80)
        print("DETAILED RESULTS")
        print("="*80)
        print()
        
        print(f"🏆 Best Sharpe Ratio: {comparison.best_sharpe_method.replace('_', ' ').title()}")
        best_sharpe_result = comparison.method_results[comparison.best_sharpe_method]
        print(f"   Sharpe: {best_sharpe_result.metrics.get('sharpe_ratio', 0):.3f}")
        print(f"   Total Return: {best_sharpe_result.total_return*100:.2f}%")
        print(f"   Max Drawdown: {best_sharpe_result.metrics.get('max_drawdown', 0)*100:.2f}%")
        print()
        
        print(f"💰 Best Total Return: {comparison.best_return_method.replace('_', ' ').title()}")
        best_return_result = comparison.method_results[comparison.best_return_method]
        print(f"   Total Return: {best_return_result.total_return*100:.2f}%")
        print(f"   Annualized Return: {best_return_result.metrics.get('annualized_return', 0)*100:.2f}%")
        print(f"   Sharpe Ratio: {best_return_result.metrics.get('sharpe_ratio', 0):.3f}")
        print()
        
        print(f"⚖️  Best Risk-Adjusted: {comparison.best_risk_adjusted_method.replace('_', ' ').title()}")
        print()
        
        print("Comparison Table:")
        print("-" * 80)
        print(comparison.comparison_metrics.to_string(index=False))
        print()
        
        # Insights
        print("\n" + "="*80)
        print("INSIGHTS")
        print("="*80)
        print()
        
        # Calculate performance spread
        returns = [result.total_return for result in comparison.method_results.values()]
        sharpes = [result.metrics.get('sharpe_ratio', 0) for result in comparison.method_results.values()]
        
        return_spread = (max(returns) - min(returns)) * 100
        sharpe_spread = max(sharpes) - min(sharpes)
        
        print(f"Performance Spread:")
        print(f"  Return Range: {return_spread:.2f}%")
        print(f"  Sharpe Range: {sharpe_spread:.3f}")
        print()
        
        if return_spread > 10:
            print("✅ Significant performance difference found!")
            print("   Optimization method choice matters for this strategy.")
        else:
            print("ℹ️  Modest performance difference between methods.")
            print("   The momentum filter is likely the dominant factor.")
        print()
        
        # Save results
        print("="*80)
        print("SAVING RESULTS")
        print("="*80)
        
        output_dir = project_root / 'optimization_results'
        saved_files = comparison.save(output_dir, prefix='demo_optimization_comparison')
        
        print(f"\nResults saved to: {output_dir}")
        for file_type, file_path in saved_files.items():
            print(f"  ✓ {file_type}: {file_path.name}")
        print()
        
        # Recommendations
        print("="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        print()
        
        best_method = comparison.best_sharpe_method
        if best_method == 'momentum_based':
            print("The baseline momentum-based approach performed best.")
            print("  → Recommendation: Stick with the default strategy weighting")
        elif best_method == 'equal_weight':
            print("Equal weight allocation performed best!")
            print("  → Recommendation: Simplify by using 1/N allocation")
            print("  → This is easier to implement and often robust")
        elif best_method in ['risk_parity', 'inverse_volatility']:
            print("Risk-based methods performed best!")
            print("  → Recommendation: Use volatility/risk-based position sizing")
            print("  → This helps manage portfolio risk more effectively")
        elif best_method == 'maximum_sharpe':
            print("Maximum Sharpe optimization performed best!")
            print("  → Recommendation: Use mean-variance optimization")
            print("  → But be aware of estimation errors with limited data")
        
        print()
        print("="*80)
        print("DEMO COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error during comparison: {e}")
        import traceback
        traceback.print_exc()


def run_quick_comparison():
    """
    Quick comparison with fewer methods and shorter period.
    
    This is faster and good for testing.
    """
    
    print("="*80)
    print("QUICK OPTIMIZATION METHOD COMPARISON")
    print("="*80)
    print()
    
    # Smaller configuration for faster testing
    universe = ['SPY', 'AGG', 'GLD']
    safe_asset = 'AGG'
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    print("Loading price data...")
    data_provider = get_default_data_source()
    data_start = start_date - timedelta(days=400)
    
    price_data = {}
    for symbol in universe:
        try:
            price_data[symbol] = data_provider.fetch_data(
                symbol, start_date=data_start, end_date=end_date
            )
        except Exception as e:
            print(f"Failed to load {symbol}: {e}")
    
    if not price_data:
        print("Error: No price data loaded!")
        return
    
    # Create strategy
    strategy = DualMomentumStrategy({
        'lookback_period': 126,
        'position_count': 2,
        'safe_asset': safe_asset,
    })
    
    print(f"Comparing 3 methods on {len(universe)} assets...")
    print()
    
    comparison = compare_optimization_methods_in_backtest(
        strategy=strategy,
        price_data=price_data,
        optimization_methods=['momentum_based', 'equal_weight', 'risk_parity'],
        initial_capital=100000,
        start_date=start_date,
        end_date=end_date,
        optimization_lookback=30,
        verbose=True,
    )
    
    print(f"\n🏆 Winner: {comparison.best_sharpe_method.replace('_', ' ').title()}")
    print(f"📊 Best Sharpe: {comparison.method_results[comparison.best_sharpe_method].metrics.get('sharpe_ratio', 0):.3f}")
    print()
    print("Quick comparison complete!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Optimization Method Comparison in Backtesting Demo'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick comparison with fewer methods and shorter period'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_comparison()
    else:
        run_optimization_comparison_demo()
