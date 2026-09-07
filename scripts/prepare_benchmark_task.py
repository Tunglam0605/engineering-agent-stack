#!/usr/bin/env python3
"""Materialize a controlled benchmark task and produce a concrete Codex run manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple
import uuid

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.context_packet import (
    ContextEvidence,
    build_context_packet,
    build_full_context_packet,
    render_context_prompt,
)
from benchmark_task_lib import (
    context_fixture_path,
    load_task,
    materialize_workspace,
    read_prompt,
    resolve_task_path,
)

CONTEXT_TOPOLOGIES = {"full-context", "bounded-context-packet"}


def _load_context_fixture(task: dict) -> dict:
    path = context_fixture_path(task)
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: context fixture must be a YAML mapping")
    return value


def prepare_prompt(task: dict, topology: str) -> Tuple[str, Optional[str], Optional[dict]]:
    family = task.get("family")
    if family != "context-efficiency":
        if topology in CONTEXT_TOPOLOGIES:
            raise ValueError("context topology is only valid for context-efficiency tasks")
        return read_prompt(task), None, None

    if topology not in CONTEXT_TOPOLOGIES:
        raise ValueError("context-efficiency task requires full-context or bounded-context-packet topology")

    fixture = _load_context_fixture(task)
    raw_evidence = fixture.get("evidence")
    limits = fixture.get("bounded_limits")
    if not isinstance(raw_evidence, list) or not isinstance(limits, dict):
        raise ValueError("context fixture requires evidence list and bounded_limits mapping")
    evidence = [ContextEvidence(**item) for item in raw_evidence]
    base_prompt = read_prompt(task)

    if topology == "full-context":
        packet = build_full_context_packet(task=base_prompt, evidence=evidence)
        selected = evidence
        strategy = "full"
    else:
        packet = build_context_packet(
            task=base_prompt,
            evidence=evidence,
            max_evidence_items=limits["max_evidence_items"],
            max_chars=limits["max_chars"],
        )
        by_id = {item.evidence_id: item for item in evidence}
        selected = [by_id[evidence_id] for evidence_id in packet.retained_evidence_ids]
        strategy = "bounded"

    prompt = render_context_prompt(base_prompt, selected)
    if len(prompt) != packet.context_size_chars:
        raise ValueError("context packet measurement drifted from rendered prompt")
    measurement = {
        "context_size_chars": packet.context_size_chars,
        "token_proxy": packet.token_proxy,
        "retained_evidence_count": len(selected),
        "retained_evidence_ids": [item.evidence_id for item in selected],
        "packet_content_size_chars": packet.context_size_chars,
    }
    return prompt, strategy, measurement


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
        prompt, context_strategy, context_measurement = prepare_prompt(task, args.topology)
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
            "prompt": prompt,
            "skip_git_repo_check": True,
            "codex_args": [],
        }
        if context_strategy is not None:
            manifest["context_strategy"] = context_strategy
            manifest["context_measurement"] = context_measurement

        run_root.mkdir(parents=True, exist_ok=True)
        manifest_path = run_root / "manifest.yaml"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
        (run_root / "task-source.txt").write_text(f"{task_path.as_posix()}\n", encoding="utf-8")

        print(f"PREPARED: {run_root}")
        print(f"MANIFEST: {manifest_path}")
        print(f"WORKSPACE: {workspace}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
