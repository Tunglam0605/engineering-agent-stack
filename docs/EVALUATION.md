# Evaluation and Benchmarking

The stack separates **quality evaluation** from **efficiency benchmarking** and now also separates **provider measurement** from **quality grading**.

## Rule 1: quality gate first

A cheaper route is not better if it fails the required engineering quality threshold.

```text
provider run
   |
   v
usage/latency capture
   |
   v
quality grading
   |
   +--> quality < threshold ----> reject
   |
   +--> quality >= threshold ---> compare cost / latency / token usage
```

This prevents cost optimization from silently degrading correctness and prevents the runtime capture layer from inventing a quality score.

## Evaluation layers

### Policy routing evals

`evals/routing-cases.yaml` checks deterministic behavior after task signals have already been classified. It answers:

- direct or delegated?
- which role/profile?
- is independent review required?

It does **not** measure natural-language classification quality.

### Natural-language routing evals

Planned for v0.2. These evaluate whether an orchestrator infers the correct task shape, risk and uncertainty from realistic tasks without over-delegating.

### Role quality evals

Each role is measured against task-family-specific criteria:

- scout: discovery accuracy and call-flow correctness
- implementer: behavior correctness and targeted-test success
- reviewer: defect recall and false-positive rate
- architect: constraint coverage, trade-off quality and critical-risk detection

## Two-stage measurement pipeline

### Stage A — run capture

`schemas/run-capture.yaml` is provider-measurement evidence before grading.

For current Codex CLI builds:

```bash
python scripts/capture_codex_exec.py \
  --manifest benchmarks/run-manifest.example.yaml
```

The runner executes `codex exec --json --ephemeral`, measures wall-clock latency, parses the public JSONL usage events and writes a local `capture.json` plus raw artifacts under `benchmarks/local-runs/`.

Raw run directories are git-ignored by default.

Existing JSONL can also be normalized without launching Codex:

```bash
python scripts/normalize_codex_exec.py \
  --events path/to/events.jsonl \
  --manifest benchmarks/run-manifest.example.yaml \
  --latency-ms 1234 \
  --output /tmp/capture.json
```

### Stage B — quality promotion

A capture becomes a benchmark record only after quality is graded:

```bash
python scripts/promote_run_capture.py /tmp/capture.json \
  --score 0.98 \
  --threshold 0.95 \
  --grader targeted-tests+review \
  --output /tmp/results.jsonl
```

Then summarize candidate performance:

```bash
python scripts/summarize_benchmarks.py /tmp/results.jsonl
```

## Benchmark records

Promoted experiment runs conform to `schemas/benchmark-record.yaml` and capture at minimum:

- experiment/task identity
- provider/model/reasoning setting
- role and semantic compute profile
- quality score + threshold
- latency
- input/output token usage
- outcome

Provider price remains optional because prices change. Cost should be derived later from a dated pricing snapshot.

## Experiment discipline

The first planned experiments live in `benchmarks/experiment-plan.yaml`.

Rules:

1. Compare at least two candidates.
2. Repeat every task at least three times before changing a default.
3. Never promote a routing/model change from one anecdotal run.
4. Record model/version/environment when available.
5. Prefer the lowest compute tier that consistently clears the required quality threshold.
6. Keep critical/realtime/security/release tasks on stricter quality gates even if average cost is higher.
7. Keep raw traces local unless a sanitized fixture is intentionally created.
8. Treat runtime capture and quality grading as separate responsibilities.

## Efficiency objective

```text
maximize quality / (cost * latency)
subject to quality >= task threshold
```

No scalar score may hide failures. Reports should show quality, tokens, latency, agent count and cost separately before any aggregate score is used.

## Current stage

Deterministic routing, canonical role validation, generated Codex configuration, benchmark contracts and the Codex real-run capture pipeline are implemented. The next milestone is collecting repeated real runs for Luna/Terra/Sol comparisons and natural-language router evaluation.
