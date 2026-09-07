#!/usr/bin/env python3
"""Deterministically grade a controlled benchmark task result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from benchmark_task_lib import load_task, resolve_task_path


def text_checks(grader: dict[str, Any], text: str) -> list[dict[str, Any]]:
    lowered = text.lower()
    checks: list[dict[str, Any]] = []

    for needle in grader.get("required_all", []):
        passed = needle.lower() in lowered
        checks.append({"name": f"contains:{needle}", "passed": passed})

    for index, group in enumerate(grader.get("required_any_groups", []), start=1):
        passed = any(item.lower() in lowered for item in group)
        checks.append({"name": f"contains-any-group:{index}", "passed": passed, "candidates": group})

    for needle in grader.get("forbidden_any", []):
        passed = needle.lower() not in lowered
        checks.append({"name": f"forbids:{needle}", "passed": passed})
    return checks


def command_checks(grader: dict[str, Any], workspace: Path) -> list[dict[str, Any]]:
    command = grader["command"]
    timeout = float(grader.get("timeout_seconds", 30))
    result = subprocess.run(command, cwd=workspace, capture_output=True, text=True, check=False, timeout=timeout)
    return [{"name": "command-exit-zero", "passed": result.returncode == 0, "command": command, "exit_code": result.returncode, "stdout_tail": result.stdout[-2000:], "stderr_tail": result.stderr[-2000:]}]


def capture_checks(grader: dict[str, Any], capture_path: Path | None) -> list[dict[str, Any]]:
    if capture_path is None or "max_file_changes" not in grader:
        return []
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    summary = capture.get("event_summary", {})
    file_changes = summary.get("file_changes")
    maximum = int(grader["max_file_changes"])
    passed = isinstance(file_changes, int) and file_changes <= maximum
    return [{"name": "max-file-changes", "passed": passed, "actual": file_changes, "maximum": maximum}]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--last-message", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        task = load_task(resolve_task_path(args.task_id))
        grader = task["grader"]
        grader_type = grader["type"]

        checks: list[dict[str, Any]] = []
        if grader_type == "text_evidence":
            if args.last_message is None:
                raise ValueError("text_evidence grader requires --last-message")
            text = args.last_message.read_text(encoding="utf-8")
            checks.extend(text_checks(grader, text))
        elif grader_type == "command":
            if args.workspace is None or not args.workspace.is_dir():
                raise ValueError("command grader requires an existing --workspace")
            checks.extend(command_checks(grader, args.workspace))
        else:
            raise ValueError(f"unsupported grader type: {grader_type}")

        checks.extend(capture_checks(grader, args.capture))
        if not checks:
            raise ValueError("grader produced no checks")

        passed_count = sum(bool(check["passed"]) for check in checks)
        score = passed_count / len(checks)
        threshold = float(task["quality_threshold"])
        result = {"task_id": task["id"], "grader": grader_type, "quality": {"score": round(score, 6), "threshold": threshold, "passed": score >= threshold}, "checks": checks}

        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(payload, encoding="utf-8")
            print(f"WROTE: {args.output}")
        else:
            print(payload, end="")
        return 0 if result["quality"]["passed"] else 1

    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
