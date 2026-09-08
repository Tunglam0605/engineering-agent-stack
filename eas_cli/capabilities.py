from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Dict, Iterable, Optional

from runtime.capabilities.builtins import load_builtin_catalog
from runtime.capabilities.detection import detect_project
from runtime.capabilities.project import (
    ProjectCapabilityService, initialize_project_profile, load_project_profile,
    profile_path, project_root,
)
from runtime.capabilities.snapshot import bind_snapshot, migrate_snapshot, read_snapshot

from .version import __version__


def _service() -> ProjectCapabilityService:
    return ProjectCapabilityService(eas_version=__version__)


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        command = payload.get("command")
        if command == "preset-list":
            for item in payload["presets"]:
                print("{} {} - {}".format(item["id"], item["version"], item["description"]))
        elif command == "preset-show":
            print(json.dumps(payload["preset"], sort_keys=True, indent=2))
        elif command == "preset-detect":
            detection = payload["detection"]
            print("Detection: {} confidence={}".format(detection["status"], detection["confidence"]))
            if detection["recommended_preset"]:
                print("Recommended preset: " + detection["recommended_preset"])
            if detection["contradictions"]:
                for item in detection["contradictions"]:
                    print("AMBIGUITY: " + item)
            print("Release readiness: NOT ASSESSED")
        elif command == "preset-check":
            print("Preset {}: {}".format(payload["preset"], payload["status"]))
            for item in payload["checks"]:
                print("{} [{}] {}".format(item["rule_id"], item["classification"], item["status"]))
        elif command == "project-status":
            profile = payload["profile"]
            print("Project: " + payload["project"])
            print("Profile: " + (profile["preset"] if profile else "none"))
            print("Detection: {} / {}".format(payload["detection"]["status"], payload["detection"]["confidence"]))
            if payload["detection_conflict"]:
                print("CONFLICT: tracked={} detected={} (tracked profile remains authoritative)".format(
                    payload["detection_conflict"]["tracked_preset"],
                    payload["detection_conflict"]["detected_preset"],
                ))
            print("Snapshot: " + payload["snapshot"]["status"])
        elif command == "project-migrate-snapshot":
            print("Snapshot migrated explicitly: " + payload["digest"])
        else:
            print(json.dumps(payload, sort_keys=True, indent=2))


def preset_list(*, as_json: bool = False) -> int:
    catalog = load_builtin_catalog()
    payload = {
        "command": "preset-list",
        "presets": [
            {
                "id": preset.id,
                "version": preset.version,
                "description": preset.description,
                "skills": list(preset.skills),
                "required_rules": list(preset.required_rules),
            }
            for preset in sorted(catalog.presets.values(), key=lambda item: item.id)
        ],
    }
    _emit(payload, as_json)
    return 0


def preset_show(preset_id: str, *, as_json: bool = False) -> int:
    catalog = load_builtin_catalog()
    preset = catalog.presets.get(preset_id)
    if preset is None:
        raise ValueError("unknown preset: " + preset_id)
    payload = {"command": "preset-show", "preset": asdict(preset)}
    _emit(payload, as_json)
    return 0


def preset_detect(project: Path, *, as_json: bool = False) -> int:
    root = project_root(project)
    payload = {"command": "preset-detect", "project": str(root), "detection": detect_project(root).as_dict()}
    _emit(payload, as_json)
    return 0


def _parse_overrides(items: Iterable[str]) -> Dict[str, object]:
    result: Dict[str, object] = {}
    for item in items:
        if "=" not in item:
            raise ValueError("override must use PATH=JSON_VALUE")
        path, raw = item.split("=", 1)
        if path in result:
            raise ValueError("duplicate CLI override: " + path)
        try:
            result[path] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("override value must be valid JSON: " + item) from exc
    return result


def preset_check(
    project: Path,
    preset_id: Optional[str],
    *,
    overrides: Iterable[str] = (),
    as_json: bool = False,
) -> int:
    root = project_root(project)
    service = _service()
    profile = load_project_profile(root)
    active = preset_id or (profile.preset if profile is not None else None)
    if active is None:
        raise ValueError("preset check requires PRESET or a tracked .eas/project.toml")
    payload = service.check_preset(root, active)
    parsed_overrides = _parse_overrides(overrides)
    snapshot = service.resolve_snapshot(
        root,
        preset_id=active if profile is None else None,
        cli_overrides=parsed_overrides or None,
    )
    payload["resolved_digest"] = snapshot.digest
    payload["override_paths"] = sorted(parsed_overrides)
    _emit(payload, as_json)
    return 0 if payload["status"] == "PASS" else 3


def project_status(project: Path, *, as_json: bool = False) -> int:
    payload = _service().project_status(project)
    _emit(payload, as_json)
    return 0


def initialize_profile_and_snapshot(project: Path, preset_id: str, *, dry_run: bool = False) -> Path:
    root = project_root(project)
    # Validate preset and non-overwrite before any caller mutates project-managed files.
    path = initialize_project_profile(root, preset_id, dry_run=True)
    if dry_run:
        return path
    created = initialize_project_profile(root, preset_id, dry_run=False)
    try:
        snapshot = _service().resolve_snapshot(root)
        bind_snapshot(root, snapshot)
    except Exception:
        # Roll back only the profile created by this operation. Runtime metadata is
        # written atomically and cannot silently replace a prior binding.
        try:
            created.unlink()
            if created.parent.is_dir() and not any(created.parent.iterdir()):
                created.parent.rmdir()
        except OSError:
            pass
        raise
    return created


def project_migrate_snapshot(
    project: Path,
    expected_old_digest: Optional[str],
    *,
    as_json: bool = False,
) -> int:
    root = project_root(project)
    if load_project_profile(root) is None:
        raise ValueError("snapshot migration requires a tracked project profile")
    current = _service().resolve_snapshot(root)
    old = read_snapshot(root)
    if old is None and expected_old_digest is not None:
        raise RuntimeError("no persisted snapshot exists to match expected digest")
    path = migrate_snapshot(root, current, expected_old_digest=expected_old_digest)
    payload = {
        "command": "project-migrate-snapshot",
        "path": str(path),
        "digest": current.digest,
        "previous_digest": None if old is None else old.digest,
    }
    _emit(payload, as_json)
    return 0
