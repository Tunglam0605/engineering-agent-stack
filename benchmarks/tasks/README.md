# Controlled Benchmark Tasks

`controlled-v1` is the first repeatable task suite for comparing model/reasoning tiers without depending on a large external repository.

Each task contains:

```text
task.yaml
prompt.md
workspace/
```

Read-only tasks use deterministic evidence checks. Write tasks use executable tests wherever practical.

## Workflow

Prepare a clean workspace and concrete run manifest:

```bash
python scripts/prepare_benchmark_task.py \
  --task-id scout-symbol-001 \
  --experiment-id scout-luna-vs-terra \
  --model gpt-5.6-luna \
  --reasoning-effort medium \
  --profile cheap
```

Run Codex using the generated `manifest.yaml`, then grade the result:

```bash
python scripts/capture_codex_exec.py --manifest <prepared>/manifest.yaml

python scripts/grade_benchmark_task.py \
  --task-id scout-symbol-001 \
  --last-message <run>/last-message.txt \
  --capture <run>/capture.json
```

For write tasks, pass the materialized workspace to the grader:

```bash
python scripts/grade_benchmark_task.py \
  --task-id implementer-bounded-bug-001 \
  --workspace <prepared>/workspace
```

The task suite is intentionally small. New tasks should be added only when they improve coverage of a real routing/model decision.
