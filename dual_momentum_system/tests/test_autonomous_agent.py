"""Tests for the autonomous backtesting agent."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.agents import AgentConfig, AutonomousBacktestAgent
from src.core.types import AssetMetadata, AssetType, PriceData


def _make_price_data(
    symbol: str,
    *,
    periods: int = 400,
    start: str = "2020-01-01",
    drift: float = 0.0005,
    volatility: float = 0.01,
    seed: int = 7,
) -> PriceData:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start, periods=periods, freq="B")
    returns = rng.normal(loc=drift, scale=volatility, size=periods)
    close = 100 * np.cumprod(1 + returns)
    open_ = close / (1 + returns * 0.5)
    high = np.maximum(open_, close) * (1 + np.abs(returns) * 0.1)
    low = np.minimum(open_, close) * (1 - np.abs(returns) * 0.1)
    volume = np.full(periods, 1_000_000)
    df = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=dates,
    )
    metadata = AssetMetadata(symbol=symbol, name=symbol, asset_type=AssetType.EQUITY)
    return PriceData(symbol=symbol, data=df, metadata=metadata)


def test_autonomous_agent_basic_run(tmp_path: Path) -> None:
    price_data = {
        "SPY": _make_price_data("SPY", seed=1),
        "EFA": _make_price_data("EFA", seed=2),
        "AGG": _make_price_data("AGG", seed=3, volatility=0.005),
    }

    config = AgentConfig(
        symbols=["SPY", "EFA"],
        safe_asset="AGG",
        start_date=pd.Timestamp("2021-01-01"),
        end_date=pd.Timestamp("2022-12-31"),
        optimisation_methods=["grid_search"],
        custom_parameter_space=[
            {"name": "lookback_period", "param_type": "int", "values": [63, 126]},
            {"name": "position_count", "param_type": "int", "values": [1]},
            {"name": "absolute_threshold", "param_type": "float", "values": [0.0, 0.01]},
            {"name": "use_volatility_adjustment", "param_type": "categorical", "values": [False]},
            {"name": "rebalance_frequency", "param_type": "categorical", "values": ["monthly"]},
        ],
        write_outputs=False,
    )

    agent = AutonomousBacktestAgent(config)
    result = agent.run(price_data=price_data)

    assert result.best_method == "grid_search"
    assert "lookback_period" in result.best_params
    assert result.backtest_result.metrics["total_return"] != 0
    assert result.risk_assessment.passed is True
    assert result.report.root_dir is None


def test_autonomous_agent_risk_constraint_failure(tmp_path: Path) -> None:
    price_data = {
        "SPY": _make_price_data("SPY", seed=5, volatility=0.02),
        "AGG": _make_price_data("AGG", seed=6, volatility=0.005),
    }

    config = AgentConfig(
        symbols=["SPY"],
        safe_asset="AGG",
        start_date=pd.Timestamp("2021-01-01"),
        end_date=pd.Timestamp("2022-12-31"),
        optimisation_methods=["grid_search"],
        custom_parameter_space=[
            {"name": "lookback_period", "param_type": "int", "values": [63]},
            {"name": "position_count", "param_type": "int", "values": [1]},
            {"name": "absolute_threshold", "param_type": "float", "values": [0.0]},
            {"name": "use_volatility_adjustment", "param_type": "categorical", "values": [False]},
            {"name": "rebalance_frequency", "param_type": "categorical", "values": ["monthly"]},
        ],
        risk_constraints={"max_drawdown": 0.01},
        write_outputs=False,
    )

    agent = AutonomousBacktestAgent(config)
    result = agent.run(price_data=price_data)

    assert result.risk_assessment.passed is False
    assert any("max_drawdown" in msg for msg in result.risk_assessment.violations)
