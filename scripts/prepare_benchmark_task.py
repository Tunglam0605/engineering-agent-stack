#!/usr/bin/env python3
"""Materialize a controlled benchmark task and produce a concrete Codex run manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import uuid

import yaml

from benchmark_task_lib import load_task, materialize_workspace, read_prompt, resolve_task_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--topology", default="delegated")
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks/local-runs/prepared"))
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()

    try:
        task_path = resolve_task_path(args.task_id)
        task = load_task(task_path)
        run_root = args.destination
        if run_root is None:
            run_root = args.output_dir / f"{args.task_id}-{uuid.uuid4().hex[:8]}"
        run_root = run_root.resolve()
        workspace = materialize_workspace(task, run_root / "workspace")

        manifest = {
            "version": 1,
            "experiment_id": args.experiment_id,
            "task_id": args.task_id,
            "provider": "openai-codex",
            "role": str(task["role"]),
            "profile": args.profile,
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "topology": args.topology,
            "quality_threshold": float(task["quality_threshold"]),
            "cwd": str(workspace),
            "prompt": read_prompt(task),
            "skip_git_repo_check": True,
            "codex_args": [],
        }

        run_root.mkdir(parents=True, exist_ok=True)
        manifest_path = run_root / "manifest.yaml"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
        (run_root / "task-source.txt").write_text(f"{task_path.as_posix()}\n", encoding="utf-8")

        print(f"PREPARED: {run_root}")
        print(f"MANIFEST: {manifest_path}")
        print(f"WORKSPACE: {workspace}")
        return 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
