from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, Optional

from .paths import eas_home, resolve_repo
from .version import __version__

ROLE_NAMES = (
    "architect",
    "debugger",
    "implementer",
    "researcher",
    "reviewer",
    "scout",
    "test-engineer",
)


def _command_version(command: str, args: list[str]) -> Dict[str, Any]:
    executable = shutil.which(command)
    if not executable:
        return {"status": "MISSING", "path": None, "version": None}
    try:
        completed = subprocess.run(
            [executable] + args,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        return {"status": "ERROR", "path": executable, "version": None, "detail": str(exc)}
    text = (completed.stdout or completed.stderr).strip().splitlines()
    return {
        "status": "OK" if completed.returncode == 0 else "ERROR",
        "path": executable,
        "version": text[0] if text else None,
    }


def _source_check() -> Dict[str, Any]:
    repo = resolve_repo(required=False)
    if repo is None:
        return {"status": "MISSING", "path": None}
    return {"status": "OK", "path": str(repo)}


def _installation_check(root: Path) -> Dict[str, Any]:
    repo = resolve_repo(required=False)
    agents_dir = root / "agents"
    config = root / "config.toml"
    if repo is None:
        installed = sorted(path.stem for path in agents_dir.glob("*.toml")) if agents_dir.is_dir() else []
        return {
            "status": "UNKNOWN",
            "root": str(root),
            "roles": installed,
            "config": config.is_file(),
        }

    canonical_dir = repo / "adapters" / "codex" / "agents"
    missing = []
    drifted = []
    installed = []
    for name in ROLE_NAMES:
        source = canonical_dir / (name + ".toml")
        target = agents_dir / (name + ".toml")
        if not target.is_file():
            missing.append(name)
        else:
            installed.append(name)
            try:
                if target.read_bytes() != source.read_bytes():
                    drifted.append(name)
            except OSError:
                drifted.append(name)

    if missing:
        status = "MISSING"
    elif drifted:
        status = "DRIFTED"
    else:
        status = "OK"
    return {
        "status": status,
        "root": str(root),
        "roles": installed,
        "missing": missing,
        "drifted": drifted,
        "config": config.is_file(),
    }


def _project_root(project: Optional[Path] = None) -> Optional[Path]:
    candidate = (project or Path.cwd()).expanduser().resolve()
    probe = candidate
    while True:
        if (probe / ".git").exists():
            return probe
        if probe.parent == probe:
            return None
        probe = probe.parent


def doctor_payload(project: Optional[Path] = None) -> Dict[str, Any]:
    source = _source_check()
    personal = _installation_check(eas_home() / ".codex")
    root = _project_root(project)
    project_check: Dict[str, Any]
    if root is None:
        project_check = {"status": "NOT_APPLICABLE", "root": None}
    else:
        project_check = _installation_check(root / ".codex")
        project_check["project"] = str(root)

    checks: Dict[str, Any] = {
        "python": {
            "status": "OK" if sys.version_info >= (3, 9) else "UNSUPPORTED",
            "version": ".".join(str(v) for v in sys.version_info[:3]),
            "path": sys.executable,
        },
        "git": _command_version("git", ["--version"]),
        "codex": _command_version("codex", ["--version"]),
        "source": source,
        "personal": personal,
        "project": project_check,
    }
    hard_failures = {
        checks["python"]["status"],
        checks["git"]["status"],
        checks["source"]["status"],
    } & {"MISSING", "ERROR", "UNSUPPORTED"}
    core_status = "DEGRADED" if hard_failures else "HEALTHY"
    return {
        "command": "doctor",
        "version": __version__,
        "core": {"status": core_status},
        "provider": {"status": "UNKNOWN", "probed": False},
        "checks": checks,
    }


def status_payload(project: Optional[Path] = None) -> Dict[str, Any]:
    repo = resolve_repo(required=False)
    canonical = list(ROLE_NAMES)
    personal = _installation_check(eas_home() / ".codex")
    root = _project_root(project)
    project_check = _installation_check(root / ".codex") if root is not None else {
        "status": "NOT_APPLICABLE",
        "root": None,
    }
    return {
        "command": "status",
        "version": __version__,
        "source": str(repo) if repo else None,
        "roles": {
            "expected": len(canonical),
            "canonical": canonical,
            "personal": personal,
            "project": project_check,
        },
        "policy": {
            "readers": 4,
            "writers": 3,
            "recursive_delegation": False,
        },
        "provider": {"status": "UNKNOWN", "probed": False},
    }


def render_payload(payload: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
        return

    command = payload["command"]
    print("Engineering Agent Stack {} {}".format(__version__, command))
    if command == "doctor":
        print("Core: {}".format(payload["core"]["status"]))
        for name, check in payload["checks"].items():
            print("{:<9} {}".format(name + ":", check.get("status", "UNKNOWN")))
        print("Provider: UNKNOWN (not probed)")
    else:
        print("Roles: {}/{} canonical".format(
            len(payload["roles"]["canonical"]), payload["roles"]["expected"]
        ))
        print("Source: {}".format(payload["source"] or "not found"))
        print("Provider: UNKNOWN (not probed)")
