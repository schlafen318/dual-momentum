"""
Backtesting module for executing and evaluating trading strategies.

This module provides the backtesting engine, performance metrics,
and risk management components.
"""

from .engine import BacktestEngine
from .performance import PerformanceCalculator
from .basic_risk import BasicRiskManager
from .vectorized_engine import VectorizedBacktestEngine, SignalGenerator
from .vectorized_metrics import VectorizedMetricsCalculator
from .advanced_analytics import AdvancedAnalytics

__all__ = [
    'BacktestEngine',
    'PerformanceCalculator',
    'BasicRiskManager',
    'VectorizedBacktestEngine',
    'SignalGenerator',
    'VectorizedMetricsCalculator',
    'AdvancedAnalytics',
]
