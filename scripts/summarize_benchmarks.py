#!/usr/bin/env python3
"""Summarize normalized benchmark JSONL records without provider SDK dependencies."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys
from typing import Any


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: record must be an object")
            records.append(value)
    return records


def validate_record(record: dict[str, Any], index: int) -> None:
    for key in ["experiment_id", "task_id", "provider", "model", "reasoning_effort", "role", "profile", "quality", "latency_ms", "usage", "outcome"]:
        if key not in record:
            raise ValueError(f"record {index}: missing {key}")
    quality = record["quality"]
    usage = record["usage"]
    if not isinstance(quality, dict) or not isinstance(usage, dict):
        raise ValueError(f"record {index}: quality and usage must be objects")
    for key in ["score", "threshold", "passed"]:
        if key not in quality:
            raise ValueError(f"record {index}: quality missing {key}")
    for key in ["input_tokens", "output_tokens"]:
        if key not in usage:
            raise ValueError(f"record {index}: usage missing {key}")


def candidate_key(record: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(record["model"]),
        str(record["reasoning_effort"]),
        str(record["role"]),
        str(record["profile"]),
    )


def summarize(records: list[dict[str, Any]]) -> int:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for index, record in enumerate(records, start=1):
        validate_record(record, index)
        groups[candidate_key(record)].append(record)

    print("| Model | Effort | Role | Profile | Runs | Quality pass | Mean quality | Mean tokens | Mean latency ms |")
    print("|---|---|---|---|---:|---:|---:|---:|---:|")

    for key in sorted(groups):
        model, effort, role, profile = key
        rows = groups[key]
        quality_scores = [float(row["quality"]["score"]) for row in rows]
        quality_passes = [bool(row["quality"]["passed"]) for row in rows]
        tokens = [int(row["usage"]["input_tokens"]) + int(row["usage"]["output_tokens"]) for row in rows]
        latency = [float(row["latency_ms"]) for row in rows]
        pass_rate = sum(quality_passes) / len(quality_passes)
        print(
            f"| {model} | {effort} | {role} | {profile} | {len(rows)} | "
            f"{pass_rate:.0%} | {statistics.mean(quality_scores):.3f} | "
            f"{statistics.mean(tokens):.0f} | {statistics.mean(latency):.0f} |"
        )

    failing = [row for row in records if not bool(row["quality"]["passed"])]
    print()
    print(f"Records: {len(records)}; quality-gate failures: {len(failing)}")
    if failing:
        print("Cost/latency comparisons must not promote candidates that fail their task quality threshold.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records", type=Path, help="JSONL file containing normalized benchmark records")
    args = parser.parse_args()

    try:
        records = load_records(args.records)
        if not records:
            raise ValueError("no benchmark records found")
        return summarize(records)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
