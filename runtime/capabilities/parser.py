from __future__ import annotations

from datetime import date, datetime
import math
from pathlib import Path, PureWindowsPath
import re
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

import yaml
try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10
    import tomli as tomllib  # type: ignore[no-redef]

from .models import (
    CORE_ROLES, RULE_CLASSES, RULE_SEVERITIES,
    ExtensionManifest, PresetContract, ProjectProfile, RuleContract, SkillContract,
)

ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
RANGE_CLAUSE_RE = re.compile(r"^(>=|<=|>|<|==)(.+)$")
FORBIDDEN_EXEC_KEYS = {
    "script", "scripts", "hook", "hooks", "entrypoint", "entrypoints",
    "command", "commands", "exec", "executable", "import", "eval",
    "mcp_server", "mcp_servers", "remote", "remote_url", "url_loader",
}
SECRET_FRAGMENTS = (
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "private_key", "credential", "auth_key",
)


class StrictYamlLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: StrictYamlLoader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError("YAML mapping keys must be strings")
        if key in result:
            raise ValueError("duplicate YAML key: " + key)
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictYamlLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def validate_id(value: Any, name: str = "id") -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError(name + " must match [a-z0-9][a-z0-9._-]{0,63}")
    if PureWindowsPath(value).is_reserved():
        raise ValueError(name + " is reserved on Windows: " + value)
    return value


def validate_semver(value: Any, name: str = "version") -> str:
    if not isinstance(value, str) or not SEMVER_RE.fullmatch(value):
        raise ValueError(name + " must be SemVer 2.0")
    return value


def validate_requires_eas(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 96:
        raise ValueError("requires_eas must be a short version range string")
    clauses = value.split(",")
    if not 1 <= len(clauses) <= 2:
        raise ValueError("requires_eas supports one or two comma-separated clauses")
    for raw in clauses:
        clause = raw.strip()
        match = RANGE_CLAUSE_RE.fullmatch(clause)
        if not match:
            raise ValueError("unsupported requires_eas clause: " + clause)
        validate_semver(match.group(2), "requires_eas version")
    return ",".join(item.strip() for item in clauses)



def _semver_key(value: str):
    match = SEMVER_RE.fullmatch(validate_semver(value))
    major, minor, patch = (int(match.group(i)) for i in (1, 2, 3))
    prerelease = match.group(4)
    if prerelease is None:
        pre_key = (1,)
    else:
        parts = []
        for part in prerelease.split("."):
            if part.isdigit():
                parts.append((0, int(part)))
            else:
                parts.append((1, part))
        pre_key = (0, tuple(parts))
    return (major, minor, patch, pre_key)


def version_satisfies_range(version: str, range_text: str) -> bool:
    current = _semver_key(version)
    normalized = validate_requires_eas(range_text)
    for clause in normalized.split(","):
        match = RANGE_CLAUSE_RE.fullmatch(clause)
        if match is None:
            return False
        operator, target_text = match.groups()
        target = _semver_key(target_text)
        if operator == ">=" and not current >= target:
            return False
        if operator == "<=" and not current <= target:
            return False
        if operator == ">" and not current > target:
            return False
        if operator == "<" and not current < target:
            return False
        if operator == "==" and not current == target:
            return False
    return True

def _strict_scalar_tree(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(path + " contains a non-finite number")
        return
    if isinstance(value, (date, datetime)):
        raise ValueError(path + " contains an implicit date/time scalar")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _strict_scalar_tree(item, "{}[{}]".format(path, index))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(path + " has a non-string mapping key")
            _strict_scalar_tree(item, path + "." + key)
        return
    raise ValueError(path + " contains unsupported scalar type " + type(value).__name__)


def _scan_yaml_features(text: str) -> None:
    try:
        for token in yaml.scan(text):
            if isinstance(token, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken)):
                raise ValueError("YAML anchors and aliases are not supported")
            if isinstance(token, yaml.tokens.TagToken):
                raise ValueError("YAML custom tags are not supported")
    except yaml.YAMLError as exc:
        raise ValueError("malformed YAML: " + str(exc)) from exc


def load_yaml_mapping(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    _scan_yaml_features(text)
    try:
        value = yaml.load(text, Loader=StrictYamlLoader)
    except (yaml.YAMLError, ValueError) as exc:
        raise ValueError("{}: {}".format(path, exc)) from exc
    if not isinstance(value, dict):
        raise ValueError(str(path) + ": expected a mapping")
    _strict_scalar_tree(value)
    return value


def load_toml_mapping(path: Path) -> Dict[str, Any]:
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeError) as exc:  # type: ignore[attr-defined]
        raise ValueError("malformed TOML: " + str(exc)) from exc
    if not isinstance(value, dict):
        raise ValueError(str(path) + ": expected a TOML table")
    _strict_scalar_tree(value)
    return value


def _expect_keys(data: Mapping[str, Any], required: Iterable[str], optional: Iterable[str] = ()) -> None:
    required_set = set(required)
    optional_set = set(optional)
    missing = sorted(required_set - set(data))
    unknown = sorted(set(data) - required_set - optional_set)
    if missing:
        raise ValueError("missing required keys: " + ", ".join(missing))
    if unknown:
        raise ValueError("unknown keys: " + ", ".join(unknown))


def _text(value: Any, name: str, limit: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(name + " must be non-empty text <= {} chars".format(limit))
    return value.strip()


def _string_list(value: Any, name: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(name + " must be a list of non-empty strings")
    if not allow_empty and not value:
        raise ValueError(name + " must not be empty")
    seen = set()
    out = []
    for item in value:
        clean = item.strip()
        folded = clean.casefold()
        if folded in seen:
            raise ValueError(name + " contains a duplicate/case-fold collision: " + clean)
        seen.add(folded)
        out.append(clean)
    return out


def safe_relative_path(value: Any, name: str = "path") -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(name + " must be a non-empty normalized relative path")
    raw = value.replace("\\", "/")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise ValueError(name + " must be package-relative")
    parts = []
    for part in raw.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError(name + " must not contain parent traversal")
        if part.endswith((".", " ")) or re.search(r'[<>:"|?*\x00-\x1f]', part):
            raise ValueError(name + " contains a cross-platform ambiguous component")
        if PureWindowsPath(part).is_reserved():
            raise ValueError(name + " contains a reserved Windows component")
        parts.append(part)
    if not parts:
        raise ValueError(name + " resolves to an empty path")
    return "/".join(parts)


def _existing_reparse(path: Path) -> bool:
    try:
        stat = path.lstat()
    except OSError:
        return False
    attrs = getattr(stat, "st_file_attributes", 0)
    return path.is_symlink() or bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT


def safe_join(root: Path, relative: str) -> Path:
    normalized = safe_relative_path(relative)
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*normalized.split("/"))
    probe = root_resolved
    for part in normalized.split("/"):
        probe = probe / part
        if probe.exists() and _existing_reparse(probe):
            raise ValueError("resource path crosses a symlink/reparse point: " + normalized)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("resource path escapes package root: " + normalized) from exc
    return candidate


def reject_casefold_collisions(paths: Sequence[str], name: str = "paths") -> None:
    seen: Dict[str, str] = {}
    for item in paths:
        normalized = safe_relative_path(item)
        folded = normalized.casefold()
        previous = seen.get(folded)
        if previous is not None and previous != normalized:
            raise ValueError("{} case-fold collision: {} vs {}".format(name, previous, normalized))
        if previous is not None:
            raise ValueError("{} duplicate: {}".format(name, normalized))
        seen[folded] = normalized


def reject_executable_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() in FORBIDDEN_EXEC_KEYS:
                raise ValueError(path + " contains forbidden executable field: " + key)
            reject_executable_keys(item, path + "." + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_executable_keys(item, "{}[{}]".format(path, index))


def reject_secret_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            folded = key.casefold()
            if any(fragment in folded for fragment in SECRET_FRAGMENTS):
                raise ValueError(path + " contains a secret-like field: " + key)
            reject_secret_fields(item, path + "." + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_secret_fields(item, "{}[{}]".format(path, index))


def _validate_common(data: Mapping[str, Any], kind: str) -> None:
    if data.get("kind") != kind:
        raise ValueError("kind must be " + kind)
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported schema_version; v0.6 supports only 1")
    validate_id(data.get("id"))


def parse_extension_manifest(data: Mapping[str, Any]) -> ExtensionManifest:
    _expect_keys(
        data,
        {"kind", "schema_version", "id", "version", "description", "requires_eas", "provenance", "provides"},
        {"defaults"},
    )
    _validate_common(data, "extension-manifest")
    validate_semver(data["version"])
    validate_requires_eas(data["requires_eas"])
    _text(data["description"], "description", 1024)
    provenance = data["provenance"]
    if not isinstance(provenance, dict):
        raise ValueError("provenance must be a mapping")
    _expect_keys(provenance, {"source", "revision", "license"})
    for key in ("source", "revision", "license"):
        _text(provenance[key], "provenance." + key, 512)
    provides = data["provides"]
    if not isinstance(provides, dict):
        raise ValueError("provides must be a mapping")
    _expect_keys(provides, {"skills", "rules", "presets"})
    parsed_provides = {}
    all_paths = []
    for key in ("skills", "rules", "presets"):
        values = _string_list(provides[key], "provides." + key)
        normalized = [safe_relative_path(item, "provides." + key) for item in values]
        reject_casefold_collisions(normalized, "provides." + key)
        parsed_provides[key] = normalized
        all_paths.extend(normalized)
    reject_casefold_collisions(all_paths, "provides")
    defaults = data.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError("defaults must be a mapping")
    reject_executable_keys(defaults, "defaults")
    return ExtensionManifest(
        kind="extension-manifest", schema_version=1, id=data["id"], version=data["version"],
        description=data["description"].strip(), requires_eas=data["requires_eas"],
        provenance=dict(provenance), provides=parsed_provides, defaults=dict(defaults),
    )


def parse_skill(data: Mapping[str, Any]) -> SkillContract:
    _expect_keys(
        data,
        {"kind", "schema_version", "id", "version", "summary", "roles", "task_tags", "body", "context_cost"},
        {"triggers", "references"},
    )
    _validate_common(data, "skill")
    validate_semver(data["version"])
    summary = _text(data["summary"], "summary", 1024)
    roles = _string_list(data["roles"], "roles", allow_empty=False)
    invalid_roles = sorted(set(roles) - CORE_ROLES)
    if invalid_roles:
        raise ValueError("skill contains unknown core roles: " + ", ".join(invalid_roles))
    task_tags = _string_list(data["task_tags"], "task_tags")
    for tag in task_tags:
        validate_id(tag, "task tag")
    triggers = _string_list(data.get("triggers", []), "triggers")
    body = safe_relative_path(data["body"], "body")
    references = [safe_relative_path(item, "references") for item in _string_list(data.get("references", []), "references")]
    reject_casefold_collisions([body] + references, "skill resources")
    cost = data["context_cost"]
    if type(cost) is not int or not 1 <= cost <= 65536:
        raise ValueError("context_cost must be an integer in [1, 65536]")
    return SkillContract(
        kind="skill", schema_version=1, id=data["id"], version=data["version"], summary=summary,
        roles=roles, task_tags=task_tags, triggers=triggers, body=body,
        references=references, context_cost=cost,
    )


def parse_rule(data: Mapping[str, Any]) -> RuleContract:
    _expect_keys(
        data,
        {"kind", "schema_version", "id", "version", "classification", "scope", "severity", "evidence", "text"},
        {"checker_id"},
    )
    _validate_common(data, "rule")
    validate_semver(data["version"])
    classification = data["classification"]
    if classification not in RULE_CLASSES:
        raise ValueError("classification must be guidance|validator|gate")
    severity = data["severity"]
    if severity not in RULE_SEVERITIES:
        raise ValueError("severity must be info|warning|error")
    scope = _string_list(data["scope"], "scope", allow_empty=False)
    evidence = _string_list(data["evidence"], "evidence")
    checker_id = data.get("checker_id")
    if checker_id is not None:
        validate_id(checker_id, "checker_id")
    if classification == "guidance" and checker_id is not None:
        raise ValueError("guidance rules cannot claim an executable checker")
    if classification in {"validator", "gate"} and checker_id is None:
        raise ValueError(classification + " rules must reference a trusted checker_id")
    return RuleContract(
        kind="rule", schema_version=1, id=data["id"], version=data["version"],
        classification=classification, scope=scope, severity=severity, evidence=evidence,
        text=_text(data["text"], "text"), checker_id=checker_id,
    )


def parse_preset(data: Mapping[str, Any]) -> PresetContract:
    _expect_keys(
        data,
        {"kind", "schema_version", "id", "version", "description", "skills", "required_rules", "defaults", "detection_hints"},
    )
    _validate_common(data, "preset")
    validate_semver(data["version"])
    skills = _string_list(data["skills"], "skills")
    required_rules = _string_list(data["required_rules"], "required_rules")
    for item in skills:
        validate_id(item, "skill id")
    for item in required_rules:
        validate_id(item, "rule id")
    defaults = data["defaults"]
    if not isinstance(defaults, dict):
        raise ValueError("defaults must be a mapping")
    reject_executable_keys(defaults, "defaults")
    hints = _string_list(data["detection_hints"], "detection_hints")
    return PresetContract(
        kind="preset", schema_version=1, id=data["id"], version=data["version"],
        description=_text(data["description"], "description", 1024), skills=skills,
        required_rules=required_rules, defaults=dict(defaults), detection_hints=hints,
    )


def parse_project_profile(data: Mapping[str, Any]) -> ProjectProfile:
    _expect_keys(data, {"kind", "schema_version", "id", "preset"}, {"values", "required_rules", "skills"})
    _validate_common(data, "project-profile")
    preset = validate_id(data["preset"], "preset")
    values = data.get("values", {})
    if not isinstance(values, dict):
        raise ValueError("values must be a mapping")
    reject_executable_keys(values, "values")
    reject_secret_fields(data)
    rules = _string_list(data.get("required_rules", []), "required_rules")
    skills = _string_list(data.get("skills", []), "skills")
    for item in rules:
        validate_id(item, "required rule")
    for item in skills:
        validate_id(item, "skill")
    return ProjectProfile(
        kind="project-profile", schema_version=1, id=data["id"], preset=preset,
        values=dict(values), required_rules=rules, skills=skills,
    )


def parse_contract(path: Path, expected_kind: Optional[str] = None):
    data = load_toml_mapping(path) if path.suffix.casefold() == ".toml" else load_yaml_mapping(path)
    reject_executable_keys(data)
    kind = data.get("kind")
    if expected_kind is not None and kind != expected_kind:
        raise ValueError("{}: expected kind {}, got {}".format(path, expected_kind, kind))
    parsers = {
        "extension-manifest": parse_extension_manifest,
        "skill": parse_skill,
        "rule": parse_rule,
        "preset": parse_preset,
        "project-profile": parse_project_profile,
    }
    parser = parsers.get(kind)
    if parser is None:
        raise ValueError("unsupported contract kind: " + str(kind))
    return parser(data)
