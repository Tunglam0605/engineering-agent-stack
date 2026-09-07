# Benchmarks

Benchmarks answer a different question from evals:

- **Evals:** did the role/routing/model meet the required engineering quality?
- **Benchmarks:** what token, latency and normalized/actual cost was required to reach that quality?

The repository never treats lower cost as a win when quality falls below the case threshold.

## Current benchmark foundation

```text
experiment-plan.yaml                  comparison matrix + quality rubrics
pricing/openai-2026-09-07.yaml        point-in-time normalized cost proxy
fixtures/sample-results.jsonl         synthetic harness-only records
results/README.md                      rules for real result provenance
schemas/benchmark-result.yaml         benchmark-result-v1 contract
scripts/validate_benchmarks.py        plan/schema/fixture validator
scripts/benchmark_report.py           quality-gated aggregate report
docs/BENCHMARKING.md                   experimental protocol
```

## Run the harness checks

```bash
python scripts/validate_benchmarks.py
python scripts/benchmark_report.py \
  benchmarks/fixtures/sample-results.jsonl \
  --allow-synthetic
```

The sample JSONL is deliberately synthetic. It proves the math and aggregation paths work; it is not evidence that one model is better than another.

## Real-run record

A real JSONL row records, at minimum:

```text
run identity + timestamp + stack commit
case/version + variant
provider/model/reasoning
input/output tokens
latency
quality score + threshold
validation result
synthetic=false
```

Optional fields may capture actual billed cost, tool-call count, delegated-agent count, peak parallelism, task fingerprints and environment metadata.

## Cost basis

When `actual_cost_usd` is unavailable, the report estimates a **normalized API list-price cost** from the dated pricing snapshot. This is a comparison proxy, not a claim about ChatGPT/Codex subscription billing.

Do not compare runs using a stale pricing snapshot without documenting that choice.

## Decision policy

A candidate progresses in two stages:

1. **Screening** — small repeat count to reject clear quality failures without overspending.
2. **Confirmation** — larger repeat count only for contenders that passed screening.

No script auto-promotes a default. Human/maintainer review must confirm the quality evidence, failure modes and cost/latency trade-off.

See [`docs/BENCHMARKING.md`](../docs/BENCHMARKING.md).
