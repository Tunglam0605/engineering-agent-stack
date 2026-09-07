#!/usr/bin/env python3
"""Validate that researched upstream repositories are acknowledged and provenance policy is present."""

from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "research" / "matrix" / "repository-comparison.yaml"
ACK = ROOT / "ACKNOWLEDGEMENTS.md"
PROVENANCE = ROOT / "docs" / "PROVENANCE.md"
README = ROOT / "README.md"


def main() -> int:
    try:
        matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
        ack_text = ACK.read_text(encoding="utf-8")
        provenance_text = PROVENANCE.read_text(encoding="utf-8")
        readme_text = README.read_text(encoding="utf-8")
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 2

    failures: list[str] = []
    repos = matrix.get("repositories", []) if isinstance(matrix, dict) else []
    names = [entry.get("name") for entry in repos if isinstance(entry, dict)]
    names = [name for name in names if isinstance(name, str) and name]

    if not names:
        failures.append("research matrix contains no repositories")
    for name in names:
        if name not in ack_text:
            failures.append(f"unacknowledged research source: {name}")

    if "ACKNOWLEDGEMENTS.md" not in readme_text:
        failures.append("README must link ACKNOWLEDGEMENTS.md")
    if "PROVENANCE.md" not in readme_text:
        failures.append("README must link docs/PROVENANCE.md")

    required_policy_terms = (
        "Conceptual reference",
        "Adapted material",
        "Vendored material",
        "Generated material",
    )
    for term in required_policy_terms:
        if term not in provenance_text:
            failures.append(f"provenance policy missing class: {term}")

    if failures:
        print(f"FAIL: {len(failures)} provenance/acknowledgement problem(s).")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS: {len(names)} research source(s) are acknowledged and provenance policy is present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
