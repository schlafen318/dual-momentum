"""
Comprehensive demo of vectorized backtesting engine with advanced analytics.

This example demonstrates:
1. Setting up multi-asset price data
2. Running vectorized backtests with different strategies
3. Calculating comprehensive performance metrics
4. Advanced analytics: rolling stats, Monte Carlo, regime analysis
5. Comparing multiple strategies
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

from src.backtesting.vectorized_engine import (
    VectorizedBacktestEngine,
    SignalGenerator
)
from src.backtesting.advanced_analytics import AdvancedAnalytics


def generate_sample_data(
    symbols: list,
    start_date: str = '2015-01-01',
    end_date: str = '2023-12-31',
    initial_price: float = 100.0
) -> pd.DataFrame:
    """
    Generate sample price data for demonstration.
    
    Args:
        symbols: List of asset symbols
        start_date: Start date
        end_date: End date
        initial_price: Starting price
    
    Returns:
        DataFrame with close prices for each symbol
    """
    logger.info(f"Generating sample data for {len(symbols)} assets")
    
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # Generate price data with different characteristics
    np.random.seed(42)
    
    prices = {}
    for i, symbol in enumerate(symbols):
        # Different expected returns and volatilities for each asset
        daily_return = 0.0005 + i * 0.0001  # 0.05% to 0.15% daily
        daily_vol = 0.01 + i * 0.002  # 1% to 2% daily volatility
        
        # Generate returns
        returns = np.random.normal(daily_return, daily_vol, len(dates))
        
        # Add some autocorrelation (momentum)
        for j in range(1, len(returns)):
            returns[j] += 0.05 * returns[j-1]
        
        # Calculate prices
        price_series = initial_price * np.exp(np.cumsum(returns))
        prices[symbol] = price_series
    
    price_df = pd.DataFrame(prices, index=dates)
    
    logger.info(f"Generated {len(dates)} days of data from {dates[0]} to {dates[-1]}")
    
    return price_df


def demo_basic_backtest():
    """Demonstrate basic vectorized backtest."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 1: Basic Vectorized Backtest with Momentum Strategy")
    logger.info("="*80)
    
    # Generate sample data
    symbols = ['ASSET_A', 'ASSET_B', 'ASSET_C', 'ASSET_D', 'ASSET_E']
    prices = generate_sample_data(symbols)
    
    # Create engine
    engine = VectorizedBacktestEngine(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005,
        freq='D'
    )
    
    # Generate momentum signals
    signals = SignalGenerator.momentum_signals(
        prices,
        lookback=252,
        top_n=3,
        normalize=True
    )
    
    # Run backtest
    results = engine.run_backtest(
        price_data=prices,
        signals=signals,
        size_type='percent'
    )
    
    # Display results
    logger.info(f"\nBacktest Results:")
    logger.info(f"  Start Date: {results.start_date}")
    logger.info(f"  End Date: {results.end_date}")
    logger.info(f"  Initial Capital: ${results.initial_capital:,.2f}")
    logger.info(f"  Final Capital: ${results.final_capital:,.2f}")
    logger.info(f"  Total Return: {results.total_return:.2%}")
    logger.info(f"\nKey Metrics:")
    logger.info(f"  CAGR: {results.metrics['cagr']:.2%}")
    logger.info(f"  Sharpe Ratio: {results.metrics['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {results.metrics['max_drawdown']:.2%}")
    logger.info(f"  Win Rate: {results.metrics.get('win_rate', 0):.2%}")
    logger.info(f"  Number of Trades: {results.metrics.get('num_trades', 0)}")
    
    return results


def demo_signal_strategy():
    """Demonstrate signal-based strategy with entry/exit signals."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 2: Signal-Based Strategy (SMA Crossover)")
    logger.info("="*80)
    
    # Generate sample data
    symbols = ['TECH', 'HEALTH', 'FINANCE']
    prices = generate_sample_data(symbols, initial_price=50.0)
    
    # Create engine
    engine = VectorizedBacktestEngine(
        initial_capital=50000,
        commission=0.001,
        freq='D'
    )
    
    # Generate SMA crossover signals
    entries, exits = SignalGenerator.sma_crossover_signals(
        prices,
        fast_window=50,
        slow_window=200
    )
    
    # Run backtest
    results = engine.run_signal_strategy(
        price_data=prices,
        entries=entries,
        exits=exits,
        size=0.33,  # Equal weight across 3 assets
        direction='longonly'
    )
    
    # Display results
    logger.info(f"\nSMA Crossover Results:")
    logger.info(f"  Total Return: {results.total_return:.2%}")
    logger.info(f"  CAGR: {results.metrics['cagr']:.2%}")
    logger.info(f"  Sharpe: {results.metrics['sharpe_ratio']:.2f}")
    logger.info(f"  Sortino: {results.metrics['sortino_ratio']:.2f}")
    logger.info(f"  Calmar: {results.metrics['calmar_ratio']:.2f}")
    
    return results


def demo_strategy_comparison():
    """Compare multiple strategies."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 3: Multi-Strategy Comparison")
    logger.info("="*80)
    
    # Generate sample data
    symbols = ['SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'AGG', 'TLT']
    prices = generate_sample_data(symbols, initial_price=100.0)
    
    # Create engine
    engine = VectorizedBacktestEngine(
        initial_capital=100000,
        commission=0.001,
        freq='D'
    )
    
    # Define multiple strategies
    strategies = {
        'Momentum_12M_Top3': SignalGenerator.momentum_signals(
            prices, lookback=252, top_n=3, normalize=True
        ),
        'Momentum_6M_Top5': SignalGenerator.momentum_signals(
            prices, lookback=126, top_n=5, normalize=True
        ),
        'Equal_Weight_Monthly': SignalGenerator.equal_weight_signals(
            prices, rebalance_freq='M'
        ),
        'Equal_Weight_Quarterly': SignalGenerator.equal_weight_signals(
            prices, rebalance_freq='Q'
        ),
    }
    
    # Run comparison
    results = engine.run_multi_strategy_comparison(
        price_data=prices,
        strategies=strategies
    )
    
    # Compare results
    logger.info("\nStrategy Comparison:")
    logger.info(f"{'Strategy':<30} {'Return':>10} {'Sharpe':>10} {'MaxDD':>10} {'Calmar':>10}")
    logger.info("-" * 70)
    
    for name, result in results.items():
        logger.info(
            f"{name:<30} "
            f"{result.total_return:>9.2%} "
            f"{result.metrics['sharpe_ratio']:>10.2f} "
            f"{result.metrics['max_drawdown']:>9.2%} "
            f"{result.metrics['calmar_ratio']:>10.2f}"
        )
    
    return results


def demo_rolling_metrics():
    """Demonstrate rolling metrics analysis."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 4: Rolling Performance Metrics")
    logger.info("="*80)
    
    # Generate sample data and run backtest
    symbols = ['MOMENTUM_1', 'MOMENTUM_2', 'MOMENTUM_3']
    prices = generate_sample_data(symbols)
    
    engine = VectorizedBacktestEngine(initial_capital=100000, commission=0.001)
    signals = SignalGenerator.momentum_signals(prices, lookback=252, top_n=2)
    results = engine.run_backtest(prices, signals)
    
    # Calculate rolling metrics
    analytics = AdvancedAnalytics(freq='D')
    
    rolling_stats = analytics.calculate_rolling_metrics(
        returns=results.returns,
        window=252,  # 1-year rolling window
        metrics=['return', 'volatility', 'sharpe', 'max_drawdown']
    )
    
    # Display summary
    logger.info("\nRolling Metrics Summary (252-day window):")
    logger.info(f"\nRolling Return:")
    logger.info(f"  Mean: {rolling_stats['rolling_return'].mean():.2%}")
    logger.info(f"  Min: {rolling_stats['rolling_return'].min():.2%}")
    logger.info(f"  Max: {rolling_stats['rolling_return'].max():.2%}")
    
    logger.info(f"\nRolling Sharpe:")
    logger.info(f"  Mean: {rolling_stats['rolling_sharpe'].mean():.2f}")
    logger.info(f"  Min: {rolling_stats['rolling_sharpe'].min():.2f}")
    logger.info(f"  Max: {rolling_stats['rolling_sharpe'].max():.2f}")
    
    logger.info(f"\nRolling Max Drawdown:")
    logger.info(f"  Mean: {rolling_stats['rolling_max_drawdown'].mean():.2%}")
    logger.info(f"  Worst: {rolling_stats['rolling_max_drawdown'].min():.2%}")
    
    return rolling_stats


def demo_monte_carlo():
    """Demonstrate Monte Carlo simulation."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 5: Monte Carlo Simulation")
    logger.info("="*80)
    
    # Generate sample data and run backtest
    symbols = ['STOCK_1', 'STOCK_2', 'STOCK_3', 'STOCK_4']
    prices = generate_sample_data(symbols)
    
    engine = VectorizedBacktestEngine(initial_capital=100000, commission=0.001)
    signals = SignalGenerator.momentum_signals(prices, lookback=252, top_n=2)
    results = engine.run_backtest(prices, signals)
    
    # Run Monte Carlo simulation
    analytics = AdvancedAnalytics(freq='D')
    
    mc_results = analytics.monte_carlo_simulation(
        returns=results.returns,
        num_simulations=1000,
        method='bootstrap',
        confidence_levels=[0.05, 0.25, 0.50, 0.75, 0.95]
    )
    
    # Display results
    stats = mc_results['statistics']
    
    logger.info("\nMonte Carlo Simulation Results (1000 paths):")
    logger.info(f"  Expected Final Value: {stats['mean_final_value']:.4f}")
    logger.info(f"  Median Final Value: {stats['median_final_value']:.4f}")
    logger.info(f"  Std Dev: {stats['std_final_value']:.4f}")
    logger.info(f"  Min: {stats['min_final_value']:.4f}")
    logger.info(f"  Max: {stats['max_final_value']:.4f}")
    logger.info(f"  Probability of Profit: {stats['probability_positive']:.2%}")
    logger.info(f"  Expected Return: {stats['expected_return']:.2%}")
    logger.info(f"  Expected CAGR: {stats['expected_cagr']:.2%}")
    logger.info(f"  VaR (95%): {stats['var_95']:.2%}")
    logger.info(f"  CVaR (95%): {stats['cvar_95']:.2%}")
    
    return mc_results


def demo_regime_analysis():
    """Demonstrate regime detection and analysis."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 6: Regime Detection and Analysis")
    logger.info("="*80)
    
    # Generate sample data and run backtest
    symbols = ['GROWTH', 'VALUE', 'MOMENTUM']
    prices = generate_sample_data(symbols)
    
    engine = VectorizedBacktestEngine(initial_capital=100000, commission=0.001)
    signals = SignalGenerator.momentum_signals(prices, lookback=126, top_n=2)
    results = engine.run_backtest(prices, signals)
    
    # Detect regimes
    analytics = AdvancedAnalytics(freq='D')
    
    # Try different regime detection methods
    methods = ['volatility', 'trend', 'percentile']
    
    for method in methods:
        logger.info(f"\n{method.upper()} Regime Detection:")
        
        regimes = analytics.detect_regimes(
            returns=results.returns,
            method=method,
            n_regimes=2
        )
        
        regime_analysis = analytics.analyze_regimes(
            returns=results.returns,
            regimes=regimes
        )
        
        logger.info(f"\n{regime_analysis.to_string()}")
    
    return regime_analysis


def demo_drawdown_analysis():
    """Demonstrate detailed drawdown analysis."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 7: Detailed Drawdown Analysis")
    logger.info("="*80)
    
    # Generate sample data and run backtest
    symbols = ['RISKY_1', 'RISKY_2', 'SAFE']
    prices = generate_sample_data(symbols)
    
    engine = VectorizedBacktestEngine(initial_capital=100000, commission=0.001)
    signals = SignalGenerator.momentum_signals(prices, lookback=252, top_n=2)
    results = engine.run_backtest(prices, signals)
    
    # Analyze drawdowns
    analytics = AdvancedAnalytics(freq='D')
    
    dd_analysis = analytics.calculate_drawdown_analysis(
        equity_curve=results.equity_curve,
        top_n=5
    )
    
    logger.info("\nTop 5 Drawdowns:")
    if len(dd_analysis) > 0:
        for idx, row in dd_analysis.iterrows():
            logger.info(f"\nDrawdown #{idx + 1}:")
            logger.info(f"  Depth: {row['depth']:.2%}")
            logger.info(f"  Start: {row['start_date']}")
            logger.info(f"  Trough: {row['trough_date']}")
            logger.info(f"  Recovery: {row['recovery_date']}")
            logger.info(f"  Duration to Trough: {row['length_days']} days")
            if row['recovery_days']:
                logger.info(f"  Recovery Time: {row['recovery_days']} days")
                logger.info(f"  Total Duration: {row['total_days']} days")
            else:
                logger.info(f"  Status: Still in drawdown")
    
    return dd_analysis


def demo_stress_testing():
    """Demonstrate stress testing."""
    logger.info("\n" + "="*80)
    logger.info("DEMO 8: Stress Testing")
    logger.info("="*80)
    
    # Generate sample data and run backtest
    symbols = ['TECH_STOCK', 'BOND', 'GOLD']
    prices = generate_sample_data(symbols)
    
    engine = VectorizedBacktestEngine(initial_capital=100000, commission=0.001)
    signals = SignalGenerator.momentum_signals(prices, lookback=252, top_n=2)
    results = engine.run_backtest(prices, signals)
    
    # Perform stress tests
    analytics = AdvancedAnalytics(freq='D')
    
    stress_results = analytics.calculate_stress_tests(
        returns=results.returns
    )
    
    logger.info("\nStress Test Results:")
    logger.info(f"\n{stress_results.to_string()}")
    
    return stress_results


def main():
    """Run all demos."""
    logger.info("="*80)
    logger.info("VECTORIZED BACKTESTING ENGINE - COMPREHENSIVE DEMO")
    logger.info("="*80)
    
    try:
        # Run all demos
        demo_basic_backtest()
        demo_signal_strategy()
        demo_strategy_comparison()
        demo_rolling_metrics()
        demo_monte_carlo()
        demo_regime_analysis()
        demo_drawdown_analysis()
        demo_stress_testing()
        
        logger.info("\n" + "="*80)
        logger.info("ALL DEMOS COMPLETED SUCCESSFULLY!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error during demo: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
