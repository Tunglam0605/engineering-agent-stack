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
    "agents/core/README.md",
    "agents/specialists/README.md",
    "evals/README.md",
    "evals/routing-cases.yaml",
    "benchmarks/README.md",
    "adapters/codex/README.md",
    "adapters/codex/config.toml.example",
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
    codex_names = ["scout", "researcher", "implementer", "debugger", "test-engineer", "reviewer", "architect"]
    paths.extend(f"adapters/codex/agents/{name}.toml" for name in codex_names)
    return paths


def main() -> int:
    paths = required_paths()
    missing = [path for path in paths if not (ROOT / path).is_file()]
    empty = [path for path in paths if (ROOT / path).is_file() and (ROOT / path).stat().st_size == 0]

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
        "and Codex adapter candidates are structurally complete."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
