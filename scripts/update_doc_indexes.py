#!/usr/bin/env python3
"""Regenerate README indexes for documentation collections.

The documentation library is organised into category directories (e.g.
``docs/getting-started`` or ``docs/dual-momentum-system/reference``). Each
collection keeps a short ``README.md`` that links to the available documents and
sub-collections. This script rebuilds those index files so they stay in sync
whenever documents are added, removed, or renamed.

Run without arguments to refresh every configured directory:

    python scripts/update_doc_indexes.py

Or target a subset by passing relative paths:

    python scripts/update_doc_indexes.py docs/getting-started docs/guides
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class IndexSpec:
    """Configuration for a documentation directory."""

    title: str
    intro: str
    extra_links: Sequence[tuple[str, str]] | None = None


REPO_ROOT = Path(__file__).resolve().parents[1]

DIRECTORY_CONFIG = {
    Path("docs/getting-started"): IndexSpec(
        "Getting Started",
        "Quick-start entry points for the workspace.",
    ),
    Path("docs/guides"): IndexSpec(
        "How-To Guides",
        "Task-oriented guides that walk through repeatable workflows.",
    ),
    Path("docs/reference"): IndexSpec(
        "Reference Library",
        "Deep-dive reference material and diagrams.",
    ),
    Path("docs/troubleshooting"): IndexSpec(
        "Troubleshooting",
        "Resources for diagnosing and fixing issues.",
    ),
    Path("docs/troubleshooting/fix-summaries"): IndexSpec(
        "Fix Summary Library",
        "Historical fixes and diagnostic write-ups sorted chronologically by filename. "
        "Each document captures the root cause, remediation steps, and validation for a specific issue.",
    ),
    Path("docs/history"): IndexSpec(
        "Project History",
        "Historical artifacts and status reports.",
    ),
    Path("docs/history/status-reports"): IndexSpec(
        "Project Status Reports",
        "Milestone reports, completion summaries, and status memos for the broader workspace.",
    ),
    Path("docs/dual-momentum-system"): IndexSpec(
        "Dual Momentum Documentation",
        "Documentation specific to the dual momentum backtesting system.",
    ),
    Path("docs/dual-momentum-system/getting-started"): IndexSpec(
        "Dual Momentum: Getting Started",
        "Kick-off guides for running the dual momentum system.",
    ),
    Path("docs/dual-momentum-system/guides"): IndexSpec(
        "Dual Momentum: Guides",
        "Operational guides for dual momentum features.",
    ),
    Path("docs/dual-momentum-system/reference"): IndexSpec(
        "Dual Momentum: Reference",
        "Reference materials for dual momentum internals.",
        extra_links=[
            (
                "Constraints file to force specific versions during pip resolution",
                "../../../dual_momentum_system/constraints.txt",
            )
        ],
    ),
    Path("docs/dual-momentum-system/troubleshooting"): IndexSpec(
        "Dual Momentum: Troubleshooting",
        "Issue resolution notes for the dual momentum system.",
    ),
    Path("docs/dual-momentum-system/troubleshooting/fix-summaries"): IndexSpec(
        "Dual Momentum Fix Summaries",
        "Detailed investigations and fixes specific to the dual momentum system. "
        "Use these references when similar regressions appear again.",
    ),
    Path("docs/dual-momentum-system/history"): IndexSpec(
        "Dual Momentum: History",
        "Status updates and historical records for the dual momentum system.",
    ),
    Path("docs/dual-momentum-system/history/status-reports"): IndexSpec(
        "Dual Momentum Status Reports",
        "Progress summaries specific to the dual momentum system implementation and verification efforts.",
    ),
}


def heading_for_file(path: Path) -> str:
    """Derive a display label from the first heading or filename."""

    label = path.stem.replace("_", " ")
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    label = stripped.lstrip("#").strip()
                break
    except OSError:
        pass
    return label


def build_index(directory: Path, spec: IndexSpec) -> None:
    """Write or update the README for a documentation directory."""

    files: List[Path] = []
    subdirs: List[Path] = []

    for entry in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if entry.name == "README.md" or entry.name.startswith("."):
            continue
        if entry.is_dir():
            subdirs.append(entry)
        elif entry.is_file():
            files.append(entry)

    lines: List[str] = [f"# {spec.title}", "", spec.intro.strip(), ""]

    document_lines: List[str] = []
    for file_path in files:
        label = heading_for_file(file_path)
        document_lines.append(f"- [{label}]({file_path.name})")

    if spec.extra_links:
        for label, target in spec.extra_links:
            document_lines.append(f"- [{label}]({target})")

    if document_lines:
        lines.extend(["## Documents", "", *document_lines, ""])

    if subdirs:
        lines.extend(["## Collections", ""])
        for subdir in subdirs:
            readme = subdir / "README.md"
            target = f"{subdir.name}/README.md" if readme.exists() else f"{subdir.name}/"
            label = subdir.name.replace("-", " ").title()
            lines.append(f"- [{label}]({target})")
        lines.append("")

    directory.joinpath("README.md").write_text("\n".join(lines), encoding="utf-8")


def iter_targets(requested: Sequence[Path] | None) -> Iterable[tuple[Path, IndexSpec]]:
    if requested:
        requested_resolved = {p.resolve() for p in requested}
        for rel_path, spec in DIRECTORY_CONFIG.items():
            abs_path = (REPO_ROOT / rel_path).resolve()
            if abs_path in requested_resolved:
                yield abs_path, spec
    else:
        for rel_path, spec in DIRECTORY_CONFIG.items():
            yield (REPO_ROOT / rel_path).resolve(), spec


def parse_args() -> Sequence[Path]:
    import argparse

    parser = argparse.ArgumentParser(description="Regenerate documentation index files.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional documentation directories to update (relative to the repo root).",
    )
    args = parser.parse_args()

    if not args.paths:
        return []

    resolved: List[Path] = []
    for raw in args.paths:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = (REPO_ROOT / candidate).resolve()
        resolved.append(candidate)
    return resolved


def main() -> None:
    requested = parse_args()
    targets = list(iter_targets(requested))
    if not targets:
        available = ", ".join(str(path) for path in DIRECTORY_CONFIG)
        raise SystemExit(f"No matching documentation directories. Available: {available}")

    for directory, spec in targets:
        if not directory.exists():
            raise SystemExit(f"Configured directory missing: {directory}")
        build_index(directory, spec)


if __name__ == "__main__":
    main()
