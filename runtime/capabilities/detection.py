from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple

from .models import DetectionEvidence, DetectionResult

_MAX_SCAN_FILES = 400
_SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "node_modules", "__pycache__"}


def _relative(project: Path, path: Path) -> str:
    return path.relative_to(project).as_posix()


def _bounded_files(project: Path) -> List[Path]:
    result: List[Path] = []
    for path in sorted(project.rglob("*"), key=lambda p: p.as_posix().casefold()):
        try:
            rel_parts = path.relative_to(project).parts
        except ValueError:
            continue
        if any(part in _SKIP_DIRS for part in rel_parts):
            continue
        if path.is_file():
            result.append(path)
            if len(result) >= _MAX_SCAN_FILES:
                break
    return result


def _safe_text(path: Path, limit: int = 128000) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if len(data) > limit:
        data = data[:limit]
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _score_embedded(project: Path, files: List[Path]) -> DetectionEvidence:
    score = 0
    paths: List[str] = []
    rationale: List[str] = []
    missing: List[str] = []
    ioc = [p for p in files if p.suffix.casefold() == ".ioc"]
    if ioc:
        score += 6
        paths.extend(_relative(project, p) for p in ioc[:3])
        rationale.append("STM32CubeMX .ioc project evidence")
    else:
        missing.append("no STM32 .ioc file")
    freertos = [p for p in files if p.name.casefold() == "freertosconfig.h"]
    if freertos:
        score += 6
        paths.extend(_relative(project, p) for p in freertos[:3])
        rationale.append("FreeRTOSConfig.h evidence")
    else:
        missing.append("no FreeRTOSConfig.h")
    cmake = project / "CMakeLists.txt"
    if cmake.is_file() and "stm32" in _safe_text(cmake).casefold():
        score += 3
        paths.append("CMakeLists.txt")
        rationale.append("CMake contains STM32 context")
    core_inc = project / "Core" / "Inc"
    core_src = project / "Core" / "Src"
    if core_inc.is_dir() and core_src.is_dir():
        score += 2
        paths.extend(["Core/Inc", "Core/Src"])
        rationale.append("STM32Cube-style Core/Inc and Core/Src layout")
    return DetectionEvidence("embedded", score, sorted(set(paths)), rationale, missing)


def _score_ros2(project: Path, files: List[Path]) -> DetectionEvidence:
    score = 0
    paths: List[str] = []
    rationale: List[str] = []
    missing: List[str] = []
    packages = [p for p in files if p.name == "package.xml"]
    if packages:
        score += 6
        paths.extend(_relative(project, p) for p in packages[:5])
        rationale.append("ROS package.xml evidence")
    else:
        missing.append("no package.xml")
    colcon = [p for p in files if p.name in {"colcon.meta", "colcon.pkg"}]
    if colcon:
        score += 3
        paths.extend(_relative(project, p) for p in colcon[:3])
        rationale.append("colcon workspace metadata")
    cmakes = [p for p in files if p.name == "CMakeLists.txt"]
    if any("ament_" in _safe_text(p) or "find_package(rclcpp" in _safe_text(p) for p in cmakes[:20]):
        score += 5
        for p in cmakes[:5]:
            text = _safe_text(p)
            if "ament_" in text or "find_package(rclcpp" in text:
                paths.append(_relative(project, p))
        rationale.append("ament/rclcpp build evidence")
    else:
        missing.append("no ament/rclcpp build marker")
    return DetectionEvidence("ros2", score, sorted(set(paths)), rationale, missing)


def _score_release(project: Path, files: List[Path]) -> DetectionEvidence:
    score = 0
    paths: List[str] = []
    rationale: List[str] = []
    missing: List[str] = []
    workflow_candidates = [
        project / ".github" / "workflows" / "release.yml",
        project / ".github" / "workflows" / "release.yaml",
    ]
    workflow = next((p for p in workflow_candidates if p.is_file()), None)
    if workflow is not None:
        score += 5
        paths.append(_relative(project, workflow))
        rationale.append("release workflow context")
    else:
        missing.append("no release workflow")
    changelog = project / "CHANGELOG.md"
    if changelog.is_file():
        score += 2
        paths.append("CHANGELOG.md")
        rationale.append("changelog process context")
    else:
        missing.append("no CHANGELOG.md")
    pyproject = project / "pyproject.toml"
    if pyproject.is_file() and "version" in _safe_text(pyproject):
        score += 2
        paths.append("pyproject.toml")
        rationale.append("package version metadata")
    package_json = project / "package.json"
    if package_json.is_file() and '"version"' in _safe_text(package_json):
        score += 2
        paths.append("package.json")
        rationale.append("package version metadata")
    # Deliberately no git-status/test/tag inference here: detection only recognizes
    # repository/process context and never claims release readiness.
    return DetectionEvidence("release", score, sorted(set(paths)), rationale, missing)


def _revision(evidence: List[DetectionEvidence], contradictions: List[str]) -> str:
    payload = {
        "evidence": [item.as_dict() for item in evidence],
        "contradictions": contradictions,
        "detector": "eas-v0.6-1",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def detect_project(project: Path) -> DetectionResult:
    root = project.expanduser().resolve()
    if not root.is_dir():
        raise ValueError("project path must be a directory")
    files = _bounded_files(root)
    evidence = [
        _score_embedded(root, files),
        _score_ros2(root, files),
        _score_release(root, files),
    ]
    ranked = sorted(evidence, key=lambda item: (-item.score, item.preset))
    top = ranked[0]
    second = ranked[1]
    contradictions: List[str] = []
    if top.score == 0:
        status = "NONE"
        confidence = "UNKNOWN"
        recommended = None
    elif top.score >= 5 and second.score >= 5 and top.score - second.score <= 2:
        status = "AMBIGUOUS"
        confidence = "UNKNOWN"
        recommended = None
        contradictions.append(
            "strong evidence competes between {} ({}) and {} ({})".format(
                top.preset, top.score, second.preset, second.score
            )
        )
    else:
        status = "RECOMMENDED"
        recommended = top.preset
        confidence = "HIGH" if top.score >= 10 else "MEDIUM" if top.score >= 5 else "LOW"
    rev = _revision(evidence, contradictions)
    return DetectionResult(
        status=status,
        confidence=confidence,
        recommended_preset=recommended,
        evidence=evidence,
        contradictions=contradictions,
        evidence_revision=rev,
        release_ready=False,
    )
