#!/usr/bin/env python3
"""Validate the minimum repository architecture without third-party dependencies."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "AGENTS.md",
    "docs/ARCHITECTURE.md",
    "docs/ROADMAP.md",
    "research/README.md",
    "research/matrix/repository-comparison.yaml",
    "config/model-profiles.yaml",
    "config/routing-policy.yaml",
    "policies/delegation.md",
    "policies/context-budget.md",
    "policies/escalation.md",
    "policies/quality-gates.md",
    "schemas/agent-contract.yaml",
    "schemas/assignment-result.yaml",
    "agents/core/README.md",
    "agents/specialists/README.md",
    "evals/README.md",
    "benchmarks/README.md",
    "adapters/codex/README.md",
]

REFERENCE_NOTES = [
    "research/repositories/agency-agents.md",
    "research/repositories/oh-my-codex.md",
    "research/repositories/infiquetra-codex-plugins.md",
    "research/repositories/codex-config.md",
    "research/repositories/codex-safe-starter.md",
    "research/repositories/cli-agent-orchestrator.md",
]


def main() -> int:
    missing = [path for path in REQUIRED + REFERENCE_NOTES if not (ROOT / path).is_file()]
    empty = [
        path
        for path in REQUIRED + REFERENCE_NOTES
        if (ROOT / path).is_file() and (ROOT / path).stat().st_size == 0
    ]

    if missing or empty:
        if missing:
            print("Missing required files:")
            for path in missing:
                print(f"  - {path}")
        if empty:
            print("Empty required files:")
            for path in empty:
                print(f"  - {path}")
        return 1

    print(f"OK: {len(REQUIRED)} core artifacts and {len(REFERENCE_NOTES)} research notes present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
