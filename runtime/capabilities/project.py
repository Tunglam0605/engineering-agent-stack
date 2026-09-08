from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .builtins import BuiltinCatalog, builtin_root, load_builtin_catalog
from .detection import detect_project
from .models import ProjectProfile, ResolvedCapabilitySnapshot
from .parser import parse_contract, validate_id, version_satisfies_range
from .resolver import resolve_config
from .snapshot import build_snapshot, read_snapshot, source_digest
from .trusted import TrustedCheckerRegistry


def project_root(path: Path) -> Path:
    probe = path.expanduser().resolve()
    if probe.is_file():
        probe = probe.parent
    while True:
        if (probe / ".git").exists():
            return probe
        if probe.parent == probe:
            raise ValueError("project is not inside a Git repository")
        probe = probe.parent


def profile_path(project: Path) -> Path:
    return project_root(project) / ".eas" / "project.toml"


def load_project_profile(project: Path) -> Optional[ProjectProfile]:
    path = profile_path(project)
    if not path.is_file():
        return None
    profile = parse_contract(path, "project-profile")
    if not isinstance(profile, ProjectProfile):
        raise ValueError("project profile parser returned wrong contract")
    return profile


def _profile_values(profile: ProjectProfile) -> Dict[str, Any]:
    values = {section: dict(inner) for section, inner in profile.values.items()}
    if profile.required_rules:
        rules = values.setdefault("rules", {})
        if "required_rules" in rules and rules["required_rules"] != profile.required_rules:
            raise ValueError("project profile defines required_rules twice with different values")
        rules["required_rules"] = list(profile.required_rules)
    if profile.skills:
        skills = values.setdefault("skills", {})
        if "enabled" in skills and skills["enabled"] != profile.skills:
            raise ValueError("project profile defines skills twice with different values")
        skills["enabled"] = list(profile.skills)
    return values


def _find_preset_resource(catalog: BuiltinCatalog, preset_id: str) -> Path:
    ext_id = catalog.preset_extension[preset_id]
    manifest = catalog.extensions[ext_id]
    root = catalog.preset_roots[preset_id]
    for relative in manifest.provides["presets"]:
        candidate = root / Path(relative)
        parsed = parse_contract(candidate, "preset")
        if parsed.id == preset_id:
            return candidate
    raise ValueError("unable to locate built-in preset resource: " + preset_id)


def _sources_for(
    catalog: BuiltinCatalog,
    preset_id: str,
    profile: Optional[ProjectProfile],
    project: Path,
) -> List[Dict[str, str]]:
    ext_id = catalog.preset_extension[preset_id]
    ext = catalog.extensions[ext_id]
    ext_path = builtin_root() / ext_id / "manifest.yaml"
    preset_path = _find_preset_resource(catalog, preset_id)
    sources = [
        {"kind": "extension", "id": ext.id, "version": ext.version, "digest": source_digest(ext_path)},
        {"kind": "preset", "id": preset_id, "version": catalog.presets[preset_id].version, "digest": source_digest(preset_path)},
    ]
    if profile is not None:
        path = profile_path(project)
        sources.append({
            "kind": "project-profile", "id": profile.id, "version": "schema-1",
            "digest": source_digest(path),
        })
    return sources


class ProjectCapabilityService:
    def __init__(self, catalog: Optional[BuiltinCatalog] = None, *, eas_version: str = "0.6.0") -> None:
        self.catalog = catalog or load_builtin_catalog()
        self.eas_version = eas_version
        self.checkers = TrustedCheckerRegistry()
        self.checkers.validate_references(self.catalog.rules.values())

    def resolve_snapshot(
        self,
        project: Path,
        *,
        preset_id: Optional[str] = None,
        cli_overrides: Optional[Mapping[str, Any]] = None,
    ) -> ResolvedCapabilitySnapshot:
        root = project_root(project)
        profile = load_project_profile(root)
        active = preset_id or (profile.preset if profile is not None else None)
        if active is None:
            raise ValueError("no active preset; create .eas/project.toml or pass an explicit preset")
        if active not in self.catalog.presets:
            raise ValueError("unknown preset: " + active)
        if profile is not None and preset_id is not None and profile.preset != preset_id:
            raise ValueError("explicit preset conflicts with tracked project profile")
        preset = self.catalog.presets[active]
        ext_id = self.catalog.preset_extension[active]
        extension = self.catalog.extensions[ext_id]
        if not version_satisfies_range(self.eas_version, extension.requires_eas):
            raise ValueError(
                "extension {} {} requires EAS {}, current {}".format(
                    extension.id, extension.version, extension.requires_eas, self.eas_version
                )
            )
        project_values = _profile_values(profile) if profile is not None else None
        resolved = resolve_config(
            extension_defaults=[(extension.id, extension.defaults)],
            preset_defaults=preset.defaults,
            project_values=project_values,
            cli_overrides=cli_overrides,
        )
        enabled = list((resolved.values.get("skills") or {}).get("enabled") or preset.skills)
        unknown_skills = sorted(set(enabled) - set(preset.skills))
        if unknown_skills:
            raise ValueError("project enables skills outside active preset: " + ", ".join(unknown_skills))
        selected_rules = list((resolved.values.get("rules") or {}).get("required_rules") or [])
        unknown_rules = sorted(set(selected_rules) - set(self.catalog.rules))
        if unknown_rules:
            raise ValueError("project requires unknown rules: " + ", ".join(unknown_rules))
        detection = detect_project(root)
        project_id = profile.id if profile is not None else root.name.casefold().replace("_", "-")
        try:
            validate_id(project_id, "project id")
        except ValueError:
            project_id = "project"
        return build_snapshot(
            eas_version=self.eas_version,
            project_id=project_id,
            active_preset=active,
            sources=_sources_for(self.catalog, active, profile, root),
            resolved_values=resolved.values,
            lineage=resolved.lineage,
            selected_skills=enabled,
            selected_rules=selected_rules,
            detection=detection.as_dict(),
        )

    def project_status(self, project: Path) -> dict:
        root = project_root(project)
        profile = load_project_profile(root)
        detection = detect_project(root)
        conflict = None
        if (
            profile is not None
            and detection.status == "RECOMMENDED"
            and detection.recommended_preset is not None
            and detection.recommended_preset != profile.preset
            and detection.confidence in {"HIGH", "MEDIUM"}
        ):
            conflict = {
                "tracked_preset": profile.preset,
                "detected_preset": detection.recommended_preset,
                "message": "tracked project profile remains authoritative; detection never auto-activates",
            }
        snapshot_state = "UNBOUND"
        current_digest = None
        persisted_digest = None
        snapshot_error = None
        if profile is not None:
            current = self.resolve_snapshot(root)
            current_digest = current.digest
            try:
                persisted = read_snapshot(root)
            except ValueError as exc:
                persisted = None
                snapshot_state = "CORRUPT"
                snapshot_error = str(exc)
            if snapshot_state != "CORRUPT" and persisted is not None:
                persisted_digest = persisted.digest
                snapshot_state = "BOUND" if persisted.digest == current.digest else "DRIFT"
        return {
            "command": "project-status",
            "project": str(root),
            "profile": None if profile is None else {
                "id": profile.id, "preset": profile.preset,
                "path": str(profile_path(root)), "tracked_policy": "commit-friendly-no-secrets",
            },
            "detection": detection.as_dict(),
            "detection_conflict": conflict,
            "snapshot": {
                "status": snapshot_state,
                "current_digest": current_digest,
                "persisted_digest": persisted_digest,
                "error": snapshot_error,
            },
        }

    def check_preset(self, project: Path, preset_id: str) -> dict:
        root = project_root(project)
        if preset_id not in self.catalog.presets:
            raise ValueError("unknown preset: " + preset_id)
        preset = self.catalog.presets[preset_id]
        results = []
        overall = "PASS"
        for rule_id in preset.required_rules:
            rule = self.catalog.rules[rule_id]
            if rule.classification == "guidance":
                results.append({
                    "rule_id": rule.id,
                    "classification": rule.classification,
                    "status": "GUIDANCE",
                    "message": "requires engineering judgment; no automatic enforcement claim",
                })
                continue
            checked = self.checkers.run(rule.checker_id, root)
            results.append({
                "rule_id": rule.id,
                "classification": rule.classification,
                **checked.as_dict(),
            })
            if checked.status in {"FAIL", "ERROR"}:
                overall = "FAIL"
        return {
            "command": "preset-check",
            "preset": preset_id,
            "status": overall,
            "checks": results,
            "enforcement_boundary": "only trusted core checker IDs execute; package content is declarative",
        }


def _derive_project_id(root: Path) -> str:
    value = re.sub(r"[^a-z0-9._-]+", "-", root.name.casefold()).strip("-._")
    if not value:
        value = "project"
    value = value[:64]
    try:
        return validate_id(value, "project id")
    except ValueError:
        return "project"


def initialize_project_profile(
    project: Path,
    preset_id: str,
    *,
    dry_run: bool = False,
    catalog: Optional[BuiltinCatalog] = None,
) -> Path:
    root = project_root(project)
    catalog = catalog or load_builtin_catalog()
    if preset_id not in catalog.presets:
        raise ValueError("unknown preset: " + preset_id)
    path = root / ".eas" / "project.toml"
    if path.exists():
        raise RuntimeError("project profile already exists; init never overwrites " + str(path))
    project_id = _derive_project_id(root)
    content = (
        'kind = "project-profile"\n'
        'schema_version = 1\n'
        'id = "{}"\n'.format(project_id)
        + 'preset = "{}"\n'.format(preset_id)
        + '\n# Tracked, commit-friendly configuration only. Do not place secrets here.\n'
        + '[values]\n'
    )
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        # Parse immediately so a malformed writer can never leave a silently accepted profile.
        parse_contract(path, "project-profile")
    return path
