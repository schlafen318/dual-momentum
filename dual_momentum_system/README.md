# Dual Momentum System

This directory contains the production-ready dual momentum backtesting engine,
Streamlit-based optimisation UI, and supporting utilities.

## Key Components

- `src/` - core library code organised by plugins (asset classes, data
  sources, strategies, risk managers) and supporting infrastructure.
- `frontend/` - Streamlit dashboards and interactive tooling for exploring
  optimisation results.
- `config/` - strategy and risk configuration templates.
- `tests/` & `test_*.py` - automated coverage for the plugin framework and key
  behaviours.
- `run_tests.sh`, `run_portfolio_comparison.sh` - helper scripts for CI-parity
  test execution and portfolio comparisons.

## Documentation

- `../docs/dual-momentum-system/getting-started/README.md` - quick-start guides
  for installing and running the system locally.
- `../docs/dual-momentum-system/guides/README.md` - operational runbooks for
  deployment, logging, and optimisation workflows.
- `../docs/dual-momentum-system/reference/README.md` - architectural notes and
  configuration references.
- `../docs/dual-momentum-system/troubleshooting/README.md` - investigation logs
  and fix summaries for common failure modes.
- `../docs/dual-momentum-system/history/README.md` - milestone reports and
  verification history.

## Development Workflow

1. Install dependencies with `pip install -r requirements.txt` from this
   directory (use a virtual environment).
2. Run `./run_tests.sh` or `pytest` to validate changes. Use the `tests/`
   markers to target specific suites.
3. When adding new plugins, follow the patterns in `src/core` and document new
   behaviour under `docs/dual-momentum-system/`.
4. For UI changes, use `streamlit run frontend/app.py` (or the appropriate
   entrypoint) and capture key decisions in the guides collection.

Refer to the documentation hub at `../docs/README.md` for additional context
and contribution guidelines.
