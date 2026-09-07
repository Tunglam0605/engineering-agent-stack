# KevinBigham/codex-safe-starter

Source: https://github.com/KevinBigham/codex-safe-starter

## Focus

Portable, Git-backed safer Codex operating layer with read-only agents, setup checks, smoke validation and staged evaluation.

## Useful patterns

- Read-only exploration/review roles by default.
- Use the narrowest relevant validation before completion.
- Small, reversible changes with explicit security and rollback boundaries.
- Project-local configuration rather than casually mutating global state.

## Decisions

- **ADOPT:** narrow validation, read-only reviewer/explorer posture and reversible setup.
- **ADAPT:** smoke/eval concepts into provider-neutral repository checks.
