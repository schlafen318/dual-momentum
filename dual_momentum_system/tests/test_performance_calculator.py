"""
Unit tests for PerformanceCalculator risk metrics.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.performance import PerformanceCalculator


def test_average_drawdown_matches_vectorized_logic():
    """Average drawdown should reflect mean of negative drawdown periods."""
    calculator = PerformanceCalculator()
    dates = pd.date_range('2020-01-01', periods=5, freq='D')
    equity_curve = pd.Series([100, 110, 90, 95, 120], index=dates)
    expected_avg = (-0.1818181818 - 0.1363636364) / 2
    
    avg_drawdown = calculator.average_drawdown(equity_curve)
    
    assert avg_drawdown == pytest.approx(expected_avg, rel=1e-6)


def test_calculate_metrics_includes_avg_drawdown():
    """calculate_metrics should expose avg_drawdown in output."""
    calculator = PerformanceCalculator()
    dates = pd.date_range('2020-01-01', periods=5, freq='D')
    equity_curve = pd.Series([100, 110, 90, 95, 120], index=dates)
    returns = equity_curve.pct_change().dropna()
    
    metrics = calculator.calculate_metrics(returns, equity_curve)
    
    assert 'avg_drawdown' in metrics
    assert metrics['avg_drawdown'] == pytest.approx(calculator.average_drawdown(equity_curve), rel=1e-6)
