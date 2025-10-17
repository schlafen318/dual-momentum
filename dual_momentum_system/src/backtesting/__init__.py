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
