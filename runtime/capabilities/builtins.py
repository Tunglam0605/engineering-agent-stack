from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .models import ExtensionManifest, PresetContract, RuleContract, SkillContract
from .parser import parse_contract, reject_casefold_collisions, safe_join


@dataclass(frozen=True)
class BuiltinCatalog:
    extensions: Dict[str, ExtensionManifest]
    skills: Dict[str, SkillContract]
    rules: Dict[str, RuleContract]
    presets: Dict[str, PresetContract]
    preset_extension: Dict[str, str]
    skill_roots: Dict[str, Path]
    rule_roots: Dict[str, Path]
    preset_roots: Dict[str, Path]


def builtin_root() -> Path:
    return Path(__file__).resolve().parent / "resources" / "extensions"


def _insert_unique(target: dict, ident: str, value, label: str) -> None:
    folded = ident.casefold()
    for existing in target:
        if existing.casefold() == folded:
            raise ValueError("duplicate/case-fold {} id: {} vs {}".format(label, existing, ident))
    target[ident] = value


def load_builtin_catalog(root: Path = None) -> BuiltinCatalog:
    base = (root or builtin_root()).resolve()
    if not base.is_dir():
        raise ValueError("built-in capability resource root missing: " + str(base))
    extensions: Dict[str, ExtensionManifest] = {}
    skills: Dict[str, SkillContract] = {}
    rules: Dict[str, RuleContract] = {}
    presets: Dict[str, PresetContract] = {}
    preset_extension: Dict[str, str] = {}
    skill_roots: Dict[str, Path] = {}
    rule_roots: Dict[str, Path] = {}
    preset_roots: Dict[str, Path] = {}

    dirs = sorted((p for p in base.iterdir() if p.is_dir()), key=lambda p: p.name.casefold())
    names = [p.name for p in dirs]
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("built-in extension directory case-fold collision")

    for ext_root in dirs:
        manifest_path = ext_root / "manifest.yaml"
        manifest = parse_contract(manifest_path, "extension-manifest")
        _insert_unique(extensions, manifest.id, manifest, "extension")
        all_paths = []
        for group in ("skills", "rules", "presets"):
            all_paths.extend(manifest.provides[group])
        reject_casefold_collisions(all_paths, "manifest provides")
        for relative in manifest.provides["skills"]:
            path = safe_join(ext_root, relative)
            if not path.is_file():
                raise ValueError("declared skill resource missing: " + relative)
            skill = parse_contract(path, "skill")
            _insert_unique(skills, skill.id, skill, "skill")
            skill_roots[skill.id] = ext_root
        for relative in manifest.provides["rules"]:
            path = safe_join(ext_root, relative)
            if not path.is_file():
                raise ValueError("declared rule resource missing: " + relative)
            rule = parse_contract(path, "rule")
            _insert_unique(rules, rule.id, rule, "rule")
            rule_roots[rule.id] = ext_root
        for relative in manifest.provides["presets"]:
            path = safe_join(ext_root, relative)
            if not path.is_file():
                raise ValueError("declared preset resource missing: " + relative)
            preset = parse_contract(path, "preset")
            _insert_unique(presets, preset.id, preset, "preset")
            preset_extension[preset.id] = manifest.id
            preset_roots[preset.id] = ext_root

    if set(presets) != {"embedded", "ros2", "release"}:
        raise ValueError("v0.6 built-ins must define exactly embedded, ros2 and release presets")
    for preset in presets.values():
        missing_skills = sorted(set(preset.skills) - set(skills))
        missing_rules = sorted(set(preset.required_rules) - set(rules))
        if missing_skills:
            raise ValueError("preset {} references missing skills: {}".format(preset.id, missing_skills))
        if missing_rules:
            raise ValueError("preset {} references missing rules: {}".format(preset.id, missing_rules))
        extension_id = preset_extension[preset.id]
        # v0.6 built-ins deliberately keep each preset self-contained; this prevents
        # hidden cross-extension dependency resolution from entering the contract.
        manifest = extensions[extension_id]
        declared_skill_paths = set(manifest.provides["skills"])
        declared_rule_paths = set(manifest.provides["rules"])
        if not declared_skill_paths or not declared_rule_paths:
            raise ValueError("built-in preset extension must declare skills and rules")

    return BuiltinCatalog(
        extensions=extensions, skills=skills, rules=rules, presets=presets,
        preset_extension=preset_extension, skill_roots=skill_roots,
        rule_roots=rule_roots, preset_roots=preset_roots,
    )
