"""
Example: Strategy Comparison Agent

This script demonstrates how to use the StrategyComparisonAgent to automatically
test all strategies and identify outperforming strategies.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.strategy_comparison_agent import (
    StrategyComparisonAgent,
    ComparisonConfig
)
from loguru import logger


def main():
    """Run strategy comparison."""
    
    print("=" * 80)
    print("STRATEGY COMPARISON AGENT EXAMPLE")
    print("=" * 80)
    print()
    
    # Create agent
    agent = StrategyComparisonAgent()
    
    # Configure comparison
    config = ComparisonConfig(
        # Date range
        start_date=datetime(2015, 1, 1),
        end_date=datetime(2024, 1, 1),
        
        # Universe
        universe=['SPY', 'EFA', 'EEM', 'AGG'],
        benchmark_symbol='SPY',
        
        # Engine parameters
        initial_capital=100000.0,
        commission=0.001,
        slippage=0.0005,
        
        # Comparison criteria
        min_excess_return=0.0,  # At least match benchmark
        min_sharpe_ratio=None,  # No minimum Sharpe requirement
        
        # Execution
        max_workers=4,  # Parallel execution
        parallel=True,
        
        # Optional: Filter specific strategies
        # strategy_ids=['dual_momentum_classic'],  # Test only specific strategies
        # exclude_strategy_ids=[],  # Exclude certain strategies
    )
    
    # Run comparison
    print("Running strategy comparison...")
    print("This may take several minutes depending on the number of strategies.")
    print()
    
    results = agent.compare_all_strategies(config)
    
    # Get outperforming strategies
    outperforming = agent.get_outperforming_strategies(results, config)
    
    # Display results
    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Strategies Tested: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r.success)}")
    print(f"Outperforming: {len(outperforming)}")
    print()
    
    if outperforming:
        print("=" * 80)
        print("OUTPERFORMING STRATEGIES")
        print("=" * 80)
        print()
        print(
            f"{'Strategy':<30} {'Return':>12} {'Excess':>12} {'Sharpe':>10} {'Max DD':>10}"
        )
        print("-" * 80)
        
        for result in outperforming:
            print(
                f"{result.strategy_name[:28]:<30} "
                f"{result.total_return:>11.2%} "
                f"{result.excess_return:>11.2%} "
                f"{result.sharpe_ratio:>9.2f} "
                f"{result.max_drawdown:>9.2%}"
            )
        print()
    else:
        print("No outperforming strategies found.")
        print()
    
    # Show top 5 by excess return
    successful = [r for r in results if r.success]
    if successful:
        successful.sort(key=lambda x: x.excess_return or -999, reverse=True)
        top_5 = successful[:5]
        
        print("=" * 80)
        print("TOP 5 STRATEGIES BY EXCESS RETURN")
        print("=" * 80)
        print()
        print(
            f"{'Strategy':<30} {'Return':>12} {'Excess':>12} {'Sharpe':>10} {'Max DD':>10}"
        )
        print("-" * 80)
        
        for result in top_5:
            print(
                f"{result.strategy_name[:28]:<30} "
                f"{result.total_return:>11.2%} "
                f"{result.excess_return or 0:>11.2%} "
                f"{result.sharpe_ratio or 0:>9.2f} "
                f"{result.max_drawdown or 0:>9.2%}"
            )
        print()
    
    # Generate full report
    report = agent.generate_report(results)
    print(report)
    
    # Save report to file
    output_file = Path("strategy_comparison_report.txt")
    agent.generate_report(results, output_file=output_file)
    print(f"\nFull report saved to: {output_file}")


if __name__ == "__main__":
    main()

