from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .models import ResolvedCapabilitySnapshot
from ..workflow_state import strict_json

SNAPSHOT_SCHEMA_VERSION = 1


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _digest_payload(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def source_digest(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def build_snapshot(
    *,
    eas_version: str,
    project_id: str,
    active_preset: str,
    sources: List[Dict[str, str]],
    resolved_values: Dict[str, Any],
    lineage: Dict[str, List[str]],
    selected_skills: List[str],
    selected_rules: List[str],
    detection: Dict[str, Any],
) -> ResolvedCapabilitySnapshot:
    body = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "eas_version": eas_version,
        "project_id": project_id,
        "active_preset": active_preset,
        "sources": sources,
        "resolved_values": resolved_values,
        "lineage": lineage,
        "selected_skills": selected_skills,
        "selected_rules": selected_rules,
        "detection": detection,
    }
    digest = _digest_payload(body)
    return ResolvedCapabilitySnapshot(digest=digest, **body)


def validate_snapshot(snapshot: ResolvedCapabilitySnapshot) -> None:
    body = snapshot.as_dict()
    digest = body.pop("digest")
    if snapshot.schema_version != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError("unsupported capability snapshot schema")
    expected = _digest_payload(body)
    if digest != expected:
        raise ValueError("capability snapshot digest mismatch")


def git_dir(project: Path) -> Path:
    root = project.expanduser().resolve()
    dotgit = root / ".git"
    if dotgit.is_dir():
        return dotgit.resolve()
    if dotgit.is_file():
        line = dotgit.read_text(encoding="utf-8").strip()
        if not line.lower().startswith("gitdir:"):
            raise ValueError("unsupported .git file format")
        raw = line.split(":", 1)[1].strip()
        candidate = Path(raw)
        return (candidate if candidate.is_absolute() else root / candidate).resolve()
    raise ValueError("project must be a Git repository root")


def snapshot_path(project: Path) -> Path:
    return git_dir(project) / "eas" / "capabilities" / "snapshot.json"


def _snapshot_from_dict(payload: dict) -> ResolvedCapabilitySnapshot:
    required = {
        "schema_version", "eas_version", "project_id", "active_preset", "sources",
        "resolved_values", "lineage", "selected_skills", "selected_rules", "detection", "digest",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("capability snapshot has unknown or missing fields")
    if type(payload["schema_version"]) is not int:
        raise ValueError("snapshot schema_version must be an integer")
    for key in ("eas_version", "project_id", "active_preset", "digest"):
        if not isinstance(payload[key], str) or not payload[key]:
            raise ValueError("snapshot {} must be non-empty text".format(key))
    if not isinstance(payload["sources"], list) or not all(isinstance(item, dict) for item in payload["sources"]):
        raise ValueError("snapshot sources must be a list of mappings")
    if not isinstance(payload["resolved_values"], dict) or not isinstance(payload["lineage"], dict):
        raise ValueError("snapshot resolved_values/lineage must be mappings")
    if not isinstance(payload["selected_skills"], list) or not isinstance(payload["selected_rules"], list):
        raise ValueError("snapshot selected ids must be lists")
    if not isinstance(payload["detection"], dict):
        raise ValueError("snapshot detection must be a mapping")
    snapshot = ResolvedCapabilitySnapshot(**payload)
    validate_snapshot(snapshot)
    return snapshot


def read_snapshot(project: Path) -> Optional[ResolvedCapabilitySnapshot]:
    path = snapshot_path(project)
    if not path.is_file():
        return None
    try:
        payload = strict_json(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("capability snapshot is invalid JSON: " + str(exc)) from exc
    return _snapshot_from_dict(payload)


def write_snapshot(project: Path, snapshot: ResolvedCapabilitySnapshot) -> Path:
    validate_snapshot(snapshot)
    path = snapshot_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.tmp")
    content = json.dumps(snapshot.as_dict(), sort_keys=True, indent=2, allow_nan=False) + "\n"
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)
    if os.name == "posix":
        fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return path


def bind_snapshot(project: Path, snapshot: ResolvedCapabilitySnapshot) -> Path:
    """Create the binding, or require an exact digest match if already bound."""
    current = read_snapshot(project)
    if current is None:
        return write_snapshot(project, snapshot)
    if current.digest != snapshot.digest:
        raise RuntimeError(
            "capability snapshot drift detected; explicit migration is required ({} -> {})".format(
                current.digest, snapshot.digest
            )
        )
    return snapshot_path(project)


def migrate_snapshot(
    project: Path,
    snapshot: ResolvedCapabilitySnapshot,
    *,
    expected_old_digest: Optional[str] = None,
) -> Path:
    """Explicitly replace a persisted binding after caller review/approval."""
    current = read_snapshot(project)
    if current is not None and expected_old_digest is not None and current.digest != expected_old_digest:
        raise RuntimeError("capability snapshot changed before migration; re-read status")
    return write_snapshot(project, snapshot)
