"""Autonomous backtesting agent for the Dual Momentum framework."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import pandas as pd
from loguru import logger

from ..asset_classes.equity import EquityAsset
from ..backtesting import (
    BacktestEngine,
    HyperparameterTuner,
    MethodComparisonResult,
    OptimizationResult,
    ParameterSpace,
)
from ..backtesting.utils import (
    calculate_data_fetch_dates,
    prepare_backtest_data,
    validate_data_sufficiency,
)
from ..core.types import BacktestResult, PriceData
from ..data_sources import get_default_data_source
from ..strategies.dual_momentum import DualMomentumStrategy

try:  # Advanced analytics optional
    from ..backtesting.advanced_analytics import AdvancedAnalytics
except Exception:  # pragma: no cover - optional dependency
    AdvancedAnalytics = None  # type: ignore


DEFAULT_LOOKBACKS = [63, 126, 189, 252, 315, 378]
DEFAULT_THRESHOLDS = [-0.05, 0.0, 0.01, 0.02, 0.05]
DEFAULT_METHODS = ("grid_search", "random_search", "bayesian_optimization")


def _to_timestamp(value: Optional[Union[str, datetime, pd.Timestamp]]) -> Optional[pd.Timestamp]:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value
    return pd.Timestamp(value)


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


@dataclass
class ReportArtifacts:
    """Paths to generated artefacts."""

    root_dir: Optional[Path] = None
    markdown_path: Optional[Path] = None
    json_path: Optional[Path] = None
    csv_paths: Dict[str, Path] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """Outcome of risk constraint evaluation."""

    passed: bool
    violations: List[str] = field(default_factory=list)


@dataclass
class AgentConfig:
    """Configuration surface for the autonomous agent."""

    symbols: Sequence[str]
    safe_asset: Optional[str] = "AGG"
    start_date: Optional[Union[str, datetime, pd.Timestamp]] = None
    end_date: Optional[Union[str, datetime, pd.Timestamp]] = None
    initial_capital: float = 100_000.0
    commission: float = 0.001
    slippage: float = 0.0005
    risk_free_rate: float = 0.0
    optimisation_metric: str = "sharpe_ratio"
    higher_is_better: Optional[bool] = None
    optimisation_methods: Sequence[str] = DEFAULT_METHODS
    max_trials: int = 30
    n_initial_points: int = 10
    random_seed: Optional[int] = 42
    risk_constraints: Dict[str, float] = field(default_factory=dict)
    report_options: Dict[str, Any] = field(default_factory=dict)
    data_source_config: Dict[str, Any] = field(default_factory=dict)
    custom_parameter_space: Optional[Sequence[Union[ParameterSpace, Dict[str, Any]]]] = None
    allow_weekly_rebalance: bool = False
    output_dir: Optional[Union[str, Path]] = None
    run_name: Optional[str] = None
    write_outputs: bool = True
    benchmark_symbol: Optional[str] = None
    benchmark_price_data: Optional[PriceData] = None
    warmup_lookback: int = 252
    max_lookback_multiplier: float = 0.4
    minimum_lookback: int = 63
    history_years: int = 10

    def __post_init__(self) -> None:
        if not self.symbols:
            raise ValueError("AgentConfig.symbols must contain at least one asset symbol")

        self.start_date = _to_timestamp(self.start_date)
        self.end_date = _to_timestamp(self.end_date)

        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")

        self.optimisation_methods = tuple({m for m in self.optimisation_methods if m}) or DEFAULT_METHODS

        if self.higher_is_better is None:
            self.higher_is_better = self.optimisation_metric not in {"max_drawdown", "volatility", "annual_volatility"}

        if self.max_trials <= 0:
            raise ValueError("max_trials must be positive")

        if self.n_initial_points < 1:
            self.n_initial_points = 1

    def to_dict(self) -> Dict[str, Any]:  # convenience for JSON serialisation
        payload = asdict(self)
        # convert timestamps to isoformat
        for key in ("start_date", "end_date"):
            value = payload.get(key)
            if isinstance(value, pd.Timestamp):
                payload[key] = value.isoformat()
        # ParameterSpace objects cannot be serialised directly
        if self.custom_parameter_space:
            payload["custom_parameter_space"] = [
                _parameter_space_to_dict(ps) if isinstance(ps, ParameterSpace) else ps
                for ps in self.custom_parameter_space
            ]
        if isinstance(payload.get("output_dir"), Path):
            payload["output_dir"] = str(payload["output_dir"])
        if isinstance(payload.get("benchmark_price_data"), PriceData):
            payload["benchmark_price_data"] = payload["benchmark_price_data"].symbol
        return payload


@dataclass
class AutonomousRunResult:
    """Container for agent outputs."""

    config: AgentConfig
    best_params: Dict[str, Any]
    best_method: str
    best_score: float
    optimisation_result: OptimizationResult
    method_comparison: Optional[MethodComparisonResult]
    backtest_result: BacktestResult
    risk_assessment: RiskAssessment
    report: ReportArtifacts
    parameter_space: List[ParameterSpace]


def _parameter_space_from_spec(spec: Dict[str, Any]) -> ParameterSpace:
    return ParameterSpace(
        name=spec["name"],
        param_type=spec["param_type"],
        values=spec.get("values"),
        min_value=spec.get("min_value"),
        max_value=spec.get("max_value"),
        log_scale=spec.get("log_scale", False),
    )


def _parameter_space_to_dict(ps: ParameterSpace) -> Dict[str, Any]:
    return {
        "name": ps.name,
        "param_type": ps.param_type,
        "values": ps.values,
        "min_value": ps.min_value,
        "max_value": ps.max_value,
        "log_scale": ps.log_scale,
    }


class AutonomousBacktestAgent:
    """Coordinate data preparation, hyperparameter search, risk checks, and reporting."""

    def __init__(
        self,
        config: AgentConfig,
        *,
        data_source: Optional[Any] = None,
        asset_class: Optional[EquityAsset] = None,
    ) -> None:
        self.config = config
        self.asset_class = asset_class or EquityAsset()
        self.data_source = data_source or get_default_data_source(config.data_source_config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        *,
        price_data: Optional[Dict[str, PriceData]] = None,
        benchmark_data: Optional[PriceData] = None,
    ) -> AutonomousRunResult:
        """Execute the full autonomous workflow."""

        logger.info("Starting autonomous backtest agent run")

        price_data, benchmark_data = self._prepare_data(price_data, benchmark_data)

        parameter_space = self._prepare_parameter_space(price_data)

        backtest_engine = self._build_backtest_engine()

        tuner = HyperparameterTuner(
            strategy_class=DualMomentumStrategy,
            backtest_engine=backtest_engine,
            price_data=price_data,
            base_config=self._base_strategy_config(),
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            benchmark_data=benchmark_data,
        )

        comparison = self._run_optimisation(tuner, parameter_space)

        optimisation_result = comparison.results[comparison.best_method]

        risk_assessment = self._evaluate_risk(optimisation_result.best_backtest.metrics)

        report = self._build_report(
            optimisation_result=optimisation_result,
            comparison=comparison,
            risk_assessment=risk_assessment,
        )

        logger.info(
            "Autonomous run complete: method=%s score=%.4f",
            comparison.best_method,
            optimisation_result.best_score,
        )

        return AutonomousRunResult(
            config=self.config,
            best_params=optimisation_result.best_params,
            best_method=comparison.best_method,
            best_score=optimisation_result.best_score,
            optimisation_result=optimisation_result,
            method_comparison=comparison,
            backtest_result=optimisation_result.best_backtest,
            risk_assessment=risk_assessment,
            report=report,
            parameter_space=parameter_space,
        )

    # ------------------------------------------------------------------
    # Preparation helpers
    # ------------------------------------------------------------------
    def _prepare_data(
        self,
        price_data: Optional[Dict[str, PriceData]],
        benchmark_data: Optional[PriceData],
    ) -> Tuple[Dict[str, PriceData], Optional[PriceData]]:
        if price_data is not None:
            logger.info("Using provided price data and skipping fetch")
            return price_data, benchmark_data or self.config.benchmark_price_data

        symbols = list(dict.fromkeys(self.config.symbols))
        if self.config.safe_asset:
            symbols.append(self.config.safe_asset)

        end_date = self.config.end_date or pd.Timestamp.today().normalize()
        start_date = self.config.start_date or (end_date - pd.DateOffset(years=self.config.history_years))

        # Ensure warm-up availability
        warmup_start, _ = calculate_data_fetch_dates(
            backtest_start_date=start_date.to_pydatetime(),
            backtest_end_date=end_date.to_pydatetime(),
            lookback_period=self.config.warmup_lookback,
        )

        strategy = DualMomentumStrategy(
            {
                "safe_asset": self.config.safe_asset,
                "lookback_period": self.config.warmup_lookback,
                "rebalance_frequency": "monthly",
            }
        )

        logger.info(
            "Fetching data for %d symbols from %s to %s",
            len(symbols),
            warmup_start.date(),
            end_date.date(),
        )

        price_data = prepare_backtest_data(
            strategy=strategy,
            symbols=symbols,
            data_source=self.data_source,
            start_date=pd.Timestamp(warmup_start),
            end_date=end_date,
            asset_class=self.asset_class,
            include_safe_asset=bool(self.config.safe_asset),
        )

        # Validate sufficiency for the default lookback
        ok, message = validate_data_sufficiency(price_data, self.config.warmup_lookback)
        if not ok:
            logger.warning(message)

        benchmark = benchmark_data or self.config.benchmark_price_data
        if benchmark is None and self.config.benchmark_symbol:
            try:
                logger.info("Fetching benchmark data for %s", self.config.benchmark_symbol)
                raw = self.data_source.fetch_data(
                    self.config.benchmark_symbol,
                    start_date=pd.Timestamp(warmup_start),
                    end_date=end_date,
                )
                benchmark = self.asset_class.normalize_data(raw, self.config.benchmark_symbol)
            except Exception as exc:  # pragma: no cover - network fallback
                logger.warning("Unable to fetch benchmark data: %s", exc)
                benchmark = None

        return price_data, benchmark

    def _prepare_parameter_space(self, price_data: Dict[str, PriceData]) -> List[ParameterSpace]:
        if self.config.custom_parameter_space:
            spaces = []
            for spec in self.config.custom_parameter_space:
                spaces.append(spec if isinstance(spec, ParameterSpace) else _parameter_space_from_spec(spec))
            for space in spaces:
                space.validate()
            logger.info("Using custom parameter space (%d definitions)", len(spaces))
            return spaces

        risk_symbols = [s for s in self.config.symbols if s in price_data]
        if not risk_symbols:
            raise ValueError("No risk asset price data available for parameter planning")

        min_bars = min(len(price_data[s].data) for s in risk_symbols)
        max_lookback = int(min(min_bars * self.config.max_lookback_multiplier, DEFAULT_LOOKBACKS[-1]))
        max_lookback = max(max_lookback, self.config.minimum_lookback)

        lookbacks = sorted({lb for lb in DEFAULT_LOOKBACKS if lb <= max_lookback})
        if not lookbacks:
            lookbacks = [self.config.minimum_lookback]

        max_positions = max(1, min(4, len(risk_symbols)))
        position_counts = list(range(1, max_positions + 1))

        thresholds = DEFAULT_THRESHOLDS.copy()
        if -0.02 not in thresholds:
            thresholds.append(-0.02)
        thresholds = sorted(set(thresholds))

        spaces = [
            ParameterSpace(name="lookback_period", param_type="int", values=lookbacks),
            ParameterSpace(name="position_count", param_type="int", values=position_counts),
            ParameterSpace(name="absolute_threshold", param_type="float", values=thresholds),
            ParameterSpace(name="use_volatility_adjustment", param_type="categorical", values=[True, False]),
        ]

        frequencies = ["monthly"]
        if self.config.allow_weekly_rebalance:
            frequencies.append("weekly")
        spaces.append(ParameterSpace(name="rebalance_frequency", param_type="categorical", values=frequencies))

        for space in spaces:
            space.validate()

        logger.info(
            "Parameter space summary: lookbacks=%s positions=%s thresholds=%s",
            lookbacks,
            position_counts,
            thresholds,
        )

        return spaces

    def _build_backtest_engine(self) -> BacktestEngine:
        return BacktestEngine(
            initial_capital=self.config.initial_capital,
            commission=self.config.commission,
            slippage=self.config.slippage,
            risk_free_rate=self.config.risk_free_rate,
        )

    def _base_strategy_config(self) -> Dict[str, Any]:
        config = {
            "safe_asset": self.config.safe_asset,
            "rebalance_frequency": "monthly",
            "position_count": min(1, len(self.config.symbols)),
            "universe": list(self.config.symbols),
        }
        return config

    # ------------------------------------------------------------------
    # Optimisation & evaluation
    # ------------------------------------------------------------------
    def _run_optimisation(
        self,
        tuner: HyperparameterTuner,
        parameter_space: List[ParameterSpace],
    ) -> MethodComparisonResult:
        methods = [m for m in self.config.optimisation_methods if m in DEFAULT_METHODS]
        comparison = tuner.compare_optimization_methods(
            param_space=parameter_space,
            methods=methods,
            n_trials=self.config.max_trials,
            n_initial_points=self.config.n_initial_points,
            metric=self.config.optimisation_metric,
            higher_is_better=bool(self.config.higher_is_better),
            random_state=self.config.random_seed,
            verbose=False,
        )
        return comparison

    def _evaluate_risk(self, metrics: Dict[str, float]) -> RiskAssessment:
        violations: List[str] = []
        constraints = self.config.risk_constraints

        if not constraints:
            return RiskAssessment(passed=True)

        max_drawdown = constraints.get("max_drawdown")
        if max_drawdown is not None:
            observed = abs(metrics.get("max_drawdown", 0.0))
            if observed > max_drawdown:
                violations.append(
                    f"max_drawdown {observed:.4f} exceeds constraint {max_drawdown:.4f}"
                )

        max_vol = constraints.get("max_volatility") or constraints.get("max_annual_volatility")
        if max_vol is not None:
            observed = metrics.get("volatility", metrics.get("annual_volatility", 0.0))
            if observed > max_vol:
                violations.append(
                    f"volatility {observed:.4f} exceeds constraint {max_vol:.4f}"
                )

        min_sharpe = constraints.get("min_sharpe")
        if min_sharpe is not None:
            observed = metrics.get("sharpe_ratio", 0.0)
            if observed < min_sharpe:
                violations.append(
                    f"sharpe_ratio {observed:.4f} below constraint {min_sharpe:.4f}"
                )

        return RiskAssessment(passed=not violations, violations=violations)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def _build_report(
        self,
        *,
        optimisation_result: OptimizationResult,
        comparison: MethodComparisonResult,
        risk_assessment: RiskAssessment,
    ) -> ReportArtifacts:
        markdown = self._render_markdown(optimisation_result, comparison, risk_assessment)
        json_payload = self._render_report_json(optimisation_result, comparison, risk_assessment)

        artifacts = ReportArtifacts()
        if not self.config.write_outputs:
            artifacts.markdown_path = None
            artifacts.json_path = None
            artifacts.root_dir = None
            return artifacts

        output_root = Path(self.config.output_dir or "autonomy_runs").expanduser().resolve()
        run_name = self.config.run_name or datetime.now().strftime("run_%Y%m%d_%H%M%S")
        run_dir = output_root / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        markdown_path = run_dir / "report.md"
        markdown_path.write_text(markdown)

        json_path = run_dir / "report.json"
        json_path.write_text(json.dumps(json_payload, indent=2))

        csv_paths: Dict[str, Path] = {}
        trials_path = run_dir / f"trials_{comparison.best_method}.csv"
        optimisation_result.all_results.to_csv(trials_path, index=False)
        csv_paths[comparison.best_method] = trials_path

        comparison_path = run_dir / "method_comparison.csv"
        comparison.comparison_metrics.to_csv(comparison_path, index=False)
        csv_paths["method_comparison"] = comparison_path

        artifacts.root_dir = run_dir
        artifacts.markdown_path = markdown_path
        artifacts.json_path = json_path
        artifacts.csv_paths = csv_paths

        logger.info("Report artefacts written to %s", run_dir)

        return artifacts

    def _render_markdown(
        self,
        optimisation_result: OptimizationResult,
        comparison: MethodComparisonResult,
        risk_assessment: RiskAssessment,
    ) -> str:
        br = optimisation_result.best_backtest
        metrics = br.metrics
        lines = [
            "# Autonomous Backtest Report",
            "",
            f"**Selected optimisation method:** `{comparison.best_method}`",
            f"**Optimisation score:** {optimisation_result.best_score:.4f} ({self.config.optimisation_metric})",
            f"**Risk assessment:** {'PASS' if risk_assessment.passed else 'FAIL'}",
            "",
            "## Universe",
            f"- Risk assets: {', '.join(self.config.symbols)}",
            f"- Safe asset: {self.config.safe_asset or 'None'}",
            f"- Backtest window: {br.start_date.date()} ? {br.end_date.date()}",
            "",
            "## Best Parameters",
        ]

        for key, value in optimisation_result.best_params.items():
            lines.append(f"- `{key}` = {value}")

        lines.extend(
            [
                "",
                "## Performance Summary",
                "",
                "| Metric | Value |",
                "| --- | --- |",
                f"| Total return | {_format_pct(metrics.get('total_return', 0.0))} |",
                f"| Annual return | {_format_pct(metrics.get('annual_return', 0.0))} |",
                f"| Volatility | {_format_pct(metrics.get('volatility', metrics.get('annual_volatility', 0.0)))} |",
                f"| Sharpe ratio | {metrics.get('sharpe_ratio', 0.0):.2f} |",
                f"| Sortino ratio | {metrics.get('sortino_ratio', 0.0):.2f} |",
                f"| Calmar ratio | {metrics.get('calmar_ratio', 0.0):.2f} |",
                f"| Max drawdown | {_format_pct(metrics.get('max_drawdown', 0.0))} |",
                f"| Win rate | {_format_pct(metrics.get('win_rate', 0.0))} |",
            ]
        )

        if comparison.comparison_metrics is not None and not comparison.comparison_metrics.empty:
            lines.extend(["", "## Method Comparison", ""])
            lines.append(comparison.comparison_metrics.to_markdown(index=False))

        if risk_assessment.violations:
            lines.extend(["", "## Risk Violations", ""])
            for item in risk_assessment.violations:
                lines.append(f"- {item}")

        return "\n".join(lines) + "\n"

    def _render_report_json(
        self,
        optimisation_result: OptimizationResult,
        comparison: MethodComparisonResult,
        risk_assessment: RiskAssessment,
    ) -> Dict[str, Any]:
        best_backtest = optimisation_result.best_backtest
        payload = {
            "config": self.config.to_dict(),
            "best_method": comparison.best_method,
            "best_score": optimisation_result.best_score,
            "best_params": optimisation_result.best_params,
            "metrics": optimisation_result.best_backtest.metrics,
            "risk": {
                "passed": risk_assessment.passed,
                "violations": risk_assessment.violations,
            },
            "backtest": {
                "start_date": best_backtest.start_date.isoformat(),
                "end_date": best_backtest.end_date.isoformat(),
                "final_capital": best_backtest.final_capital,
                "num_trades": best_backtest.num_trades,
            },
            "comparison": comparison.comparison_metrics.to_dict(orient="records"),
        }
        return payload
