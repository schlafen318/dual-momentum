"""
Portfolio optimization module.

Provides various portfolio construction methods beyond mean-variance optimization.
"""

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
from .comparison import (
    PortfolioMethodComparison,
    compare_portfolio_methods,
    get_available_methods,
    get_method_description,
)

__all__ = [
    'PortfolioOptimizer',
    'OptimizationResult',
    'EqualWeightOptimizer',
    'InverseVolatilityOptimizer',
    'MinimumVarianceOptimizer',
    'MaximumSharpeOptimizer',
    'RiskParityOptimizer',
    'MaximumDiversificationOptimizer',
    'HierarchicalRiskParityOptimizer',
    'PortfolioMethodComparison',
    'compare_portfolio_methods',
    'get_available_methods',
    'get_method_description',
]
