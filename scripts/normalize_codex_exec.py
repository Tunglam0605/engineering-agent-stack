#!/usr/bin/env python3
"""Normalize an existing `codex exec --json` event stream into a run capture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import yaml

from codex_capture_lib import build_capture, parse_codex_events


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: manifest must be a YAML mapping")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True, help="Codex exec JSONL file")
    parser.add_argument("--manifest", type=Path, required=True, help="Run metadata YAML")
    parser.add_argument("--latency-ms", type=float, required=True)
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--started-at")
    parser.add_argument("--finished-at")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        meta = load_manifest(args.manifest)
        summary = parse_codex_events(args.events)
        capture = build_capture(
            meta,
            summary,
            latency_ms=args.latency_ms,
            exit_code=args.exit_code,
            started_at=args.started_at,
            finished_at=args.finished_at,
            artifacts={"raw_events": str(args.events)},
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(capture, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"WROTE: {args.output}")
        print(
            f"usage: input={capture['usage']['input_tokens']} "
            f"output={capture['usage']['output_tokens']} "
            f"latency_ms={capture['latency_ms']} outcome={capture['outcome']}"
        )
        return 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
