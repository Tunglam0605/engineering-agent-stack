from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional


def eas_home() -> Path:
    raw = os.environ.get("EAS_HOME")
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home().resolve()


def managed_repo_path() -> Path:
    return eas_home() / ".codex" / "engineering-agent-stack"


def _valid_repo(path: Path) -> bool:
    return (
        (path / "scripts" / "install_codex.py").is_file()
        and (path / "adapters" / "codex" / "agents").is_dir()
    )


def source_candidates() -> Iterable[Path]:
    explicit = os.environ.get("EAS_REPO")
    if explicit:
        # An explicit checkout is an operator choice, not a hint. Falling back to
        # another checkout after a typo can mutate or inspect the wrong source.
        yield Path(explicit).expanduser().resolve()
        return
    source_tree = Path(__file__).resolve().parents[1]
    yield source_tree
    yield managed_repo_path()


def resolve_repo(required: bool = True) -> Optional[Path]:
    seen = set()
    for candidate in source_candidates():
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if _valid_repo(candidate):
            return candidate
    if required:
        raise RuntimeError(
            "Engineering Agent Stack source checkout not found. "
            "Set EAS_REPO or install the managed checkout under "
            "~/.codex/engineering-agent-stack."
        )
    return None
