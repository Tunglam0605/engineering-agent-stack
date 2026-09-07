#!/usr/bin/env python3
"""Validate controlled benchmark suite metadata and fixtures."""

from __future__ import annotations

import sys

from benchmark_task_lib import load_task, task_entries, validate_task, TASKS_ROOT


def main() -> int:
    failures: list[str] = []
    seen_ids: set[str] = set()
    entries = task_entries()

    if len(entries) < 4:
        failures.append("controlled suite must contain at least four tasks")

    for entry in entries:
        task_id = entry.get("id")
        rel = entry.get("path")
        if not isinstance(task_id, str) or not task_id:
            failures.append("task index entry has invalid id")
            continue
        if task_id in seen_ids:
            failures.append(f"duplicate task id in index: {task_id}")
        seen_ids.add(task_id)
        if not isinstance(rel, str) or not rel:
            failures.append(f"{task_id}: invalid task path")
            continue

        task_path = TASKS_ROOT / rel
        if not task_path.is_file():
            failures.append(f"{task_id}: missing task file {task_path}")
            continue

        task = load_task(task_path)
        if task.get("id") != task_id:
            failures.append(f"{task_id}: index id does not match task id {task.get('id')!r}")
        failures.extend(validate_task(task))

    if failures:
        print(f"FAIL: {len(failures)} controlled-task problem(s).")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS: controlled benchmark suite contains {len(entries)} valid task(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
