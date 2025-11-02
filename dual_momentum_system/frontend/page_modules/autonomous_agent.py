"""Streamlit page for the Autonomous Backtesting Agent."""

from __future__ import annotations

import json
from datetime import date
from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from src.agents import AgentConfig, AutonomousBacktestAgent


DEFAULT_SYMBOLS = "SPY, EFA, EEM"
DEFAULT_SAFE_ASSET = "AGG"
DEFAULT_BENCHMARK = "SPY"
OPTIMISATION_METHODS = [
    "grid_search",
    "random_search",
    "bayesian_optimization",
]
METRICS = [
    "sharpe_ratio",
    "sortino_ratio",
    "calmar_ratio",
    "annual_return",
    "total_return",
    "max_drawdown",
    "volatility",
]


def _parse_symbols(raw: str) -> list[str]:
    return [symbol.strip().upper() for symbol in raw.split(",") if symbol.strip()]


def _determine_higher_is_better(metric: str, user_choice: bool) -> bool:
    if metric in {"max_drawdown", "volatility"}:
        return False
    return user_choice


def _to_timestamp(value: Optional[date]) -> Optional[pd.Timestamp]:
    if value is None:
        return None
    return pd.Timestamp(value)


def _risk_constraint_payload(max_dd: float, max_vol: float, min_sharpe: float) -> Dict[str, float]:
    payload: Dict[str, float] = {}
    if max_dd > 0:
        payload["max_drawdown"] = max_dd
    if max_vol > 0:
        payload["max_volatility"] = max_vol
    if min_sharpe > 0:
        payload["min_sharpe"] = min_sharpe
    return payload


def render() -> None:
    """Render the autonomous agent Streamlit page."""

    st.title("?? Autonomous Backtesting Agent")
    st.markdown(
        """
        Configure the autonomous agent to explore parameter spaces, compare optimisation
        methods, and generate a backtest report automatically. Provide an asset universe,
        safety guardrails, and optional risk constraints, then launch the agent from the UI.
        """
    )

    default_start = date(2015, 1, 1)
    default_end = date.today()

    with st.form("autonomous_agent_form"):
        st.subheader("Configuration")
        col_assets, col_dates = st.columns([2, 1])
        with col_assets:
            symbols_input = st.text_input(
                "Risk Asset Symbols",
                value=DEFAULT_SYMBOLS,
                help="Comma-separated list of tickers to include in the optimisation universe.",
            )
            safe_asset = st.text_input(
                "Safe Asset",
                value=DEFAULT_SAFE_ASSET,
                help="Optional defensive asset (leave blank to hold cash).",
            )
            benchmark_symbol = st.text_input(
                "Benchmark Symbol",
                value=DEFAULT_BENCHMARK,
                help="Optional benchmark for comparison (leave blank to skip).",
            )
        with col_dates:
            start_date = st.date_input(
                "Start Date",
                value=default_start,
            )
            end_date = st.date_input(
                "End Date",
                value=default_end,
            )

        col_capital, col_costs = st.columns(2)
        with col_capital:
            initial_capital = st.number_input(
                "Initial Capital",
                min_value=1_000.0,
                value=100_000.0,
                step=10_000.0,
            )
            random_seed = st.number_input(
                "Random Seed",
                min_value=0,
                value=42,
                step=1,
            )
        with col_costs:
            commission = st.number_input("Commission (decimal)", min_value=0.0, value=0.001, step=0.0005)
            slippage = st.number_input("Slippage (decimal)", min_value=0.0, value=0.0005, step=0.0005)

        st.subheader("Optimisation")
        col_metric, col_methods = st.columns([1, 2])
        with col_metric:
            optimisation_metric = st.selectbox("Metric", METRICS, index=0)
            maximise_metric = st.checkbox(
                "Treat metric as maximise", value=True, help="Disable for metrics where lower is better."
            )
            higher_is_better = _determine_higher_is_better(optimisation_metric, maximise_metric)
        with col_methods:
            methods = st.multiselect(
                "Optimisation Methods",
                options=OPTIMISATION_METHODS,
                default=list(OPTIMISATION_METHODS),
            )
        max_trials = st.slider("Trials per method", 10, 100, 30, step=5)
        n_initial_points = st.slider(
            "Initial random trials (Bayesian)", 5, 30, 10, step=1, help="Used only for Bayesian optimisation"
        )

        with st.expander("Risk Constraints", expanded=False):
            st.markdown("Provide constraints as decimals (e.g., 0.25 = 25% max drawdown). Leave zero to ignore.")
            col_risk1, col_risk2, col_risk3 = st.columns(3)
            with col_risk1:
                max_drawdown = st.number_input("Max Drawdown", min_value=0.0, value=0.0, step=0.05)
            with col_risk2:
                max_volatility = st.number_input("Max Volatility", min_value=0.0, value=0.0, step=0.05)
            with col_risk3:
                min_sharpe = st.number_input("Min Sharpe", min_value=0.0, value=0.0, step=0.1)

        with st.expander("Advanced Settings", expanded=False):
            allow_weekly = st.checkbox("Allow weekly rebalancing candidates", value=False)
            write_outputs = st.checkbox("Write reports to disk", value=False)
            output_dir = st.text_input(
                "Output Directory",
                value="autonomy_runs",
                help="Directory for reports when writing is enabled.",
            )
            run_name = st.text_input("Run Name", value="", help="Optional name for report subdirectory.")
            include_benchmark = st.checkbox("Include benchmark in report", value=True)
            include_monte_carlo = st.checkbox("Include Monte Carlo analytics", value=False)

        submitted = st.form_submit_button("Run Autonomous Agent", type="primary")

    if submitted:
        try:
            symbols = _parse_symbols(symbols_input)
            if not symbols:
                st.error("Please provide at least one risk asset symbol.")
                st.stop()

            start_ts = _to_timestamp(start_date)
            end_ts = _to_timestamp(end_date)
            if start_ts and end_ts and end_ts <= start_ts:
                st.error("End date must be after start date.")
                st.stop()

            config_kwargs = {
                "symbols": symbols,
                "safe_asset": safe_asset.strip().upper() if safe_asset.strip() else None,
                "start_date": start_ts,
                "end_date": end_ts,
                "initial_capital": float(initial_capital),
                "commission": float(commission),
                "slippage": float(slippage),
                "risk_free_rate": 0.0,
                "optimisation_metric": optimisation_metric,
                "higher_is_better": higher_is_better,
                "optimisation_methods": methods or list(OPTIMISATION_METHODS),
                "max_trials": int(max_trials),
                "n_initial_points": int(n_initial_points),
                "random_seed": int(random_seed),
                "risk_constraints": _risk_constraint_payload(max_drawdown, max_volatility, min_sharpe),
                "allow_weekly_rebalance": allow_weekly,
                "write_outputs": write_outputs,
                "output_dir": output_dir.strip() or "autonomy_runs",
                "run_name": run_name.strip() or None,
                "benchmark_symbol": benchmark_symbol.strip().upper() if benchmark_symbol.strip() else None,
                "report_options": {
                    "include_benchmark": include_benchmark,
                    "include_monte_carlo": include_monte_carlo,
                },
            }

            config = AgentConfig(**config_kwargs)
            agent = AutonomousBacktestAgent(config)

            with st.spinner("Running autonomous optimisation..."):
                result = agent.run()

            st.session_state["autonomous_agent_result"] = result
            st.session_state["autonomous_agent_config"] = config.to_dict()
            st.success("Autonomous agent run completed successfully.")

        except Exception as exc:  # pylint: disable=broad-except
            st.exception(exc)
            st.stop()

    if "autonomous_agent_result" in st.session_state:
        result = st.session_state["autonomous_agent_result"]
        config_dict = st.session_state.get("autonomous_agent_config", {})

        st.subheader("Results Summary")
        col_left, col_right = st.columns(2)
        with col_left:
            st.metric("Best Method", result.best_method)
            st.metric("Best Score", f"{result.best_score:.4f}")
        with col_right:
            metrics = result.backtest_result.metrics
            total_return = metrics.get("total_return", 0.0)
            st.metric("Total Return", f"{total_return * 100:.2f}%")
            st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0.0):.2f}")

        st.markdown("### Best Parameters")
        params_df = pd.DataFrame(
            [(key, value) for key, value in result.best_params.items()],
            columns=["Parameter", "Value"],
        )
        st.table(params_df)

        st.markdown("### Risk Assessment")
        risk = result.risk_assessment
        if risk.passed:
            st.success("All configured risk constraints passed.")
        else:
            st.error("Risk constraints violated:")
            for item in risk.violations:
                st.write(f"- {item}")

        st.markdown("### Method Comparison")
        comparison_df = result.method_comparison.comparison_metrics
        st.dataframe(comparison_df, use_container_width=True)
        if not comparison_df.empty and "best_score" in comparison_df.columns:
            score_fig = px.bar(
                comparison_df,
                x="method",
                y="best_score",
                title="Best Score by Optimisation Method",
                text="best_score",
            )
            score_fig.update_traces(texttemplate="%{text:.4f}", textposition="outside")
            score_fig.update_layout(yaxis_title=result.optimisation_result.metric_name)
            st.plotly_chart(score_fig, use_container_width=True)

        st.markdown("### Trial Results")
        trials_df = result.optimisation_result.all_results
        if not trials_df.empty:
            st.dataframe(trials_df, use_container_width=True)

        st.markdown("### Performance Charts")
        equity_curve = result.backtest_result.equity_curve
        if equity_curve is not None and not equity_curve.empty:
            equity_df = equity_curve.reset_index()
            equity_df.columns = ["timestamp", "equity"]
            equity_fig = px.line(
                equity_df,
                x="timestamp",
                y="equity",
                title="Equity Curve",
            )
            equity_fig.update_layout(yaxis_title="Portfolio Value")
            st.plotly_chart(equity_fig, use_container_width=True)

            drawdown = (equity_curve / equity_curve.cummax()) - 1
            drawdown_df = drawdown.reset_index()
            drawdown_df.columns = ["timestamp", "drawdown"]
            drawdown_fig = px.area(
                drawdown_df,
                x="timestamp",
                y="drawdown",
                title="Drawdown",
            )
            drawdown_fig.update_layout(yaxis_title="Drawdown", yaxis_tickformat=".0%")
            st.plotly_chart(drawdown_fig, use_container_width=True)

        st.markdown("### Downloads")
        config_json = json.dumps(config_dict, indent=2)
        st.download_button(
            label="Download Config JSON",
            data=config_json,
            file_name="autonomous_agent_config.json",
            mime="application/json",
        )
        params_json = json.dumps(result.best_params, indent=2)
        st.download_button(
            label="Download Best Parameters",
            data=params_json,
            file_name="autonomous_agent_best_params.json",
            mime="application/json",
        )

        if result.optimisation_result.best_backtest.metrics:
            metrics_json = json.dumps(result.optimisation_result.best_backtest.metrics, indent=2)
            st.download_button(
                label="Download Metrics JSON",
                data=metrics_json,
                file_name="autonomous_agent_metrics.json",
                mime="application/json",
            )

        if result.report.root_dir:
            st.info(f"Report artefacts written to `{result.report.root_dir}`")
        else:
            st.caption("Reports were not written to disk (write outputs disabled).")
