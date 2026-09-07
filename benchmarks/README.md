# Benchmarks

Benchmarks compare compute profiles and orchestration choices under repeatable tasks.

## Measurement pipeline

```text
task manifest
   |
   v
Codex/provider run
   |
   v
run capture
(tokens + latency + outcome)
   |
   v
quality grading
   |
   v
benchmark record
   |
   v
candidate summary / routing decision
```

Provider execution and quality grading are separate responsibilities. A capture is not eligible for model/routing promotion until quality is scored.

## Current Codex flow

Create or copy a run manifest:

```bash
cp benchmarks/run-manifest.example.yaml /tmp/run.yaml
```

Dry-run the command:

```bash
python scripts/capture_codex_exec.py --manifest /tmp/run.yaml --dry-run
```

Execute and capture locally:

```bash
python scripts/capture_codex_exec.py --manifest /tmp/run.yaml
```

Local raw runs are written under `benchmarks/local-runs/` and are ignored by Git.

After independent quality grading:

```bash
python scripts/promote_run_capture.py benchmarks/local-runs/<run>/capture.json \
  --score 0.98 \
  --threshold 0.95 \
  --grader targeted-tests+review \
  --output /tmp/benchmark-results.jsonl \
  --append

python scripts/summarize_benchmarks.py /tmp/benchmark-results.jsonl
```

## Key experiments

- Luna vs Terra for repository scanning
- Terra medium vs high for implementation/debugging
- Terra high vs Sol high for review on high-risk cases
- single-agent vs delegated discovery
- full-context vs bounded-context delegation
- generic core role vs domain specialist

No default routing change should be justified by cost alone if quality falls below the task threshold. At least three repetitions per task/candidate are required before changing defaults.
