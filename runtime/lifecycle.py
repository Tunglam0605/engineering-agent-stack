from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PureWindowsPath
import re
import time
from typing import Dict, Iterator, List, Optional, Tuple

import yaml

from .preflight import _canonical_scope
from .workflow_state import empty_workflow, strict_json, timestamp, validate_workflow

ACTIVE_STATES = {"pending", "running"}
RESUMABLE_STATES = {"pending", "running", "completed"}
SUPPORTED_STATES = {"pending", "running", "completed", "failed", "blocked"}
ACTIONS = {"SPAWN", "REUSE", "ESCALATE", "REJECT"}
ALLOWED_HARD_LIMIT_EXCEPTIONS = {
    "acceptance-diagnostic",
    "required-safety-review",
    "required-release-review",
}
_GOAL_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _nonempty(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + " must be a non-empty string")
    return value.strip()


def _validate_goal_id(value: object) -> str:
    if not isinstance(value, str) or not _GOAL_ID.fullmatch(value):
        raise ValueError("goal_id must match [a-z0-9][a-z0-9._-]{0,127}")
    # Prevent cross-platform aliases such as CON/AUX/NUL/COM1 on Windows even
    # when the state was created on a POSIX host and later shared/moved.
    if PureWindowsPath(value + ".json").is_reserved():
        raise ValueError("goal_id is reserved on Windows: " + value)
    return value


def _normalize_scopes(scopes: object) -> List[str]:
    if not isinstance(scopes, list) or not all(isinstance(item, str) for item in scopes):
        raise ValueError("write_scope must be a list of strings")
    return [_canonical_scope(item) for item in scopes]


@dataclass
class GoalAssignment:
    assignment_id: str
    role: str
    task_domain: str
    state: str
    write_scope: List[str]
    change_set: Optional[str] = None
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    attempt_started_at: Optional[str] = None
    recovery: Optional[dict] = None

    def __post_init__(self) -> None:
        from .reliability import validate_recovery
        validate_recovery(self.recovery)
        self.assignment_id = _nonempty("assignment_id", self.assignment_id)
        self.role = _nonempty("role", self.role)
        self.task_domain = _nonempty("task_domain", self.task_domain)
        if self.state not in SUPPORTED_STATES:
            raise ValueError("unsupported assignment state: " + str(self.state))
        self.write_scope = _normalize_scopes(self.write_scope)
        if self.change_set is not None:
            self.change_set = _nonempty("change_set", self.change_set)
        self.created_at = _nonempty("created_at", self.created_at)
        self.updated_at = _nonempty("updated_at", self.updated_at)
        timestamp(self.created_at)
        timestamp(self.updated_at)
        if self.attempt_started_at is not None:
            timestamp(self.attempt_started_at)

    @classmethod
    def from_dict(cls, payload: dict) -> "GoalAssignment":
        if not isinstance(payload, dict):
            raise ValueError("assignment must be an object")
        return cls(
            assignment_id=payload["assignment_id"],
            role=payload["role"],
            task_domain=payload["task_domain"],
            state=payload["state"],
            write_scope=payload["write_scope"],
            change_set=payload.get("change_set"),
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
            attempt_started_at=payload.get("attempt_started_at"),
            recovery=payload.get("recovery"),
        )


@dataclass
class GoalState:
    goal_id: str
    assignments: List[GoalAssignment] = field(default_factory=list)
    next_sequence: int = 1
    revision: int = 0
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    workflow: dict = field(default_factory=empty_workflow)
    capability_snapshot_digest: Optional[str] = None

    def __post_init__(self) -> None:
        self.goal_id = _validate_goal_id(self.goal_id)
        if not isinstance(self.assignments, list) or not all(
            isinstance(item, GoalAssignment) for item in self.assignments
        ):
            raise ValueError("assignments must be a list of GoalAssignment")
        if not isinstance(self.next_sequence, int) or isinstance(self.next_sequence, bool) or self.next_sequence < 1:
            raise ValueError("next_sequence must be a positive integer")
        if not isinstance(self.revision, int) or isinstance(self.revision, bool) or self.revision < 0:
            raise ValueError("revision must be a non-negative integer")
        ids = [item.assignment_id for item in self.assignments]
        if len(ids) != len(set(ids)):
            raise ValueError("assignment ids must be unique")
        self.created_at = _nonempty("created_at", self.created_at)
        self.updated_at = _nonempty("updated_at", self.updated_at)
        timestamp(self.created_at)
        timestamp(self.updated_at)
        for ident in ids:
            if not re.fullmatch(r'a-[0-9]{4,}', ident) or int(ident[2:]) >= self.next_sequence:
                raise ValueError('assignment id must precede next_sequence')
        validate_workflow(self.workflow, self.revision, set(ids))
        if self.capability_snapshot_digest is not None and (
            not isinstance(self.capability_snapshot_digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", self.capability_snapshot_digest)
        ):
            raise ValueError("capability_snapshot_digest must be a lowercase SHA-256 hex digest or null")

    def as_dict(self) -> dict:
        version = 3 if self.capability_snapshot_digest is not None else 2
        payload = {
            "version": version,
            "goal_id": self.goal_id,
            "next_sequence": self.next_sequence,
            "revision": self.revision,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "assignments": [asdict(item) for item in self.assignments],
            "workflow": self.workflow,
        }
        if version == 3:
            payload["capability_snapshot_digest"] = self.capability_snapshot_digest
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "GoalState":
        if not isinstance(payload, dict) or type(payload.get('version')) is not int or payload['version'] not in (1, 2, 3):
            raise ValueError("goal state must be a version 1, 2 or 3 object")
        assignments = payload.get("assignments")
        if not isinstance(assignments, list):
            raise ValueError("goal state assignments must be a list")
        if payload['version'] in (2, 3) and 'revision' not in payload:
            raise ValueError('version 2/3 goal state requires revision')
        if payload['version'] == 3 and 'capability_snapshot_digest' not in payload:
            raise ValueError('version 3 goal state requires capability_snapshot_digest')
        return cls(
            goal_id=payload["goal_id"],
            next_sequence=payload["next_sequence"],
            revision=payload.get("revision", 0),
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
            assignments=[GoalAssignment.from_dict(item) for item in assignments],
            workflow=payload['workflow'] if payload['version'] in (2, 3) else payload.get('workflow', empty_workflow()),
            capability_snapshot_digest=payload.get("capability_snapshot_digest"),
        )


@dataclass(frozen=True)
class LifecycleDecision:
    action: str
    reasons: List[str]
    reuse_assignment_id: Optional[str]
    proposed_assignment_id: Optional[str]
    counters: dict
    justification: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise ValueError("unsupported lifecycle action: " + self.action)
        if not isinstance(self.justification, dict):
            raise ValueError("justification must be an object")

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LifecyclePolicy:
    max_parallel_readers: int
    max_parallel_writers: int
    soft_limit: int
    hard_limit: int
    max_architect_per_goal: int
    max_reviewer_per_change_set: int
    max_same_role_domain_scope_active: int
    stale_after_seconds: int
    timeout_after_seconds: int
    approval_ttl_seconds: int
    max_active_children: int = 2

    @classmethod
    def from_repository(cls, root: Path) -> "LifecyclePolicy":
        data = yaml.safe_load((root / "config" / "routing-policy.yaml").read_text(encoding="utf-8"))
        limits = data.get("limits") if isinstance(data, dict) else None
        lifecycle = data.get("lifecycle") if isinstance(data, dict) else None
        if not isinstance(limits, dict) or not isinstance(lifecycle, dict):
            raise ValueError("routing policy lifecycle/limits must be mappings")
        if lifecycle.get("reuse_strategy") != "resume-before-spawn":
            raise ValueError("routing policy must use resume-before-spawn")
        values = {
            "max_parallel_readers": limits.get("default_max_parallel_readers"),
            "max_active_children": limits.get("default_max_active_children", 2),
            "max_parallel_writers": limits.get("default_max_parallel_writers"),
            "soft_limit": limits.get("soft_max_child_assignments_per_goal"),
            "hard_limit": limits.get("hard_max_child_assignments_per_goal"),
            "max_architect_per_goal": limits.get("default_max_architect_assignments_per_goal"),
            "max_reviewer_per_change_set": limits.get("default_max_reviewer_assignments_per_change_set"),
            "max_same_role_domain_scope_active": limits.get("max_same_role_domain_scope_active"),
            "stale_after_seconds": lifecycle.get('stale_after_seconds', 3600),
            "timeout_after_seconds": lifecycle.get('timeout_after_seconds', 86400),
            "approval_ttl_seconds": lifecycle.get('approval_ttl_seconds', 900),
        }
        for name, value in values.items():
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(name + " must be a positive integer")
        if values["hard_limit"] < values["soft_limit"]:
            raise ValueError("hard_limit must be >= soft_limit")
        if values['max_active_children'] > 4:
            raise ValueError('max_active_children must be within 1..4')
        return cls(**values)


class GoalStore:
    def __init__(self, project: Path, goal_id: str) -> None:
        self.project = project.expanduser().resolve()
        self.goal_id = _validate_goal_id(goal_id)
        dotgit = self.project / ".git"
        if dotgit.is_dir():
            git_dir = dotgit
        elif dotgit.is_file():
            line = dotgit.read_text(encoding="utf-8").strip()
            if not line.lower().startswith("gitdir:"):
                raise ValueError("unsupported .git file format")
            raw = line.split(":", 1)[1].strip()
            candidate = Path(raw)
            git_dir = (candidate if candidate.is_absolute() else self.project / candidate).resolve()
        else:
            raise ValueError("project must be a Git repository root")
        self.directory = git_dir / "eas" / "goals"
        self.state_path = self.directory / (self.goal_id + ".json")
        self.event_path = self.directory / (self.goal_id + ".jsonl")
        self.lock_path = self.directory / (self.goal_id + ".lock")
        self._lock_held = False

    @contextmanager
    def locked(self, timeout_seconds: float = 10.0, poll_seconds: float = 0.05) -> Iterator[None]:
        if self._lock_held:
            raise RuntimeError("nested goal lock is not supported")
        if timeout_seconds <= 0 or poll_seconds <= 0:
            raise ValueError("lock timeout/poll must be positive")
        self.directory.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + timeout_seconds
        fd: Optional[int] = None
        while fd is None:
            try:
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise RuntimeError(
                        "goal state is locked; confirm the other EAS process has exited before removing "
                        + str(self.lock_path)
                    )
                time.sleep(poll_seconds)
        try:
            metadata = json.dumps({"pid": os.getpid(), "time": _utc_now()}).encode("utf-8")
            os.write(fd, metadata)
            os.close(fd)
            fd = None
            self._lock_held = True
            yield
        finally:
            self._lock_held = False
            if fd is not None:
                os.close(fd)
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass

    def _load_unlocked(self) -> GoalState:
        if not self.state_path.is_file():
            raise ValueError("goal is not initialized: " + self.goal_id)
        try:
            payload = strict_json(self.state_path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise ValueError("goal state is invalid JSON: " + str(exc)) from exc
        try:
            state = GoalState.from_dict(payload)
        except (KeyError, TypeError) as exc:
            raise ValueError('malformed goal state') from exc
        if state.goal_id != self.goal_id:
            raise ValueError('goal state id does not match store')
        return state

    def load(self) -> GoalState:
        return self._load_unlocked()

    def _save_unlocked(self, state: GoalState) -> None:
        if state.goal_id != self.goal_id:
            raise ValueError("goal state id does not match store")
        disk_revision: Optional[int] = None
        if self.state_path.exists():
            disk_revision = self._load_unlocked().revision
            if disk_revision != state.revision:
                raise RuntimeError(
                    "goal state changed concurrently: expected revision {}, found {}".format(
                        state.revision, disk_revision
                    )
                )
        elif state.revision != 0:
            raise RuntimeError("goal state disappeared concurrently")
        next_revision = state.revision + 1
        next_updated_at = _utc_now()
        payload = state.as_dict()
        payload["revision"] = next_revision
        payload["updated_at"] = next_updated_at
        GoalState.from_dict(payload)
        temp = self.state_path.with_suffix(".json.tmp")
        with temp.open('w', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(self.state_path)
        if os.name == 'posix':
            directory_fd = os.open(str(self.directory), os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        state.revision = next_revision
        state.updated_at = next_updated_at

    def save(self, state: GoalState) -> None:
        with self.locked():
            self._save_unlocked(state)

    def _append_event_unlocked(self, event: str, payload: dict) -> None:
        record = {
            "time": _utc_now(),
            "event": _nonempty("event", event),
            "goal_id": self.goal_id,
            "payload": payload,
        }
        with self.event_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

    def append_event(self, event: str, payload: dict) -> None:
        with self.locked():
            self._append_event_unlocked(event, payload)

    def initialize(self, capability_snapshot_digest: Optional[str] = None) -> GoalState:
        with self.locked():
            if self.state_path.exists():
                state = self._load_unlocked()
                if capability_snapshot_digest is not None and state.capability_snapshot_digest != capability_snapshot_digest:
                    raise RuntimeError(
                        "goal capability binding differs or is absent; use explicit bind-capabilities migration"
                    )
                return state
            state = GoalState(
                goal_id=self.goal_id, capability_snapshot_digest=capability_snapshot_digest
            )
            self._save_unlocked(state)
            event = {"goal_id": self.goal_id}
            if capability_snapshot_digest is not None:
                event["capability_snapshot_digest"] = capability_snapshot_digest
            self._append_event_unlocked("goal_initialized", event)
            return state

    def bind_capability_snapshot(self, digest: str, expected_revision: int) -> GoalState:
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("digest must be a lowercase SHA-256 hex string")
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("expected_revision must be a non-negative integer")
        with self.locked():
            state = self._load_unlocked()
            if state.revision != expected_revision:
                raise RuntimeError("goal revision changed; re-read state before capability migration")
            if any(item.state in ACTIVE_STATES for item in state.assignments):
                raise RuntimeError("cannot migrate capability binding while assignments are active")
            if state.capability_snapshot_digest == digest:
                return state
            previous = state.capability_snapshot_digest
            state.capability_snapshot_digest = digest
            self._save_unlocked(state)
            self._append_event_unlocked(
                "capability_snapshot_bound",
                {"previous_digest": previous, "digest": digest, "explicit": True},
            )
            return state

    def require_capability_snapshot(self, digest: str) -> GoalState:
        state = self.load()
        if state.capability_snapshot_digest != digest:
            raise RuntimeError(
                "goal capability snapshot binding mismatch; explicit migration is required"
            )
        return state


class LifecycleGate:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.policy = LifecyclePolicy.from_repository(self.root)
        self.role_write: Dict[str, bool] = {}
        for path in sorted((self.root / "agents" / "core").glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("id"), str):
                continue
            access = data.get("access") or {}
            write = access.get("write")
            self.role_write[data["id"]] = bool(
                write is True or (isinstance(write, str) and write.strip())
            )

    def _role_is_writer(self, role: str) -> bool:
        if role not in self.role_write:
            raise ValueError("unknown role: " + role)
        return self.role_write[role]

    def suspects(self, state: GoalState) -> List[dict]:
        now = datetime.now(timezone.utc)
        result = []
        for item in state.assignments:
            if item.state not in ACTIVE_STATES:
                continue
            age = (now - timestamp(item.attempt_started_at or item.created_at)).total_seconds()
            idle = (now - timestamp(item.updated_at)).total_seconds()
            reason = ('timeout' if age >= self.policy.timeout_after_seconds else
                      'stale' if idle >= self.policy.stale_after_seconds else None)
            if reason:
                result.append({'assignment_id': item.assignment_id, 'reason': reason})
        return result

    def _counters(self, state: GoalState) -> dict:
        active = [item for item in state.assignments if item.state in ACTIVE_STATES]
        active_writers = sum(self._role_is_writer(item.role) for item in active)
        active_readers = len(active) - active_writers
        by_role: Dict[str, int] = {}
        for item in state.assignments:
            by_role[item.role] = by_role.get(item.role, 0) + 1
        return {
            "total": len(state.assignments),
            "active": len(active),
            "active_readers": active_readers,
            "active_writers": active_writers,
            "by_role": {key: by_role[key] for key in sorted(by_role)},
            "soft_limit": self.policy.soft_limit,
            "hard_limit": self.policy.hard_limit,
        }

    @staticmethod
    def _same_scope(left: List[str], right: List[str]) -> bool:
        return tuple(sorted(left)) == tuple(sorted(right))

    def resolved_task(self, state, role, task_domain, scopes):
        return any(item.recovery and item.recovery['phase'] == 'resolved' and item.role == role
                   and item.task_domain.casefold() == task_domain.casefold()
                   and self._same_scope(item.write_scope, scopes) for item in state.assignments)

    def evaluate(
        self,
        state: GoalState,
        *,
        role: str,
        task_domain: str,
        write_scope: List[str],
        change_set: Optional[str] = None,
        reconciled: bool = False,
        override_reason: Optional[str] = None,
        exception_kind: Optional[str] = None,
        material_change: bool = False,
        fresh_context: bool = False,
    ) -> LifecycleDecision:
        role = _nonempty("role", role)
        task_domain = _nonempty("task_domain", task_domain)
        scopes = _normalize_scopes(write_scope)
        if change_set is not None:
            change_set = _nonempty("change_set", change_set)
        if (
            type(reconciled) is not bool
            or type(material_change) is not bool
            or type(fresh_context) is not bool
        ):
            raise ValueError("reconciled, material_change and fresh_context must be booleans")
        if override_reason is not None:
            override_reason = _nonempty("override_reason", override_reason)
        if exception_kind is not None and exception_kind not in ALLOWED_HARD_LIMIT_EXCEPTIONS:
            raise ValueError("unsupported exception_kind: " + exception_kind)
        if fresh_context and not override_reason:
            raise ValueError("fresh_context requires override_reason")

        justification = {
            "reconciled": reconciled,
            "override_reason": override_reason,
            "exception_kind": exception_kind,
            "material_change": material_change,
            "fresh_context": fresh_context,
        }
        writer = self._role_is_writer(role)
        if writer and not scopes:
            raise ValueError("write-capable role requires a non-empty write_scope")
        if not writer and scopes:
            raise ValueError("read-only role must not receive write_scope")

        counters = self._counters(state)

        def decision(
            action: str,
            reasons: List[str],
            reuse_id: Optional[str] = None,
            proposed_id: Optional[str] = None,
        ) -> LifecycleDecision:
            return LifecycleDecision(
                action,
                reasons,
                reuse_id,
                proposed_id,
                counters,
                dict(justification),
            )

        if self.suspects(state):
            return decision('ESCALATE', ['suspect executor requires explicit reconciliation before dispatch'])

        if any(item.recovery and item.recovery['phase'] not in {'healthy', 'replaced', 'resolved'} for item in state.assignments):
            return decision('ESCALATE', ['transport recovery barrier; reconcile before dispatch'])
        if self.resolved_task(state, role, task_domain, scopes):
            return decision('ESCALATE', ['resolved failed task remains with parent; recovery budget cannot reset'])

        exact = [
            item
            for item in state.assignments
            if item.role == role
            and item.task_domain.casefold() == task_domain.casefold()
            and self._same_scope(item.write_scope, scopes)
            and item.state in RESUMABLE_STATES
        ]
        active_exact = [item for item in exact if item.state in ACTIVE_STATES]
        if len(active_exact) >= self.policy.max_same_role_domain_scope_active:
            if fresh_context:
                return decision(
                    "ESCALATE",
                    ["same role/domain/scope assignment is already active; fresh context must wait"],
                )
            return decision("REUSE", ["resume-before-spawn active match"], active_exact[-1].assignment_id)

        candidates = exact
        if counters['active'] >= self.policy.max_active_children:
            if not writer and counters['active_readers'] >= self.policy.max_parallel_readers:
                return decision('ESCALATE', ['reader capacity reached; wait at scheduling barrier'])
            if writer and counters['active_writers'] >= self.policy.max_parallel_writers:
                return decision('ESCALATE', ['writer capacity reached; wait at scheduling barrier'])
            return decision('ESCALATE', ['active child capacity reached; wait at scheduling barrier'])
        if role == "reviewer" and change_set is not None:
            review_matches = [
                item
                for item in state.assignments
                if item.role == role
                and item.change_set == change_set
                and item.state in RESUMABLE_STATES
            ]
            if review_matches:
                candidates = review_matches

        if candidates and not fresh_context:
            chosen = candidates[-1]
            if writer and counters["active_writers"] >= self.policy.max_parallel_writers:
                return decision(
                    "ESCALATE",
                    ["writer capacity reached; completed assignment cannot resume yet"],
                )
            if not writer and counters["active_readers"] >= self.policy.max_parallel_readers:
                return decision(
                    "ESCALATE",
                    ["reader capacity reached; completed assignment cannot resume yet"],
                )
            return decision("REUSE", ["resume-before-spawn completed match"], chosen.assignment_id)

        hard_exception = (
            counters["total"] >= self.policy.hard_limit
            and exception_kind in ALLOWED_HARD_LIMIT_EXCEPTIONS
            and bool(override_reason)
        )
        if counters["total"] >= self.policy.hard_limit and not hard_exception:
            return decision("REJECT", ["hard child-assignment ceiling reached"])

        if (
            counters["total"] >= self.policy.soft_limit
            and not hard_exception
            and not (reconciled and override_reason)
        ):
            return decision(
                "ESCALATE",
                ["soft child-assignment budget requires reconciliation and justification"],
            )

        if writer and counters["active_writers"] >= self.policy.max_parallel_writers:
            return decision(
                "ESCALATE", ["writer capacity reached; serialize or resume current writer"]
            )
        if not writer and counters["active_readers"] >= self.policy.max_parallel_readers:
            return decision("ESCALATE", ["reader capacity reached; wait/reuse before spawning"])

        if role == "architect":
            architect_count = sum(
                1
                for item in state.assignments
                if item.role == "architect" and item.state not in {"failed", "blocked"}
            )
            if architect_count >= self.policy.max_architect_per_goal and not (
                material_change and override_reason
            ):
                return decision("ESCALATE", ["architect consultation budget reached"])

        if role == "reviewer" and change_set is not None:
            reviewer_count = sum(
                1
                for item in state.assignments
                if item.role == "reviewer"
                and item.change_set == change_set
                and item.state not in {"failed", "blocked"}
            )
            if reviewer_count >= self.policy.max_reviewer_per_change_set:
                return decision("ESCALATE", ["reviewer budget for change-set reached"])

        proposed = "a-{:04d}".format(state.next_sequence)
        reasons = ["new child is within lifecycle policy"]
        if hard_exception:
            reasons.append("hard-limit exception: " + str(exception_kind))
        elif counters["total"] >= self.policy.soft_limit:
            reasons.append("soft-limit reconciliation accepted")
        if fresh_context:
            reasons.append("fresh-context override accepted")
        return decision("SPAWN", reasons, proposed_id=proposed)

    def _commit_spawn_locked(
        self,
        store: GoalStore,
        state: GoalState,
        decision: LifecycleDecision,
        *,
        role: str,
        task_domain: str,
        write_scope: List[str],
        change_set: Optional[str] = None,
    ) -> GoalAssignment:
        if not store._lock_held:
            raise RuntimeError("spawn commit requires the goal lock")
        if decision.action != "SPAWN" or not decision.proposed_assignment_id:
            raise ValueError("only SPAWN decisions can be committed")
        assignment = GoalAssignment(
            assignment_id=decision.proposed_assignment_id,
            role=role,
            task_domain=task_domain,
            state="pending",
            write_scope=write_scope,
            change_set=change_set,
        )
        state.assignments.append(assignment)
        state.next_sequence += 1
        store._save_unlocked(state)
        store._append_event_unlocked(
            "assignment_spawned",
            {"assignment": asdict(assignment), "decision": decision.as_dict()},
        )
        return assignment

    def evaluate_and_commit(
        self,
        store: GoalStore,
        *,
        role: str,
        task_domain: str,
        write_scope: List[str],
        change_set: Optional[str] = None,
        reconciled: bool = False,
        override_reason: Optional[str] = None,
        exception_kind: Optional[str] = None,
        material_change: bool = False,
        fresh_context: bool = False,
    ) -> Tuple[LifecycleDecision, Optional[GoalAssignment]]:
        with store.locked():
            state = store._load_unlocked()
            result = self.evaluate(
                state,
                role=role,
                task_domain=task_domain,
                write_scope=write_scope,
                change_set=change_set,
                reconciled=reconciled,
                override_reason=override_reason,
                exception_kind=exception_kind,
                material_change=material_change,
                fresh_context=fresh_context,
            )
            assignment: Optional[GoalAssignment] = None
            if result.action == "SPAWN":
                assignment = self._commit_spawn_locked(
                    store,
                    state,
                    result,
                    role=role,
                    task_domain=task_domain,
                    write_scope=write_scope,
                    change_set=change_set,
                )
            else:
                store._append_event_unlocked("gate_decision", result.as_dict())
            return result, assignment

    def _transition_locked(
        self, store: GoalStore, state: GoalState, assignment_id: str, new_state: str,
        approval_id: Optional[str] = None,
    ) -> GoalAssignment:
        if not store._lock_held:
            raise RuntimeError("assignment transition requires the goal lock")
        assignment_id = _nonempty("assignment_id", assignment_id)
        if new_state not in SUPPORTED_STATES:
            raise ValueError("unsupported assignment state: " + str(new_state))
        for item in state.assignments:
            if item.assignment_id == assignment_id:
                old = item.state
                from .workflow import Workflow
                flow = Workflow(self)
                action = 'transition:' + new_state
                if approval_id:
                    receipt = flow.receipt(state, approval_id, action, assignment_id)
                    if receipt:
                        # Return historical acknowledgement without another state write.
                        return GoalAssignment.from_dict({**asdict(item), 'state': receipt['state']})
                suspect = any(s['assignment_id'] == assignment_id for s in self.suspects(state))
                if item.recovery and item.recovery['phase'] in {'replaced', 'resolved'} and new_state in {'pending', 'running', 'completed'}:
                    raise ValueError('retired recovery assignment cannot be reactivated')
                if new_state in ACTIVE_STATES and self.resolved_task(state, item.role, item.task_domain, item.write_scope):
                    raise ValueError('resolved failed task remains with parent; cannot reactivate historical assignment')
                if new_state in ACTIVE_STATES and old != new_state and any(
                        other.recovery and other.recovery['phase'] not in {'healthy', 'replaced', 'resolved'}
                        for other in state.assignments):
                    raise ValueError('transport recovery barrier; reconcile before dispatch')
                if item.recovery and item.recovery['phase'] not in {'healthy', 'replaced'}:
                    if new_state in {'pending', 'running', 'completed'}:
                        raise ValueError('transport recovery must be reconciled through workflow')
                risky = (suspect or (old in ACTIVE_STATES and new_state in {'failed', 'blocked'})
                         or (old in {'failed', 'blocked'} and new_state != old)
                         or (old == 'running' and new_state == 'pending'))
                if risky or approval_id:
                    flow.require_approval(state, approval_id, action, assignment_id)
                if item.recovery and item.recovery['phase'] not in {'replaced', 'resolved'} and new_state in {'failed', 'blocked'}:
                    flow.require_approval(state, approval_id, action, assignment_id)
                    item.recovery['phase'] = 'resolved'
                if old not in ACTIVE_STATES and new_state in ACTIVE_STATES:
                    counters = self._counters(state)
                    writer = self._role_is_writer(item.role)
                    exact_active = sum(
                        1
                        for other in state.assignments
                        if other.assignment_id != item.assignment_id
                        and other.role == item.role
                        and other.task_domain.casefold() == item.task_domain.casefold()
                        and self._same_scope(other.write_scope, item.write_scope)
                        and other.state in ACTIVE_STATES
                    )
                    if exact_active >= self.policy.max_same_role_domain_scope_active:
                        raise ValueError("same role/domain/scope assignment is already active")
                    if writer and counters["active_writers"] >= self.policy.max_parallel_writers:
                        raise ValueError("writer capacity reached; cannot reactivate assignment")
                    if not writer and counters["active_readers"] >= self.policy.max_parallel_readers:
                        raise ValueError("reader capacity reached; cannot reactivate assignment")
                    if counters['active'] >= self.policy.max_active_children:
                        raise ValueError('active child capacity reached; cannot reactivate assignment')
                item.state = new_state
                item.updated_at = _utc_now()
                if old not in ACTIVE_STATES and new_state in ACTIVE_STATES or old == 'running' and new_state == 'pending':
                    item.attempt_started_at = item.updated_at
                if approval_id:
                    flow.record_receipt(state, approval_id, action, item)
                store._save_unlocked(state)
                store._append_event_unlocked(
                    "assignment_transition",
                    {"assignment_id": assignment_id, "from": old, "to": new_state},
                )
                return item
        raise ValueError("assignment not found: " + assignment_id)

    def transition_atomic(
        self, store: GoalStore, assignment_id: str, new_state: str,
        approval_id: Optional[str] = None,
    ) -> GoalAssignment:
        with store.locked():
            state = store._load_unlocked()
            return self._transition_locked(store, state, assignment_id, new_state, approval_id)

    def summary(self, state: GoalState) -> dict:
        counters = self._counters(state)
        if counters["total"] >= self.policy.hard_limit:
            budget = "hard_limit"
        elif counters["total"] >= self.policy.soft_limit:
            budget = "soft_limit"
        else:
            budget = "within_budget"
        return {
            "goal_id": state.goal_id,
            "revision": state.revision,
            **counters,
            "budget_state": budget,
            "assignments": [asdict(item) for item in state.assignments],
            "suspect": self.suspects(state),
            "checkpoint": state.workflow['checkpoint'],
        }
