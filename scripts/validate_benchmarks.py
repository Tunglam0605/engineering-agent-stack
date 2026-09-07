#!/usr/bin/env python3
"""Validate benchmark/evaluation metadata and guard against premature claims."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "benchmark-record.yaml"
PLAN_PATH = ROOT / "benchmarks" / "experiment-plan.yaml"
MODEL_PROFILES_PATH = ROOT / "config" / "model-profiles.yaml"
TASK_INDEX_PATH = ROOT / "benchmarks" / "tasks" / "index.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return value


def main() -> int:
    try:
        schema = load_yaml(SCHEMA_PATH)
        plan = load_yaml(PLAN_PATH)
        profiles = load_yaml(MODEL_PROFILES_PATH)
        task_index = load_yaml(TASK_INDEX_PATH)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 2

    failures: list[str] = []

    required_fields = schema.get("required_fields", [])
    if not isinstance(required_fields, list) or len(required_fields) < 8:
        failures.append("benchmark record schema must define a non-trivial required_fields list")

    indexed_tasks = task_index.get("tasks", [])
    if not isinstance(indexed_tasks, list):
        failures.append("controlled task index must contain a tasks list")
        known_task_ids: set[str] = set()
    else:
        known_task_ids = {str(item["id"]) for item in indexed_tasks if isinstance(item, dict) and isinstance(item.get("id"), str)}

    experiments = plan.get("experiments", [])
    if not isinstance(experiments, list) or not experiments:
        failures.append("benchmark plan must contain at least one experiment")
    else:
        seen: set[str] = set()
        known_profiles = set(profiles.get("profiles", {}))
        for experiment in experiments:
            if not isinstance(experiment, dict):
                failures.append("every experiment must be a mapping")
                continue
            exp_id = experiment.get("id")
            if not isinstance(exp_id, str) or not exp_id:
                failures.append("every experiment must have a non-empty id")
                continue
            if exp_id in seen:
                failures.append(f"duplicate experiment id: {exp_id}")
            seen.add(exp_id)

            candidates = experiment.get("candidates", [])
            measures = experiment.get("measures", [])
            task_ids = experiment.get("task_ids", [])
            if not isinstance(candidates, list) or len(candidates) < 2:
                failures.append(f"{exp_id}: requires at least two candidates")
            if not isinstance(measures, list) or "quality_score" not in measures:
                failures.append(f"{exp_id}: quality_score must be measured")
            if not isinstance(task_ids, list) or not task_ids:
                failures.append(f"{exp_id}: must reference at least one controlled task")
            else:
                for task_id in task_ids:
                    if task_id not in known_task_ids:
                        failures.append(f"{exp_id}: unknown controlled task {task_id!r}")

            context_topologies = {"full-context", "bounded-context-packet"}
            observed_context_topologies = {
                str(candidate.get("topology"))
                for candidate in candidates
                if isinstance(candidate, dict) and candidate.get("topology") in context_topologies
            } if isinstance(candidates, list) else set()
            if observed_context_topologies:
                if observed_context_topologies != context_topologies:
                    failures.append(
                        f"{exp_id}: context experiment must compare full-context and bounded-context-packet"
                    )
                for measure in ("context_size_chars", "token_proxy"):
                    if measure not in measures:
                        failures.append(f"{exp_id}: context experiment must measure {measure}")

            for candidate in candidates if isinstance(candidates, list) else []:
                if not isinstance(candidate, dict):
                    failures.append(f"{exp_id}: candidate must be a mapping")
                    continue
                profile = candidate.get("profile")
                if profile is not None and profile not in known_profiles:
                    failures.append(f"{exp_id}: unknown semantic profile {profile!r}")

    acceptance = plan.get("acceptance", {})
    if acceptance.get("no_default_change_from_single_run") is not True:
        failures.append("benchmark acceptance must forbid default changes from a single run")
    repetitions = acceptance.get("min_repetitions_per_task", 0)
    if not isinstance(repetitions, int) or repetitions < 3:
        failures.append("min_repetitions_per_task must be at least 3")

    if failures:
        print(f"FAIL: {len(failures)} benchmark contract problem(s).")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS: benchmark contract valid with {len(experiments)} planned experiment(s) and {len(known_task_ids)} controlled task(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
