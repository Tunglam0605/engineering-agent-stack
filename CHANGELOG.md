# Changelog

All notable project changes will be documented here.

## [Unreleased]

### Added
- Research Wave 2 analysis covering OpenAI Agents SDK, Microsoft Agent Framework, AutoGen, LangGraph, Deep Agents, CrewAI, smolagents and OpenHands.
- Authoritative `openai/codex` implementation/public-contract research note.
- Current official Codex subagent and OpenAI model-palette source notes.
- Research Wave 2 synthesis and over-orchestration anti-pattern guidance.
- Seven provider-neutral core role definitions.
- Semantic core-agent contract validator.
- Executable deterministic routing-policy evaluator.
- Deterministic Codex adapter generator with `--check` drift mode.
- Codex role-to-semantic-profile mapping separate from canonical roles.
- Development dependency manifest for YAML-based validation/generation.
- Normalized benchmark/run-capture contracts and Codex JSONL capture pipeline.
- `controlled-v1` benchmark suite with scout, implementer, reviewer and trivial-orchestration tasks.
- Deterministic text-evidence and command/test task graders.
- Controlled workspace materializer that generates concrete Codex run manifests.
- Safe Codex installer with project/personal scope, dry-run, drift check, conflict refusal, and backup-on-force behavior.
- `ACKNOWLEDGEMENTS.md` with explicit credit to all repositories currently in the research matrix.
- `docs/PROVENANCE.md` defining conceptual, adapted, vendored, and generated-material provenance classes.
- Provenance validator that ensures all research-matrix repositories are acknowledged.
- Dedicated Codex installation guide.
- CI coverage for provenance, installer, controlled task validation, preparation, grading, capture, and adapter drift.

### Changed
- Repository comparison matrix remains the source-of-truth list for acknowledged research inputs.
- `config/model-profiles.yaml` uses the explicit `gpt-5.6-sol` model ID for the critical candidate while retaining Astra as benchmark-only.
- Codex adapter follows current public standalone custom-agent discovery rather than internal/undocumented role-registration mechanisms.
- Scout and researcher keep the Luna cost tier but default to medium reasoning in the Codex adapter as a quality floor.
- Routing fixtures contain explicit classified signals; policy routing and natural-language classifier evaluation are separated.
- Benchmark experiments reference concrete controlled task IDs.
- Context budgeting is now explicitly adaptive across input context, work budget, and result budget instead of being interpreted as a hard total-token quota.
- README now documents upstream research lineage, thanks, attribution rules, installation flow, and current benchmark status.
- Contribution and repository-agent rules now require license-aware provenance for directly adapted or vendored third-party material.
- Roadmap marks the Codex installer/provenance gates complete and real project smoke testing/repeated real runs as the next release gates.

## [0.0.1] - 2026-09-07

### Added
- Initial GitHub repository, MIT license and Python `.gitignore`.
- Research-first repository architecture.
- Initial source repository comparison matrix.
- Provider-neutral model profile and routing policy drafts.
- Delegation, context, escalation and verification policies.
- Core agent contract schema and result contract schema.
- Repository structure validator and CI workflow.
