"""
Optimization Method Comparison Demo

This example demonstrates how to compare multiple optimization methods
(Grid Search, Random Search, Bayesian Optimization) to find which works
best for your parameter tuning problem.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting import (
    BacktestEngine,
    HyperparameterTuner,
    ParameterSpace,
)
from src.strategies.dual_momentum import DualMomentumStrategy
from src.data_sources import get_default_data_source


def run_method_comparison_demo():
    """
    Demonstrate optimization method comparison.
    
    This example:
    1. Sets up a parameter search space
    2. Compares Grid Search, Random Search, and Bayesian Optimization
    3. Shows which method performs best for this problem
    4. Analyzes convergence and efficiency
    """
    
    print("="*80)
    print("OPTIMIZATION METHOD COMPARISON DEMO")
    print("="*80)
    print()
    
    # Configuration
    universe = ['SPY', 'EFA', 'EEM', 'AGG', 'TLT']
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
    
    # Create backtest engine
    print("Creating backtest engine...")
    engine = BacktestEngine(
        initial_capital=initial_capital,
        commission=0.001,  # 0.1%
        slippage=0.0005,   # 0.05%
    )
    print("  ✓ Engine created")
    print()
    
    # Define parameter space
    print("Defining parameter space...")
    param_space = [
        ParameterSpace(
            name='lookback_period',
            param_type='int',
            values=[126, 189, 252]  # 6, 9, 12 months
        ),
        ParameterSpace(
            name='position_count',
            param_type='int',
            values=[1, 2, 3]
        ),
        ParameterSpace(
            name='absolute_threshold',
            param_type='float',
            values=[0.0, 0.01, 0.02]
        ),
    ]
    
    n_combinations = 3 * 3 * 3  # 27 combinations
    print(f"  Parameters: lookback_period, position_count, absolute_threshold")
    print(f"  Total combinations: {n_combinations}")
    print()
    
    # Create tuner
    print("Creating hyperparameter tuner...")
    tuner = HyperparameterTuner(
        strategy_class=DualMomentumStrategy,
        backtest_engine=engine,
        price_data=price_data,
        base_config={
            'safe_asset': safe_asset,
            'rebalance_frequency': 'monthly',
        },
        start_date=start_date,
        end_date=end_date,
    )
    print("  ✓ Tuner created")
    print()
    
    # Compare methods
    print("="*80)
    print("COMPARING OPTIMIZATION METHODS")
    print("="*80)
    print()
    print("This will run three optimization methods:")
    print("  1. Grid Search (exhaustive, 27 combinations)")
    print("  2. Random Search (random sampling, 27 trials)")
    print("  3. Bayesian Optimization (smart search, 27 trials)")
    print()
    print("Starting comparison...")
    print()
    
    try:
        comparison = tuner.compare_optimization_methods(
            param_space=param_space,
            methods=['grid_search', 'random_search', 'bayesian_optimization'],
            n_trials=27,  # Same as grid search for fair comparison
            n_initial_points=10,
            metric='sharpe_ratio',
            higher_is_better=True,
            random_state=42,
            verbose=True,
        )
        
        # Display results
        print("\n" + "="*80)
        print("DETAILED COMPARISON RESULTS")
        print("="*80)
        print()
        
        print(f"🏆 WINNER: {comparison.best_method.replace('_', ' ').title()}")
        print(f"📊 Best Score: {comparison.best_overall_score:.4f}")
        print(f"⚙️  Best Parameters: {comparison.best_overall_params}")
        print()
        
        print("Comparison Metrics:")
        print("-" * 80)
        print(comparison.comparison_metrics.to_string(index=False))
        print()
        
        # Efficiency analysis
        print("\nEfficiency Analysis:")
        print("-" * 80)
        for method, result in comparison.results.items():
            time_per_trial = result.optimization_time / result.n_trials
            improvement_pct = (result.best_score / comparison.best_overall_score - 1) * 100
            
            print(f"\n{method.replace('_', ' ').title()}:")
            print(f"  Best score: {result.best_score:.4f} ({improvement_pct:+.1f}% vs best)")
            print(f"  Total time: {result.optimization_time:.2f}s")
            print(f"  Time per trial: {time_per_trial:.3f}s")
            print(f"  Trials completed: {result.n_trials}")
        
        # Save results
        print("\n" + "="*80)
        print("SAVING RESULTS")
        print("="*80)
        
        output_dir = project_root / 'optimization_results'
        saved_files = tuner.save_comparison_results(
            comparison=comparison,
            output_dir=output_dir,
            prefix='demo_comparison'
        )
        
        print(f"\nResults saved to: {output_dir}")
        for file_type, file_path in saved_files.items():
            print(f"  ✓ {file_type}: {file_path.name}")
        
        # Recommendations
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        print()
        
        best_method = comparison.best_method
        if best_method == 'grid_search':
            print("Grid Search found the best solution.")
            print("  → Recommendation: Use Grid Search when search space is small")
            print("  → It guarantees finding the optimal solution in the search space")
        elif best_method == 'random_search':
            print("Random Search found the best solution!")
            print("  → Recommendation: Random Search is efficient for this problem")
            print("  → Consider using it for larger search spaces")
        else:  # bayesian_optimization
            print("Bayesian Optimization found the best solution!")
            print("  → Recommendation: Use Bayesian Optimization for expensive evaluations")
            print("  → It learns from previous trials and is most sample-efficient")
        
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
    Quick comparison with smaller parameter space.
    
    This is faster and good for testing.
    """
    
    print("="*80)
    print("QUICK OPTIMIZATION METHOD COMPARISON")
    print("="*80)
    print()
    
    # Smaller configuration for faster testing
    universe = ['SPY', 'AGG']
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
    
    # Simple parameter space
    param_space = [
        ParameterSpace(
            name='lookback_period',
            param_type='int',
            values=[126, 252]  # 6 and 12 months
        ),
        ParameterSpace(
            name='position_count',
            param_type='int',
            values=[1, 2]
        ),
    ]
    
    print(f"Parameter space: {len([126, 252]) * len([1, 2])} combinations")
    print()
    
    # Create tuner
    engine = BacktestEngine(initial_capital=100000)
    tuner = HyperparameterTuner(
        strategy_class=DualMomentumStrategy,
        backtest_engine=engine,
        price_data=price_data,
        base_config={'safe_asset': safe_asset},
        start_date=start_date,
        end_date=end_date,
    )
    
    # Compare just two methods for speed
    print("Comparing Grid Search vs Random Search...")
    print()
    
    comparison = tuner.compare_optimization_methods(
        param_space=param_space,
        methods=['grid_search', 'random_search'],
        n_trials=10,
        metric='sharpe_ratio',
        higher_is_better=True,
        random_state=42,
        verbose=True,
    )
    
    print(f"\n🏆 Winner: {comparison.best_method.replace('_', ' ').title()}")
    print(f"📊 Score: {comparison.best_overall_score:.4f}")
    print()
    print("Quick comparison complete!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Optimization Method Comparison Demo'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick comparison with smaller parameter space'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_comparison()
    else:
        run_method_comparison_demo()
