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
- One-command PowerShell acceptance wrapper and cross-platform Python acceptance harness.
- Disposable live acceptance sandbox covering Scout read-only, direct-first, and Implementer bounded-write behavior.
- Optional extended live coverage for Researcher, Debugger, Test Engineer, Reviewer, and Architect.
- Observable `collab_agent_tool_call` / `spawn_agent` telemetry normalization for child model, reasoning, and role metadata when exposed by Codex.
- Offline Windows GitHub Actions acceptance job.

### Changed
- Repository comparison matrix remains the source-of-truth list for acknowledged research inputs.
- `config/model-profiles.yaml` uses `gpt-5.6-sol` for the critical candidate while retaining Astra as benchmark-only.
- Scout and researcher retain the Luna cost tier but use medium reasoning as the current quality-floor candidate.
- Context budgeting is adaptive across input context, work budget, and result budget rather than a hard total-token quota.
- Project-scoped installation can now install/refresh only the managed Engineering Agent Stack block inside an existing `AGENTS.md`.
- README now makes Windows + Codex project-scoped acceptance the primary quick-start path and retains explicit upstream acknowledgements.
- CI now asserts synthetic subagent-spawn telemetry, project parent instructions, and Windows offline acceptance.
- v0.1 release gating now depends on a real Windows Codex live acceptance run rather than adding more agent prompts.

## [0.0.1] - 2026-09-07

### Added
- Initial GitHub repository, MIT license and Python `.gitignore`.
- Research-first repository architecture.
- Initial source repository comparison matrix.
- Provider-neutral model profile and routing policy drafts.
- Delegation, context, escalation and verification policies.
- Core agent contract schema and result contract schema.
- Repository structure validator and CI workflow.
