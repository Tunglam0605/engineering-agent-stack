# Evaluations

Evals measure correctness and routing quality independently from token cost.

## Two separate routing questions

This project intentionally separates:

1. **Task classification** — can an agent convert a natural-language request into reliable structured signals?
2. **Policy routing** — given those signals, does the deterministic policy choose the expected direct/delegate/role/profile path?

`routing-cases.yaml` currently tests **policy routing only**. This prevents a weak keyword classifier from being confused with a routing-policy regression.

Run:

```bash
python scripts/evaluate_routing.py
```

## Current suites

- deterministic direct-vs-delegate policy routing ✅
- over-delegation regression fixtures ✅
- risk-based role/profile escalation fixtures ✅

## Planned suites

- natural-language task classification accuracy
- repository discovery accuracy
- call-flow tracing
- ordinary bug root cause
- concurrency/realtime bug analysis
- implementation correctness
- independent review defect detection
- context-compression fidelity
- escalation precision/recall

Results should report **quality first**. Token/cost/latency measurements belong under `benchmarks/` and must not justify a default that falls below the required quality threshold.
