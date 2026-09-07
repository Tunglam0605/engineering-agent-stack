#!/usr/bin/env python3
"""Stack-owned acceptance harness for Engineering Agent Stack.

This release gate validates invariants that this repository controls directly:
repository structure, generated adapter drift, isolated project installation,
direct-first behavior, and bounded write scope. Provider-specific child-agent
spawning/model-routing experiments intentionally live in provider_probe_codex.py.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

from codex_capture_lib import summarize_events
from install_codex import validate_config

ROOT = Path(__file__).resolve().parents[1]
CORE_ROLES = (
    "scout",
    "researcher",
    "implementer",
    "debugger",
    "test-engineer",
    "reviewer",
    "architect",
)
MANAGED_START = "<!-- engineering-agent-stack:start -->"
MANAGED_END = "<!-- engineering-agent-stack:end -->"


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)


def run(
    command: List[str],
    *,
    cwd: Optional[Path] = None,
    input_text: Optional[str] = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess:
    """Run a subprocess with locale-independent UTF-8 text pipes.

    Codex emits UTF-8 JSONL. Windows engineering environments may inherit
    cp1252/OEM code pages, so relying on subprocess' locale default can crash a
    reader thread before the harness sees any output. Replacement is preferred
    to a harness crash because malformed provider text is diagnostic data, not
    a reason to lose the entire acceptance report.
    """
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd is not None else None,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout,
    )


def trimmed(text: Optional[str], limit: int = 700) -> str:
    value = " ".join((text or "").strip().split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def record(
    checks: List[Check],
    name: str,
    ok: bool,
    detail: str = "",
    metrics: Optional[Dict[str, Any]] = None,
) -> bool:
    checks.append(Check(name, "PASS" if ok else "FAIL", detail, metrics or {}))
    return ok


def warn(checks: List[Check], name: str, detail: str) -> None:
    checks.append(Check(name, "WARN", detail))


def skip(checks: List[Check], name: str, detail: str) -> None:
    checks.append(Check(name, "SKIP", detail))


def progress(message: str) -> None:
    print("[live] " + message, flush=True)


def git(
    args: List[str],
    cwd: Path,
    timeout: int = 60,
    *,
    text: bool = True,
) -> subprocess.CompletedProcess:
    if text:
        return run(["git"] + args, cwd=cwd, timeout=timeout)
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _output_bytes(value: object) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8", errors="surrogateescape")
    return b""


def _git_z_records(result: subprocess.CompletedProcess) -> List[bytes]:
    return [record for record in _output_bytes(result.stdout).split(b"\0") if record]


def _git_path(raw_path: bytes) -> str:
    """Decode Git's raw pathname bytes with the filesystem's lossless codec."""
    return os.fsdecode(raw_path)


def _index_flagged_paths(sandbox: Path) -> Dict[str, List[str]]:
    result = git(["ls-files", "-v", "-z", "--"], sandbox, text=False)
    if result.returncode != 0:
        raise RuntimeError(
            "unable to inspect sandbox index flags: "
            + trimmed(os.fsdecode(_output_bytes(result.stderr or result.stdout)))
        )

    flagged: Dict[str, List[str]] = {
        "assume-unchanged": [],
        "skip-worktree": [],
    }
    for record in _git_z_records(result):
        if len(record) < 3 or record[1:2] != b" ":
            raise RuntimeError("unable to parse sandbox index flags losslessly")
        tag = record[:1]
        path = _git_path(record[2:])
        if tag in (b"S", b"s"):
            flagged["skip-worktree"].append(path)
        if tag.islower():
            flagged["assume-unchanged"].append(path)
    return flagged


def _raise_for_index_flags(sandbox: Path) -> None:
    flagged = _index_flagged_paths(sandbox)
    details = [
        name + ": " + ", ".join(paths)
        for name, paths in flagged.items()
        if paths
    ]
    if details:
        raise RuntimeError(
            "refusing exact-scope check with abnormal index flags: " + "; ".join(details)
        )


def workspace_delta(sandbox: Path) -> List[str]:
    """Return every tracked, staged, or untracked path changed in a sandbox."""
    _raise_for_index_flags(sandbox)
    commands = (
        ["diff", "--name-only", "-z", "--"],
        ["diff", "--cached", "--name-only", "-z", "--"],
        ["ls-files", "--others", "-z", "--"],
    )
    changed = set()
    for args in commands:
        result = git(args, sandbox, text=False)
        if result.returncode != 0:
            raise RuntimeError(
                "unable to inspect sandbox workspace delta: "
                + trimmed(os.fsdecode(_output_bytes(result.stderr or result.stdout)))
            )
        for raw_path in _git_z_records(result):
            changed.add(_git_path(raw_path))
    return sorted(changed)


def clean_sandbox_workspace(sandbox: Path) -> None:
    """Restore HEAD and remove untracked content inside a disposable sandbox."""
    expected = sandbox.resolve()
    if expected == ROOT.resolve():
        raise RuntimeError("refusing to clean the real repository as a disposable sandbox")
    top_level = git(["rev-parse", "--show-toplevel"], expected)
    if top_level.returncode != 0:
        raise RuntimeError(
            "refusing sandbox cleanup outside a Git worktree: "
            + trimmed(top_level.stderr or top_level.stdout)
        )
    actual = Path((top_level.stdout or "").strip()).resolve()
    if actual != expected:
        raise RuntimeError(
            "refusing sandbox cleanup because Git top level is {} not {}".format(
                actual, expected
            )
        )
    flagged = _index_flagged_paths(expected)
    for flag_name, flagged_paths in flagged.items():
        if not flagged_paths:
            continue
        clear_flags = git(
            [
                "update-index",
                "--no-" + flag_name,
                "--",
            ]
            + sorted(set(flagged_paths)),
            expected,
        )
        if clear_flags.returncode != 0:
            raise RuntimeError(
                "sandbox cleanup failed to clear " + flag_name + ": "
                + trimmed(clear_flags.stderr or clear_flags.stdout)
            )
    for args in (["reset", "--hard", "HEAD"], ["clean", "-ffdx"]):
        result = git(args, expected)
        if result.returncode != 0:
            raise RuntimeError(
                "sandbox cleanup failed: " + trimmed(result.stderr or result.stdout)
            )


def _prefer_windows_cmd_shim(path: Path) -> Path:
    if os.name == "nt" and path.suffix.lower() == ".ps1":
        sibling = path.with_suffix(".cmd")
        if sibling.is_file():
            return sibling
    return path


def resolve_command(command: str) -> Optional[str]:
    """Resolve native executables and Windows npm launchers safely."""
    raw = Path(command).expanduser()
    if raw.is_file():
        return str(_prefer_windows_cmd_shim(raw.resolve()))

    if os.name == "nt" and raw.suffix == "":
        for suffix in (".cmd", ".exe", ".bat"):
            found = shutil.which(command + suffix)
            if found:
                return found

    found = shutil.which(command)
    if found:
        return str(_prefer_windows_cmd_shim(Path(found).resolve()))

    if os.name == "nt" and raw.suffix == "":
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            if not directory:
                continue
            candidate = Path(directory) / (command + ".ps1")
            if candidate.is_file():
                return str(_prefer_windows_cmd_shim(candidate.resolve()))
    return None


def external_command(executable: str, args: List[str]) -> List[str]:
    executable_path = _prefer_windows_cmd_shim(Path(executable).expanduser())
    executable = str(executable_path)
    suffix = executable_path.suffix.lower()
    if os.name == "nt" and suffix == ".ps1":
        return [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            executable,
        ] + args
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/s", "/c", executable] + args
    return [executable] + args


def init_sandbox(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    result = git(["init"], path)
    if result.returncode != 0:
        raise RuntimeError("git init failed: " + trimmed(result.stderr or result.stdout))
    git(["config", "user.name", "Engineering Agent Stack Acceptance"], path)
    git(["config", "user.email", "acceptance@example.invalid"], path)
    (path / "README.md").write_text(
        "# Acceptance Sandbox\n\nDisposable local Codex test repository.\n",
        encoding="utf-8",
    )
    (path / "DIRECT.md").write_text("This is teh direct-path check.\n", encoding="utf-8")
    (path / "IMPLEMENT.md").write_text("status: old\n", encoding="utf-8")
    src = path / "src"
    src.mkdir()
    (src / "retry.py").write_text(
        "def should_retry(attempt: int, max_attempts: int) -> bool:\n"
        "    return attempt > max_attempts\n",
        encoding="utf-8",
    )
    git(["add", "."], path)
    result = git(["commit", "-m", "seed acceptance sandbox"], path)
    if result.returncode != 0:
        raise RuntimeError("initial commit failed: " + trimmed(result.stderr or result.stdout))


def commit_all(path: Path, message: str) -> None:
    git(["add", "."], path)
    result = git(["commit", "-m", message], path)
    combined = ((result.stdout or "") + (result.stderr or "")).lower()
    if result.returncode != 0 and "nothing to commit" not in combined:
        raise RuntimeError("git commit failed: " + trimmed(result.stderr or result.stdout))


def parse_jsonl_text(text: Optional[str]) -> List[Dict[str, Any]]:
    """Parse JSONL defensively; None/empty output is a valid zero-event stream."""
    events: List[Dict[str, Any]] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def timeout_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def codex_exec(
    *,
    codex_bin: str,
    cwd: Path,
    prompt: str,
    main_model: str,
    reasoning_effort: str,
    sandbox_mode: str,
    timeout: int,
    config_overrides: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Execute Codex with stable UTF-8 capture and optional session overrides."""
    with tempfile.NamedTemporaryFile(
        prefix="engineering-agent-stack-last-message-",
        suffix=".txt",
        delete=False,
    ) as handle:
        last_message = Path(handle.name)

    overrides = [
        "approval_policy='never'",
        "model_reasoning_effort='" + reasoning_effort + "'",
    ]
    overrides.extend(config_overrides or [])
    codex_args: List[str] = []
    for override in overrides:
        codex_args.extend(["-c", override])
    codex_args.extend(
        [
            "exec",
            "--json",
            "--ephemeral",
            "--model",
            main_model,
            "--sandbox",
            sandbox_mode,
            "--output-last-message",
            str(last_message),
            "-",
        ]
    )

    command = external_command(codex_bin, codex_args)
    started = time.perf_counter()
    timed_out = False
    try:
        result = run(command, cwd=cwd, input_text=prompt, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        result = subprocess.CompletedProcess(
            command,
            124,
            stdout=timeout_text(exc.stdout),
            stderr=timeout_text(exc.stderr),
        )

    latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
    stdout = timeout_text(result.stdout)
    stderr = timeout_text(result.stderr)
    events = parse_jsonl_text(stdout)
    summary = summarize_events(events) if events else None
    last_text = ""
    if last_message.is_file():
        last_text = last_message.read_text(encoding="utf-8", errors="replace")
    try:
        last_message.unlink(missing_ok=True)
    except OSError:
        pass

    return {
        "returncode": result.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "last_message": last_text,
        "latency_ms": latency_ms,
        "summary": summary,
        "timed_out": timed_out,
    }


def event_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    return ((result.get("summary") or {}).get("event_summary") or {})


def observed_spawn_events(result: Dict[str, Any]) -> int:
    """Return spawn_agent events observed in public Codex exec JSONL."""
    value = event_summary(result).get("agent_spawns", 0)
    return value if isinstance(value, int) else 0


def spawn_models(result: Dict[str, Any]) -> List[str]:
    values = event_summary(result).get("agent_spawn_models", [])
    return [str(value) for value in values] if isinstance(values, list) else []


def spawn_roles(result: Dict[str, Any]) -> List[str]:
    values = event_summary(result).get("agent_spawn_roles", [])
    return [str(value) for value in values] if isinstance(values, list) else []


def metrics(result: Dict[str, Any]) -> Dict[str, Any]:
    usage = ((result.get("summary") or {}).get("usage") or {})
    return {
        "input_tokens": usage.get("input_tokens", 0),
        "cached_input_tokens": usage.get("cached_input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "reasoning_output_tokens": usage.get("reasoning_output_tokens", 0),
        "latency_ms": result.get("latency_ms"),
        # Retain the normalized compatibility key while treating it only as
        # public JSONL evidence, not proof of runtime child activity.
        "agent_spawns": observed_spawn_events(result),
        "timed_out": bool(result.get("timed_out")),
    }


def validator(checks: List[Check], script: str) -> None:
    result = run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT)
    record(
        checks,
        "Repository validation: " + script,
        result.returncode == 0,
        trimmed(result.stdout if result.returncode == 0 else result.stderr or result.stdout),
    )


def verify_install(checks: List[Check], sandbox: Path) -> bool:
    installed = sorted(path.stem for path in (sandbox / ".codex" / "agents").glob("*.toml"))
    roles_ok = installed == sorted(CORE_ROLES)
    record(checks, "7/7 project-scoped custom-agent files", roles_ok, "installed=" + repr(installed))

    config = sandbox / ".codex" / "config.toml"
    config_problems = validate_config(config)
    config_ok = not config_problems
    record(
        checks,
        "Codex delegation configuration",
        config_ok,
        str(config) if config_ok else "; ".join(config_problems),
    )

    agents_md = sandbox / "AGENTS.md"
    instructions = agents_md.read_text(encoding="utf-8") if agents_md.is_file() else ""
    instructions_ok = MANAGED_START in instructions and MANAGED_END in instructions
    record(checks, "Parent orchestration instructions installed", instructions_ok, str(agents_md))
    return roles_ok and config_ok and instructions_ok


def live_direct(checks: List[Check], sandbox: Path, args: argparse.Namespace) -> None:
    progress("[1/2] Direct-first: trivial one-file edit")
    clean_sandbox_workspace(sandbox)
    try:
        result = codex_exec(
            codex_bin=args.codex_bin,
            cwd=sandbox,
            prompt=(
                "Acceptance sandbox: this one-file edit is already authorized. "
                "Fix only the typo `teh` to `the` in DIRECT.md, verify the exact diff, "
                "and do not ask for confirmation. This task is trivial and should be handled directly."
            ),
            main_model=args.main_model,
            reasoning_effort=args.reasoning_effort,
            sandbox_mode="workspace-write",
            timeout=args.timeout,
        )
        process_ok = result["returncode"] == 0 and not result.get("timed_out")
        content_ok = (sandbox / "DIRECT.md").read_text(encoding="utf-8") == "This is the direct-path check.\n"
        names = workspace_delta(sandbox)
        unstaged_diff_check = git(["diff", "--check"], sandbox)
        staged_diff_check = git(["diff", "--cached", "--check"], sandbox)

        record(
            checks,
            "Direct-first trivial edit correctness",
            process_ok and content_ok,
            trimmed(result["stderr"] or result["last_message"]),
            metrics(result),
        )
        record(
            checks,
            "Direct-first exact write scope",
            process_ok
            and names == ["DIRECT.md"]
            and unstaged_diff_check.returncode == 0
            and staged_diff_check.returncode == 0,
            "changed=" + repr(names),
        )
        if result.get("summary") is None:
            warn(checks, "Direct-first delegation telemetry", "Codex JSONL did not expose parseable event telemetry")
        else:
            record(
                checks,
                "Direct-first public JSONL spawn-event observation",
                observed_spawn_events(result) == 0,
                "observed_spawn_events="
                + str(observed_spawn_events(result))
                + "; public JSONL does not prove that no child was spawned",
                metrics(result),
            )
    finally:
        clean_sandbox_workspace(sandbox)


def live_bounded_write(checks: List[Check], sandbox: Path, args: argparse.Namespace) -> None:
    progress("[2/2] Bounded write: exact one-file scope")
    clean_sandbox_workspace(sandbox)
    try:
        result = codex_exec(
            codex_bin=args.codex_bin,
            cwd=sandbox,
            prompt=(
                "Acceptance sandbox: this change is already authorized. "
                "Change IMPLEMENT.md from `status: old` to `status: new`. "
                "Do not change any other path. Verify the final diff and do not ask for confirmation."
            ),
            main_model=args.main_model,
            reasoning_effort=args.reasoning_effort,
            sandbox_mode="workspace-write",
            timeout=args.timeout,
        )
        process_ok = result["returncode"] == 0 and not result.get("timed_out")
        content_ok = (sandbox / "IMPLEMENT.md").read_text(encoding="utf-8") == "status: new\n"
        names = workspace_delta(sandbox)
        unstaged_diff_check = git(["diff", "--check"], sandbox)
        staged_diff_check = git(["diff", "--cached", "--check"], sandbox)

        record(
            checks,
            "Bounded write correctness",
            process_ok and content_ok,
            trimmed(result["stderr"] or result["last_message"]),
            metrics(result),
        )
        record(
            checks,
            "Bounded write exact scope",
            process_ok
            and names == ["IMPLEMENT.md"]
            and unstaged_diff_check.returncode == 0
            and staged_diff_check.returncode == 0,
            "changed=" + repr(names),
        )
    finally:
        clean_sandbox_workspace(sandbox)


def write_report(path: Path, checks: List[Check], *, mode: str, codex_version: Optional[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failures = sum(check.status == "FAIL" for check in checks)
    warnings = sum(check.status == "WARN" for check in checks)
    skips = sum(check.status == "SKIP" for check in checks)
    overall = "PASS" if failures == 0 else "FAIL"
    lines = [
        "# Engineering Agent Stack Acceptance Report",
        "",
        "- Scope: `stack-owned release gate`",
        "- Provider child-spawn/model-routing probes: `excluded`",
        "- Timestamp (UTC): `" + datetime.now(timezone.utc).isoformat() + "`",
        "- Overall: **" + overall + "**",
        "- Mode: `" + mode + "`",
        "- Platform: `" + platform.platform() + "`",
        "- Python: `" + platform.python_version() + "`",
        "- Codex: `" + (codex_version or "not exercised") + "`",
        "- Failures: `" + str(failures) + "`",
        "- Warnings: `" + str(warnings) + "`",
        "- Skips: `" + str(skips) + "`",
        "",
        "## Checks",
        "",
        "| Status | Check | Detail |",
        "|---|---|---|",
    ]
    for check in checks:
        detail = check.detail.replace("|", "\\|").replace("\n", " ")
        lines.append("| " + check.status + " | " + check.name + " | " + detail + " |")
        if check.metrics:
            lines.extend(
                [
                    "",
                    "Metrics for **" + check.name + "**:",
                    "",
                    "```json",
                    json.dumps(check.metrics, indent=2, sort_keys=True),
                    "```",
                    "",
                ]
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `PASS`: a stack-owned acceptance condition was observed.",
            "- `WARN`: optional runtime telemetry was unavailable; the stack-owned condition still completed.",
            "- `SKIP`: intentionally not exercised in this mode.",
            "- `FAIL`: a repository/installer/direct-write invariant failed and blocks the release gate.",
            "- `agent_spawns` in normalized metrics is a compatibility field counting `spawn_agent` events observed in public JSONL; zero is not proof that no child ran.",
            "",
            "Provider-specific child spawning, role selection, and child-model routing are tested separately by `scripts/provider-probe.ps1`.",
            "",
            "Raw Codex transcripts are intentionally not copied into this report.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="run the two stack-owned live Codex behavior checks")
    mode.add_argument("--offline", action="store_true", help="skip all Codex model invocations")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--main-model", default="gpt-5.6-terra")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--keep-sandbox", action="store_true")
    parser.add_argument("--sandbox-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    live = bool(args.live)
    checks: List[Check] = []
    codex_version: Optional[str] = None
    temp_context = None
    report = args.report
    if report is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report = ROOT / "acceptance-reports" / ("acceptance-" + stamp + ".md")
    report = report.expanduser().resolve()

    for script in (
        "validate_structure.py",
        "validate_provenance.py",
        "validate_agents.py",
        "evaluate_routing.py",
        "validate_task_suite.py",
        "validate_benchmarks.py",
    ):
        validator(checks, script)

    generated = run([sys.executable, str(ROOT / "scripts" / "generate_codex_adapter.py"), "--check"], cwd=ROOT)
    record(
        checks,
        "Generated Codex adapter drift check",
        generated.returncode == 0,
        trimmed(generated.stdout if generated.returncode == 0 else generated.stderr or generated.stdout),
    )
    git_version = run(["git", "--version"])
    record(checks, "Git available", git_version.returncode == 0, trimmed(git_version.stdout or git_version.stderr))

    try:
        if args.sandbox_dir:
            sandbox = args.sandbox_dir.expanduser().resolve()
            if sandbox.exists():
                raise RuntimeError("sandbox directory already exists: " + str(sandbox))
            sandbox.mkdir(parents=True)
        elif args.keep_sandbox:
            sandbox = Path(tempfile.mkdtemp(prefix="engineering-agent-stack-acceptance-"))
        else:
            temp_context = tempfile.TemporaryDirectory(prefix="engineering-agent-stack-acceptance-")
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
            "Project-scoped installation",
            install_ok,
            trimmed(install.stdout if install_ok else install.stderr or install.stdout),
        )
        if install_ok:
            verify_install(checks, sandbox)
            commit_all(sandbox, "install engineering agent stack")
            check_install = run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "install_codex.py"),
                    "--project",
                    str(sandbox),
                    "--project-instructions",
                    "--check",
                ],
                cwd=ROOT,
            )
            record(
                checks,
                "Installed adapter consistency check",
                check_install.returncode == 0,
                trimmed(
                    check_install.stdout
                    if check_install.returncode == 0
                    else check_install.stderr or check_install.stdout
                ),
            )

        if live and install_ok:
            resolved_codex = resolve_command(args.codex_bin)
            if not resolved_codex:
                record(checks, "Codex CLI available", False, "unable to resolve " + repr(args.codex_bin) + " from PATH")
            else:
                args.codex_bin = resolved_codex
                version = run(external_command(args.codex_bin, ["--version"]), timeout=30)
                if version.returncode != 0:
                    record(
                        checks,
                        "Codex CLI available",
                        False,
                        trimmed(version.stderr or version.stdout or "Codex CLI failed to execute"),
                    )
                else:
                    codex_version = trimmed(version.stdout or version.stderr)
                    record(checks, "Codex CLI available", True, codex_version + " via " + args.codex_bin)
                    live_direct(checks, sandbox, args)
                    live_bounded_write(checks, sandbox, args)
        else:
            skip(
                checks,
                "Live Codex stack-owned behavior tests",
                "offline mode; run scripts/acceptance-test.ps1 without -Offline to exercise them",
            )
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        checks.append(Check("Acceptance harness execution", "FAIL", str(exc)))
    finally:
        if temp_context is not None:
            temp_context.cleanup()

    write_report(report, checks, mode="live" if live else "offline", codex_version=codex_version)
    print("REPORT: " + str(report))
    for check in checks:
        print("{:<4}  {}: {}".format(check.status, check.name, check.detail))
    return 1 if any(check.status == "FAIL" for check in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
