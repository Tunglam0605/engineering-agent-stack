# Changelog

All notable project changes will be documented here.

## [Unreleased]

### Added
- Research Wave 2 analysis covering OpenAI Agents SDK, Microsoft Agent Framework, AutoGen, LangGraph, Deep Agents, CrewAI, smolagents and OpenHands.
- Authoritative `openai/codex` implementation/public-contract research note.
- Current official Codex subagent, exec JSONL, and OpenAI model-palette source notes.
- Research Wave 2 synthesis and over-orchestration anti-pattern guidance.
- Seven provider-neutral core role definitions.
- Semantic core-agent contract validator.
- Executable deterministic routing-policy evaluator.
- Deterministic Codex adapter generator with `--check` drift mode.
- Codex role-to-semantic-profile mapping separate from canonical roles.
- Development dependency manifest for YAML-based validation/generation.
- Pre-grade run-capture schema that separates provider measurement from quality scoring.
- Codex `exec --json` parser and local benchmark capture wrapper.
- Capture-to-benchmark promotion tool with explicit quality threshold.
- Synthetic CI fixture covering capture, promotion, and benchmark summarization.

### Changed
- Repository comparison matrix expanded to fifteen sources.
- `config/model-profiles.yaml` uses the explicit `gpt-5.6-sol` model ID for the critical candidate while retaining Astra as benchmark-only.
- Codex adapter follows current public standalone custom-agent discovery rather than internal/undocumented role-registration mechanisms.
- Scout and researcher keep the Luna cost tier but default to medium reasoning in the Codex adapter as a quality floor.
- Routing fixtures contain explicit classified signals; policy routing and natural-language classifier evaluation are separated.
- CI validates structure, canonical agent semantics, routing policy, benchmark contracts, capture pipeline, and generated-adapter drift.
- Local raw benchmark traces are ignored by Git; only sanitized fixtures and normalized/promoted records should be committed intentionally.
- Roadmap marks the v0.1 core infrastructure as candidate-complete and v0.2 efficiency work as active.

## [0.0.1] - 2026-09-07

### Added
- Initial GitHub repository, MIT license and Python `.gitignore`.
- Research-first repository architecture.
- Initial source repository comparison matrix.
- Provider-neutral model profile and routing policy drafts.
- Delegation, context, escalation and verification policies.
- Core agent contract schema and result contract schema.
- Repository structure validator and CI workflow.
