# Repository Agent Contract

This repository designs reusable engineering agents. Changes must preserve the distinction between **role**, **compute profile**, **provider**, **execution policy**, and **provenance**.

## Working rules

- Inspect relevant files before editing.
- Prefer the smallest coherent change.
- Do not copy third-party prompts wholesale; extract concepts and cite the source repository in research notes.
- If material is directly adapted or vendored, check the upstream license and record provenance before merging.
- Treat model names and tool configuration as replaceable implementation details, not role identity.
- Do not add a new agent when an existing role plus a skill/policy can express the need.
- Do not claim benchmark superiority without recorded evidence.
- Keep provider-neutral contracts under `agents/`, `policies/`, `schemas/`, and `config/`; provider-specific behavior belongs under `adapters/`.
- Keep generated provider artifacts traceable to their canonical local source and generator.

## Research changes

A repository study should record:

1. What problem the source solves.
2. Useful patterns.
3. Risks/limitations.
4. ADOPT / ADAPT / EXPERIMENT / REJECT decisions.
5. Which local design artifact is affected.
6. Acknowledgement/provenance updates when the source is new or material is reused directly.

## Agent changes

Every production role must define:

- mission and non-goals
- read/write boundary
- expected inputs
- bounded output contract
- escalation conditions
- completion evidence
- compatible compute profiles

## Validation

Before declaring a change complete, run the relevant checks:

```bash
python scripts/validate_structure.py
python scripts/validate_provenance.py
python scripts/validate_agents.py
python scripts/evaluate_routing.py
python scripts/validate_task_suite.py
python scripts/validate_benchmarks.py
python scripts/generate_codex_adapter.py --check
```

## Safety and quality

- Independent review is required for high-risk or release-critical behavior.
- Concurrent writers must have disjoint write scopes.
- Child agents should not recursively orchestrate unless an explicit workflow contract allows it.
- Raw logs, full transcripts, and entire source trees should not be returned when concise evidence is sufficient.
- Adaptive token/context budgets may reduce waste but must not suppress evidence required for correctness or safety.
