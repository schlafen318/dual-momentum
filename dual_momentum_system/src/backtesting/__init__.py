"""
Backtesting module for executing and evaluating trading strategies.

This module provides the backtesting engine, performance metrics,
and risk management components.
"""

from .engine import BacktestEngine
from .performance import PerformanceCalculator
from .basic_risk import BasicRiskManager
from .hyperparameter_tuner import (
    HyperparameterTuner,
    ParameterSpace,
    OptimizationResult,
    create_default_param_space,
)

__all__ = [
    'BacktestEngine',
    'PerformanceCalculator',
    'BasicRiskManager',
    'HyperparameterTuner',
    'ParameterSpace',
    'OptimizationResult',
    'create_default_param_space',
]

# Optional advanced analytics (require scipy and vectorbt)
try:
    from .advanced_analytics import AdvancedAnalytics
    __all__.append('AdvancedAnalytics')
except (ImportError, SystemError):
    pass  # scipy/vectorbt not installed or incompatible, skip advanced analytics

# Optional vectorized components (require vectorbt)
try:
    from .vectorized_engine import VectorizedBacktestEngine, SignalGenerator
    from .vectorized_metrics import VectorizedMetricsCalculator
    __all__.extend([
        'VectorizedBacktestEngine',
        'SignalGenerator',
        'VectorizedMetricsCalculator',
    ])
except (ImportError, SystemError):
    pass  # vectorbt not installed or incompatible, skip vectorized components
