# Repository Agent Contract

This repository designs reusable engineering agents. Changes must preserve the distinction between **role**, **compute profile**, and **execution policy**.

## Working rules

- Inspect relevant files before editing.
- Prefer the smallest coherent change.
- Do not copy third-party prompts wholesale; extract concepts and cite the source repository in research notes.
- Treat model names and tool configuration as replaceable implementation details, not role identity.
- Do not add a new agent when an existing role plus a skill/policy can express the need.
- Do not claim benchmark superiority without recorded evidence.
- Keep provider-neutral contracts under `agents/`, `policies/`, `schemas/`, and `config/`; provider-specific behavior belongs under `adapters/`.

## Research changes

A repository study should record:

1. What problem the source solves.
2. Useful patterns.
3. Risks/limitations.
4. ADOPT / ADAPT / EXPERIMENT / REJECT decisions.
5. Which local design artifact is affected.

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

Before declaring a change complete:

```bash
python scripts/validate_structure.py
```

For future agent/runtime changes, also run the relevant evals and benchmarks once those harnesses exist.

## Safety and quality

- Independent review is required for high-risk or release-critical behavior.
- Concurrent writers must have disjoint write scopes.
- Child agents should not recursively orchestrate unless an explicit workflow contract allows it.
- Raw logs, full transcripts, and entire source trees should not be returned when concise evidence is sufficient.
