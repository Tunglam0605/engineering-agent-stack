"""Declarative capability system for EAS v0.6."""

from .models import (
    DetectionResult, ExtensionManifest, ProjectProfile, RuleContract,
    SkillContract, PresetContract, ResolvedCapabilitySnapshot,
)
from .builtins import BuiltinCatalog, load_builtin_catalog
from .project import ProjectCapabilityService

__all__ = [
    "BuiltinCatalog", "DetectionResult", "ExtensionManifest", "PresetContract",
    "ProjectCapabilityService", "ProjectProfile", "ResolvedCapabilitySnapshot",
    "RuleContract", "SkillContract", "load_builtin_catalog",
]
