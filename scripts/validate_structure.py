#!/usr/bin/env python3
"""Validate the minimum repository architecture without third-party dependencies."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md", "ACKNOWLEDGEMENTS.md", "AGENTS.md", "CHANGELOG.md", "CONTRIBUTING.md", "requirements-dev.txt",
    "docs/ARCHITECTURE.md", "docs/ROADMAP.md", "docs/EVALUATION.md", "docs/INSTALL_CODEX.md", "docs/ACCEPTANCE_WINDOWS.md", "docs/PROVENANCE.md",
    "research/README.md", "research/matrix/repository-comparison.yaml", "research/patterns/wave-2-synthesis.md", "research/anti-patterns/over-orchestration.md",
    "research/sources/openai-codex-subagents.md", "research/sources/openai-codex-exec-jsonl.md", "research/sources/openai-models-2026-09-07.md",
    "config/model-profiles.yaml", "config/routing-policy.yaml",
    "policies/delegation.md", "policies/context-budget.md", "policies/escalation.md", "policies/quality-gates.md",
    "schemas/agent-contract.yaml", "schemas/assignment-result.yaml", "schemas/benchmark-record.yaml", "schemas/run-capture.yaml", "schemas/benchmark-task.yaml",
    "agents/core/README.md", "agents/specialists/README.md",
    "evals/README.md", "evals/routing-cases.yaml",
    "benchmarks/README.md", "benchmarks/experiment-plan.yaml", "benchmarks/run-manifest.example.yaml", "benchmarks/fixtures/codex-exec-events.jsonl", "benchmarks/tasks/README.md", "benchmarks/tasks/index.yaml",
    "adapters/codex/README.md", "adapters/codex/role-profiles.yaml", "adapters/codex/config.toml.example", "adapters/codex/AGENTS.md.example",
    "scripts/validate_structure.py", "scripts/validate_provenance.py", "scripts/validate_agents.py", "scripts/evaluate_routing.py", "scripts/validate_benchmarks.py", "scripts/validate_task_suite.py", "scripts/summarize_benchmarks.py",
    "scripts/generate_codex_adapter.py", "scripts/install_codex.py", "scripts/acceptance_test_codex.py", "scripts/acceptance-test.ps1",
    "scripts/codex_capture_lib.py", "scripts/benchmark_task_lib.py", "scripts/normalize_codex_exec.py", "scripts/capture_codex_exec.py", "scripts/promote_run_capture.py", "scripts/prepare_benchmark_task.py", "scripts/grade_benchmark_task.py",
]

CORE_ROLES = ["scout", "researcher", "implementer", "debugger", "test-engineer", "reviewer", "architect"]
REFERENCE_NOTES = ["openai-codex", "agency-agents", "oh-my-codex", "infiquetra-codex-plugins", "codex-config", "codex-safe-starter", "cli-agent-orchestrator", "openai-agents-python", "microsoft-agent-framework", "autogen", "langgraph", "deepagents", "crewai", "smolagents", "openhands"]
CONTROLLED_TASKS = ["scout-symbol-001", "implementer-bounded-bug-001", "reviewer-regression-001", "orchestrator-trivial-edit-001"]


def required_paths() -> list[str]:
    paths = list(REQUIRED)
    paths.extend(f"agents/core/{role}.yaml" for role in CORE_ROLES)
    paths.extend(f"research/repositories/{name}.md" for name in REFERENCE_NOTES)
    paths.extend(f"adapters/codex/agents/{role}.toml" for role in CORE_ROLES)
    paths.extend(f"benchmarks/tasks/{task_id}/task.yaml" for task_id in CONTROLLED_TASKS)
    paths.extend(f"benchmarks/tasks/{task_id}/prompt.md" for task_id in CONTROLLED_TASKS)
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
        f"{len(paths)} required artifacts present; {len(CORE_ROLES)} core roles, {len(REFERENCE_NOTES)} research notes, "
        f"{len(CONTROLLED_TASKS)} controlled benchmark tasks, provenance controls, Windows acceptance tooling, "
        "Codex installation/capture tooling, and adapter artifacts are structurally complete."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
