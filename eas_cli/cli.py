from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Optional, Sequence

from .health import doctor_payload, render_payload, status_payload
from .operations import init_project, run_installer, uninstall, update_source
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eas",
        description="Engineering Agent Stack distribution CLI for Codex.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="print the EAS CLI version")

    doctor = sub.add_parser("doctor", help="run read-only environment and installation checks")
    doctor.add_argument("--json", action="store_true", help="emit stable JSON")

    status = sub.add_parser("status", help="show stack, role, and installation status")
    status.add_argument("--json", action="store_true", help="emit stable JSON")

    install = sub.add_parser("install", help="install the seven managed roles for personal Codex")
    install.add_argument("--dry-run", action="store_true")
    install.add_argument("--force", action="store_true")

    init = sub.add_parser("init", help="initialize EAS in a Git project")
    init.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    init.add_argument("--dry-run", action="store_true")
    init.add_argument("--force", action="store_true")

    check = sub.add_parser("check", help="verify a personal or project installation")
    scope = check.add_mutually_exclusive_group()
    scope.add_argument("--project", type=Path)
    scope.add_argument("--personal", action="store_true")
    check.add_argument("--project-instructions", action="store_true")

    update = sub.add_parser("update", help="safely fast-forward a source-managed checkout")
    update.add_argument("--check", action="store_true", help="check for an update without merging")

    remove = sub.add_parser("uninstall", help="remove only EAS-managed role artifacts")
    remove_scope = remove.add_mutually_exclusive_group()
    remove_scope.add_argument("--project", type=Path)
    remove_scope.add_argument("--personal", action="store_true")
    remove.add_argument("--project-instructions", action="store_true")
    remove.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "version":
            print("eas {}".format(__version__))
            return 0

        if args.command == "doctor":
            render_payload(doctor_payload(), args.json)
            return 0

        if args.command == "status":
            render_payload(status_payload(), args.json)
            return 0

        if args.command == "install":
            return run_installer(dry_run=args.dry_run, force=args.force)

        if args.command == "init":
            return init_project(args.project, dry_run=args.dry_run, force=args.force)

        if args.command == "check":
            if args.project_instructions and args.project is None:
                parser.error("--project-instructions requires --project")
            return run_installer(
                project=args.project,
                project_instructions=args.project_instructions,
                check=True,
            )

        if args.command == "update":
            return update_source(check_only=args.check)

        if args.command == "uninstall":
            if args.project_instructions and args.project is None:
                parser.error("--project-instructions requires --project")
            return uninstall(
                project=args.project,
                project_instructions=args.project_instructions,
                dry_run=args.dry_run,
            )

    except (OSError, RuntimeError, ValueError) as exc:
        print("ERROR: {}".format(exc))
        return 2

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
