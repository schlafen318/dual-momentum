"""CLI entrypoint for the autonomous backtesting agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from loguru import logger

from src.agents import AgentConfig, AutonomousBacktestAgent


def _load_config(path: Path) -> AgentConfig:
    raw = json.loads(path.read_text())
    return AgentConfig(**raw)


def _apply_overrides(config: AgentConfig, args: argparse.Namespace) -> AgentConfig:
    data = config.to_dict()

    if args.output_dir is not None:
        data["output_dir"] = str(args.output_dir)
    if args.run_name is not None:
        data["run_name"] = args.run_name
    if args.no_write:
        data["write_outputs"] = False
    if args.random_seed is not None:
        data["random_seed"] = args.random_seed

    return AgentConfig(**data)


def _print_summary(result) -> None:
    br = result.backtest_result
    metrics = br.metrics
    print("=== Autonomous Backtest Summary ===")
    print(f"Best method: {result.best_method}")
    print(f"Best score: {result.best_score:.4f} ({result.config.optimisation_metric})")
    print("Best parameters:")
    for key, value in result.best_params.items():
        print(f"  - {key}: {value}")
    print("Performance:")
    print(f"  Total return: {metrics.get('total_return', 0.0):.2%}")
    print(f"  Sharpe ratio: {metrics.get('sharpe_ratio', 0.0):.2f}")
    print(f"  Max drawdown: {metrics.get('max_drawdown', 0.0):.2%}")
    if result.report.root_dir:
        print(f"Artefacts written to: {result.report.root_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomous Dual Momentum backtesting agent")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to agent configuration JSON file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Override the output directory for reports",
    )
    parser.add_argument(
        "--run-name",
        type=str,
        help="Optional run name to use for report subdirectories",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Disable writing reports to disk (overrides config)",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        help="Override the random seed used by optimisation",
    )

    args = parser.parse_args()

    if args.verbose:
        logger.remove()
        logger.add(lambda msg: print(msg, end=""))

    config = _load_config(args.config)
    config = _apply_overrides(config, args)
    agent = AutonomousBacktestAgent(config)
    result = agent.run()
    _print_summary(result)


if __name__ == "__main__":  # pragma: no cover - CLI execution
    main()
