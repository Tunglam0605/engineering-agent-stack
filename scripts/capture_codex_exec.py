#!/usr/bin/env python3
"""Run Codex non-interactively and capture usage/latency into a normalized local record.

Raw provider traces are intentionally written under a local output directory and
should remain git-ignored. Promotion into benchmark results is a separate quality
grading step.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time
from typing import Any
import uuid

import yaml

from codex_capture_lib import build_capture, parse_codex_events, validate_meta


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: manifest must be a YAML mapping")
    validate_meta(value)
    return value


def resolve_prompt(meta: dict[str, Any], manifest_path: Path) -> str:
    prompt = meta.get("prompt")
    prompt_file = meta.get("prompt_file")
    if bool(prompt) == bool(prompt_file):
        raise ValueError("manifest must define exactly one of prompt or prompt_file")
    if prompt_file:
        path = Path(str(prompt_file))
        if not path.is_absolute():
            path = manifest_path.parent / path
        return path.read_text(encoding="utf-8")
    return str(prompt)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def codex_version(codex_bin: str) -> str | None:
    try:
        result = subprocess.run(
            [codex_bin, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (result.stdout or result.stderr).strip()
    return text or None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks/local-runs"))
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        meta = load_manifest(args.manifest)
        prompt = resolve_prompt(meta, args.manifest)
        cwd = Path(str(meta.get("cwd", "."))).expanduser().resolve()
        if not cwd.is_dir():
            raise ValueError(f"cwd does not exist: {cwd}")

        run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
        run_dir = args.output_dir / run_id
        events_path = run_dir / "events.jsonl"
        stderr_path = run_dir / "stderr.log"
        last_message_path = run_dir / "last-message.txt"
        capture_path = run_dir / "capture.json"

        command = [
            args.codex_bin,
            "-c",
            f"model_reasoning_effort={meta['reasoning_effort']}",
            "exec",
            "--json",
            "--ephemeral",
            "--model",
            str(meta["model"]),
            "--output-last-message",
            str(last_message_path.resolve()),
        ]
        if bool(meta.get("skip_git_repo_check", False)):
            command.append("--skip-git-repo-check")
        extra = meta.get("codex_args", [])
        if extra:
            if not isinstance(extra, list) or not all(isinstance(x, str) for x in extra):
                raise ValueError("codex_args must be a list of strings")
            command.extend(extra)
        command.append("-")

        if args.dry_run:
            print("cwd:", cwd)
            print("command:", shlex.join(command))
            print("prompt bytes:", len(prompt.encode("utf-8")))
            return 0

        run_dir.mkdir(parents=True, exist_ok=False)
        started_at = iso_now()
        start = time.perf_counter()
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                input=prompt,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise ValueError(f"failed to execute {args.codex_bin!r}: {exc}") from exc
        latency_ms = (time.perf_counter() - start) * 1000.0
        finished_at = iso_now()

        events_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")

        summary = parse_codex_events(events_path)
        environment = {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cwd": str(cwd),
            "codex_version": codex_version(args.codex_bin),
        }
        capture = build_capture(
            meta,
            summary,
            latency_ms=latency_ms,
            exit_code=result.returncode,
            started_at=started_at,
            finished_at=finished_at,
            capture_id=run_id,
            artifacts={
                "raw_events": str(events_path),
                "stderr": str(stderr_path),
                "last_message": str(last_message_path),
            },
            environment=environment,
        )
        capture_path.write_text(
            json.dumps(capture, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        print(f"WROTE: {capture_path}")
        print(
            f"outcome={capture['outcome']} exit={result.returncode} "
            f"input={capture['usage']['input_tokens']} "
            f"output={capture['usage']['output_tokens']} "
            f"latency_ms={capture['latency_ms']}"
        )
        return 0 if result.returncode == 0 and capture["outcome"] == "completed" else 1

    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
