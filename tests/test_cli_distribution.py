from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import contextlib
import io
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
ROLES = {
    "architect.toml",
    "debugger.toml",
    "implementer.toml",
    "researcher.toml",
    "reviewer.toml",
    "scout.toml",
    "test-engineer.toml",
}


class CliDistributionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temp_dir.name)
        self.home = self.sandbox / "home"
        self.home.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cli(
        self,
        *args: str,
        cwd: Optional[Path] = None,
        source: Optional[Path] = ROOT,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["EAS_HOME"] = str(self.home)
        if source is None:
            env.pop("EAS_REPO", None)
        else:
            env["EAS_REPO"] = str(source)
        return subprocess.run(
            [PYTHON, "-m", "eas_cli", *args],
            cwd=str(cwd or ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=False,
        )

    def init_git(self, project: Path) -> None:
        project.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=str(project),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "tests@example.invalid"],
            cwd=str(project),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "EAS Tests"],
            cwd=str(project),
            check=True,
        )

    def test_version_uses_single_package_version(self) -> None:
        result = self.run_cli("version")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "eas 0.3.0")

        wrapper = subprocess.run(
            [PYTHON, str(ROOT / "scripts" / "eas.py"), "version"],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(wrapper.returncode, 0, wrapper.stderr)
        self.assertEqual(wrapper.stdout.strip(), "eas 0.3.0")

    def test_doctor_and_status_json_are_read_only_and_structured(self) -> None:
        before = sorted(path.relative_to(self.home) for path in self.home.rglob("*"))

        doctor_result = self.run_cli("doctor", "--json")
        status_result = self.run_cli("status", "--json")

        self.assertEqual(doctor_result.returncode, 0, doctor_result.stderr)
        self.assertEqual(status_result.returncode, 0, status_result.stderr)
        doctor = json.loads(doctor_result.stdout)
        status = json.loads(status_result.stdout)
        self.assertEqual(doctor["command"], "doctor")
        self.assertEqual(doctor["version"], "0.3.0")
        self.assertIn(doctor["core"]["status"], {"HEALTHY", "DEGRADED"})
        self.assertEqual(doctor["provider"], {"status": "UNKNOWN", "probed": False})
        self.assertEqual(
            set(doctor["checks"]),
            {"python", "git", "codex", "source", "personal", "project"},
        )
        self.assertEqual(status["command"], "status")
        self.assertEqual(status["version"], "0.3.0")
        self.assertEqual(status["roles"]["expected"], 7)
        self.assertEqual(len(status["roles"]["canonical"]), 7)
        self.assertEqual(
            status["policy"],
            {"readers": 4, "writers": 3, "recursive_delegation": False},
        )
        self.assertEqual(
            before,
            sorted(path.relative_to(self.home) for path in self.home.rglob("*")),
        )

    def test_init_preserves_agents_content_and_installs_project_roles(self) -> None:
        project = self.sandbox / "project"
        self.init_git(project)
        original = "# Local project rules\n\nKeep this paragraph.\n"
        (project / "AGENTS.md").write_text(original, encoding="utf-8")

        result = self.run_cli("init", str(project))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = {path.name for path in (project / ".codex" / "agents").glob("*.toml")}
        self.assertEqual(installed, ROLES)
        instructions = (project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(original.strip(), instructions)
        self.assertIn("<!-- engineering-agent-stack:start -->", instructions)
        self.assertTrue((project / ".codex" / "config.toml").is_file())

    def test_init_dry_run_makes_no_changes(self) -> None:
        project = self.sandbox / "project"
        self.init_git(project)

        result = self.run_cli("init", str(project), "--dry-run")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((project / ".codex").exists())
        self.assertFalse((project / "AGENTS.md").exists())

    def test_uninstall_preserves_config_unrelated_roles_and_agents_content(self) -> None:
        project = self.sandbox / "project"
        self.init_git(project)
        original = "# Keep me\n"
        (project / "AGENTS.md").write_text(original, encoding="utf-8")
        self.assertEqual(self.run_cli("init", str(project)).returncode, 0)
        config = project / ".codex" / "config.toml"
        config_text = config.read_text(encoding="utf-8")
        unrelated = project / ".codex" / "agents" / "local-specialist.toml"
        unrelated.write_text("name = 'local'\n", encoding="utf-8")

        result = self.run_cli(
            "uninstall", "--project", str(project), "--project-instructions"
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(config.read_text(encoding="utf-8"), config_text)
        self.assertTrue(unrelated.is_file())
        self.assertEqual(
            {path.name for path in (project / ".codex" / "agents").glob("*.toml")},
            {"local-specialist.toml"},
        )
        self.assertEqual((project / "AGENTS.md").read_text(encoding="utf-8"), original)

    def test_uninstall_refuses_drift_without_partial_deletion(self) -> None:
        project = self.sandbox / "project"
        self.init_git(project)
        self.assertEqual(self.run_cli("init", str(project)).returncode, 0)
        drifted = project / ".codex" / "agents" / "architect.toml"
        drifted.write_text(drifted.read_text(encoding="utf-8") + "# local\n", encoding="utf-8")

        result = self.run_cli("uninstall", "--project", str(project))

        self.assertEqual(result.returncode, 2)
        self.assertIn("REFUSED", result.stdout)
        self.assertEqual(
            {path.name for path in (project / ".codex" / "agents").glob("*.toml")},
            ROLES,
        )

    def test_update_refuses_dirty_source_checkout_before_fetch(self) -> None:
        checkout = self.sandbox / "checkout"
        self.init_git(checkout)
        (checkout / "scripts").mkdir()
        shutil.copy2(ROOT / "scripts" / "install_codex.py", checkout / "scripts" / "install_codex.py")
        subprocess.run(["git", "add", "."], cwd=str(checkout), check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=str(checkout), check=True)
        (checkout / "dirty.txt").write_text("dirty\n", encoding="utf-8")

        result = self.run_cli("update", source=checkout)

        self.assertEqual(result.returncode, 2)
        self.assertIn("dirty", result.stdout.lower())
        self.assertNotIn("fetch", result.stdout.lower())


    def make_update_remote(self) -> tuple[Path, Path]:
        seed = self.sandbox / "seed"
        remote = self.sandbox / "remote.git"
        checkout = self.sandbox / "update-checkout"
        self.init_git(seed)
        (seed / "scripts").mkdir()
        (seed / "adapters" / "codex" / "agents").mkdir(parents=True)
        (seed / "scripts" / "install_codex.py").write_text(
            "def validate_config(path):\n    return []\n",
            encoding="utf-8",
        )
        (seed / "scripts" / "generate_codex_adapter.py").write_text(
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        (seed / "adapters" / "codex" / "agents" / "scout.toml").write_text(
            "name = 'scout-v1'\n",
            encoding="utf-8",
        )
        (seed / "adapters" / "codex" / "agents" / "reviewer.toml").write_text(
            "name = 'reviewer-v1'\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "."], cwd=str(seed), check=True)
        subprocess.run(["git", "commit", "-m", "v1"], cwd=str(seed), check=True)
        subprocess.run(["git", "clone", "--bare", str(seed), str(remote)], check=True)
        subprocess.run(["git", "clone", str(remote), str(checkout)], check=True)
        subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=str(checkout), check=True)
        subprocess.run(["git", "config", "user.name", "EAS Tests"], cwd=str(checkout), check=True)
        return seed, checkout

    def push_update_fixture(self, seed: Path, remote: Path, *, generator_exit: int = 0) -> str:
        (seed / "scripts" / "generate_codex_adapter.py").write_text(
            "raise SystemExit({})\n".format(generator_exit),
            encoding="utf-8",
        )
        (seed / "VERSION-FIXTURE").write_text("v2\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(seed), check=True)
        subprocess.run(["git", "commit", "-m", "v2"], cwd=str(seed), check=True)
        subprocess.run(["git", "push", str(remote), "main"], cwd=str(seed), check=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(seed),
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()

    def test_update_fast_forwards_explicit_source_only_checkout(self) -> None:
        seed, checkout = self.make_update_remote()
        remote = self.sandbox / "remote.git"
        expected_head = self.push_update_fixture(seed, remote)

        result = self.run_cli("update", source=checkout)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        actual_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(checkout),
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        self.assertEqual(actual_head, expected_head)
        self.assertTrue((checkout / "VERSION-FIXTURE").is_file())
        self.assertIn("source checkout is in sync", result.stdout)

    def test_update_rolls_back_source_when_post_merge_generator_fails(self) -> None:
        seed, checkout = self.make_update_remote()
        remote = self.sandbox / "remote.git"
        old_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(checkout),
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        self.push_update_fixture(seed, remote, generator_exit=9)

        result = self.run_cli("update", source=checkout)

        self.assertEqual(result.returncode, 9, result.stdout + result.stderr)
        actual_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(checkout),
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        self.assertEqual(actual_head, old_head)
        self.assertFalse((checkout / "VERSION-FIXTURE").exists())

    def test_update_refuses_incompatible_personal_config_before_fetch(self) -> None:
        seed, checkout = self.make_update_remote()
        installer = checkout / "scripts" / "install_codex.py"
        installer.write_text(
            "def validate_config(path):\n    return ['fixture incompatible config']\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "."], cwd=str(checkout), check=True)
        subprocess.run(["git", "commit", "-m", "local fixture installer"], cwd=str(checkout), check=True)
        personal = self.home / ".codex"
        personal.mkdir()
        (personal / "config.toml").write_text("fixture = true\n", encoding="utf-8")

        result = self.run_cli("update", source=checkout)

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("not compatible", result.stdout)
        self.assertNotIn("unable to refresh origin/main", result.stdout)

    def test_update_refuses_partial_personal_install_without_creating_missing_roles(self) -> None:
        seed, checkout = self.make_update_remote()
        remote = self.sandbox / "remote.git"
        self.push_update_fixture(seed, remote)
        personal = self.home / ".codex"
        agents = personal / "agents"
        agents.mkdir(parents=True)
        (personal / "config.toml").write_text("fixture = true\n", encoding="utf-8")
        source_scout = checkout / "adapters" / "codex" / "agents" / "scout.toml"
        (agents / "scout.toml").write_bytes(source_scout.read_bytes())
        reviewer = agents / "reviewer.toml"
        self.assertFalse(reviewer.exists())

        result = self.run_cli("update", source=checkout)

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("installation is incomplete", result.stdout)
        self.assertIn("will not create missing managed roles", result.stdout)
        self.assertFalse(reviewer.exists())

    def test_init_from_subdirectory_targets_repository_root(self) -> None:
        project = self.sandbox / "project-root"
        self.init_git(project)
        nested = project / "src" / "module"
        nested.mkdir(parents=True)

        result = self.run_cli("init", str(nested))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((project / ".codex" / "agents" / "scout.toml").is_file())
        self.assertTrue((project / "AGENTS.md").is_file())
        self.assertFalse((nested / ".codex").exists())
        self.assertFalse((nested / "AGENTS.md").exists())
        self.assertIn("Repository root resolved", result.stdout)

    def test_invalid_explicit_eas_repo_refuses_without_fallback(self) -> None:
        missing = self.sandbox / "definitely-missing-eas-repository"

        result = self.run_cli("update", source=missing)

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("EAS_REPO is not a Git checkout", result.stdout)
        self.assertNotIn("UP TO DATE", result.stdout)
        self.assertNotIn("UPDATED", result.stdout)

    def test_uninstall_managed_block_preserves_indented_suffix(self) -> None:
        from eas_cli.operations import MANAGED_END, MANAGED_START, _strip_managed_block

        existing = "before\n\n{}\nmanaged\n{}\n\n    indented code\n".format(
            MANAGED_START, MANAGED_END
        )
        stripped, changed = _strip_managed_block(existing)

        self.assertTrue(changed)
        self.assertEqual(stripped, "before\n\n    indented code\n")

    def test_update_reports_rollback_failure(self) -> None:
        import subprocess as subprocess_module
        from eas_cli import operations

        failed = subprocess_module.CompletedProcess(
            ["git"], 1, stdout="", stderr="locked by another process"
        )
        output = io.StringIO()
        with mock.patch.object(operations, "run_command", return_value=failed):
            with contextlib.redirect_stdout(output):
                ok = operations._rollback_update(Path("."), "deadbeef")

        self.assertFalse(ok)
        self.assertIn("ROLLBACK FAILED", output.getvalue())
        self.assertIn("locked by another process", output.getvalue())

    def test_invalid_explicit_eas_repo_is_authoritative_for_doctor(self) -> None:
        missing = self.sandbox / "missing-explicit-source"

        result = self.run_cli("doctor", "--json", source=missing)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["checks"]["source"]["status"], "MISSING")
        self.assertEqual(payload["core"]["status"], "DEGRADED")

    def test_init_uninstall_roundtrip_preserves_agents_bytes(self) -> None:
        project = self.sandbox / "lossless-project"
        self.init_git(project)
        original = b"# User rules  \r\n\r\n    indented code  \nlast-line\r\nno-final-newline"
        agents_md = project / "AGENTS.md"
        agents_md.write_bytes(original)

        installed = self.run_cli("init", str(project))
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        managed = agents_md.read_bytes()
        self.assertTrue(managed.endswith(original))
        self.assertIn(b"<!-- engineering-agent-stack:start -->", managed)

        removed = self.run_cli(
            "uninstall", "--project", str(project), "--project-instructions"
        )
        self.assertEqual(removed.returncode, 0, removed.stdout + removed.stderr)
        self.assertEqual(agents_md.read_bytes(), original)

    def test_release_tag_validator_accepts_only_package_version(self) -> None:
        good = subprocess.run(
            [PYTHON, str(ROOT / "scripts" / "validate_release_tag.py"), "--tag", "v0.3.0"],
            cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", check=False,
        )
        bad = subprocess.run(
            [PYTHON, str(ROOT / "scripts" / "validate_release_tag.py"), "--tag", "v9.9.9"],
            cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", check=False,
        )

        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)
        self.assertIn("does not match package version", bad.stdout)

    def test_validation_workflow_uses_isolated_package_build(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")

        self.assertIn("python -m pip install . --no-deps", workflow)
        self.assertNotIn("--no-build-isolation", workflow)

    def test_release_workflow_requires_linux_windows_and_scoped_publish_permission(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

        self.assertIn("validate-linux:", workflow)
        self.assertIn("validate-windows:", workflow)
        self.assertGreaterEqual(workflow.count('python-version: "3.9"'), 3)
        self.assertIn("needs: [validate-linux, validate-windows]", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("publish:\n    needs: [validate-linux, validate-windows]", workflow)
        self.assertIn("      contents: write", workflow)
        self.assertIn("validate_release_tag.py", workflow)
        self.assertEqual(workflow.count("Build and smoke-test Python 3.9 package"), 2)
        self.assertGreaterEqual(workflow.count("python -m build"), 3)
        self.assertGreaterEqual(workflow.count("generate_codex_adapter.py --check"), 3)
        self.assertGreaterEqual(workflow.count("import yaml, tomli, eas_cli"), 2)

    def test_bootstrap_and_package_contracts(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        powershell = (ROOT / "install.ps1").read_text(encoding="utf-8")
        shell = (ROOT / "install.sh").read_text(encoding="utf-8")
        official = "https://github.com/Tunglam0605/engineering-agent-stack.git"

        self.assertIn('requires-python = ">=3.9"', pyproject)
        self.assertIn("PyYAML>=6.0.2,<7", pyproject)
        self.assertIn("tomli>=2.0.1,<3; python_version < '3.11'", pyproject)
        self.assertIn('eas = "eas_cli.cli:main"', pyproject)
        for script in (powershell, shell):
            self.assertIn(official, script)
            self.assertIn("install_codex.py", script)
            self.assertIn("--dry-run", script)
            self.assertIn("--check", script)
            self.assertIn(".local", script)
            self.assertIn(".venv", script)
            self.assertIn("PyYAML>=6.0.2,<7", script)
            self.assertIn("tomli>=2.0.1,<3", script)
            self.assertIn("pip install", script)
        self.assertIn("$BootstrapPython = @(Find-Python)", powershell)
        self.assertIn('[ValidateSet("main")]', powershell)
        self.assertIn('if [ "$REF" != "main" ]', shell)
        self.assertIn("printf '%s\\n' \"$cmd\"", shell)
        self.assertNotIn("printf '%s\\\\n' \"$cmd\"", shell)
        self.assertIn('exec "$VENV_PYTHON" "$CHECKOUT/scripts/eas.py" "\\$@"', shell)
        self.assertNotIn('exec "$VENV_PYTHON" "$CHECKOUT/scripts/eas.py" "\\\\$@"', shell)
        self.assertNotIn("$env:PATH =", powershell)
        self.assertNotIn("export PATH=", shell)


if __name__ == "__main__":
    unittest.main()
