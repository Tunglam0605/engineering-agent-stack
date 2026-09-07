#!/usr/bin/env python3
"""Safely install generated Engineering Agent Stack roles into Codex.

The installer never rewrites an existing Codex config.toml. Agent files are
preflighted before any write and existing differing role files require --force.

For project-scoped installs, --project-instructions manages one clearly marked
Engineering Agent Stack block inside the project's AGENTS.md so the parent Codex
session receives the orchestration policy as well as the child role catalog.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_AGENTS = ROOT / "adapters" / "codex" / "agents"
CONFIG_EXAMPLE = ROOT / "adapters" / "codex" / "config.toml.example"
PROJECT_INSTRUCTIONS_EXAMPLE = ROOT / "adapters" / "codex" / "AGENTS.md.example"
MANAGED_START = "<!-- engineering-agent-stack:start -->"
MANAGED_END = "<!-- engineering-agent-stack:end -->"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def target_root(args: argparse.Namespace) -> Path:
    if args.project is not None:
        return args.project.expanduser().resolve() / ".codex"
    home = args.home.expanduser().resolve() if args.home else Path.home().resolve()
    return home / ".codex"


def source_roles() -> list[Path]:
    roles = sorted(SOURCE_AGENTS.glob("*.toml"))
    if not roles:
        raise ValueError(f"no generated Codex roles found under {SOURCE_AGENTS}")
    return roles


def validate_config(config_path: Path) -> list[str]:
    if not config_path.is_file():
        return [f"missing config: {config_path}"]
    text = read_text(config_path)
    problems: list[str] = []
    if "[agents]" not in text:
        problems.append(f"{config_path}: missing [agents] table")
    if "enabled = true" not in text:
        problems.append(f"{config_path}: [agents] does not visibly enable agents")
    return problems


def project_instruction_block() -> str:
    if not PROJECT_INSTRUCTIONS_EXAMPLE.is_file():
        raise ValueError(f"missing project instruction template: {PROJECT_INSTRUCTIONS_EXAMPLE}")
    text = read_text(PROJECT_INSTRUCTIONS_EXAMPLE).strip()
    if MANAGED_START not in text or MANAGED_END not in text:
        raise ValueError(f"{PROJECT_INSTRUCTIONS_EXAMPLE}: managed markers are required")
    return text


def merge_managed_block(existing: str, block: str) -> str:
    start = existing.find(MANAGED_START)
    end = existing.find(MANAGED_END)
    if (start == -1) != (end == -1):
        raise ValueError("AGENTS.md contains only one Engineering Agent Stack managed marker")
    if start != -1:
        end += len(MANAGED_END)
        prefix = existing[:start].rstrip()
        suffix = existing[end:].lstrip()
        parts = [part for part in (prefix, block, suffix) if part]
        return "\n\n".join(parts).rstrip() + "\n"
    if not existing.strip():
        return block.rstrip() + "\n"
    return existing.rstrip() + "\n\n" + block.rstrip() + "\n"


def check_project_instructions(project: Path) -> list[str]:
    agents_md = project / "AGENTS.md"
    if not agents_md.is_file():
        return [f"missing project instructions: {agents_md}"]
    existing = read_text(agents_md)
    expected = project_instruction_block()
    start = existing.find(MANAGED_START)
    end = existing.find(MANAGED_END)
    if start == -1 or end == -1 or end < start:
        return [f"{agents_md}: missing Engineering Agent Stack managed block"]
    end += len(MANAGED_END)
    actual_block = existing[start:end].strip()
    if actual_block != expected.strip():
        return [f"{agents_md}: Engineering Agent Stack managed block drifted"]
    return []


def check_installation(root: Path, *, project: Path | None = None, project_instructions: bool = False) -> int:
    agents_dir = root / "agents"
    failures: list[str] = []
    for src in source_roles():
        dest = agents_dir / src.name
        if not dest.is_file():
            failures.append(f"missing role: {dest}")
        elif read_text(dest) != read_text(src):
            failures.append(f"drifted role: {dest}")
    failures.extend(validate_config(root / "config.toml"))
    if project_instructions:
        if project is None:
            failures.append("project instructions require a project-scoped install")
        else:
            failures.extend(check_project_instructions(project))
    if failures:
        print(f"FAIL: {len(failures)} Codex installation problem(s).")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    suffix = " + parent orchestration instructions" if project_instructions else ""
    print(f"PASS: Codex installation matches {len(source_roles())} generated role(s){suffix}: {root}")
    return 0


def install_project_instructions(project: Path, *, dry_run: bool) -> None:
    block = project_instruction_block()
    agents_md = project / "AGENTS.md"
    existing = read_text(agents_md) if agents_md.is_file() else ""
    merged = merge_managed_block(existing, block)
    if existing == merged:
        print(f"unchanged: {agents_md}")
        return
    print(f"install managed orchestration block: {agents_md}")
    if dry_run:
        return
    if agents_md.is_file():
        backup = agents_md.with_name("AGENTS.md.engineering-agent-stack.bak")
        shutil.copy2(agents_md, backup)
        print(f"backup: {backup}")
    agents_md.write_text(merged, encoding="utf-8")


def install(root: Path, *, force: bool, dry_run: bool, project: Path | None = None, project_instructions: bool = False) -> int:
    agents_dir = root / "agents"
    config_path = root / "config.toml"
    roles = source_roles()
    conflicts: list[Path] = []
    for src in roles:
        dest = agents_dir / src.name
        if dest.exists() and dest.is_file() and read_text(dest) != read_text(src) and not force:
            conflicts.append(dest)
    if conflicts:
        print("REFUSED: existing Codex agent files differ from generated roles.")
        for path in conflicts:
            print(f"  - {path}")
        print("Re-run with --force only after reviewing the local files.")
        return 2

    print(f"target: {root}")
    for src in roles:
        dest = agents_dir / src.name
        state = "unchanged" if dest.is_file() and read_text(dest) == read_text(src) else "install"
        print(f"{state}: {dest}")
    if config_path.exists():
        print(f"preserve: {config_path}")
        print(f"merge/check [agents] using: {CONFIG_EXAMPLE}")
    else:
        print(f"create: {config_path}")
    if project_instructions:
        if project is None:
            raise ValueError("--project-instructions is only valid for project-scoped installs")
        install_project_instructions(project, dry_run=True)
    if dry_run:
        print("DRY-RUN: no files written.")
        return 0

    agents_dir.mkdir(parents=True, exist_ok=True)
    for src in roles:
        dest = agents_dir / src.name
        if dest.exists() and read_text(dest) != read_text(src) and force:
            backup = dest.with_suffix(dest.suffix + ".bak")
            shutil.copy2(dest, backup)
            print(f"backup: {backup}")
        shutil.copy2(src, dest)
    if not config_path.exists():
        root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CONFIG_EXAMPLE, config_path)
        print(f"created config from generated example: {config_path}")
    else:
        problems = validate_config(config_path)
        if problems:
            print("NOTICE: roles installed, but existing config requires manual merge:")
            for problem in problems:
                print(f"  - {problem}")
            print(f"reference: {CONFIG_EXAMPLE}")
    if project_instructions and project is not None:
        install_project_instructions(project, dry_run=False)
    print(f"INSTALLED: {len(roles)} generated Codex role(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--project", type=Path, help="Project root; installs into <project>/.codex")
    scope.add_argument("--personal", action="store_true", help="Install into ~/.codex")
    parser.add_argument("--home", type=Path, help="Override home directory for --personal (useful for CI/tests)")
    parser.add_argument("--project-instructions", action="store_true", help="install/check a managed parent-orchestration block in <project>/AGENTS.md")
    parser.add_argument("--check", action="store_true", help="Verify installed roles and [agents] config")
    parser.add_argument("--dry-run", action="store_true", help="Show planned writes without changing files")
    parser.add_argument("--force", action="store_true", help="Overwrite differing generated role files after making .bak backups")
    args = parser.parse_args()
    if args.home is not None and not args.personal:
        parser.error("--home is only valid with --personal")
    if args.project_instructions and args.project is None:
        parser.error("--project-instructions requires --project")
    if args.check and args.dry_run:
        parser.error("--check and --dry-run cannot be combined")
    try:
        root = target_root(args)
        project = args.project.expanduser().resolve() if args.project else None
        if args.check:
            return check_installation(root, project=project, project_instructions=args.project_instructions)
        return install(root, force=args.force, dry_run=args.dry_run, project=project, project_instructions=args.project_instructions)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
