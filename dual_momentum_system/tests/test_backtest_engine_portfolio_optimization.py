"""Tests for portfolio optimization integration in BacktestEngine."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.backtesting.engine import BacktestEngine
from src.core.types import Signal, SignalReason


def _make_price_history(start_price: float, dates: pd.DatetimeIndex) -> pd.DataFrame:
    close_values = start_price + np.linspace(0, 5, len(dates))
    return pd.DataFrame(
        {
            'open': close_values,
            'high': close_values,
            'low': close_values,
            'close': close_values,
            'volume': np.ones(len(dates)),
        },
        index=dates,
    )


class _DummyStrategy:
    def __init__(self, portfolio_opt_config: dict):
        self.config = {
            'position_count': 2,
            'portfolio_optimization': portfolio_opt_config,
        }

    def get_required_history(self) -> int:
        return 30


@pytest.fixture()
def aligned_data():
    dates = pd.date_range('2020-01-01', periods=60, freq='D')
    return {
        'AAA': _make_price_history(100.0, dates),
        'BBB': _make_price_history(120.0, dates),
    }, dates


def _build_signals(current_date: datetime):
    return [
        Signal(
            timestamp=current_date,
            symbol='AAA',
            direction=1,
            strength=1.0,
            reason=SignalReason.RELATIVE_TOP,
        ),
        Signal(
            timestamp=current_date,
            symbol='BBB',
            direction=1,
            strength=0.9,
            reason=SignalReason.RELATIVE_TOP,
        ),
    ]


def test_compute_optimized_weights_equal_weight(aligned_data):
    data_dict, dates = aligned_data
    current_date = dates[-1]
    strategy = _DummyStrategy(
        {
            'enabled': True,
            'method': 'equal_weight',
            'lookback': 30,
            'min_history': 10,
        }
    )

    engine = BacktestEngine()
    signals = _build_signals(current_date)

    result = engine._compute_optimized_risk_weights(
        strategy,
        strategy.config['portfolio_optimization'],
        signals,
        data_dict,
        current_date,
    )

    assert result is not None
    weights, method, history = result
    assert method == 'equal_weight'
    assert history >= 10
    assert pytest.approx(sum(weights.values()), rel=1e-6) == 1.0
    assert pytest.approx(weights['AAA'], rel=1e-6) == pytest.approx(weights['BBB'], rel=1e-6)


def test_compute_optimized_weights_invalid_method_returns_none(aligned_data):
    data_dict, dates = aligned_data
    current_date = dates[-1]
    strategy = _DummyStrategy(
        {
            'enabled': True,
            'method': 'not_supported',
        }
    )

    engine = BacktestEngine()
    signals = _build_signals(current_date)

    result = engine._compute_optimized_risk_weights(
        strategy,
        strategy.config['portfolio_optimization'],
        signals,
        data_dict,
        current_date,
    )

    assert result is None


def test_compute_optimized_weights_insufficient_history_returns_none(aligned_data):
    data_dict, dates = aligned_data
    current_date = dates[-1]
    strategy = _DummyStrategy(
        {
            'enabled': True,
            'method': 'equal_weight',
            'lookback': 40,
            'min_history': 80,
        }
    )

    engine = BacktestEngine()
    signals = _build_signals(current_date)

    result = engine._compute_optimized_risk_weights(
        strategy,
        strategy.config['portfolio_optimization'],
        signals,
        data_dict,
        current_date,
    )

    assert result is None
