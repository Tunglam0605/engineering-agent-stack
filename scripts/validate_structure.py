#!/usr/bin/env python3
"""Validate the minimum repository architecture without third-party dependencies."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "requirements-dev.txt",
    "docs/ARCHITECTURE.md",
    "docs/ROADMAP.md",
    "docs/BENCHMARKING.md",
    "research/README.md",
    "research/matrix/repository-comparison.yaml",
    "research/patterns/wave-2-synthesis.md",
    "research/anti-patterns/over-orchestration.md",
    "research/sources/openai-codex-subagents.md",
    "research/sources/openai-models-2026-09-07.md",
    "config/model-profiles.yaml",
    "config/routing-policy.yaml",
    "policies/delegation.md",
    "policies/context-budget.md",
    "policies/escalation.md",
    "policies/quality-gates.md",
    "schemas/agent-contract.yaml",
    "schemas/assignment-result.yaml",
    "schemas/benchmark-result.yaml",
    "agents/core/README.md",
    "agents/specialists/README.md",
    "evals/README.md",
    "evals/routing-cases.yaml",
    "benchmarks/README.md",
    "benchmarks/experiment-plan.yaml",
    "benchmarks/pricing/openai-2026-09-07.yaml",
    "benchmarks/fixtures/sample-results.jsonl",
    "benchmarks/results/README.md",
    "adapters/codex/README.md",
    "adapters/codex/role-profiles.yaml",
    "adapters/codex/config.toml.example",
    "scripts/validate_agents.py",
    "scripts/evaluate_routing.py",
    "scripts/generate_codex_adapter.py",
    "scripts/validate_benchmarks.py",
    "scripts/benchmark_report.py",
]

CORE_ROLES = [
    "scout",
    "researcher",
    "implementer",
    "debugger",
    "test-engineer",
    "reviewer",
    "architect",
]

REFERENCE_NOTES = [
    "openai-codex",
    "agency-agents",
    "oh-my-codex",
    "infiquetra-codex-plugins",
    "codex-config",
    "codex-safe-starter",
    "cli-agent-orchestrator",
    "openai-agents-python",
    "microsoft-agent-framework",
    "autogen",
    "langgraph",
    "deepagents",
    "crewai",
    "smolagents",
    "openhands",
]


def required_paths() -> list[str]:
    paths = list(REQUIRED)
    paths.extend(f"agents/core/{role}.yaml" for role in CORE_ROLES)
    paths.extend(f"research/repositories/{name}.md" for name in REFERENCE_NOTES)
    paths.extend(f"adapters/codex/agents/{role}.toml" for role in CORE_ROLES)
    return paths


def main() -> int:
    paths = required_paths()
    missing = [path for path in paths if not (ROOT / path).is_file()]
    empty = [
        path
        for path in paths
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

    print(
        "OK: "
        f"{len(paths)} required artifacts present; "
        f"{len(CORE_ROLES)} core roles, {len(REFERENCE_NOTES)} research notes, "
        "generated Codex adapter artifacts, and benchmark foundations are structurally complete."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
