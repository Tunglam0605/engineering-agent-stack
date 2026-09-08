from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import List, Optional, Sequence, Tuple

from .paths import eas_home, resolve_repo

MANAGED_START = "<!-- engineering-agent-stack:start -->"
MANAGED_END = "<!-- engineering-agent-stack:end -->"


def _read_text_preserve_newlines(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _write_text_preserve_newlines(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def run_command(args: Sequence[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args),
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def load_installer(repo: Path) -> ModuleType:
    path = repo / "scripts" / "install_codex.py"
    spec = importlib.util.spec_from_file_location("eas_install_codex", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load installer: {}".format(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def installer_command(
    repo: Path,
    *,
    project: Optional[Path] = None,
    project_instructions: bool = False,
    dry_run: bool = False,
    force: bool = False,
    check: bool = False,
) -> List[str]:
    cmd = [sys.executable, str(repo / "scripts" / "install_codex.py")]
    if project is not None:
        cmd.extend(["--project", str(project)])
    else:
        cmd.extend(["--personal", "--home", str(eas_home())])
    if project_instructions:
        cmd.append("--project-instructions")
    if dry_run:
        cmd.append("--dry-run")
    if force:
        cmd.append("--force")
    if check:
        cmd.append("--check")
    return cmd


def run_installer(**kwargs) -> int:
    repo = kwargs.pop("repo", None) or resolve_repo()
    result = run_command(installer_command(repo, **kwargs), cwd=repo)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return int(result.returncode)


def git_repository_root(path: Path) -> Optional[Path]:
    candidate = path.expanduser().resolve()
    result = run_command(["git", "-C", str(candidate), "rev-parse", "--show-toplevel"])
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return Path(result.stdout.strip()).resolve()


def is_git_repo(path: Path) -> bool:
    return git_repository_root(path) is not None


def init_project(path: Path, dry_run: bool = False, force: bool = False) -> int:
    requested = path.expanduser().resolve()
    project = git_repository_root(requested)
    if project is None:
        print("REFUSED: target is not a Git repository: {}".format(requested))
        return 2
    if requested != project:
        print("Repository root resolved: {}".format(project))
    return run_installer(
        repo=resolve_repo(),
        project=project,
        project_instructions=True,
        dry_run=dry_run,
        force=force,
    )


def _strip_managed_block(existing: str) -> Tuple[str, bool]:
    start = existing.find(MANAGED_START)
    end = existing.find(MANAGED_END)
    if start == -1 and end == -1:
        return existing, False
    if start == -1 or end == -1 or end < start:
        raise ValueError("AGENTS.md contains incomplete Engineering Agent Stack markers")
    end += len(MANAGED_END)
    prefix = existing[:start]
    suffix = existing[end:]

    # v0.3 new installs prepend the managed block followed by an exact two-newline
    # separator, making the original file a byte-for-byte suffix.
    if start == 0:
        if suffix.startswith("\n\n"):
            return suffix[2:], True
        if suffix == "\n":
            return "", True
        return suffix, True

    # Legacy/mid-file blocks: remove only separator newlines owned by EAS. Never
    # call strip/lstrip/rstrip on user-owned content.
    if prefix.endswith("\n\n"):
        prefix = prefix[:-1]
    if suffix == "\n":
        suffix = ""
    elif suffix.startswith("\n\n"):
        suffix = suffix[1:]
    return prefix + suffix, True


def uninstall(
    *,
    project: Optional[Path] = None,
    project_instructions: bool = False,
    dry_run: bool = False,
) -> int:
    repo = resolve_repo()
    sources = sorted((repo / "adapters" / "codex" / "agents").glob("*.toml"))
    if project is None:
        target_root = eas_home() / ".codex"
        agents_md = None
    else:
        project = project.expanduser().resolve()
        target_root = project / ".codex"
        agents_md = project / "AGENTS.md"

    conflicts: List[Path] = []
    removable: List[Path] = []
    for src in sources:
        dest = target_root / "agents" / src.name
        if not dest.exists():
            continue
        if not dest.is_file() or dest.read_bytes() != src.read_bytes():
            conflicts.append(dest)
        else:
            removable.append(dest)

    instructions_update: Optional[Tuple[Path, str]] = None
    if project_instructions and agents_md is not None and agents_md.exists():
        try:
            new_text, changed = _strip_managed_block(
                _read_text_preserve_newlines(agents_md)
            )
        except (OSError, ValueError) as exc:
            print("REFUSED: {}".format(exc))
            return 2
        if changed:
            instructions_update = (agents_md, new_text)

    if conflicts:
        print("REFUSED: managed role files have local drift; no files were removed.")
        for path in conflicts:
            print("  - {}".format(path))
        return 2

    for path in removable:
        print("remove managed role: {}".format(path))
    if instructions_update is not None:
        print("remove managed orchestration block: {}".format(instructions_update[0]))
    if dry_run:
        print("DRY-RUN: no files written.")
        return 0

    for path in removable:
        path.unlink()
    if instructions_update is not None:
        path, new_text = instructions_update
        _write_text_preserve_newlines(path, new_text)
    print("UNINSTALLED: {} managed role(s). config.toml preserved.".format(len(removable)))
    return 0


def _git_text(repo: Path, *args: str) -> Tuple[int, str, str]:
    result = run_command(["git", "-C", str(repo)] + list(args))
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _update_checkout() -> Optional[Path]:
    import os

    explicit = os.environ.get("EAS_REPO")
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if not (candidate / ".git").exists():
            raise ValueError("EAS_REPO is not a Git checkout: {}".format(candidate))
        return candidate
    repo = resolve_repo(required=False)
    if repo is not None and (repo / ".git").exists():
        return repo
    return None


def _managed_role_snapshot(repo: Path) -> Tuple[List[Tuple[Path, Path, Optional[bytes]]], Optional[str]]:
    source_dir = repo / "adapters" / "codex" / "agents"
    if not source_dir.is_dir():
        return [], None

    records: List[Tuple[Path, Path, Optional[bytes]]] = []
    target_dir = eas_home() / ".codex" / "agents"
    for source in sorted(source_dir.glob("*.toml")):
        target = target_dir / source.name
        previous = target.read_bytes() if target.is_file() else None
        if previous is not None and previous != source.read_bytes():
            return [], "personal managed role has local drift: {}".format(target)
        records.append((source, target, previous))
    return records, None


def _refresh_managed_roles(
    repo: Path, records: List[Tuple[Path, Path, Optional[bytes]]]
) -> int:
    if not records:
        return 0

    installer = load_installer(repo)
    config_path = eas_home() / ".codex" / "config.toml"
    problems = installer.validate_config(config_path) if config_path.exists() else []
    if problems:
        print("REFUSED: personal Codex config is not compatible with the updated stack.")
        for problem in problems:
            print("  - {}".format(problem))
        return 2

    new_source_dir = repo / "adapters" / "codex" / "agents"
    replacements: List[Tuple[Path, bytes, Optional[bytes]]] = []
    for old_source, target, previous in records:
        new_source = new_source_dir / old_source.name
        if not new_source.is_file():
            print("REFUSED: updated stack is missing managed role: {}".format(old_source.name))
            return 2
        replacements.append((target, new_source.read_bytes(), previous))

    changed: List[Tuple[Path, Optional[bytes]]] = []
    try:
        for target, content, previous in replacements:
            target.parent.mkdir(parents=True, exist_ok=True)
            if previous == content:
                continue
            target.write_bytes(content)
            changed.append((target, previous))
    except OSError as exc:
        rollback_errors: List[str] = []
        for target, previous in reversed(changed):
            try:
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(previous)
            except OSError as rollback_exc:
                rollback_errors.append("{}: {}".format(target, rollback_exc))
        if rollback_errors:
            print("ROLLBACK FAILED: managed role refresh failed and manual recovery is required: {}".format(exc))
            for item in rollback_errors:
                print("  - role rollback failed: {}".format(item))
        else:
            print("ERROR: managed role refresh failed; role changes were rolled back: {}".format(exc))
        return 2

    return 0


def _restore_role_records(
    records: List[Tuple[Path, Path, Optional[bytes]]]
) -> List[str]:
    errors: List[str] = []
    for _, target, previous in records:
        try:
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(previous)
        except OSError as exc:
            errors.append("{}: {}".format(target, exc))
    return errors


def _rollback_update(
    repo: Path, old_head: str, records: Optional[List[Tuple[Path, Path, Optional[bytes]]]] = None
) -> bool:
    failures: List[str] = []
    reset = run_command(["git", "-C", str(repo), "reset", "--hard", old_head])
    if reset.returncode != 0:
        detail = reset.stderr.strip() or reset.stdout.strip() or "unknown git reset failure"
        failures.append("source rollback failed: {}".format(detail))
    if records is not None:
        failures.extend("role rollback failed: {}".format(item) for item in _restore_role_records(records))
    if failures:
        print("ROLLBACK FAILED: manual recovery is required.")
        for failure in failures:
            print("  - {}".format(failure))
        return False
    return True


def update_source(check_only: bool = False) -> int:
    try:
        repo = _update_checkout()
    except ValueError as exc:
        print("REFUSED: {}".format(exc))
        return 2
    if repo is None:
        print(
            "Source-managed checkout not available. "
            "Update Engineering Agent Stack with the package/bootstrap manager."
        )
        return 0

    code, dirty, _ = _git_text(repo, "status", "--porcelain", "--untracked-files=all")
    if code != 0:
        print("REFUSED: unable to inspect source Git state.")
        return 2
    if dirty:
        print("REFUSED: source checkout is dirty; clean or stash changes before update.")
        return 2

    code, branch, _ = _git_text(repo, "branch", "--show-current")
    if code != 0 or branch != "main":
        print("REFUSED: source checkout must be on main before update.")
        return 2

    role_records, drift_problem = _managed_role_snapshot(repo)
    if drift_problem:
        print("REFUSED: {}; update will not overwrite it.".format(drift_problem))
        return 2

    personal_config = eas_home() / ".codex" / "config.toml"
    installed_role_count = sum(previous is not None for _, _, previous in role_records)
    expected_role_count = len(role_records)
    if 0 < installed_role_count < expected_role_count:
        print(
            "REFUSED: personal EAS role installation is incomplete; "
            "eas update will not create missing managed roles."
        )
        return 2
    if personal_config.exists():
        installer = load_installer(repo)
        config_problems = installer.validate_config(personal_config)
        if config_problems:
            print("REFUSED: personal Codex config is not compatible with the current stack.")
            for problem in config_problems:
                print("  - {}".format(problem))
            return 2
        if installed_role_count == 0:
            # A compatible config alone does not prove EAS owns a personal role install.
            role_records = []
    elif installed_role_count:
        print("REFUSED: personal managed roles exist but config.toml is missing.")
        return 2
    else:
        # Source-only installations may update without implicitly creating a personal Codex install.
        role_records = []

    code, old_head, _ = _git_text(repo, "rev-parse", "HEAD")
    if code != 0 or not old_head:
        print("REFUSED: unable to resolve the current source commit.")
        return 2

    fetch = run_command(["git", "-C", str(repo), "fetch", "origin", "main"])
    if fetch.returncode != 0:
        print("ERROR: unable to refresh origin/main.")
        if fetch.stderr:
            print(fetch.stderr.strip())
        return 2

    code, counts, _ = _git_text(
        repo, "rev-list", "--left-right", "--count", "HEAD...origin/main"
    )
    if code != 0:
        print("ERROR: unable to compare HEAD with origin/main.")
        return 2
    try:
        ahead_s, behind_s = counts.replace("\t", " ").split()
        ahead = int(ahead_s)
        behind = int(behind_s)
    except (ValueError, TypeError):
        print("ERROR: unexpected Git divergence output: {}".format(counts))
        return 2

    if ahead:
        label = "diverged" if behind else "ahead"
        print("REFUSED: local main is {}; fast-forward update is not safe.".format(label))
        return 2

    if check_only:
        if behind:
            print("UPDATE AVAILABLE: {} commit(s) behind origin/main.".format(behind))
        else:
            print("UP TO DATE: source checkout matches origin/main.")
        return 0

    if behind:
        merge = run_command(["git", "-C", str(repo), "merge", "--ff-only", "origin/main"])
        if merge.returncode != 0:
            print("REFUSED: fast-forward update failed.")
            if merge.stderr:
                print(merge.stderr.strip())
            return 2
        if merge.stdout:
            print(merge.stdout, end="")

    generator = run_command(
        [sys.executable, str(repo / "scripts" / "generate_codex_adapter.py"), "--check"],
        cwd=repo,
    )
    if generator.stdout:
        print(generator.stdout, end="")
    if generator.stderr:
        print(generator.stderr, file=sys.stderr, end="")
    if generator.returncode != 0:
        if behind and not _rollback_update(repo, old_head):
            return 2
        return int(generator.returncode)

    refresh_code = _refresh_managed_roles(repo, role_records)
    if refresh_code != 0:
        if behind and not _rollback_update(repo, old_head):
            return 2
        return refresh_code

    if not role_records:
        if not behind:
            print("UP TO DATE: source checkout matches origin/main.")
        else:
            print("UPDATED: source checkout is in sync; no personal EAS install was detected.")
        return 0

    check = run_command(installer_command(repo, check=True), cwd=repo)
    if check.stdout:
        print(check.stdout, end="")
    if check.stderr:
        print(check.stderr, file=sys.stderr, end="")
    if check.returncode != 0:
        if behind:
            if not _rollback_update(repo, old_head, role_records):
                return 2
        else:
            role_errors = _restore_role_records(role_records)
            if role_errors:
                print("ROLLBACK FAILED: manual recovery is required.")
                for item in role_errors:
                    print("  - role rollback failed: {}".format(item))
                return 2
        return int(check.returncode)

    if not behind:
        print("UP TO DATE: source checkout matches origin/main.")
    else:
        print("UPDATED: source checkout and managed personal roles are in sync.")
    return 0
