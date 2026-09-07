# Benchmarks

Benchmarks compare compute profiles and orchestration choices under repeatable tasks.

Minimum normalized record:

```text
experiment_id
task_id
role / workflow
provider + model
reasoning tier
input tokens
output tokens
latency
estimated cost (optional)
quality score
pass/fail
notes
```

Key experiments:

- Luna vs Terra for repository scanning
- Terra medium vs high for implementation/debugging
- Terra high vs Sol high for review on high-risk cases
- single-agent vs delegated discovery
- direct vs delegated trivial work
- full-context vs bounded-context delegation
- generic core role vs domain specialist

No default routing change should be justified by cost alone if quality falls below the task threshold.

## Controlled task suite

`benchmarks/tasks/index.yaml` defines the initial `controlled-v1` suite. It currently covers:

- `scout-symbol-001` — read-only call-flow tracing
- `implementer-bounded-bug-001` — minimal code fix with executable tests
- `reviewer-regression-001` — seeded correctness regressions
- `orchestrator-trivial-edit-001` — direct-vs-delegated overhead baseline

Task fixtures are intentionally small and synthetic so repeated model comparisons measure the model/routing choice rather than unrelated repository noise.

Validate them with:

```bash
python scripts/validate_task_suite.py
```

Materialize a clean run workspace with:

```bash
python scripts/prepare_benchmark_task.py \
  --task-id scout-symbol-001 \
  --experiment-id scout-luna-vs-terra \
  --model gpt-5.6-luna \
  --reasoning-effort medium \
  --profile cheap
```

Then use the generated manifest with the Codex capture pipeline.

## Raw run capture

Real Codex executions should be captured with `codex exec --json` through:

```bash
python scripts/capture_codex_exec.py --manifest <manifest.yaml>
```

Provider traces and working copies stay under `benchmarks/local-runs/` and are git-ignored. After independent quality grading, promote only the normalized record required for comparison.

## Grading

Controlled tasks use deterministic graders where possible:

- `text_evidence`: final answer must contain required evidence
- `command`: modified workspace must pass a deterministic command/test suite

Run:

```bash
python scripts/grade_benchmark_task.py \
  --task-id <task-id> \
  --last-message <last-message.txt>
```

or, for write tasks:

```bash
python scripts/grade_benchmark_task.py \
  --task-id <task-id> \
  --workspace <materialized-workspace>
```

The resulting quality score is evaluated before tokens, latency, or cost.
