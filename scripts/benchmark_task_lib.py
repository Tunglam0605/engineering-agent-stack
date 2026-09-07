#!/usr/bin/env python3
"""Shared helpers for controlled benchmark task definitions."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS_ROOT = ROOT / "benchmarks" / "tasks"
INDEX_PATH = TASKS_ROOT / "index.yaml"

ALLOWED_ROLES = {
    "scout",
    "researcher",
    "implementer",
    "debugger",
    "test-engineer",
    "reviewer",
    "architect",
    "orchestrator",
}
ALLOWED_MODES = {"read-only", "write"}
ALLOWED_GRADERS = {"text_evidence", "command"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return value


def load_index() -> dict[str, Any]:
    return load_yaml(INDEX_PATH)


def task_entries() -> list[dict[str, Any]]:
    index = load_index()
    tasks = index.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError(f"{INDEX_PATH}: tasks must be a list")
    entries: list[dict[str, Any]] = []
    for entry in tasks:
        if not isinstance(entry, dict):
            raise ValueError(f"{INDEX_PATH}: each task entry must be a mapping")
        entries.append(entry)
    return entries


def resolve_task_path(task_id: str) -> Path:
    matches = [entry for entry in task_entries() if entry.get("id") == task_id]
    if len(matches) != 1:
        raise ValueError(f"task id {task_id!r} resolved to {len(matches)} entries")
    rel = matches[0].get("path")
    if not isinstance(rel, str) or not rel:
        raise ValueError(f"task id {task_id!r} has no valid path")
    path = TASKS_ROOT / rel
    if not path.is_file():
        raise ValueError(f"task file does not exist: {path}")
    return path


def load_task(task_path: Path) -> dict[str, Any]:
    task = load_yaml(task_path)
    task["_task_path"] = task_path
    return task


def prompt_path(task: dict[str, Any]) -> Path:
    task_path = Path(task["_task_path"])
    rel = task.get("prompt_file")
    if not isinstance(rel, str) or not rel:
        raise ValueError(f"{task_path}: prompt_file must be a non-empty string")
    return task_path.parent / rel


def workspace_path(task: dict[str, Any]) -> Path:
    task_path = Path(task["_task_path"])
    rel = task.get("workspace")
    if not isinstance(rel, str) or not rel:
        raise ValueError(f"{task_path}: workspace must be a non-empty string")
    return task_path.parent / rel


def context_fixture_path(task: dict[str, Any]) -> Path:
    task_path = Path(task["_task_path"])
    rel = task.get("context_fixture")
    if not isinstance(rel, str) or not rel:
        raise ValueError(f"{task_path}: context_fixture must be a non-empty string")
    path = (task_path.parent / rel).resolve()
    root = ROOT.resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"{task_path}: context_fixture must stay inside repository: {path}")
    return path


def read_prompt(task: dict[str, Any]) -> str:
    path = prompt_path(task)
    return path.read_text(encoding="utf-8")


def validate_task(task: dict[str, Any]) -> list[str]:
    task_path = Path(task["_task_path"])
    failures: list[str] = []
    required = [
        "version",
        "id",
        "role",
        "family",
        "mode",
        "prompt_file",
        "workspace",
        "quality_threshold",
        "grader",
    ]
    for field in required:
        if field not in task:
            failures.append(f"{task_path}: missing required field {field}")

    task_id = task.get("id")
    if not isinstance(task_id, str) or not task_id:
        failures.append(f"{task_path}: id must be a non-empty string")

    role = task.get("role")
    if role not in ALLOWED_ROLES:
        failures.append(f"{task_path}: unsupported role {role!r}")

    mode = task.get("mode")
    if mode not in ALLOWED_MODES:
        failures.append(f"{task_path}: unsupported mode {mode!r}")

    threshold = task.get("quality_threshold")
    if not isinstance(threshold, (int, float)) or not 0.0 <= float(threshold) <= 1.0:
        failures.append(f"{task_path}: quality_threshold must be within [0, 1]")

    try:
        ppath = prompt_path(task)
        if not ppath.is_file() or ppath.stat().st_size == 0:
            failures.append(f"{task_path}: prompt file missing or empty: {ppath}")
    except ValueError as exc:
        failures.append(str(exc))

    try:
        wpath = workspace_path(task)
        if not wpath.is_dir():
            failures.append(f"{task_path}: workspace directory missing: {wpath}")
        elif not any(path.is_file() for path in wpath.rglob("*")):
            failures.append(f"{task_path}: workspace contains no files: {wpath}")
    except ValueError as exc:
        failures.append(str(exc))

    if task.get("family") == "context-efficiency":
        try:
            fixture_path = context_fixture_path(task)
            if not fixture_path.is_file():
                failures.append(f"{task_path}: context fixture missing: {fixture_path}")
            else:
                fixture = load_yaml(fixture_path)
                evidence = fixture.get("evidence")
                limits = fixture.get("bounded_limits")
                if not isinstance(evidence, list) or not evidence:
                    failures.append(f"{task_path}: context fixture requires non-empty evidence list")
                if not isinstance(limits, dict):
                    failures.append(f"{task_path}: context fixture requires bounded_limits mapping")
                else:
                    max_items = limits.get("max_evidence_items")
                    max_chars = limits.get("max_chars")
                    if not isinstance(max_items, int) or max_items <= 0:
                        failures.append(f"{task_path}: max_evidence_items must be positive")
                    if not isinstance(max_chars, int) or max_chars <= 0:
                        failures.append(f"{task_path}: max_chars must be positive")
        except (OSError, ValueError, yaml.YAMLError) as exc:
            failures.append(str(exc))

    grader = task.get("grader")
    if not isinstance(grader, dict):
        failures.append(f"{task_path}: grader must be a mapping")
        return failures

    grader_type = grader.get("type")
    if grader_type not in ALLOWED_GRADERS:
        failures.append(f"{task_path}: unsupported grader type {grader_type!r}")
    elif grader_type == "text_evidence":
        required_all = grader.get("required_all", [])
        groups = grader.get("required_any_groups", [])
        if not required_all and not groups:
            failures.append(f"{task_path}: text_evidence grader requires required_all or required_any_groups")
        if required_all and (not isinstance(required_all, list) or not all(isinstance(item, str) and item for item in required_all)):
            failures.append(f"{task_path}: required_all must be a list of non-empty strings")
        if groups and (not isinstance(groups, list) or not all(isinstance(group, list) and group and all(isinstance(item, str) and item for item in group) for group in groups)):
            failures.append(f"{task_path}: required_any_groups must be a list of non-empty string lists")
    elif grader_type == "command":
        command = grader.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
            failures.append(f"{task_path}: command grader requires a non-empty string list")

    if mode == "read-only" and grader.get("max_file_changes") is None:
        failures.append(f"{task_path}: read-only task must declare grader.max_file_changes")

    return failures


def materialize_workspace(task: dict[str, Any], destination: Path) -> Path:
    source = workspace_path(task)
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    return destination
