# Research

This directory records the evidence behind the stack's design decisions.

## Evaluation dimensions

Each source repository is assessed on:

1. agent taxonomy
2. role contract
3. delegation policy
4. routing
5. model/reasoning selection
6. context management
7. concurrency
8. write ownership
9. verification
10. escalation
11. cost control
12. portability

## Decision vocabulary

- **ADOPT** — use the pattern with minimal conceptual change.
- **ADAPT** — preserve the idea but change the implementation for this stack.
- **EXPERIMENT** — plausible; requires benchmark/eval evidence.
- **REJECT** — incompatible with the project's efficiency, safety or maintainability goals.

## Important distinction

Research notes describe patterns, not copied prompts. Source repositories retain their own licenses and authorship. When implementation code or text is ever reused, its license obligations must be reviewed explicitly.

See [`matrix/repository-comparison.yaml`](matrix/repository-comparison.yaml) for the living comparison.

The [v0.6 Research & Architecture Audit](v0.6/README.md) has a **completed research checkpoint (implementation not started)** covering Skills, Rules, Config, Presets, and declarative Extensions. Its recommendations are not implemented.
