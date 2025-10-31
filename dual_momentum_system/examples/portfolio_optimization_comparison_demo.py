"""
Portfolio Optimization Methods Comparison Demo

This example demonstrates how to compare multiple portfolio optimization methods
beyond traditional mean-variance optimization.

Methods compared:
1. Equal Weight - Simple 1/N allocation
2. Inverse Volatility - Weight by inverse volatility
3. Minimum Variance - Lowest volatility portfolio
4. Maximum Sharpe - Best risk-adjusted returns
5. Risk Parity - Equal risk contribution
6. Maximum Diversification - Highest diversification ratio
7. Hierarchical Risk Parity (HRP) - Machine learning approach
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

from src.portfolio_optimization import compare_portfolio_methods, get_available_methods
from src.data_sources import get_default_data_source


def run_full_comparison_demo():
    """
    Comprehensive comparison of all portfolio optimization methods.
    """
    
    print("="*80)
    print("PORTFOLIO OPTIMIZATION METHODS COMPARISON DEMO")
    print("="*80)
    print()
    
    # Configuration
    symbols = ['SPY', 'EFA', 'EEM', 'AGG', 'TLT', 'GLD']
    start_date = datetime(2018, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    print("Configuration:")
    print(f"  Assets: {', '.join(symbols)}")
    print(f"  Date Range: {start_date.date()} to {end_date.date()}")
    print()
    
    # Load price data
    print("Loading price data...")
    data_provider = get_default_data_source()
    
    price_data = {}
    for symbol in symbols:
        try:
            data = data_provider.fetch_data(
                symbol,
                start_date=start_date,
                end_date=end_date
            )
            price_data[symbol] = data.data
            print(f"  ✓ Loaded {symbol}")
        except Exception as e:
            print(f"  ✗ Failed to load {symbol}: {e}")
    
    if not price_data:
        print("\nError: No price data loaded!")
        return
    
    print(f"\nLoaded data for {len(price_data)} assets")
    print()
    
    # Create returns DataFrame
    print("Calculating returns...")
    returns_df = pd.DataFrame({
        symbol: data['close'].pct_change()
        for symbol, data in price_data.items()
    }).dropna()
    
    print(f"  Returns data: {len(returns_df)} periods")
    print(f"  Mean returns (annualized):")
    for symbol in returns_df.columns:
        ann_return = returns_df[symbol].mean() * 252
        print(f"    {symbol}: {ann_return*100:.2f}%")
    print()
    
    # Compare all methods
    print("="*80)
    print("COMPARING ALL PORTFOLIO OPTIMIZATION METHODS")
    print("="*80)
    print()
    
    try:
        comparison = compare_portfolio_methods(
            returns=returns_df,
            methods=None,  # Compare all methods
            min_weight=0.0,  # No shorting
            max_weight=0.5,  # Max 50% in any single asset
            risk_free_rate=0.02,  # 2% risk-free rate
            verbose=True,
        )
        
        # Display detailed results
        print("\n" + "="*80)
        print("DETAILED RESULTS")
        print("="*80)
        print()
        
        print("Comparison Metrics:")
        print("-" * 80)
        print(comparison.comparison_metrics.to_string(index=False))
        print()
        
        # Show weights from each method
        print("\nPortfolio Weights by Method:")
        print("-" * 80)
        weights_df = comparison.get_weights_df()
        print(weights_df.to_string())
        print()
        
        # Best methods
        print("\n" + "="*80)
        print("BEST METHODS")
        print("="*80)
        print()
        
        print(f"🏆 Best Sharpe Ratio: {comparison.best_sharpe_method.replace('_', ' ').title()}")
        best_sharpe = comparison.results[comparison.best_sharpe_method]
        print(f"   Sharpe: {best_sharpe.sharpe_ratio:.4f}")
        print(f"   Return: {best_sharpe.expected_return*252*100:.2f}% (annualized)")
        print(f"   Volatility: {best_sharpe.expected_volatility*np.sqrt(252)*100:.2f}% (annualized)")
        print()
        
        print(f"🎯 Best Diversification: {comparison.best_diversification_method.replace('_', ' ').title()}")
        best_div = comparison.results[comparison.best_diversification_method]
        print(f"   Diversification Ratio: {best_div.diversification_ratio:.4f}")
        print()
        
        print(f"📉 Lowest Volatility: {comparison.lowest_volatility_method.replace('_', ' ').title()}")
        low_vol = comparison.results[comparison.lowest_volatility_method]
        print(f"   Volatility: {low_vol.expected_volatility*np.sqrt(252)*100:.2f}% (annualized)")
        print()
        
        # Risk contribution analysis
        print("\n" + "="*80)
        print("RISK CONTRIBUTION ANALYSIS")
        print("="*80)
        print()
        
        print("Risk Parity Method - Risk Contributions:")
        rp_result = comparison.results['risk_parity']
        risk_contrib_df = pd.DataFrame({
            'Asset': list(rp_result.risk_contributions.keys()),
            'Weight': [rp_result.weights[k] for k in rp_result.risk_contributions.keys()],
            'Risk Contribution': list(rp_result.risk_contributions.values())
        })
        print(risk_contrib_df.to_string(index=False))
        print()
        
        # Save results
        print("="*80)
        print("SAVING RESULTS")
        print("="*80)
        print()
        
        output_dir = project_root / 'portfolio_optimization_results'
        saved_files = comparison.save(
            output_dir=output_dir,
            prefix='full_comparison_demo'
        )
        
        print(f"Results saved to: {output_dir}")
        for file_type, file_path in saved_files.items():
            print(f"  ✓ {file_type}: {file_path.name}")
        print()
        
        # Recommendations
        print("="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        print()
        
        print("Based on the comparison:")
        print()
        
        if comparison.best_sharpe_method == 'maximum_sharpe':
            print("✓ Maximum Sharpe is optimal - Use when maximizing risk-adjusted returns")
        elif comparison.best_sharpe_method == 'risk_parity':
            print("✓ Risk Parity performs best - Good for balanced risk exposure")
        elif comparison.best_sharpe_method == 'hierarchical_risk_parity':
            print("✓ HRP performs best - ML approach works well for this asset mix")
        
        print()
        print("Consider:")
        print("  • Equal Weight as simple, robust baseline")
        print("  • Minimum Variance if return expectations are uncertain")
        print("  • Risk Parity for stable, balanced portfolios")
        print("  • HRP when assets have complex correlation structures")
        
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
    Quick comparison with fewer methods and assets.
    """
    
    print("="*80)
    print("QUICK PORTFOLIO OPTIMIZATION COMPARISON")
    print("="*80)
    print()
    
    # Smaller configuration
    symbols = ['SPY', 'AGG', 'GLD']
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    print(f"Assets: {', '.join(symbols)}")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print()
    
    # Load data
    print("Loading data...")
    data_provider = get_default_data_source()
    
    price_data = {}
    for symbol in symbols:
        try:
            data = data_provider.fetch_data(symbol, start_date=start_date, end_date=end_date)
            price_data[symbol] = data.data
        except Exception as e:
            print(f"Failed to load {symbol}: {e}")
    
    if not price_data:
        print("Error: No data loaded!")
        return
    
    # Calculate returns
    returns_df = pd.DataFrame({
        symbol: data['close'].pct_change()
        for symbol, data in price_data.items()
    }).dropna()
    
    print(f"Loaded {len(returns_df)} periods of data")
    print()
    
    # Compare selected methods
    print("Comparing: Equal Weight, Risk Parity, Maximum Sharpe")
    print()
    
    comparison = compare_portfolio_methods(
        returns=returns_df,
        methods=['equal_weight', 'risk_parity', 'maximum_sharpe'],
        risk_free_rate=0.02,
        verbose=True,
    )
    
    print("\nWeights:")
    print(comparison.get_weights_df().to_string())
    print()
    print(f"Best Sharpe: {comparison.best_sharpe_method.replace('_', ' ').title()}")
    print()
    print("Quick comparison complete!")


def demonstrate_individual_methods():
    """
    Demonstrate using individual portfolio optimization methods.
    """
    
    print("="*80)
    print("INDIVIDUAL METHOD DEMONSTRATION")
    print("="*80)
    print()
    
    # Load data
    symbols = ['SPY', 'AGG', 'GLD']
    data_provider = get_default_data_source()
    
    price_data = {}
    for symbol in symbols:
        try:
            data = data_provider.fetch_data(
                symbol, 
                start_date=datetime(2020, 1, 1), 
                end_date=datetime(2023, 12, 31)
            )
            price_data[symbol] = data.data
        except Exception as e:
            print(f"Failed to load {symbol}: {e}")
            return
    
    # Calculate returns
    returns_df = pd.DataFrame({
        symbol: data['close'].pct_change()
        for symbol, data in price_data.items()
    }).dropna()
    
    print(f"Assets: {', '.join(symbols)}")
    print(f"Data points: {len(returns_df)}")
    print()
    
    # Try each method individually
    from src.portfolio_optimization import (
        EqualWeightOptimizer,
        RiskParityOptimizer,
        MaximumSharpeOptimizer,
    )
    
    methods = [
        ('Equal Weight', EqualWeightOptimizer()),
        ('Risk Parity', RiskParityOptimizer(risk_free_rate=0.02)),
        ('Maximum Sharpe', MaximumSharpeOptimizer(risk_free_rate=0.02)),
    ]
    
    for name, optimizer in methods:
        print(f"\n{name}:")
        print("-" * 40)
        result = optimizer.optimize(returns_df)
        
        print(f"Weights: {result.weights}")
        print(f"Expected Return: {result.expected_return*252*100:.2f}% (annualized)")
        print(f"Expected Volatility: {result.expected_volatility*np.sqrt(252)*100:.2f}% (annualized)")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.4f}")
    
    print()
    print("Individual method demonstration complete!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Portfolio Optimization Comparison Demo'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick comparison with fewer methods'
    )
    parser.add_argument(
        '--individual',
        action='store_true',
        help='Demonstrate individual methods'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_comparison()
    elif args.individual:
        demonstrate_individual_methods()
    else:
        run_full_comparison_demo()
