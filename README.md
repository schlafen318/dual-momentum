# Dual Momentum Workspace

This repository hosts the dual momentum backtesting platform along with its
supporting tools, automation scripts, and a comprehensive documentation hub.

## Repository Structure

- `docs/` - centralised documentation library with getting-started guides,
  operational runbooks, historical fixes, and reference material.
- `dual_momentum_system/` - the core Python implementation, tests, and
  deployment resources for the dual momentum engine and Streamlit UI.
- `diagnose_cash_allocation.py` - targeted debugging script for allocation
  anomalies.
- `logs/` - archived runtime logs.
- `start.sh`, `requirements.txt`, `runtime.txt` - environment bootstrap assets.

## Getting Started

1. Review `docs/getting-started/README.md` for quick-start playbooks. New users
   should begin with the portfolio optimisation or Railway deployment guides.
2. Install dependencies with `pip install -r requirements.txt` (or use the
   project-specific requirements inside `dual_momentum_system/`).
3. Execute `dual_momentum_system/run_tests.sh` to validate the environment.

## Documentation Map

- `docs/README.md` - top-level index of all guides, references, and historical
  records.
- `docs/troubleshooting/fix-summaries/README.md` - catalogue of resolved issues
  and root-cause analyses.
- `docs/dual-momentum-system/README.md` - system-specific navigation covering
  architecture, configuration, and operations.

## Contributing

- Follow the structure outlined in `docs/README.md` when adding new
  documentation.
- Run formatting and tests (`dual_momentum_system/run_tests.sh`) before
  submitting changes.
- Include clear validation notes in any new troubleshooting or fix summaries.

## Documentation Maintenance

- Regenerate category indexes after adding or renaming documents with
  `python scripts/update_doc_indexes.py`.
- Keep supporting assets (images, datasets) inside the relevant documentation
  collection to preserve context.

For questions about the codebase or documentation structure, start with the
appropriate section in the docs hub and escalate findings via issues or pull
requests as needed.
