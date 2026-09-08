#!/usr/bin/env python3
"""Codex provider/runtime capability probe for Engineering Agent Stack.

This command is intentionally NOT a release gate. It exercises provider-owned
behavior such as spawn_agent, custom-role selection, native subagent routing,
child-model metadata, and effective read/write behavior.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Tuple

from acceptance_core import (
    Check,
    CORE_ROLES,
    ROOT,
    codex_exec,
    clean_sandbox_workspace,
    commit_all,
    external_command,
    git,
    init_sandbox,
    metrics,
    record,
    resolve_command,
    run,
    observed_spawn_events,
    spawn_models,
    spawn_roles,
    trimmed,
    verify_install,
    warn,
    workspace_delta,
)

KNOWN_EPHEMERAL_FORK_ERROR = "collab spawn failed: no thread with id:"
KNOWN_WAIT_TIMEOUT_ERROR = "timeout_ms must be at least 10000"


def progress(message: str) -> None:
    print("[provider-probe] " + message, flush=True)


def toml_string(value: str) -> str:
    """Encode a string as a TOML-compatible basic string."""
    return json.dumps(value, ensure_ascii=True)


def provider_overrides(sandbox: Path) -> List[str]:
    instructions = (
        "Engineering Agent Stack provider delegation diagnostic. "
        "If the user prompt begins with Provider probe., call spawn_agent exactly once "
        "using agent_type equal to the requested custom role and fork_turns equal to none. "
        "Put the complete assignment in the child message, wait for the child result, "
        "and never perform the requested child task directly in the parent. "
        "If spawn_agent fails, report the runtime failure instead of falling back."
    )
    overrides = [
        "agents.enabled=true",
        "agents.max_concurrent_threads_per_session=4",
        "developer_instructions=" + toml_string(instructions),
    ]
    for role in CORE_ROLES:
        role_file = (sandbox / ".codex" / "agents" / (role + ".toml")).resolve()
        overrides.append("agents." + role + ".config_file=" + toml_string(str(role_file)))
    return overrides


def delegation_prompt(role: str, task: str) -> str:
    return (
        "Provider probe. Call spawn_agent exactly once with agent_type `"
        + role
        + "` and fork_turns `none`. Put the complete assignment in the child message. "
        "If wait_agent is used, omit timeout_ms or use at least 10000 ms. "
        + task
    )


def runtime_diagnostic(result: Dict) -> str:
    stderr = str(result.get("stderr") or "")
    notes: List[str] = []
    if result.get("timed_out"):
        notes.append("Codex process timed out")
    if KNOWN_EPHEMERAL_FORK_ERROR in stderr:
        notes.append("upstream V2 ephemeral history-fork failure observed")
    if KNOWN_WAIT_TIMEOUT_ERROR in stderr:
        notes.append("Codex requested wait timeout below runtime minimum")
    return "; ".join(notes)


def result_detail(result: Dict, changed: Optional[List[str]] = None) -> str:
    summary = ((result.get("summary") or {}).get("event_summary") or {})
    observed_spawn_event_count = observed_spawn_events(result)
    detail = "observed_spawn_events={} collab_calls={} roles={} models={}".format(
        observed_spawn_event_count,
        summary.get("collab_tool_calls", 0),
        spawn_roles(result),
        spawn_models(result),
    )
    if changed is not None:
        detail += " changed=" + repr(changed)
    diagnostic = runtime_diagnostic(result)
    if diagnostic:
        detail += "; " + diagnostic
    if result.get("stderr"):
        detail += "; " + trimmed(str(result.get("stderr")))
    if observed_spawn_event_count == 0:
        detail += "; public JSONL does not prove that no child was spawned"
        if result.get("last_message"):
            detail += "; final_provider_message=" + trimmed(str(result.get("last_message")))
    return detail


def check_model_route(checks: List[Check], role: str, expected_model: str, result: Dict) -> None:
    models = spawn_models(result)
    if not models:
        warn(
            checks,
            role + " provider model telemetry",
            "current Codex JSONL did not expose child model metadata",
        )
        return
    record(
        checks,
        role + " provider model route",
        expected_model in models,
        "expected={}; observed={}".format(expected_model, models),
    )


def probe_readonly_role(
    checks: List[Check],
    sandbox: Path,
    args: argparse.Namespace,
    overrides: List[str],
    role: str,
    task: str,
    expected_model: str,
    label: str,
) -> None:
    before = git(["status", "--porcelain"], sandbox).stdout or ""
    result = codex_exec(
        codex_bin=args.codex_bin,
        cwd=sandbox,
        prompt=delegation_prompt(role, task),
        main_model=args.main_model,
        reasoning_effort=args.reasoning_effort,
        sandbox_mode="read-only",
        timeout=args.timeout,
        config_overrides=overrides,
    )
    after = git(["status", "--porcelain"], sandbox).stdout or ""
    record(
        checks,
        label + " observed spawn event",
        result["returncode"] == 0 and observed_spawn_events(result) >= 1,
        result_detail(result),
        metrics(result),
    )
    record(
        checks,
        label + " read-only behavior",
        before == after,
        "git status unchanged" if before == after else "before={!r}; after={!r}".format(before, after),
    )
    check_model_route(checks, role, expected_model, result)


def probe_implementer(
    checks: List[Check],
    sandbox: Path,
    args: argparse.Namespace,
    overrides: List[str],
) -> None:
    clean_sandbox_workspace(sandbox)
    try:
        result = codex_exec(
            codex_bin=args.codex_bin,
            cwd=sandbox,
            prompt=delegation_prompt(
                "implementer",
                "Change IMPLEMENT.md from `status: old` to `status: new` and do not change any other path.",
            ),
            main_model=args.main_model,
            reasoning_effort=args.reasoning_effort,
            sandbox_mode="workspace-write",
            timeout=args.timeout,
            config_overrides=overrides,
        )
        content_ok = (sandbox / "IMPLEMENT.md").read_text(encoding="utf-8") == "status: new\n"
        names = workspace_delta(sandbox)
        record(
            checks,
            "Codex provider Implementer observed spawn event",
            result["returncode"] == 0
            and observed_spawn_events(result) >= 1
            and content_ok,
            result_detail(result, names),
            metrics(result),
        )
        record(
            checks,
            "Codex provider Implementer write scope",
            names == ["IMPLEMENT.md"],
            "changed=" + repr(names),
        )
        check_model_route(checks, "implementer", "gpt-5.6-terra", result)
    finally:
        clean_sandbox_workspace(sandbox)


def write_report(
    path: Path,
    checks: List[Check],
    codex_version: Optional[str],
    extended: bool,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failures = sum(check.status == "FAIL" for check in checks)
    warnings = sum(check.status == "WARN" for check in checks)
    overall = "PASS" if failures == 0 else "FAIL"
    lines = [
        "# Codex Provider Delegation Probe",
        "",
        "- Scope: `provider/runtime diagnostic; not a release gate`",
        "- Timestamp (UTC): `" + datetime.now(timezone.utc).isoformat() + "`",
        "- Overall probe result: **" + overall + "**",
        "- Mode: `" + ("extended" if extended else "basic") + "`",
        "- Platform: `" + platform.platform() + "`",
        "- Python: `" + platform.python_version() + "`",
        "- Codex: `" + (codex_version or "not exercised") + "`",
        "- Failures: `" + str(failures) + "`",
        "- Warnings: `" + str(warnings) + "`",
        "",
        "## Checks",
        "",
        "| Status | Check | Detail |",
        "|---|---|---|",
    ]
    for check in checks:
        detail = check.detail.replace("|", "\\|").replace("\n", " ")
        lines.append("| {} | {} | {} |".format(check.status, check.name, detail))
        if check.metrics:
            lines.extend(["", "```json", json.dumps(check.metrics, indent=2, sort_keys=True), "```", ""])
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A FAIL here means the current Codex provider/runtime did not satisfy the requested delegation capability.",
            "It does not fail Engineering Agent Stack's stack-owned release gate.",
            "`observed_spawn_events` counts `spawn_agent` items present in public `codex exec --json` output; zero does not prove that no child was spawned.",
            "Collaboration-call counts and the final provider message are retained when spawn-event evidence is absent.",
            "",
            "Raw Codex transcripts are intentionally not copied into this report.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--main-model", default="gpt-5.6-terra")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--extended", action="store_true")
    parser.add_argument("--keep-sandbox", action="store_true")
    parser.add_argument("--sandbox-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    checks: List[Check] = []
    codex_version: Optional[str] = None
    temp_context = None
    report = args.report
    if report is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report = ROOT / "acceptance-reports" / ("provider-probe-" + stamp + ".md")
    report = report.expanduser().resolve()

    try:
        if args.sandbox_dir:
            sandbox = args.sandbox_dir.expanduser().resolve()
            if sandbox.exists():
                raise RuntimeError("sandbox directory already exists: " + str(sandbox))
            sandbox.mkdir(parents=True)
        elif args.keep_sandbox:
            sandbox = Path(tempfile.mkdtemp(prefix="engineering-agent-stack-provider-probe-"))
        else:
            temp_context = tempfile.TemporaryDirectory(prefix="engineering-agent-stack-provider-probe-")
            sandbox = Path(temp_context.name)

        init_sandbox(sandbox)
        install = run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install_codex.py"),
                "--project",
                str(sandbox),
                "--project-instructions",
            ],
            cwd=ROOT,
        )
        install_ok = install.returncode == 0
        record(
            checks,
            "Provider probe project installation",
            install_ok,
            trimmed(install.stdout if install_ok else install.stderr or install.stdout),
        )
        if not install_ok:
            raise RuntimeError("provider probe cannot continue because project installation failed")
        verify_install(checks, sandbox)
        commit_all(sandbox, "install engineering agent stack")

        resolved_codex = resolve_command(args.codex_bin)
        if not resolved_codex:
            record(
                checks,
                "Codex CLI available",
                False,
                "unable to resolve " + repr(args.codex_bin) + " from PATH",
            )
        else:
            args.codex_bin = resolved_codex
            version = run(external_command(args.codex_bin, ["--version"]), timeout=30)
            if version.returncode != 0:
                record(checks, "Codex CLI available", False, trimmed(version.stderr or version.stdout))
            else:
                codex_version = trimmed(version.stdout or version.stderr)
                record(checks, "Codex CLI available", True, codex_version + " via " + args.codex_bin)
                overrides = provider_overrides(sandbox)

                progress("[1/2] Scout custom child")
                probe_readonly_role(
                    checks,
                    sandbox,
                    args,
                    overrides,
                    "scout",
                    "Inspect README.md only, do not edit files, and return concise evidence.",
                    "gpt-5.6-luna",
                    "Codex provider Scout",
                )

                progress("[2/2] Implementer custom child")
                probe_implementer(checks, sandbox, args, overrides)

                if args.extended:
                    cases: List[Tuple[str, str, str]] = [
                        ("researcher", "Read README.md and summarize its purpose only. Do not edit files.", "gpt-5.6-luna"),
                        ("debugger", "Inspect src/retry.py and identify the logic defect. Do not edit files.", "gpt-5.6-terra"),
                        ("test-engineer", "Inspect src/retry.py and propose the narrowest test for its defect. Do not edit files.", "gpt-5.6-terra"),
                        ("reviewer", "Review src/retry.py for correctness defects. Do not edit files.", "gpt-5.6-terra"),
                        ("architect", "Assess whether this tiny sandbox needs architectural restructuring. Do not edit files.", "gpt-5.6-sol"),
                    ]
                    for index, (role, task, expected_model) in enumerate(cases, start=1):
                        progress("[extended {}/{}] {}".format(index, len(cases), role))
                        probe_readonly_role(
                            checks,
                            sandbox,
                            args,
                            overrides,
                            role,
                            task,
                            expected_model,
                            "Codex provider " + role,
                        )
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        checks.append(Check("Provider probe execution", "FAIL", str(exc)))
    finally:
        if temp_context is not None:
            temp_context.cleanup()

    write_report(report, checks, codex_version, args.extended)
    print("REPORT: " + str(report))
    for check in checks:
        print("{:<4}  {}: {}".format(check.status, check.name, check.detail))
    print("INFO  Provider delegation probe is diagnostic only and does not gate stack release.")
    return 1 if any(check.status == "FAIL" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
