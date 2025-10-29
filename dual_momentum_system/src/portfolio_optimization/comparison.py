"""
Portfolio optimization method comparison functionality.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

import pandas as pd
import numpy as np
from loguru import logger

from .base import PortfolioOptimizer, OptimizationResult
from .methods import (
    EqualWeightOptimizer,
    InverseVolatilityOptimizer,
    MinimumVarianceOptimizer,
    MaximumSharpeOptimizer,
    RiskParityOptimizer,
    MaximumDiversificationOptimizer,
    HierarchicalRiskParityOptimizer,
)


@dataclass
class PortfolioMethodComparison:
    """
    Results from comparing multiple portfolio optimization methods.
    
    Attributes:
        results: Dictionary mapping method names to OptimizationResults
        returns_data: Historical returns used for optimization
        comparison_metrics: DataFrame comparing methods on various metrics
        best_sharpe_method: Method with highest Sharpe ratio
        best_diversification_method: Method with highest diversification ratio
        lowest_volatility_method: Method with lowest volatility
        timestamp: When comparison was performed
    """
    results: Dict[str, OptimizationResult]
    returns_data: pd.DataFrame
    comparison_metrics: pd.DataFrame
    best_sharpe_method: str
    best_diversification_method: str
    lowest_volatility_method: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_weights_df(self) -> pd.DataFrame:
        """Get weights from all methods as DataFrame."""
        weights_dict = {}
        for method, result in self.results.items():
            weights_dict[method] = result.weights
        
        return pd.DataFrame(weights_dict).fillna(0)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            'n_methods_compared': len(self.results),
            'n_assets': len(self.returns_data.columns),
            'best_sharpe_method': self.best_sharpe_method,
            'best_sharpe_ratio': self.results[self.best_sharpe_method].sharpe_ratio,
            'best_diversification_method': self.best_diversification_method,
            'best_diversification_ratio': self.results[self.best_diversification_method].diversification_ratio,
            'lowest_volatility_method': self.lowest_volatility_method,
            'lowest_volatility': self.results[self.lowest_volatility_method].expected_volatility,
            'timestamp': self.timestamp.isoformat(),
        }
    
    def save(self, output_dir: Path, prefix: str = 'portfolio_comparison') -> Dict[str, Path]:
        """
        Save comparison results to disk.
        
        Args:
            output_dir: Directory to save results
            prefix: Filename prefix
        
        Returns:
            Dictionary mapping file types to paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = self.timestamp.strftime('%Y%m%d_%H%M%S')
        base_name = f"{prefix}_{timestamp_str}"
        
        saved_files = {}
        
        # Save comparison metrics
        metrics_path = output_dir / f"{base_name}_comparison.csv"
        self.comparison_metrics.to_csv(metrics_path, index=False)
        saved_files['comparison_csv'] = metrics_path
        
        # Save weights from all methods
        weights_path = output_dir / f"{base_name}_weights.csv"
        self.get_weights_df().to_csv(weights_path)
        saved_files['weights_csv'] = weights_path
        
        # Save summary as JSON
        summary_path = output_dir / f"{base_name}_summary.json"
        with open(summary_path, 'w') as f:
            summary = self.get_summary()
            summary['methods'] = list(self.results.keys())
            json.dump(summary, f, indent=2)
        saved_files['summary_json'] = summary_path
        
        # Save individual method results
        for method, result in self.results.items():
            method_path = output_dir / f"{base_name}_{method}.json"
            with open(method_path, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            saved_files[f'{method}_json'] = method_path
        
        logger.info(f"Saved comparison results to {output_dir}")
        
        return saved_files


def compare_portfolio_methods(
    returns: pd.DataFrame,
    methods: Optional[List[str]] = None,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    risk_free_rate: float = 0.0,
    verbose: bool = True,
    **kwargs
) -> PortfolioMethodComparison:
    """
    Compare multiple portfolio optimization methods.
    
    Args:
        returns: DataFrame of asset returns (each column is an asset)
        methods: List of method names to compare. Options:
            - 'equal_weight'
            - 'inverse_volatility'
            - 'minimum_variance'
            - 'maximum_sharpe'
            - 'risk_parity'
            - 'maximum_diversification'
            - 'hierarchical_risk_parity'
            If None, compares all methods.
        min_weight: Minimum weight per asset
        max_weight: Maximum weight per asset
        risk_free_rate: Risk-free rate for Sharpe calculations
        verbose: Print progress messages
        **kwargs: Additional method-specific parameters
    
    Returns:
        PortfolioMethodComparison with results from all methods
    
    Example:
        >>> returns = pd.DataFrame(...)  # Historical returns
        >>> comparison = compare_portfolio_methods(
        ...     returns=returns,
        ...     methods=['equal_weight', 'risk_parity', 'maximum_sharpe'],
        ...     risk_free_rate=0.02
        ... )
        >>> print(comparison.comparison_metrics)
        >>> print(f"Best Sharpe: {comparison.best_sharpe_method}")
    """
    # Method registry
    method_classes = {
        'equal_weight': EqualWeightOptimizer,
        'inverse_volatility': InverseVolatilityOptimizer,
        'minimum_variance': MinimumVarianceOptimizer,
        'maximum_sharpe': MaximumSharpeOptimizer,
        'risk_parity': RiskParityOptimizer,
        'maximum_diversification': MaximumDiversificationOptimizer,
        'hierarchical_risk_parity': HierarchicalRiskParityOptimizer,
    }
    
    # Default to all methods if not specified
    if methods is None:
        methods = list(method_classes.keys())
    
    # Validate methods
    for method in methods:
        if method not in method_classes:
            raise ValueError(
                f"Invalid method '{method}'. Must be one of {list(method_classes.keys())}"
            )
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"PORTFOLIO OPTIMIZATION METHOD COMPARISON")
        print(f"={'='*80}")
        print(f"Assets: {', '.join(returns.columns)}")
        print(f"Data points: {len(returns)}")
        print(f"Methods: {', '.join(methods)}")
        print(f"{'='*80}\n")
    
    results = {}
    
    # Run each method
    for method in methods:
        if verbose:
            print(f"Running {method.replace('_', ' ').title()}...")
        
        try:
            # Create optimizer
            optimizer_class = method_classes[method]
            optimizer = optimizer_class(
                min_weight=min_weight,
                max_weight=max_weight,
                risk_free_rate=risk_free_rate,
            )
            
            # Optimize
            result = optimizer.optimize(returns, **kwargs)
            results[method] = result
            
            if verbose:
                print(f"  ✓ Sharpe: {result.sharpe_ratio:.4f}, "
                      f"Volatility: {result.expected_volatility:.4f}, "
                      f"Diversification: {result.diversification_ratio:.4f}")
        
        except Exception as e:
            logger.error(f"Error running {method}: {e}")
            if verbose:
                print(f"  ✗ Failed: {e}")
    
    if not results:
        raise RuntimeError("All optimization methods failed")
    
    # Create comparison metrics DataFrame
    comparison_data = []
    for method, result in results.items():
        comparison_data.append({
            'method': method.replace('_', ' ').title(),
            'expected_return': result.expected_return if result.expected_return is not None else np.nan,
            'expected_volatility': result.expected_volatility if result.expected_volatility is not None else np.nan,
            'sharpe_ratio': result.sharpe_ratio if result.sharpe_ratio is not None else np.nan,
            'diversification_ratio': result.diversification_ratio if result.diversification_ratio is not None else np.nan,
            'max_weight': max(result.weights.values()) if result.weights else np.nan,
            'min_weight': min(result.weights.values()) if result.weights else np.nan,
            'n_nonzero': sum(1 for w in result.weights.values() if w > 0.001) if result.weights else 0,
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Identify best methods
    best_sharpe_method = max(results.items(), key=lambda x: x[1].sharpe_ratio if x[1].sharpe_ratio is not None else -np.inf)[0]
    best_div_method = max(results.items(), key=lambda x: x[1].diversification_ratio if x[1].diversification_ratio is not None else -np.inf)[0]
    lowest_vol_method = min(results.items(), key=lambda x: x[1].expected_volatility if x[1].expected_volatility is not None else np.inf)[0]
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"COMPARISON COMPLETE")
        print(f"{'='*80}")
        print(f"Best Sharpe Ratio: {best_sharpe_method.replace('_', ' ').title()}")
        print(f"Best Diversification: {best_div_method.replace('_', ' ').title()}")
        print(f"Lowest Volatility: {lowest_vol_method.replace('_', ' ').title()}")
        print(f"\nComparison Metrics:")
        print(comparison_df.to_string(index=False))
        print(f"{'='*80}\n")
    
    return PortfolioMethodComparison(
        results=results,
        returns_data=returns,
        comparison_metrics=comparison_df,
        best_sharpe_method=best_sharpe_method,
        best_diversification_method=best_div_method,
        lowest_volatility_method=lowest_vol_method,
        metadata={
            'min_weight': min_weight,
            'max_weight': max_weight,
            'risk_free_rate': risk_free_rate,
        }
    )


def get_available_methods() -> List[str]:
    """Get list of available portfolio optimization methods."""
    return [
        'equal_weight',
        'inverse_volatility',
        'minimum_variance',
        'maximum_sharpe',
        'risk_parity',
        'maximum_diversification',
        'hierarchical_risk_parity',
    ]


def get_method_description(method: str) -> str:
    """Get description of a portfolio optimization method."""
    descriptions = {
        'equal_weight': 'Equal weight (1/N) - Simple but effective benchmark',
        'inverse_volatility': 'Inverse volatility weighting - Lower vol gets higher weight',
        'minimum_variance': 'Minimum variance - Lowest possible volatility portfolio',
        'maximum_sharpe': 'Maximum Sharpe ratio - Best risk-adjusted returns',
        'risk_parity': 'Risk parity - Equal risk contribution from each asset',
        'maximum_diversification': 'Maximum diversification - Highest diversification ratio',
        'hierarchical_risk_parity': 'HRP - Machine learning clustering approach',
    }
    return descriptions.get(method, 'No description available')
