from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from runtime.lifecycle import GoalStore, LifecycleGate
from runtime.workflow import Workflow
from runtime.capabilities.project import ProjectCapabilityService, load_project_profile
from runtime.capabilities.snapshot import bind_snapshot, read_snapshot

from .paths import resolve_repo
from .version import __version__


def _git_root(project: Path) -> Path:
    probe = project.expanduser().resolve()
    while True:
        if (probe / ".git").exists():
            return probe
        if probe.parent == probe:
            raise ValueError("project is not inside a Git repository")
        probe = probe.parent




def _capability_service() -> ProjectCapabilityService:
    return ProjectCapabilityService(eas_version=__version__)


def _current_bound_digest(project_root: Path, *, create_if_missing: bool = False) -> Optional[str]:
    if load_project_profile(project_root) is None:
        return None
    snapshot = _capability_service().resolve_snapshot(project_root)
    persisted = read_snapshot(project_root)
    if persisted is None:
        if not create_if_missing:
            raise RuntimeError(
                "project capability snapshot is unbound; initialize or explicitly migrate the snapshot first"
            )
        bind_snapshot(project_root, snapshot)
        persisted = snapshot
    if persisted.digest != snapshot.digest:
        raise RuntimeError(
            "project capability snapshot drift detected; run explicit project migrate-snapshot before lifecycle operations"
        )
    return snapshot.digest


def _require_goal_binding(project_root: Path, store: GoalStore) -> Optional[str]:
    digest = _current_bound_digest(project_root, create_if_missing=False)
    if digest is not None:
        store.require_capability_snapshot(digest)
    return digest


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
        return
    print(json.dumps(payload, sort_keys=True, indent=2))


def goal_init(goal_id: str, project: Path, *, as_json: bool = False) -> int:
    project_root = _git_root(project)
    store = GoalStore(project_root, goal_id)
    digest = _current_bound_digest(project_root, create_if_missing=True)
    state = store.initialize(capability_snapshot_digest=digest)
    payload = {
        "command": "goal-init",
        "goal_id": state.goal_id,
        "state_path": str(store.state_path),
        "event_path": str(store.event_path),
        "capability_snapshot_digest": state.capability_snapshot_digest,
    }
    _render(payload, as_json)
    return 0


def goal_status(goal_id: str, project: Path, *, as_json: bool = False) -> int:
    project_root = _git_root(project)
    store = GoalStore(project_root, goal_id)
    state = store.load()
    gate = LifecycleGate(resolve_repo(required=True))
    binding = {"required": False, "status": "LEGACY", "goal_digest": state.capability_snapshot_digest, "project_digest": None}
    if load_project_profile(project_root) is not None:
        binding["required"] = True
        try:
            project_digest = _current_bound_digest(project_root, create_if_missing=False)
            binding["project_digest"] = project_digest
            binding["status"] = "BOUND" if state.capability_snapshot_digest == project_digest else "MIGRATION_REQUIRED"
        except (RuntimeError, ValueError) as exc:
            binding["status"] = "PROJECT_SNAPSHOT_ERROR"
            binding["error"] = str(exc)
    payload = {"command": "goal-status", **gate.summary(state), "capability_binding": binding}
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
    _require_goal_binding(project_root, store)
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
    approval_id: Optional[str] = None,
) -> int:
    project_root = _git_root(project)
    store = GoalStore(project_root, goal_id)
    _require_goal_binding(project_root, store)
    gate = LifecycleGate(resolve_repo(required=True))
    assignment = gate.transition_atomic(store, assignment_id, state_name, approval_id=approval_id)
    payload = {
        "command": "goal-transition",
        "goal_id": goal_id,
        "assignment_id": assignment.assignment_id,
        "state": assignment.state,
    }
    _render(payload, as_json)
    return 0


def goal_bind_capabilities(
    goal_id: str,
    project: Path,
    revision: int,
    *,
    as_json: bool = False,
) -> int:
    root = _git_root(project)
    if load_project_profile(root) is None:
        raise ValueError("goal capability migration requires a tracked .eas/project.toml")
    digest = _current_bound_digest(root, create_if_missing=True)
    if digest is None:
        raise RuntimeError("capability digest could not be resolved")
    store = GoalStore(root, goal_id)
    state = store.bind_capability_snapshot(digest, revision)
    payload = {
        "command": "goal-bind-capabilities",
        "goal_id": goal_id,
        "revision": state.revision,
        "capability_snapshot_digest": state.capability_snapshot_digest,
        "explicit_migration": True,
    }
    _render(payload, as_json)
    return 0


def goal_workflow(args) -> int:
    root = _git_root(args.project)
    store = GoalStore(root, args.goal_id)
    _require_goal_binding(root, store)
    flow = Workflow(LifecycleGate(resolve_repo(required=True)))
    command = args.goal_command
    if command == 'checkpoint':
        payload = flow.checkpoint(store, args.stage, json.loads(args.evidence), args.revision)
    elif command == 'approve':
        payload = flow.approve(store, args.action, args.target, args.revision, args.approver,
                               args.reason, args.executor_stopped_evidence)
    elif command == 'recover':
        payload = flow.recover(store, args.assignment_id, args.approval)
    elif command == 'plan':
        payload = flow.plan(store)
    elif command == 'export':
        payload = flow.export(store)
    else:
        raise ValueError('unknown workflow command')
    _render(payload, args.json or command == 'export')
    return 0
