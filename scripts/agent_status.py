#!/usr/bin/env python3
"""Render a lightweight Engineering Agent Stack status snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.registry import AgentRegistry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON status snapshot")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--summary", action="store_true", help="include goal fan-out summary")
    parser.add_argument("--soft-limit", type=int, default=6)
    parser.add_argument("--hard-limit", type=int, default=8)
    parser.add_argument("--goal-id", help="parent assignment id to summarize when snapshot contains multiple goals")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("status snapshot root must be an object")
        registry = AgentRegistry.from_dict(payload)
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    try:
        if args.format == "json":
            if args.summary:
                body = registry.as_dict()
                body["summary"] = registry.summary(
                    soft_limit=args.soft_limit, hard_limit=args.hard_limit, goal_id=args.goal_id
                )
                print(json.dumps(body, sort_keys=True, separators=(",", ":")))
            else:
                print(registry.to_json())
        else:
            text = registry.to_text()
            if text:
                print(text)
            if args.summary:
                print(
                    registry.summary_text(
                        soft_limit=args.soft_limit, hard_limit=args.hard_limit, goal_id=args.goal_id
                    )
                )
    except ValueError as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
