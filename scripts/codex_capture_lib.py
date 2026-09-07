#!/usr/bin/env python3
"""Provider-specific parsing helpers for Codex exec JSONL benchmark capture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import uuid

USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)

REQUIRED_META = (
    "experiment_id",
    "task_id",
    "role",
    "profile",
    "model",
    "reasoning_effort",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: event must be a JSON object")
            events.append(value)
    if not events:
        raise ValueError(f"{path}: no JSONL events found")
    return events


def validate_meta(meta: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_META if not meta.get(field)]
    if missing:
        raise ValueError(f"run manifest missing required fields: {', '.join(missing)}")


def receiver_roles(item: dict[str, Any]) -> list[str]:
    """Extract optional role metadata from legacy/extended collaboration payloads."""
    roles: list[str] = []
    receivers = item.get("receiver_agents", [])
    if not isinstance(receivers, list):
        return roles
    for receiver in receivers:
        if isinstance(receiver, dict):
            role = receiver.get("agent_role")
            if isinstance(role, str) and role:
                roles.append(role)
    return roles


def receiver_thread_ids(item: dict[str, Any]) -> list[str]:
    """Extract receiver thread IDs exposed by current Codex exec JSONL collab items."""
    values = item.get("receiver_thread_ids", [])
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value]


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    usage = {field: 0 for field in USAGE_FIELDS}
    thread_id: str | None = None
    completed_turns = 0
    failed_turns = 0
    top_level_errors = 0
    completed_items: set[str] = set()
    tool_calls = 0
    file_changes = 0
    collab_tool_calls = 0
    observed_spawn_events = 0
    agent_spawn_models: list[str] = []
    agent_spawn_reasoning: list[str] = []
    agent_spawn_roles: list[str] = []
    agent_spawn_thread_ids: list[str] = []
    item_type_counts: dict[str, int] = {}

    for event in events:
        event_type = event.get("type")
        if event_type == "thread.started" and isinstance(event.get("thread_id"), str):
            thread_id = event["thread_id"]
        elif event_type == "turn.completed":
            completed_turns += 1
            turn_usage = event.get("usage", {})
            if isinstance(turn_usage, dict):
                for field in USAGE_FIELDS:
                    value = turn_usage.get(field, 0)
                    if isinstance(value, int) and value >= 0:
                        usage[field] += value
        elif event_type == "turn.failed":
            failed_turns += 1
        elif event_type == "error":
            top_level_errors += 1
        elif event_type == "item.completed":
            item = event.get("item")
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if isinstance(item_id, str):
                if item_id in completed_items:
                    continue
                completed_items.add(item_id)
            item_type = item.get("type")
            if not isinstance(item_type, str):
                continue
            item_type_counts[item_type] = item_type_counts.get(item_type, 0) + 1
            if item_type in {"command_execution", "mcp_tool_call", "web_search"}:
                tool_calls += 1
            if item_type == "file_change":
                changes = item.get("changes", [])
                if isinstance(changes, (list, dict)):
                    file_changes += len(changes)

            # Current Codex exec JSONL serializes collaboration calls as
            # `collab_tool_call`. Older/experimental traces used
            # `collab_agent_tool_call`. Accept both so real-machine acceptance
            # does not report a false zero-spawn result across CLI revisions.
            if item_type in {"collab_tool_call", "collab_agent_tool_call"}:
                collab_tool_calls += 1
                if item.get("tool") == "spawn_agent":
                    observed_spawn_events += 1
                    agent_spawn_thread_ids.extend(receiver_thread_ids(item))

                    # These fields are optional. Current codex exec JSONL
                    # exposes receiver thread IDs but does not currently carry
                    # child model/role/reasoning metadata in CollabToolCallItem.
                    model = item.get("model")
                    if isinstance(model, str) and model:
                        agent_spawn_models.append(model)
                    reasoning = item.get("reasoning_effort")
                    if isinstance(reasoning, str) and reasoning:
                        agent_spawn_reasoning.append(reasoning)
                    agent_spawn_roles.extend(receiver_roles(item))

    return {
        "thread_id": thread_id,
        "usage": usage,
        "event_summary": {
            "event_count": len(events),
            "turns_completed": completed_turns,
            "turns_failed": failed_turns,
            "top_level_errors": top_level_errors,
            "completed_items": len(completed_items),
            "tool_calls": tool_calls,
            "file_changes": file_changes,
            "collab_tool_calls": collab_tool_calls,
            # Compatibility field: this is the count of spawn_agent items
            # observed in public Codex exec JSONL, not runtime ground truth.
            "agent_spawns": observed_spawn_events,
            "agent_spawn_thread_ids": agent_spawn_thread_ids,
            "agent_spawn_models": agent_spawn_models,
            "agent_spawn_reasoning": agent_spawn_reasoning,
            "agent_spawn_roles": agent_spawn_roles,
            "item_type_counts": item_type_counts,
        },
    }


def build_capture(meta: dict[str, Any], event_summary: dict[str, Any], *, latency_ms: float, exit_code: int | None = None, started_at: str | None = None, finished_at: str | None = None, artifacts: dict[str, str] | None = None, environment: dict[str, Any] | None = None, capture_id: str | None = None) -> dict[str, Any]:
    validate_meta(meta)
    if latency_ms < 0:
        raise ValueError("latency_ms must be non-negative")
    events = event_summary["event_summary"]
    if exit_code not in (None, 0) or events["turns_failed"] or events["top_level_errors"]:
        outcome = "failed"
    elif events["turns_completed"] > 0:
        outcome = "completed"
    else:
        outcome = "blocked"
    record: dict[str, Any] = {
        "schema_version": 1,
        "capture_id": capture_id or str(uuid.uuid4()),
        "experiment_id": str(meta["experiment_id"]),
        "task_id": str(meta["task_id"]),
        "provider": str(meta.get("provider", "openai-codex")),
        "source": "codex-exec-jsonl",
        "role": str(meta["role"]),
        "profile": str(meta["profile"]),
        "model": str(meta["model"]),
        "reasoning_effort": str(meta["reasoning_effort"]),
        "topology": str(meta.get("topology", "unspecified")),
        "latency_ms": round(float(latency_ms), 3),
        "usage": dict(event_summary["usage"]),
        "outcome": outcome,
        "event_summary": dict(events),
    }
    if event_summary.get("thread_id"):
        record["thread_id"] = event_summary["thread_id"]
    if started_at:
        record["started_at"] = started_at
    if finished_at:
        record["finished_at"] = finished_at
    if exit_code is not None:
        record["process"] = {"exit_code": int(exit_code)}
    if artifacts:
        record["artifacts"] = artifacts
    if environment:
        record["environment"] = environment
    if "quality_threshold" in meta:
        record["quality_threshold"] = float(meta["quality_threshold"])
    return record


def parse_codex_events(path: Path) -> dict[str, Any]:
    return summarize_events(load_jsonl(path))
