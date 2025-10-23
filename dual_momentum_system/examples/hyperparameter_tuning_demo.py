"""
Hyperparameter Tuning Demo

Demonstrates how to use the hyperparameter tuning framework to optimize
strategy parameters for better performance.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting import (
    BacktestEngine,
    HyperparameterTuner,
    ParameterSpace,
    create_default_param_space,
)
from src.strategies.dual_momentum import DualMomentumStrategy
from src.data_sources.multi_source import MultiSourceDataProvider
from loguru import logger


def main():
    """Run hyperparameter tuning demonstration."""
    
    logger.info("="*80)
    logger.info("HYPERPARAMETER TUNING DEMONSTRATION")
    logger.info("="*80)
    
    # Configuration
    universe = ["SPY", "EFA", "EEM", "AGG", "TLT", "GLD"]
    safe_asset = "AGG"
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)  # 3 years
    data_start = start_date - timedelta(days=400)  # Add buffer for lookback
    
    logger.info(f"Universe: {universe}")
    logger.info(f"Period: {start_date.date()} to {end_date.date()}")
    logger.info("")
    
    # Load data
    logger.info("Loading price data...")
    data_provider = MultiSourceDataProvider()
    
    price_data = {}
    for symbol in universe:
        try:
            data = data_provider.fetch_data(
                symbol,
                start_date=data_start,
                end_date=end_date
            )
            price_data[symbol] = data
            logger.info(f"  ✓ Loaded {symbol}: {len(data.data)} bars")
        except Exception as e:
            logger.error(f"  ✗ Failed to load {symbol}: {e}")
    
    if not price_data:
        logger.error("No data loaded. Exiting.")
        return
    
    logger.info(f"\nLoaded {len(price_data)} assets")
    logger.info("")
    
    # Create backtest engine
    engine = BacktestEngine(
        initial_capital=100000,
        commission=0.001,  # 0.1%
        slippage=0.0005,   # 0.05%
    )
    
    # Base configuration (non-tuned parameters)
    base_config = {
        'safe_asset': safe_asset,
        'rebalance_frequency': 'monthly',
        'universe': universe,
    }
    
    # Create tuner
    tuner = HyperparameterTuner(
        strategy_class=DualMomentumStrategy,
        backtest_engine=engine,
        price_data=price_data,
        base_config=base_config,
        start_date=start_date,
        end_date=end_date,
    )
    
    # =========================================================================
    # Example 1: Grid Search with Custom Parameter Space
    # =========================================================================
    logger.info("="*80)
    logger.info("EXAMPLE 1: GRID SEARCH")
    logger.info("="*80)
    logger.info("")
    
    param_space_grid = [
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
    ]
    
    logger.info("Running grid search...")
    results_grid = tuner.grid_search(
        param_space=param_space_grid,
        metric='sharpe_ratio',
        higher_is_better=True,
        verbose=True,
    )
    
    logger.info("\n" + "="*80)
    logger.info("GRID SEARCH RESULTS")
    logger.info("="*80)
    logger.info(f"Best Sharpe Ratio: {results_grid.best_score:.4f}")
    logger.info(f"Best Parameters: {results_grid.best_params}")
    logger.info(f"Optimization Time: {results_grid.optimization_time:.2f}s")
    logger.info("")
    
    # =========================================================================
    # Example 2: Random Search
    # =========================================================================
    logger.info("="*80)
    logger.info("EXAMPLE 2: RANDOM SEARCH")
    logger.info("="*80)
    logger.info("")
    
    param_space_random = [
        ParameterSpace(
            name='lookback_period',
            param_type='int',
            values=[63, 126, 189, 252, 315]  # 3-15 months
        ),
        ParameterSpace(
            name='position_count',
            param_type='int',
            values=[1, 2, 3, 4]
        ),
        ParameterSpace(
            name='absolute_threshold',
            param_type='float',
            values=[0.0, 0.01, 0.02, 0.05]
        ),
    ]
    
    logger.info("Running random search...")
    results_random = tuner.random_search(
        param_space=param_space_random,
        n_trials=20,
        metric='sharpe_ratio',
        higher_is_better=True,
        random_state=42,
        verbose=True,
    )
    
    logger.info("\n" + "="*80)
    logger.info("RANDOM SEARCH RESULTS")
    logger.info("="*80)
    logger.info(f"Best Sharpe Ratio: {results_random.best_score:.4f}")
    logger.info(f"Best Parameters: {results_random.best_params}")
    logger.info(f"Optimization Time: {results_random.optimization_time:.2f}s")
    logger.info("")
    
    # =========================================================================
    # Example 3: Bayesian Optimization (requires optuna)
    # =========================================================================
    logger.info("="*80)
    logger.info("EXAMPLE 3: BAYESIAN OPTIMIZATION")
    logger.info("="*80)
    logger.info("")
    
    try:
        logger.info("Running Bayesian optimization...")
        results_bayes = tuner.bayesian_optimization(
            param_space=param_space_random,
            n_trials=30,
            n_initial_points=10,
            metric='sharpe_ratio',
            higher_is_better=True,
            random_state=42,
            verbose=True,
        )
        
        logger.info("\n" + "="*80)
        logger.info("BAYESIAN OPTIMIZATION RESULTS")
        logger.info("="*80)
        logger.info(f"Best Sharpe Ratio: {results_bayes.best_score:.4f}")
        logger.info(f"Best Parameters: {results_bayes.best_params}")
        logger.info(f"Optimization Time: {results_bayes.optimization_time:.2f}s")
        logger.info("")
        
    except ImportError:
        logger.warning("Optuna not installed. Skipping Bayesian optimization.")
        logger.warning("Install with: pip install optuna")
        logger.info("")
    
    # =========================================================================
    # Save Results
    # =========================================================================
    logger.info("="*80)
    logger.info("SAVING RESULTS")
    logger.info("="*80)
    
    output_dir = Path("optimization_results")
    output_dir.mkdir(exist_ok=True)
    
    # Save all results
    saved_files = tuner.save_results(results_random, output_dir, prefix="demo")
    
    for file_type, file_path in saved_files.items():
        logger.info(f"  ✓ Saved {file_type}: {file_path}")
    
    logger.info("")
    
    # =========================================================================
    # Display Top Results
    # =========================================================================
    logger.info("="*80)
    logger.info("TOP 5 CONFIGURATIONS (Random Search)")
    logger.info("="*80)
    
    top_results = results_random.all_results.nlargest(5, 'score')
    
    for idx, row in top_results.iterrows():
        logger.info(f"\nRank {row['trial']}")
        logger.info(f"  Score: {row['score']:.4f}")
        
        # Extract parameters
        param_cols = [col for col in row.index if col.startswith('param_')]
        for col in param_cols:
            param_name = col.replace('param_', '')
            logger.info(f"  {param_name}: {row[col]}")
        
        logger.info(f"  Total Return: {row.get('total_return', 0)*100:.2f}%")
        logger.info(f"  Max Drawdown: {row.get('max_drawdown', 0)*100:.2f}%")
    
    logger.info("")
    logger.info("="*80)
    logger.info("DEMONSTRATION COMPLETE")
    logger.info("="*80)


if __name__ == "__main__":
    main()
