# Evaluation and Benchmarking

The stack separates **quality evaluation** from **efficiency benchmarking**.

## Rule 1: quality gate first

A cheaper route is not better if it fails the required engineering quality threshold.

```text
candidate run
   |
   +--> quality < threshold ----> reject
   |
   +--> quality >= threshold ---> compare cost / latency / token usage
```

This prevents cost optimization from silently degrading correctness.

## Evaluation layers

### Policy routing evals

`evals/routing-cases.yaml` checks deterministic behavior after task signals have already been classified. It answers questions such as:

- should this task be direct or delegated?
- which role/profile should receive it?
- is independent review required?

It does **not** measure natural-language classification quality.

### Natural-language routing evals

Planned for v0.2. These will evaluate whether an orchestrator can infer the correct task shape, risk and uncertainty signals from realistic user tasks without over-delegating.

### Role quality evals

Each role is measured against task-family-specific quality criteria. Examples:

- scout: discovery accuracy and call-flow correctness
- implementer: behavior correctness and targeted-test success
- reviewer: defect recall and false-positive rate
- architect: constraint coverage, trade-off quality and critical-risk detection

## Benchmark records

Normalized experiment runs should conform to `schemas/benchmark-record.yaml` and capture at minimum:

- experiment/task identity
- provider/model/reasoning setting
- role and semantic compute profile
- quality score + threshold
- latency
- input/output token usage
- outcome

Provider price is intentionally optional because prices change. Cost can be derived later from a dated pricing snapshot without corrupting the raw usage record.

## Experiment discipline

The first planned experiments live in `benchmarks/experiment-plan.yaml`.

Rules:

1. Compare at least two candidates.
2. Repeat every task at least three times before changing a default.
3. Never promote a routing/model change from one anecdotal run.
4. Record model/version/environment when available.
5. Prefer the lowest compute tier that consistently clears the required quality threshold.
6. Keep critical/realtime/security/release tasks on stricter quality gates even if average cost is higher.

## Efficiency objective

The conceptual objective is:

```text
maximize quality / (cost * latency)
subject to quality >= task threshold
```

In practice, no single scalar should hide failures. Reports should show quality, tokens, latency, agent count and cost separately before any aggregate score is used.

## Current stage

The repository currently has deterministic policy evals and an experiment contract. Real Codex run capture and model-tier benchmark results are the next v0.2 milestone.
