from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import acceptance_core
import generate_codex_adapter as generator
import install_codex
import provider_probe_codex as provider_probe


class GeneratedCodexConfigTests(unittest.TestCase):
    def test_generated_install_uses_public_agents_surface_only(self) -> None:
        rendered = generator.render_config_example(
            generator.load_agents(),
            generator.load_yaml(generator.MODEL_PROFILES_PATH),
        )

        config = generator.tomllib.loads(rendered)

        self.assertTrue(config["agents"]["enabled"])
        self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 2)
        self.assertNotIn("multi_agent_v2", config.get("features", {}))


class WorkspaceDeltaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temp_dir.name)
        acceptance_core.init_sandbox(self.sandbox)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_staged_extra_file_violates_exact_one_file_scope(self) -> None:
        (self.sandbox / "IMPLEMENT.md").write_text("status: new\n", encoding="utf-8")
        (self.sandbox / "STAGED_EXTRA.md").write_text("extra\n", encoding="utf-8")
        acceptance_core.git(["add", "STAGED_EXTRA.md"], self.sandbox)

        changed = acceptance_core.workspace_delta(self.sandbox)

        self.assertEqual(changed, ["IMPLEMENT.md", "STAGED_EXTRA.md"])
        self.assertNotEqual(changed, ["IMPLEMENT.md"])

    def test_untracked_extra_file_violates_exact_one_file_scope(self) -> None:
        (self.sandbox / "IMPLEMENT.md").write_text("status: new\n", encoding="utf-8")
        (self.sandbox / "UNTRACKED_EXTRA.md").write_text("extra\n", encoding="utf-8")

        changed = acceptance_core.workspace_delta(self.sandbox)

        self.assertEqual(changed, ["IMPLEMENT.md", "UNTRACKED_EXTRA.md"])
        self.assertNotEqual(changed, ["IMPLEMENT.md"])

    def test_ignored_untracked_extra_file_violates_exact_one_file_scope(self) -> None:
        (self.sandbox / ".gitignore").write_text("IGNORED_EXTRA.md\n", encoding="utf-8")
        acceptance_core.commit_all(self.sandbox, "add sandbox ignore rule")
        (self.sandbox / "IMPLEMENT.md").write_text("status: new\n", encoding="utf-8")
        (self.sandbox / "IGNORED_EXTRA.md").write_text("extra\n", encoding="utf-8")

        changed = acceptance_core.workspace_delta(self.sandbox)

        self.assertEqual(changed, ["IGNORED_EXTRA.md", "IMPLEMENT.md"])
        self.assertNotEqual(changed, ["IMPLEMENT.md"])

    def test_assume_unchanged_tracked_modification_is_refused(self) -> None:
        acceptance_core.git(
            ["update-index", "--assume-unchanged", "IMPLEMENT.md"], self.sandbox
        )
        (self.sandbox / "IMPLEMENT.md").write_text("status: hidden\n", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "assume-unchanged.*IMPLEMENT.md"):
            acceptance_core.workspace_delta(self.sandbox)

    def test_skip_worktree_tracked_modification_is_refused(self) -> None:
        acceptance_core.git(
            ["update-index", "--skip-worktree", "IMPLEMENT.md"], self.sandbox
        )
        (self.sandbox / "IMPLEMENT.md").write_text("status: hidden\n", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "skip-worktree.*IMPLEMENT.md"):
            acceptance_core.workspace_delta(self.sandbox)

    def test_git_z_path_parsing_preserves_posix_backslashes(self) -> None:
        results = [
            subprocess.CompletedProcess([], 0, "H IMPLEMENT.md\0", ""),
            subprocess.CompletedProcess([], 0, "dir\\name.txt\0", ""),
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "", ""),
        ]
        with mock.patch.object(acceptance_core, "git", side_effect=results):
            changed = acceptance_core.workspace_delta(self.sandbox)

        self.assertEqual(changed, ["dir\\name.txt"])

    @unittest.skipIf(os.name == "nt", "backslash is a separator on Windows")
    def test_workspace_delta_preserves_real_posix_backslash_filename(self) -> None:
        path = self.sandbox / "back\\slash.txt"
        path.write_text("extra\n", encoding="utf-8")

        self.assertEqual(acceptance_core.workspace_delta(self.sandbox), ["back\\slash.txt"])

    def test_cleanup_restores_tracked_index_and_untracked_state(self) -> None:
        (self.sandbox / "IMPLEMENT.md").write_text("status: new\n", encoding="utf-8")
        acceptance_core.git(["add", "IMPLEMENT.md"], self.sandbox)
        (self.sandbox / "UNTRACKED_EXTRA.md").write_text("extra\n", encoding="utf-8")

        acceptance_core.clean_sandbox_workspace(self.sandbox)

        self.assertEqual(acceptance_core.workspace_delta(self.sandbox), [])
        self.assertEqual(
            (self.sandbox / "IMPLEMENT.md").read_text(encoding="utf-8"),
            "status: old\n",
        )
        self.assertFalse((self.sandbox / "UNTRACKED_EXTRA.md").exists())

    def test_cleanup_removes_ignored_untracked_content(self) -> None:
        (self.sandbox / ".gitignore").write_text("ignored/\n", encoding="utf-8")
        acceptance_core.commit_all(self.sandbox, "add sandbox ignore rule")
        ignored = self.sandbox / "ignored" / "artifact.txt"
        ignored.parent.mkdir()
        ignored.write_text("extra\n", encoding="utf-8")

        acceptance_core.clean_sandbox_workspace(self.sandbox)

        self.assertFalse(ignored.parent.exists())

    def test_cleanup_clears_assume_unchanged_and_restores_tracked_content(self) -> None:
        acceptance_core.git(
            ["update-index", "--assume-unchanged", "IMPLEMENT.md"], self.sandbox
        )
        (self.sandbox / "IMPLEMENT.md").write_text("status: hidden\n", encoding="utf-8")

        acceptance_core.clean_sandbox_workspace(self.sandbox)

        self.assertEqual(
            (self.sandbox / "IMPLEMENT.md").read_text(encoding="utf-8"),
            "status: old\n",
        )
        flags = acceptance_core.git(["ls-files", "-v", "IMPLEMENT.md"], self.sandbox)
        self.assertTrue((flags.stdout or "").startswith("H "))

    def test_cleanup_clears_skip_worktree_and_restores_tracked_content(self) -> None:
        acceptance_core.git(
            ["update-index", "--skip-worktree", "IMPLEMENT.md"], self.sandbox
        )
        (self.sandbox / "IMPLEMENT.md").write_text("status: hidden\n", encoding="utf-8")

        acceptance_core.clean_sandbox_workspace(self.sandbox)

        self.assertEqual(
            (self.sandbox / "IMPLEMENT.md").read_text(encoding="utf-8"),
            "status: old\n",
        )
        flags = acceptance_core.git(["ls-files", "-v", "IMPLEMENT.md"], self.sandbox)
        self.assertTrue((flags.stdout or "").startswith("H "))

    def test_cleanup_refuses_the_real_repository_root(self) -> None:
        sentinel = self.sandbox / "UNTRACKED_SENTINEL.md"
        sentinel.write_text("preserve me\n", encoding="utf-8")

        with mock.patch.object(acceptance_core, "ROOT", self.sandbox):
            with self.assertRaisesRegex(RuntimeError, "real repository"):
                acceptance_core.clean_sandbox_workspace(self.sandbox)

        self.assertTrue(sentinel.is_file())

    def test_live_direct_cleans_the_sandbox_when_codex_raises(self) -> None:
        args = argparse.Namespace(
            codex_bin="codex",
            main_model="unused",
            reasoning_effort="unused",
            timeout=1,
        )

        def fail_after_writes(**_kwargs: object) -> None:
            (self.sandbox / "DIRECT.md").write_text("changed\n", encoding="utf-8")
            (self.sandbox / "UNTRACKED_EXTRA.md").write_text("extra\n", encoding="utf-8")
            acceptance_core.git(["add", "DIRECT.md"], self.sandbox)
            raise RuntimeError("simulated provider failure")

        with mock.patch.object(acceptance_core, "codex_exec", side_effect=fail_after_writes):
            with self.assertRaisesRegex(RuntimeError, "simulated provider failure"):
                acceptance_core.live_direct([], self.sandbox, args)

        self.assertEqual(acceptance_core.workspace_delta(self.sandbox), [])


class InstallerConfigValidationTests(unittest.TestCase):
    def validate(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.toml"
            config_path.write_text(text, encoding="utf-8")
            return install_codex.validate_config(config_path)

    def test_missing_concurrency_cap_is_rejected(self) -> None:
        problems = self.validate("[agents]\nenabled = true\n")

        self.assertTrue(problems)
        self.assertTrue(any("max_concurrent_threads_per_session" in problem for problem in problems))

    def test_generated_config_passes(self) -> None:
        rendered = generator.render_config_example(
            generator.load_agents(),
            generator.load_yaml(generator.MODEL_PROFILES_PATH),
        )

        self.assertEqual(self.validate(rendered), [])

    def test_disabled_legacy_multi_agent_v2_is_tolerated(self) -> None:
        config = """\
[agents]
enabled = true
max_concurrent_threads_per_session = 2

[features.multi_agent_v2]
enabled = false
wait_agent_enabled = true
"""

        self.assertEqual(self.validate(config), [])

    def test_enabled_legacy_multi_agent_v2_is_rejected(self) -> None:
        rendered = generator.render_config_example(
            generator.load_agents(),
            generator.load_yaml(generator.MODEL_PROFILES_PATH),
        ) + "\n[features.multi_agent_v2]\nenabled = true\n"

        problems = self.validate(rendered)

        self.assertTrue(any("multi_agent_v2.enabled=true" in problem for problem in problems))

    def test_wrong_concurrency_cap_is_rejected(self) -> None:
        rendered = generator.render_config_example(
            generator.load_agents(),
            generator.load_yaml(generator.MODEL_PROFILES_PATH),
        ).replace("max_concurrent_threads_per_session = 2", "max_concurrent_threads_per_session = 4")

        problems = self.validate(rendered)

        self.assertTrue(any("max_concurrent_threads_per_session" in problem for problem in problems))

    def test_malformed_toml_is_rejected(self) -> None:
        problems = self.validate("[agents\nenabled = true\n")

        self.assertTrue(problems)
        self.assertTrue(any("malformed TOML" in problem for problem in problems))

    def test_install_rejects_incompatible_preserved_config_before_writes(self) -> None:
        cases = {
            "stale": "[agents]\nenabled = true\n",
            "malformed": "[agents\nenabled = true\n",
        }
        for label, config_text in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                codex_root = project / ".codex"
                codex_root.mkdir()
                config_path = codex_root / "config.toml"
                config_path.write_text(config_text, encoding="utf-8")

                with redirect_stdout(io.StringIO()):
                    result = install_codex.install(
                        codex_root,
                        force=False,
                        dry_run=False,
                        project=project,
                    )

                self.assertEqual(result, 2)
                self.assertEqual(config_path.read_text(encoding="utf-8"), config_text)
                self.assertFalse((codex_root / "agents").exists())

    def test_provider_overrides_use_public_agents_surface_only(self) -> None:
        overrides = provider_probe.provider_overrides(Path("provider-sandbox"))

        self.assertIn("agents.enabled=true", overrides)
        self.assertIn("agents.max_concurrent_threads_per_session=2", overrides)
        self.assertFalse(any("multi_agent_v2" in override for override in overrides))


class ProviderTelemetryWordingTests(unittest.TestCase):
    def test_zero_spawn_items_are_reported_as_observed_jsonl_evidence(self) -> None:
        result = {
            "summary": {
                "event_summary": {
                    "agent_spawns": 0,
                    "collab_tool_calls": 2,
                }
            },
            "last_message": "Delegation failed: upstream 502 Bad Gateway",
        }

        detail = provider_probe.result_detail(result)

        self.assertIn("observed_spawn_events=0", detail)
        self.assertIn("collab_calls=2", detail)
        self.assertIn("public JSONL does not prove that no child was spawned", detail)
        self.assertIn(
            "final_provider_message=Delegation failed: upstream 502 Bad Gateway",
            detail,
        )
        self.assertNotIn(" spawns=", " " + detail)


if __name__ == "__main__":
    unittest.main()
