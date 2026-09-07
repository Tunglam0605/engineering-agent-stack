# Benchmark Results

This directory is reserved for **real, reproducible benchmark outputs**.

Do not commit a file here as evidence unless every run records:

- the exact stack commit
- case and case version
- provider/model/reasoning
- token counts and latency
- quality score and threshold
- validation outcome
- whether the record is synthetic
- enough task/environment provenance to reproduce the run

Synthetic examples belong in `../fixtures/`, never here.

## Naming

Recommended:

```text
YYYY-MM-DD_<campaign>_<provider>.jsonl
```

Example:

```text
2026-09-10_core-routing-screening_openai.jsonl
```

## Interpretation

A cheaper model is not a winner merely because it costs less. Reject any variant below the required quality threshold first. Compare cost/latency only among quality-qualified contenders, then confirm over repeated runs before changing defaults.
