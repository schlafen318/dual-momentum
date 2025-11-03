"""Smoke tests for project documentation assets."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.agents import AgentConfig, AutonomousBacktestAgent
from src.core.types import AssetMetadata, AssetType, PriceData


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "docs"
CONFIG_ROOT = REPO_ROOT / "dual_momentum_system" / "config"


pytestmark = pytest.mark.documentation


def _iter_markdown_files() -> list[Path]:
    return sorted(DOCS_ROOT.rglob("*.md"))


def test_markdown_files_exist() -> None:
    """Ensure we have markdown documentation available."""

    markdown_files = _iter_markdown_files()
    assert markdown_files, "No markdown documentation files found under docs/"


def test_markdown_files_have_headings() -> None:
    """Every markdown file should start with a top-level heading."""

    for path in _iter_markdown_files():
        content = path.read_text(encoding="utf-8").strip()
        assert content, f"Documentation file {path} is empty"
        assert re.search(r"^# ", content, flags=re.MULTILINE), (
            f"Documentation file {path} is missing a top-level '# ' heading"
        )


def test_readme_mentions_autonomous_agent_cli() -> None:
    """Repository README should reference the autonomous agent CLI entry point."""

    readme_path = REPO_ROOT / "README.md"
    assert readme_path.exists(), "Repository README.md not found"
    readme_text = readme_path.read_text(encoding="utf-8")
    assert "run_autonomous_agent.py" in readme_text, (
        "README.md should mention the autonomous agent CLI entrypoint"
    )


def test_example_config_is_valid() -> None:
    """The example agent configuration should load without validation errors."""

    config_path = CONFIG_ROOT / "agent_config_example.json"
    assert config_path.exists(), "Sample agent configuration missing"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    config = AgentConfig(**payload)

    assert config.symbols, "Config should contain at least one symbol"
    assert config.optimisation_methods, "Config should list optimisation methods"


def test_autonomous_agent_can_be_instantiated_from_example() -> None:
    """Ensure the sample configuration produces an agent without hitting external services."""

    config_path = CONFIG_ROOT / "agent_config_example.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload.update({
        "write_outputs": False,
        "optimisation_methods": ["grid_search"],
        "benchmark_symbol": None,
    })
    config = AgentConfig(**payload)

    dummy_data_source = object()
    agent = AutonomousBacktestAgent(config, data_source=dummy_data_source)

    assert agent.config is config
    assert agent.data_source is dummy_data_source


def _synthetic_price_data(symbol: str, periods: int = 150) -> PriceData:
    dates = pd.date_range("2020-01-01", periods=periods, freq="B")
    base = 100 + np.linspace(0, 5, periods)
    df = pd.DataFrame(
        {
            "open": base,
            "high": base * 1.01,
            "low": base * 0.99,
            "close": base,
            "volume": np.full(periods, 1_000_000),
        },
        index=dates,
    )
    metadata = AssetMetadata(symbol=symbol, name=symbol, asset_type=AssetType.EQUITY)
    return PriceData(symbol=symbol, data=df, metadata=metadata)


def test_autonomous_agent_smoke_run(tmp_path: Path) -> None:
    """Execute a lightweight autonomous run to ensure documentation examples remain valid."""

    symbols = ["SPY", "EFA"]
    safe_asset = "AGG"
    price_data = {symbol: _synthetic_price_data(symbol) for symbol in symbols + [safe_asset]}

    start = price_data[symbols[0]].data.index[0]
    end = price_data[symbols[0]].data.index[-1]

    config = AgentConfig(
        symbols=symbols,
        safe_asset=safe_asset,
        start_date=start,
        end_date=end,
        initial_capital=50_000,
        commission=0.0,
        slippage=0.0,
        optimisation_metric="sharpe_ratio",
        higher_is_better=True,
        optimisation_methods=["grid_search"],
        max_trials=1,
        custom_parameter_space=[
            {"name": "lookback_period", "param_type": "int", "values": [63]},
            {"name": "position_count", "param_type": "int", "values": [1]},
            {"name": "absolute_threshold", "param_type": "float", "values": [0.0]},
            {"name": "use_volatility_adjustment", "param_type": "categorical", "values": [False]},
            {"name": "rebalance_frequency", "param_type": "categorical", "values": ["monthly"]},
        ],
        write_outputs=False,
        benchmark_symbol=None,
        output_dir=str(tmp_path),
    )

    agent = AutonomousBacktestAgent(config, data_source=object())
    result = agent.run(price_data=price_data)

    assert result.best_params["lookback_period"] == 63
    assert result.best_method == "grid_search"
    assert "total_return" in result.backtest_result.metrics
