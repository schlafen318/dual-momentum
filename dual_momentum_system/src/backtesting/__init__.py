"""
Backtesting module for executing and evaluating trading strategies.

This module provides the backtesting engine, performance metrics,
and risk management components.
"""

from .engine import BacktestEngine
from .performance import PerformanceCalculator
from .basic_risk import BasicRiskManager

__all__ = [
    'BacktestEngine',
    'PerformanceCalculator',
    'BasicRiskManager',
]

# Optional advanced analytics (require scipy)
try:
    from .advanced_analytics import AdvancedAnalytics
    __all__.append('AdvancedAnalytics')
except ImportError:
    pass  # scipy not installed, skip advanced analytics

# Optional vectorized components (require vectorbt)
try:
    from .vectorized_engine import VectorizedBacktestEngine, SignalGenerator
    from .vectorized_metrics import VectorizedMetricsCalculator
    __all__.extend([
        'VectorizedBacktestEngine',
        'SignalGenerator',
        'VectorizedMetricsCalculator',
    ])
except ImportError:
    pass  # vectorbt not installed, skip vectorized components
