#!/usr/bin/env python3
"""One-command Codex acceptance test for Engineering Agent Stack.

Offline mode validates the repository and installs the stack into an isolated
throwaway Git repository without invoking a model. Live mode adds real Codex
smoke tests and records observable subagent spawn/token/latency telemetry.
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
from typing import Any

from codex_capture_lib import summarize_events

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
KNOWN_EPHEMERAL_FORK_ERROR = "collab spawn failed: no thread with id:"
KNOWN_WAIT_TIMEOUT_ERROR = "timeout_ms must be at least 10000"


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)


def run(command: list[str], *, cwd: Path | None = None, input_text: str | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def trimmed(text: str, limit: int = 700) -> str:
    value = " ".join((text or "").strip().split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def record(checks: list[Check], name: str, ok: bool, detail: str = "", metrics: dict[str, Any] | None = None) -> bool:
    checks.append(Check(name, "PASS" if ok else "FAIL", detail, metrics or {}))
    return ok


def warn(checks: list[Check], name: str, detail: str) -> None:
    checks.append(Check(name, "WARN", detail))


def skip(checks: list[Check], name: str, detail: str) -> None:
    checks.append(Check(name, "SKIP", detail))


def progress(message: str) -> None:
    print(f"[live] {message}", flush=True)


def git(args: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=cwd, timeout=timeout)


def _prefer_windows_cmd_shim(path: Path) -> Path:
    """Prefer an adjacent npm `.cmd` launcher over `.ps1` on Windows.

    npm normally installs both launchers. Running the PowerShell shim through
    `powershell.exe -File` is fragile for CLI arguments such as the lone `-`
    stdin marker used by `codex exec`; PowerShell may try to parse that marker
    itself before the npm shim can forward it. The `.cmd` shim forwards the
    argument vector without that PowerShell parameter-binding ambiguity.
    """
    if os.name == "nt" and path.suffix.lower() == ".ps1":
        cmd_sibling = path.with_suffix(".cmd")
        if cmd_sibling.is_file():
            return cmd_sibling
    return path


def resolve_command(command: str) -> str | None:
    """Resolve executables plus Windows npm launchers such as codex.cmd/codex.ps1."""
    raw = Path(command).expanduser()
    if raw.is_file():
        return str(_prefer_windows_cmd_shim(raw.resolve()))

    # On Windows, explicitly prefer npm's .cmd shim before generic lookup.
    # PowerShell commonly resolves the same command name to the .ps1 sibling.
    if os.name == "nt" and raw.suffix == "":
        for suffix in (".cmd", ".exe", ".bat"):
            found = shutil.which(command + suffix)
            if found:
                return found

    found = shutil.which(command)
    if found:
        return str(_prefer_windows_cmd_shim(Path(found).resolve()))

    if os.name == "nt" and raw.suffix == "":
        # PowerShell scripts are not normally part of PATHEXT, so search PATH explicitly.
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            if not directory:
                continue
            candidate = Path(directory) / f"{command}.ps1"
            if candidate.is_file():
                return str(_prefer_windows_cmd_shim(candidate.resolve()))
    return None


def external_command(executable: str, args: list[str]) -> list[str]:
    """Build a subprocess-safe command for native binaries and Windows wrappers."""
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
            *args,
        ]
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/s", "/c", executable, *args]
    return [executable, *args]


def init_sandbox(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    result = git(["init"], path)
    if result.returncode != 0:
        raise RuntimeError(f"git init failed: {trimmed(result.stderr or result.stdout)}")
    git(["config", "user.name", "Engineering Agent Stack Acceptance"], path)
    git(["config", "user.email", "acceptance@example.invalid"], path)
    (path / "README.md").write_text("# Acceptance Sandbox\n\nDisposable local Codex test repository.\n", encoding="utf-8")
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
        raise RuntimeError(f"initial commit failed: {trimmed(result.stderr or result.stdout)}")


def commit_all(path: Path, message: str) -> None:
    git(["add", "."], path)
    result = git(["commit", "-m", message], path)
    combined = (result.stdout + result.stderr).lower()
    if result.returncode != 0 and "nothing to commit" not in combined:
        raise RuntimeError(f"git commit failed: {trimmed(result.stderr or result.stdout)}")


def parse_jsonl_text(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw in text.splitlines():
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


def timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def delegation_prompt(role: str, task: str) -> str:
    """Build a bounded fresh-context delegation prompt for Codex V2 acceptance.

    Current Codex releases have an upstream `exec --ephemeral` history-fork
    defect when V2 spawn_agent inherits/forks parent history. The fresh-child
    path (`fork_turns = "none"`) is also the intended stack policy for bounded
    context deltas, so acceptance makes that contract explicit.
    """
    return (
        f"Acceptance test. Use the {role} custom agent exactly once. "
        "When invoking spawn_agent, explicitly set fork_turns to `none`; do not inherit or fork parent history. "
        "Put the complete assignment and any required context in the child message. "
        "If you use wait_agent, omit timeout_ms or set timeout_ms to at least 10000. "
        f"{task}"
    )


def runtime_diagnostic(result: dict[str, Any]) -> str:
    stderr = str(result.get("stderr") or "")
    notes: list[str] = []
    if result.get("timed_out"):
        notes.append("Codex process timed out")
    if KNOWN_EPHEMERAL_FORK_ERROR in stderr:
        notes.append("known upstream Codex V2 ephemeral history-fork failure observed")
    if KNOWN_WAIT_TIMEOUT_ERROR in stderr:
        notes.append("Codex requested a V2 wait timeout below the runtime minimum")
    return "; ".join(notes)


def codex_exec(*, codex_bin: str, cwd: Path, prompt: str, main_model: str, reasoning_effort: str, sandbox_mode: str, timeout: int) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(prefix="engineering-agent-stack-last-message-", suffix=".txt", delete=False) as handle:
        last_message = Path(handle.name)
    command = external_command(
        codex_bin,
        [
            "-c",
            f"model_reasoning_effort={reasoning_effort}",
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
        ],
    )
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
    events = parse_jsonl_text(result.stdout)
    summary = summarize_events(events) if events else None
    last_text = last_message.read_text(encoding="utf-8") if last_message.is_file() else ""
    try:
        last_message.unlink(missing_ok=True)
    except OSError:
        pass
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "last_message": last_text,
        "latency_ms": latency_ms,
        "summary": summary,
        "timed_out": timed_out,
    }


def event_summary(result: dict[str, Any]) -> dict[str, Any]:
    return ((result.get("summary") or {}).get("event_summary") or {})


def spawns(result: dict[str, Any]) -> int:
    value = event_summary(result).get("agent_spawns", 0)
    return value if isinstance(value, int) else 0


def spawn_models(result: dict[str, Any]) -> list[str]:
    values = event_summary(result).get("agent_spawn_models", [])
    return [str(value) for value in values] if isinstance(values, list) else []


def spawn_roles(result: dict[str, Any]) -> list[str]:
    values = event_summary(result).get("agent_spawn_roles", [])
    return [str(value) for value in values] if isinstance(values, list) else []


def metrics(result: dict[str, Any]) -> dict[str, Any]:
    usage = ((result.get("summary") or {}).get("usage") or {})
    return {
        "input_tokens": usage.get("input_tokens", 0),
        "cached_input_tokens": usage.get("cached_input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "reasoning_output_tokens": usage.get("reasoning_output_tokens", 0),
        "latency_ms": result.get("latency_ms"),
        "agent_spawns": spawns(result),
        "timed_out": bool(result.get("timed_out")),
    }


def validator(checks: list[Check], script: str) -> None:
    result = run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT)
    record(
        checks,
        f"Repository validation: {script}",
        result.returncode == 0,
        trimmed(result.stdout if result.returncode == 0 else result.stderr or result.stdout),
    )


def verify_install(checks: list[Check], sandbox: Path) -> bool:
    installed = sorted(path.stem for path in (sandbox / ".codex" / "agents").glob("*.toml"))
    roles_ok = installed == sorted(CORE_ROLES)
    record(checks, "7/7 project-scoped custom-agent files", roles_ok, f"installed={installed}")
    config = sandbox / ".codex" / "config.toml"
    config_text = config.read_text(encoding="utf-8") if config.is_file() else ""
    config_ok = "[agents]" in config_text and "enabled = true" in config_text
    record(checks, "Codex [agents] configuration", config_ok, str(config))
    agents_md = sandbox / "AGENTS.md"
    instructions = agents_md.read_text(encoding="utf-8") if agents_md.is_file() else ""
    instructions_ok = MANAGED_START in instructions and MANAGED_END in instructions
    record(checks, "Parent orchestration instructions installed", instructions_ok, str(agents_md))
    return roles_ok and config_ok and instructions_ok


def live_scout(checks: list[Check], sandbox: Path, args: argparse.Namespace) -> None:
    progress("[1/3] Scout: read-only child delegation")
    before = git(["status", "--porcelain"], sandbox).stdout
    result = codex_exec(
        codex_bin=args.codex_bin,
        cwd=sandbox,
        prompt=delegation_prompt(
            "scout",
            "Inspect README.md only. Do not edit any file. Return concise evidence only.",
        ),
        main_model=args.main_model,
        reasoning_effort=args.reasoning_effort,
        sandbox_mode="read-only",
        timeout=args.timeout,
    )
    after = git(["status", "--porcelain"], sandbox).stdout
    ok = result["returncode"] == 0 and bool(result.get("summary")) and spawns(result) >= 1
    diagnostic = runtime_diagnostic(result)
    detail = f"spawns={spawns(result)} roles={spawn_roles(result)} models={spawn_models(result)}"
    if diagnostic:
        detail += f"; {diagnostic}"
    stderr = trimmed(result["stderr"])
    if stderr:
        detail += f"; {stderr}"
    record(checks, "Live Scout invocation", ok, detail, metrics(result))
    record(checks, "Scout read-only behavior", before == after, "git status unchanged" if before == after else f"before={before!r}; after={after!r}")
    models = spawn_models(result)
    if models and "gpt-5.6-luna" not in models:
        warn(checks, "Scout model telemetry", f"expected Luna candidate; observed={models}")
    elif not models:
        warn(checks, "Scout model telemetry", "spawn event did not expose a child model on this Codex build")
    else:
        record(checks, "Scout model telemetry", True, f"models={models}")


def live_direct(checks: list[Check], sandbox: Path, args: argparse.Namespace) -> None:
    progress("[2/3] Direct-first: trivial edit without delegation")
    git(["reset", "--hard", "HEAD"], sandbox)
    result = codex_exec(
        codex_bin=args.codex_bin,
        cwd=sandbox,
        prompt="Fix the typo `teh` to `the` in DIRECT.md. Make the smallest correct change and verify it. Follow the repository orchestration policy.",
        main_model=args.main_model,
        reasoning_effort=args.reasoning_effort,
        sandbox_mode="workspace-write",
        timeout=args.timeout,
    )
    content_ok = (sandbox / "DIRECT.md").read_text(encoding="utf-8") == "This is the direct-path check.\n"
    process_ok = result["returncode"] == 0 and not result.get("timed_out")
    record(checks, "Direct-first trivial edit correctness", process_ok and content_ok, trimmed(result["stderr"] or result["last_message"]), metrics(result))
    record(checks, "Direct-first avoids unnecessary delegation", process_ok and spawns(result) == 0, f"agent_spawns={spawns(result)}", metrics(result))
    git(["reset", "--hard", "HEAD"], sandbox)


def live_implementer(checks: list[Check], sandbox: Path, args: argparse.Namespace) -> None:
    progress("[3/3] Implementer: bounded child write")
    result = codex_exec(
        codex_bin=args.codex_bin,
        cwd=sandbox,
        prompt=delegation_prompt(
            "implementer",
            "Change IMPLEMENT.md from `status: old` to `status: new`. Do not change any other tracked file.",
        ),
        main_model=args.main_model,
        reasoning_effort=args.reasoning_effort,
        sandbox_mode="workspace-write",
        timeout=args.timeout,
    )
    changed = (sandbox / "IMPLEMENT.md").read_text(encoding="utf-8") == "status: new\n"
    names = [line.strip() for line in git(["diff", "--name-only"], sandbox).stdout.splitlines() if line.strip()]
    ok = result["returncode"] == 0 and spawns(result) >= 1 and changed
    diagnostic = runtime_diagnostic(result)
    detail = f"spawns={spawns(result)} changed={names} roles={spawn_roles(result)} models={spawn_models(result)}"
    if diagnostic:
        detail += f"; {diagnostic}"
    stderr = trimmed(result["stderr"])
    if stderr:
        detail += f"; {stderr}"
    record(checks, "Live Implementer invocation", ok, detail, metrics(result))
    record(checks, "Implementer write scope", names == ["IMPLEMENT.md"], f"changed={names}")
    models = spawn_models(result)
    if models and "gpt-5.6-terra" not in models:
        warn(checks, "Implementer model telemetry", f"expected Terra candidate; observed={models}")
    elif not models:
        warn(checks, "Implementer model telemetry", "spawn event did not expose a child model on this Codex build")
    else:
        record(checks, "Implementer model telemetry", True, f"models={models}")
    git(["reset", "--hard", "HEAD"], sandbox)


def live_extended(checks: list[Check], sandbox: Path, args: argparse.Namespace) -> None:
    cases = [
        ("researcher", "Read README.md and summarize its purpose only. Do not edit files.", "gpt-5.6-luna"),
        ("debugger", "Inspect src/retry.py and identify the logic defect. Do not edit files.", "gpt-5.6-terra"),
        ("test-engineer", "Inspect src/retry.py and propose the narrowest test for its current defect. Do not edit files.", "gpt-5.6-terra"),
        ("reviewer", "Review src/retry.py for correctness defects. Do not edit files.", "gpt-5.6-terra"),
        ("architect", "Assess whether this tiny sandbox needs architectural restructuring. Do not edit files.", "gpt-5.6-sol"),
    ]
    for index, (role, task, expected_model) in enumerate(cases, start=1):
        progress(f"[extended {index}/{len(cases)}] {role}")
        result = codex_exec(
            codex_bin=args.codex_bin,
            cwd=sandbox,
            prompt=delegation_prompt(role, task),
            main_model=args.main_model,
            reasoning_effort=args.reasoning_effort,
            sandbox_mode="read-only",
            timeout=args.timeout,
        )
        diagnostic = runtime_diagnostic(result)
        detail = f"spawns={spawns(result)} roles={spawn_roles(result)} models={spawn_models(result)}"
        if diagnostic:
            detail += f"; {diagnostic}"
        record(checks, f"Extended live role: {role}", result["returncode"] == 0 and spawns(result) >= 1, detail, metrics(result))
        models = spawn_models(result)
        if models and expected_model not in models:
            warn(checks, f"{role} model telemetry", f"expected={expected_model}; observed={models}")


def write_report(path: Path, checks: list[Check], *, mode: str, codex_version: str | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failures = sum(check.status == "FAIL" for check in checks)
    warnings = sum(check.status == "WARN" for check in checks)
    skips = sum(check.status == "SKIP" for check in checks)
    overall = "PASS" if failures == 0 else "FAIL"
    lines = [
        "# Engineering Agent Stack Acceptance Report",
        "",
        f"- Timestamp (UTC): `{datetime.now(timezone.utc).isoformat()}`",
        f"- Overall: **{overall}**",
        f"- Mode: `{mode}`",
        f"- Platform: `{platform.platform()}`",
        f"- Python: `{platform.python_version()}`",
        f"- Codex: `{codex_version or 'not exercised'}`",
        f"- Failures: `{failures}`",
        f"- Warnings: `{warnings}`",
        f"- Skips: `{skips}`",
        "",
        "## Checks",
        "",
        "| Status | Check | Detail |",
        "|---|---|---|",
    ]
    for check in checks:
        detail = check.detail.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {check.status} | {check.name} | {detail} |")
        if check.metrics:
            lines += ["", f"Metrics for **{check.name}**:", "", "```json", json.dumps(check.metrics, indent=2, sort_keys=True), "```", ""]
    lines += [
        "",
        "## Interpretation",
        "",
        "- `PASS`: required acceptance condition was observed.",
        "- `WARN`: optional telemetry was incomplete or a non-blocking expectation differed.",
        "- `SKIP`: intentionally not exercised in this mode.",
        "- `FAIL`: acceptance condition was not met; do not call the tested path stable yet.",
        "",
        "Raw Codex transcripts are intentionally not copied into this report.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="invoke Codex and consume model tokens")
    mode.add_argument("--offline", action="store_true", help="skip all Codex model invocations")
    parser.add_argument("--extended", action="store_true", help="live-test the remaining roles")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--main-model", default="gpt-5.6-terra")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--keep-sandbox", action="store_true")
    parser.add_argument("--sandbox-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.extended and not args.live:
        parser.error("--extended requires --live")

    live = bool(args.live)
    checks: list[Check] = []
    codex_version: str | None = None
    temp_context: tempfile.TemporaryDirectory[str] | None = None
    report = args.report
    if report is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report = ROOT / "acceptance-reports" / f"acceptance-{stamp}.md"
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
    record(checks, "Generated Codex adapter drift check", generated.returncode == 0, trimmed(generated.stdout if generated.returncode == 0 else generated.stderr or generated.stdout))
    git_version = run(["git", "--version"])
    record(checks, "Git available", git_version.returncode == 0, trimmed(git_version.stdout or git_version.stderr))

    try:
        if args.sandbox_dir:
            sandbox = args.sandbox_dir.expanduser().resolve()
            if sandbox.exists():
                raise RuntimeError(f"sandbox directory already exists: {sandbox}")
            sandbox.mkdir(parents=True)
        elif args.keep_sandbox:
            sandbox = Path(tempfile.mkdtemp(prefix="engineering-agent-stack-acceptance-"))
        else:
            temp_context = tempfile.TemporaryDirectory(prefix="engineering-agent-stack-acceptance-")
            sandbox = Path(temp_context.name)

        init_sandbox(sandbox)
        install = run([
            sys.executable,
            str(ROOT / "scripts" / "install_codex.py"),
            "--project",
            str(sandbox),
            "--project-instructions",
        ], cwd=ROOT)
        install_ok = install.returncode == 0
        record(checks, "Project-scoped installation", install_ok, trimmed(install.stdout if install_ok else install.stderr or install.stdout))
        if install_ok:
            verify_install(checks, sandbox)
            commit_all(sandbox, "install engineering agent stack")
            check_install = run([
                sys.executable,
                str(ROOT / "scripts" / "install_codex.py"),
                "--project",
                str(sandbox),
                "--project-instructions",
                "--check",
            ], cwd=ROOT)
            record(checks, "Installed adapter consistency check", check_install.returncode == 0, trimmed(check_install.stdout if check_install.returncode == 0 else check_install.stderr or check_install.stdout))

        if live and install_ok:
            resolved_codex = resolve_command(args.codex_bin)
            if not resolved_codex:
                record(checks, "Codex CLI available", False, f"unable to resolve {args.codex_bin!r} from PATH")
            else:
                args.codex_bin = resolved_codex
                version = run(external_command(args.codex_bin, ["--version"]), timeout=30)
                if version.returncode != 0:
                    record(checks, "Codex CLI available", False, trimmed(version.stderr or version.stdout or "Codex CLI failed to execute"))
                else:
                    codex_version = trimmed(version.stdout or version.stderr)
                    record(checks, "Codex CLI available", True, f"{codex_version} via {args.codex_bin}")
                    live_scout(checks, sandbox, args)
                    live_direct(checks, sandbox, args)
                    live_implementer(checks, sandbox, args)
                    if args.extended:
                        live_extended(checks, sandbox, args)
        else:
            skip(checks, "Live Codex model tests", "offline mode; pass --live or run scripts/acceptance-test.ps1 on Windows")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        checks.append(Check("Acceptance harness execution", "FAIL", str(exc)))
    finally:
        if temp_context is not None:
            temp_context.cleanup()

    write_report(report, checks, mode="live-extended" if live and args.extended else ("live" if live else "offline"), codex_version=codex_version)
    print(f"REPORT: {report}")
    for check in checks:
        print(f"{check.status:4}  {check.name}: {check.detail}")
    return 1 if any(check.status == "FAIL" for check in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
