from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .parser import validate_id

CORE_DEFAULTS: Dict[str, Any] = {
    "selection": {"max_skills": 3, "context_budget_tokens": 6000},
    "skills": {"enabled": []},
    "rules": {"required_rules": []},
}

_ALLOWED_TOP = {"selection", "skills", "rules", "domain", "release"}
_ALLOWED_NESTED = {
    "selection": {"max_skills", "context_budget_tokens"},
    "skills": {"enabled"},
    "rules": {"required_rules"},
    "domain": {"target", "mcu_family", "ros_distro"},
    "release": {"require_clean_tree", "require_tests"},
}
CLI_OVERRIDE_ALLOWLIST = {
    "selection.max_skills",
    "selection.context_budget_tokens",
    "skills.enabled",
    "rules.required_rules",
}
PROTECTED_OVERRIDE_PREFIXES = {
    "lifecycle", "recovery", "fanout", "write_lease", "approval",
    "model", "models", "provider", "providers", "routing", "roles", "permissions",
}


@dataclass(frozen=True)
class ResolvedConfig:
    values: Dict[str, Any]
    lineage: Dict[str, List[str]]


def _id_list(value: Any, name: str) -> List[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(name + " must be a list of ids")
    seen = set()
    out = []
    for item in value:
        validate_id(item, name)
        folded = item.casefold()
        if folded in seen:
            raise ValueError(name + " contains a duplicate/case-fold collision: " + item)
        seen.add(folded)
        out.append(item)
    return out


def validate_config_tree(value: Mapping[str, Any], source: str = "config") -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(source + " must be a mapping")
    unknown_top = sorted(set(value) - _ALLOWED_TOP)
    if unknown_top:
        raise ValueError(source + " has unknown config sections: " + ", ".join(unknown_top))
    result: Dict[str, Any] = {}
    for section, raw in value.items():
        if not isinstance(raw, Mapping):
            raise ValueError(source + "." + section + " must be a mapping")
        unknown = sorted(set(raw) - _ALLOWED_NESTED[section])
        if unknown:
            raise ValueError(source + "." + section + " has unknown fields: " + ", ".join(unknown))
        parsed: Dict[str, Any] = {}
        for key, item in raw.items():
            path = section + "." + key
            if item is None:
                raise ValueError(path + " does not support null tombstones")
            if path == "selection.max_skills":
                if type(item) is not int or not 1 <= item <= 3:
                    raise ValueError(path + " must be an integer in [1, 3]")
            elif path == "selection.context_budget_tokens":
                if type(item) is not int or not 256 <= item <= 65536:
                    raise ValueError(path + " must be an integer in [256, 65536]")
            elif path in {"skills.enabled", "rules.required_rules"}:
                item = _id_list(item, path)
            elif path == "domain.target":
                if item not in {"embedded", "ros2", "release"}:
                    raise ValueError(path + " must be embedded|ros2|release")
            elif path in {"domain.mcu_family", "domain.ros_distro"}:
                if not isinstance(item, str) or not item.strip() or len(item) > 64:
                    raise ValueError(path + " must be short non-empty text")
                item = item.strip()
            elif path in {"release.require_clean_tree", "release.require_tests"}:
                if type(item) is not bool:
                    raise ValueError(path + " must be a boolean")
            parsed[key] = item
        result[section] = parsed
    return result


def _flatten(value: Mapping[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for section, inner in value.items():
        if not isinstance(inner, Mapping):
            raise ValueError("config sections must be mappings")
        for key, item in inner.items():
            result[section + "." + key] = item
    return result


def _unflatten(value: Mapping[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for path, item in value.items():
        section, key = path.split(".", 1)
        result.setdefault(section, {})[key] = item
    return result


def _merge_required_rules(current: List[str], incoming: Sequence[str], source: str) -> List[str]:
    result = list(current)
    by_fold = {item.casefold(): item for item in result}
    for item in incoming:
        folded = item.casefold()
        previous = by_fold.get(folded)
        if previous is None:
            result.append(item)
            by_fold[folded] = item
        elif previous != item:
            raise ValueError("required_rules case-fold collision from {}: {} vs {}".format(source, previous, item))
        # Exact repeats across precedence layers are idempotent; duplicates within one
        # contract are rejected by the contract/config validator before this point.
    return result


def _apply_layer(
    values: Dict[str, Any],
    lineage: Dict[str, List[str]],
    layer: Mapping[str, Any],
    source: str,
) -> None:
    flat = _flatten(validate_config_tree(layer, source))
    for path, incoming in flat.items():
        if path == "rules.required_rules":
            current = values.get(path, [])
            values[path] = _merge_required_rules(current, incoming, source)
            lineage.setdefault(path, []).append(source)
        else:
            values[path] = incoming
            lineage[path] = [source]


def _resolve_equal_precedence_extensions(
    extension_defaults: Sequence[Tuple[str, Mapping[str, Any]]]
) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    resolved: Dict[str, Any] = {}
    lineage: Dict[str, List[str]] = {}
    for extension_id, raw in sorted(extension_defaults, key=lambda item: item[0]):
        validate_id(extension_id, "extension id")
        flat = _flatten(validate_config_tree(raw, "extension:" + extension_id))
        for path, incoming in flat.items():
            source = "extension:" + extension_id
            if path == "rules.required_rules":
                current = resolved.get(path, [])
                resolved[path] = _merge_required_rules(current, incoming, source)
                lineage.setdefault(path, []).append(source)
                continue
            if path in resolved and resolved[path] != incoming:
                raise ValueError(
                    "equal-precedence extension conflict at {}: {} vs {}".format(
                        path, ",".join(lineage[path]), source
                    )
                )
            resolved[path] = incoming
            lineage.setdefault(path, []).append(source)
    return _unflatten(resolved), lineage


def validate_cli_overrides(overrides: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(overrides, Mapping):
        raise ValueError("CLI overrides must be a mapping")
    tree: Dict[str, Dict[str, Any]] = {}
    for path, value in overrides.items():
        if not isinstance(path, str) or "." not in path:
            raise ValueError("CLI override path must be section.field")
        prefix = path.split(".", 1)[0].casefold()
        if prefix in PROTECTED_OVERRIDE_PREFIXES:
            raise ValueError("CLI override cannot modify protected path: " + path)
        if path not in CLI_OVERRIDE_ALLOWLIST:
            raise ValueError("CLI override is not allowlisted: " + path)
        section, key = path.split(".", 1)
        tree.setdefault(section, {})[key] = value
    return validate_config_tree(tree, "cli")


def resolve_config(
    *,
    core_defaults: Optional[Mapping[str, Any]] = None,
    extension_defaults: Sequence[Tuple[str, Mapping[str, Any]]] = (),
    preset_defaults: Optional[Mapping[str, Any]] = None,
    project_values: Optional[Mapping[str, Any]] = None,
    cli_overrides: Optional[Mapping[str, Any]] = None,
) -> ResolvedConfig:
    """Resolve the frozen v0.6 precedence chain deterministically.

    Precedence is exactly: core < extension defaults < preset < project profile < CLI.
    Extension defaults share one precedence level and therefore conflict if two
    extensions write different values to the same non-additive field.
    """
    values: Dict[str, Any] = {}
    lineage: Dict[str, List[str]] = {}
    _apply_layer(values, lineage, core_defaults or CORE_DEFAULTS, "core")

    ext_tree, ext_lineage = _resolve_equal_precedence_extensions(extension_defaults)
    if ext_tree:
        flat = _flatten(ext_tree)
        for path, incoming in flat.items():
            if path == "rules.required_rules":
                values[path] = _merge_required_rules(values.get(path, []), incoming, "extensions")
                lineage.setdefault(path, []).extend(ext_lineage.get(path, []))
            else:
                values[path] = incoming
                lineage[path] = list(ext_lineage.get(path, ["extensions"]))

    if preset_defaults is not None:
        _apply_layer(values, lineage, preset_defaults, "preset")
    if project_values is not None:
        _apply_layer(values, lineage, project_values, "project")
    if cli_overrides:
        _apply_layer(values, lineage, validate_cli_overrides(cli_overrides), "cli")
    return ResolvedConfig(values=_unflatten(values), lineage=lineage)
