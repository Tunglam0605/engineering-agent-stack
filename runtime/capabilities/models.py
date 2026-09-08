from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

CORE_ROLES = {
    "scout", "researcher", "implementer", "debugger",
    "test-engineer", "reviewer", "architect",
}
RULE_CLASSES = {"guidance", "validator", "gate"}
RULE_SEVERITIES = {"info", "warning", "error"}
DETECTION_STATUSES = {"RECOMMENDED", "AMBIGUOUS", "NONE"}
DETECTION_CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}


@dataclass(frozen=True)
class ExtensionManifest:
    kind: str
    schema_version: int
    id: str
    version: str
    description: str
    requires_eas: str
    provenance: Dict[str, str]
    provides: Dict[str, List[str]]
    defaults: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillContract:
    kind: str
    schema_version: int
    id: str
    version: str
    summary: str
    roles: List[str]
    task_tags: List[str]
    triggers: List[str]
    body: str
    references: List[str]
    context_cost: int


@dataclass(frozen=True)
class RuleContract:
    kind: str
    schema_version: int
    id: str
    version: str
    classification: str
    scope: List[str]
    severity: str
    evidence: List[str]
    text: str
    checker_id: Optional[str] = None


@dataclass(frozen=True)
class PresetContract:
    kind: str
    schema_version: int
    id: str
    version: str
    description: str
    skills: List[str]
    required_rules: List[str]
    defaults: Dict[str, Any]
    detection_hints: List[str]


@dataclass(frozen=True)
class ProjectProfile:
    kind: str
    schema_version: int
    id: str
    preset: str
    values: Dict[str, Any] = field(default_factory=dict)
    required_rules: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DetectionEvidence:
    preset: str
    score: int
    paths: List[str]
    rationale: List[str]
    missing: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DetectionResult:
    status: str
    confidence: str
    recommended_preset: Optional[str]
    evidence: List[DetectionEvidence]
    contradictions: List[str]
    evidence_revision: str
    release_ready: bool = False

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "confidence": self.confidence,
            "recommended_preset": self.recommended_preset,
            "evidence": [item.as_dict() for item in self.evidence],
            "contradictions": list(self.contradictions),
            "evidence_revision": self.evidence_revision,
            "release_ready": False,
        }


@dataclass(frozen=True)
class SelectedSkill:
    id: str
    score: int
    preset_order: int
    context_cost: int

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ResolvedCapabilitySnapshot:
    schema_version: int
    eas_version: str
    project_id: str
    active_preset: str
    sources: List[Dict[str, str]]
    resolved_values: Dict[str, Any]
    lineage: Dict[str, List[str]]
    selected_skills: List[str]
    selected_rules: List[str]
    detection: Dict[str, Any]
    digest: str

    def as_dict(self) -> dict:
        return asdict(self)
