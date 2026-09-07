#!/usr/bin/env python3
"""Promote a measured run capture into a quality-scored benchmark JSONL record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REQUIRED_CAPTURE = (
    "capture_id",
    "experiment_id",
    "task_id",
    "provider",
    "model",
    "reasoning_effort",
    "role",
    "profile",
    "latency_ms",
    "usage",
    "outcome",
)


def load_capture(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("capture must be a JSON object")
    missing = [field for field in REQUIRED_CAPTURE if field not in value]
    if missing:
        raise ValueError(f"capture missing fields: {', '.join(missing)}")
    usage = value["usage"]
    if not isinstance(usage, dict):
        raise ValueError("capture usage must be an object")
    for field in ("input_tokens", "output_tokens"):
        if not isinstance(usage.get(field), int) or usage[field] < 0:
            raise ValueError(f"capture usage.{field} must be a non-negative integer")
    return value


def build_record(
    capture: dict[str, Any],
    *,
    score: float,
    threshold: float,
    grader: str | None,
    notes: str | None,
) -> dict[str, Any]:
    if not 0.0 <= score <= 1.0:
        raise ValueError("quality score must be in [0, 1]")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("quality threshold must be in [0, 1]")

    passed = score >= threshold and capture["outcome"] == "completed"
    record: dict[str, Any] = {
        "experiment_id": capture["experiment_id"],
        "task_id": capture["task_id"],
        "provider": capture["provider"],
        "model": capture["model"],
        "reasoning_effort": capture["reasoning_effort"],
        "role": capture["role"],
        "profile": capture["profile"],
        "quality": {
            "score": round(score, 6),
            "threshold": round(threshold, 6),
            "passed": passed,
        },
        "latency_ms": capture["latency_ms"],
        "usage": capture["usage"],
        "outcome": capture["outcome"],
        "capture_id": capture["capture_id"],
    }
    for field in ("topology", "thread_id", "event_summary", "environment"):
        if field in capture:
            record[field] = capture[field]
    if grader:
        record["quality"]["grader"] = grader
    if notes:
        record["quality"]["notes"] = notes
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("--score", type=float, required=True)
    parser.add_argument("--threshold", type=float)
    parser.add_argument("--grader")
    parser.add_argument("--notes")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    try:
        capture = load_capture(args.capture)
        threshold = args.threshold
        if threshold is None:
            threshold = float(capture.get("quality_threshold", 1.0))
        record = build_record(
            capture,
            score=args.score,
            threshold=threshold,
            grader=args.grader,
            notes=args.notes,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if args.append else "w"
        with args.output.open(mode, encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        print(
            f"WROTE: {args.output}; quality={record['quality']['score']:.3f} "
            f"threshold={record['quality']['threshold']:.3f} "
            f"passed={record['quality']['passed']}"
        )
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
