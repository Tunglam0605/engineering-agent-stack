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
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("status snapshot root must be an object")
        registry = AgentRegistry.from_dict(payload)
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(registry.to_json() if args.format == "json" else registry.to_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
