# Changelog

All notable project changes will be documented here.

## [Unreleased]

### Added
- Research Wave 2 analysis covering OpenAI Agents SDK, Microsoft Agent Framework, AutoGen, LangGraph, Deep Agents, CrewAI, smolagents and OpenHands.
- Authoritative `openai/codex` implementation/public-contract research notes.
- Seven provider-neutral core role definitions and semantic contract validation.
- Executable deterministic routing-policy evaluator.
- Deterministic Codex adapter generator with drift checking.
- Codex role-to-semantic-profile mapping separate from canonical roles.
- Normalized benchmark/run-capture contracts and Codex JSONL capture pipeline.
- `controlled-v1` benchmark suite with deterministic text/test graders.
- Safe Codex installer with project/personal scope, dry-run, drift check, conflict refusal, and backup behavior.
- Managed parent-orchestration block for target-project `AGENTS.md`.
- `ACKNOWLEDGEMENTS.md` with explicit credit to all repositories currently in the research matrix.
- `docs/PROVENANCE.md` and provenance validation.
- Windows Codex installation/acceptance documentation.
- Stack-owned acceptance core covering repository validation, isolated installation, direct-first behavior, and exact bounded-write scope.
- Separate Codex provider/runtime probe for `spawn_agent`, custom-role selection, Multi-Agent V2 behavior, and child-model telemetry.
- Locale-independent UTF-8 subprocess capture with Windows regression coverage.
- Offline Windows GitHub Actions acceptance job.

### Changed
- Repository comparison matrix remains the source-of-truth list for acknowledged research inputs.
- `config/model-profiles.yaml` uses `gpt-5.6-sol` for the critical candidate while retaining Astra as benchmark-only.
- Scout and researcher retain the Luna cost tier but use medium reasoning as the current quality-floor candidate.
- Context budgeting is adaptive across input context, work budget, and result budget rather than a hard total-token quota.
- Project-scoped installation can now install/refresh only the managed Engineering Agent Stack block inside an existing `AGENTS.md`.
- README now makes Windows + Codex project-scoped acceptance the primary quick-start path and retains explicit upstream acknowledgements.
- CI asserts synthetic subagent telemetry, project parent instructions, Windows offline acceptance, and locale-independent UTF-8 subprocess handling.
- Stack-owned release acceptance no longer forces or gates on Codex child-agent spawning/model routing; those provider capabilities are observed by a separate diagnostic command.
- Legacy `scripts/acceptance_test_codex.py` is now a compatibility entry point for the stack-owned acceptance core.

### Removed
- The temporary acceptance normalization gate that downgraded provider failures after the fact; release/provider scope is now separated before execution.

## [0.0.1] - 2026-09-07

### Added
- Initial GitHub repository, MIT license and Python `.gitignore`.
- Research-first repository architecture.
- Initial source repository comparison matrix.
- Provider-neutral model profile and routing policy drafts.
- Delegation, context, escalation and verification policies.
- Core agent contract schema and result contract schema.
- Repository structure validator and CI workflow.
