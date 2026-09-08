from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional, Sequence

from .health import doctor_payload, render_payload, status_payload
from .goals import goal_gate, goal_init, goal_status, goal_transition
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

    goal = sub.add_parser("goal", help="manage bounded per-goal lifecycle state")
    goal_sub = goal.add_subparsers(dest="goal_command", required=True)

    goal_init_parser = goal_sub.add_parser("init", help="initialize a goal registry")
    goal_init_parser.add_argument("goal_id")
    goal_init_parser.add_argument("--project", type=Path, default=Path.cwd())
    goal_init_parser.add_argument("--json", action="store_true")

    goal_status_parser = goal_sub.add_parser("status", help="show goal fan-out and assignment state")
    goal_status_parser.add_argument("goal_id")
    goal_status_parser.add_argument("--project", type=Path, default=Path.cwd())
    goal_status_parser.add_argument("--json", action="store_true")

    goal_gate_parser = goal_sub.add_parser("gate", help="decide REUSE/SPAWN/ESCALATE/REJECT before child dispatch")
    goal_gate_parser.add_argument("goal_id")
    goal_gate_parser.add_argument("--project", type=Path, default=Path.cwd())
    goal_gate_parser.add_argument("--role", required=True)
    goal_gate_parser.add_argument("--domain", required=True)
    goal_gate_parser.add_argument("--scope", action="append", default=[])
    goal_gate_parser.add_argument("--change-set")
    goal_gate_parser.add_argument("--reconciled", action="store_true")
    goal_gate_parser.add_argument("--reason")
    goal_gate_parser.add_argument("--exception", choices=("acceptance-diagnostic", "required-safety-review", "required-release-review"))
    goal_gate_parser.add_argument("--material-change", action="store_true")
    goal_gate_parser.add_argument("--fresh-context", action="store_true")
    goal_gate_parser.add_argument("--commit", action="store_true")
    goal_gate_parser.add_argument("--json", action="store_true")

    goal_transition_parser = goal_sub.add_parser("transition", help="transition a committed assignment")
    goal_transition_parser.add_argument("goal_id")
    goal_transition_parser.add_argument("assignment_id")
    goal_transition_parser.add_argument("state", choices=("pending", "running", "completed", "failed", "blocked"))
    goal_transition_parser.add_argument("--project", type=Path, default=Path.cwd())
    goal_transition_parser.add_argument("--json", action="store_true")

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

        if args.command == "goal":
            if args.goal_command == "init":
                return goal_init(args.goal_id, args.project, as_json=args.json)
            if args.goal_command == "status":
                return goal_status(args.goal_id, args.project, as_json=args.json)
            if args.goal_command == "gate":
                return goal_gate(
                    args.goal_id, args.project, role=args.role, task_domain=args.domain,
                    write_scope=args.scope, change_set=args.change_set, reconciled=args.reconciled,
                    override_reason=args.reason, exception_kind=args.exception,
                    material_change=args.material_change, fresh_context=args.fresh_context,
                    commit=args.commit, as_json=args.json,
                )
            if args.goal_command == "transition":
                return goal_transition(
                    args.goal_id, args.project, args.assignment_id, args.state, as_json=args.json
                )

    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("ERROR: {}".format(exc))
        return 2

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
