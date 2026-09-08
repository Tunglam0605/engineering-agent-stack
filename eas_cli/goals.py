from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from runtime.lifecycle import GoalStore, LifecycleGate

from .paths import resolve_repo


def _git_root(project: Path) -> Path:
    probe = project.expanduser().resolve()
    while True:
        if (probe / ".git").exists():
            return probe
        if probe.parent == probe:
            raise ValueError("project is not inside a Git repository")
        probe = probe.parent


def _render(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
        return
    if payload.get("command") == "goal-status":
        print("Goal {}: {} assignments, {} active, budget={}".format(
            payload["goal_id"], payload["total"], payload["active"], payload["budget_state"]
        ))
        print("Readers: {} active | Writers: {} active".format(
            payload["active_readers"], payload["active_writers"]
        ))
        roles = payload.get("by_role") or {}
        if roles:
            print("Roles: " + ", ".join("{}={}".format(k, v) for k, v in sorted(roles.items())))
        return
    if payload.get("command") == "goal-gate":
        print("{}: {}".format(payload["action"], "; ".join(payload["reasons"])))
        target = payload.get("reuse_assignment_id") or payload.get("proposed_assignment_id")
        if target:
            print("Assignment: " + target)
        return
    if payload.get("command") == "goal-init":
        print("Goal initialized: {} -> {}".format(payload["goal_id"], payload["state_path"]))
        return
    if payload.get("command") == "goal-transition":
        print("{} -> {}".format(payload["assignment_id"], payload["state"]))


def goal_init(goal_id: str, project: Path, *, as_json: bool = False) -> int:
    project_root = _git_root(project)
    store = GoalStore(project_root, goal_id)
    state = store.initialize()
    payload = {
        "command": "goal-init",
        "goal_id": state.goal_id,
        "state_path": str(store.state_path),
        "event_path": str(store.event_path),
    }
    _render(payload, as_json)
    return 0


def goal_status(goal_id: str, project: Path, *, as_json: bool = False) -> int:
    project_root = _git_root(project)
    store = GoalStore(project_root, goal_id)
    state = store.load()
    gate = LifecycleGate(resolve_repo(required=True))
    payload = {"command": "goal-status", **gate.summary(state)}
    _render(payload, as_json)
    return 0


def goal_gate(
    goal_id: str,
    project: Path,
    *,
    role: str,
    task_domain: str,
    write_scope: list[str],
    change_set: Optional[str] = None,
    reconciled: bool = False,
    override_reason: Optional[str] = None,
    exception_kind: Optional[str] = None,
    material_change: bool = False,
    fresh_context: bool = False,
    commit: bool = False,
    as_json: bool = False,
) -> int:
    project_root = _git_root(project)
    store = GoalStore(project_root, goal_id)
    gate = LifecycleGate(resolve_repo(required=True))
    if commit:
        decision, assignment = gate.evaluate_and_commit(
            store, role=role, task_domain=task_domain, write_scope=write_scope,
            change_set=change_set, reconciled=reconciled, override_reason=override_reason,
            exception_kind=exception_kind, material_change=material_change,
            fresh_context=fresh_context,
        )
        payload = {"command": "goal-gate", **decision.as_dict(), "committed": True}
        if assignment is not None:
            payload["assignment_id"] = assignment.assignment_id
        elif decision.reuse_assignment_id:
            payload["assignment_id"] = decision.reuse_assignment_id
    else:
        state = store.load()
        decision = gate.evaluate(
            state, role=role, task_domain=task_domain, write_scope=write_scope,
            change_set=change_set, reconciled=reconciled, override_reason=override_reason,
            exception_kind=exception_kind, material_change=material_change,
            fresh_context=fresh_context,
        )
        payload = {"command": "goal-gate", **decision.as_dict(), "committed": False}
    _render(payload, as_json)
    return {"SPAWN": 0, "REUSE": 0, "ESCALATE": 4, "REJECT": 3}[decision.action]


def goal_transition(
    goal_id: str,
    project: Path,
    assignment_id: str,
    state_name: str,
    *,
    as_json: bool = False,
) -> int:
    project_root = _git_root(project)
    store = GoalStore(project_root, goal_id)
    gate = LifecycleGate(resolve_repo(required=True))
    assignment = gate.transition_atomic(store, assignment_id, state_name)
    payload = {
        "command": "goal-transition",
        "goal_id": goal_id,
        "assignment_id": assignment.assignment_id,
        "state": assignment.state,
    }
    _render(payload, as_json)
    return 0
