from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Callable, Dict, Iterable, Optional

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from .models import RuleContract


@dataclass(frozen=True)
class CheckResult:
    checker_id: str
    status: str
    message: str
    evidence: dict

    def as_dict(self) -> dict:
        return {
            "checker_id": self.checker_id,
            "status": self.status,
            "message": self.message,
            "evidence": dict(self.evidence),
        }


def _contract_shape(project: Path) -> CheckResult:
    return CheckResult(
        "core.contract-shape",
        "PASS",
        "contract was parsed and validated by the trusted v0.6 loader",
        {"project": str(project)},
    )


def _clean_tree(project: Path) -> CheckResult:
    result = subprocess.run(
        ["git", "-C", str(project), "status", "--porcelain", "--untracked-files=all"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        return CheckResult(
            "core.clean-tree", "ERROR", "unable to inspect Git source state",
            {"stderr": result.stderr.strip()},
        )
    dirty = [line for line in result.stdout.splitlines() if line.strip()]
    return CheckResult(
        "core.clean-tree",
        "PASS" if not dirty else "FAIL",
        "Git worktree is clean" if not dirty else "Git worktree has tracked/untracked changes",
        {"dirty_entries": dirty[:50], "dirty_count": len(dirty)},
    )


def _version_consistency(project: Path) -> CheckResult:
    pyproject = project / "pyproject.toml"
    version_py = project / "eas_cli" / "version.py"
    if not pyproject.is_file() or not version_py.is_file():
        return CheckResult(
            "core.version-consistency", "UNKNOWN",
            "project does not expose EAS package/CLI version files",
            {"pyproject": pyproject.is_file(), "version_py": version_py.is_file()},
        )
    try:
        metadata = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        package_version = metadata["project"]["version"]
    except Exception as exc:
        return CheckResult(
            "core.version-consistency", "ERROR", "unable to parse package version",
            {"error": str(exc)},
        )
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']\s*$', version_py.read_text(encoding="utf-8"), re.MULTILINE)
    cli_version = match.group(1) if match else None
    status = "PASS" if cli_version == package_version else "FAIL"
    return CheckResult(
        "core.version-consistency", status,
        "package and CLI versions agree" if status == "PASS" else "package and CLI versions differ",
        {"package_version": package_version, "cli_version": cli_version},
    )


class TrustedCheckerRegistry:
    def __init__(self) -> None:
        self._checkers: Dict[str, Callable[[Path], CheckResult]] = {
            "core.contract-shape": _contract_shape,
            "core.clean-tree": _clean_tree,
            "core.version-consistency": _version_consistency,
        }

    @property
    def ids(self):
        return frozenset(self._checkers)

    def validate_references(self, rules: Iterable[RuleContract]) -> None:
        for rule in rules:
            if rule.classification in {"validator", "gate"}:
                if rule.checker_id not in self._checkers:
                    raise ValueError(
                        "rule {} references untrusted checker {}".format(rule.id, rule.checker_id)
                    )
            elif rule.checker_id is not None:
                raise ValueError("guidance rule cannot reference a checker: " + rule.id)

    def run(self, checker_id: str, project: Path) -> CheckResult:
        checker = self._checkers.get(checker_id)
        if checker is None:
            raise ValueError("unknown trusted checker: " + checker_id)
        return checker(project.expanduser().resolve())
