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

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PYTHON = sys.executable

from runtime.capabilities.builtins import BuiltinCatalog, builtin_root, load_builtin_catalog
from runtime.capabilities.detection import detect_project
from runtime.capabilities.models import PresetContract, SkillContract
from runtime.capabilities.parser import (
    load_toml_mapping,
    load_yaml_mapping,
    parse_preset,
    parse_project_profile,
    reject_casefold_collisions,
    safe_join,
    validate_requires_eas, version_satisfies_range,
)
from runtime.capabilities.project import (
    ProjectCapabilityService,
    initialize_project_profile,
    load_project_profile,
)
from runtime.capabilities.resolver import resolve_config, validate_cli_overrides
from runtime.capabilities.skills import SkillCatalog
from runtime.capabilities.snapshot import (
    bind_snapshot,
    build_snapshot,
    migrate_snapshot,
    read_snapshot,
    snapshot_path,
    write_snapshot,
)
from runtime.lifecycle import GoalAssignment, GoalState, GoalStore


class TempGitCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git_project(self, name: str = "project") -> Path:
        project = self.root / name
        project.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-b", "main"], cwd=str(project),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
        subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=str(project), check=True)
        subprocess.run(["git", "config", "user.name", "EAS Tests"], cwd=str(project), check=True)
        return project


class ContractParserTests(TempGitCase):
    def write_yaml(self, text: str) -> Path:
        path = self.root / "contract.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_builtin_catalog_has_exactly_three_presets_and_no_agent_contracts(self) -> None:
        catalog = load_builtin_catalog()
        self.assertEqual(set(catalog.presets), {"embedded", "ros2", "release"})
        self.assertEqual(len(list((ROOT / "agents" / "core").glob("*.yaml"))), 7)
        for manifest in catalog.extensions.values():
            self.assertEqual(set(manifest.provides), {"skills", "rules", "presets"})
            self.assertNotIn("agents", manifest.provides)
            self.assertNotIn("providers", manifest.provides)

    def test_yaml_duplicate_unknown_schema_alias_tag_date_nonfinite_fail_closed(self) -> None:
        cases = {
            "duplicate": "kind: preset\nkind: preset\n",
            "alias": "base: &x [a]\ncopy: *x\n",
            "tag": "value: !!str 3\n",
            "date": "value: 2026-09-08\n",
            "nan": "value: .nan\n",
        }
        for label, text in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    load_yaml_mapping(self.write_yaml(text))

        with self.assertRaisesRegex(ValueError, "unsupported schema_version"):
            parse_preset({
                "kind": "preset", "schema_version": 99, "id": "x", "version": "1.0.0",
                "description": "x", "skills": [], "required_rules": [], "defaults": {},
                "detection_hints": [],
            })

    def test_preset_dependencies_inheritance_and_cycles_are_rejected_as_unknown_fields(self) -> None:
        base = {
            "kind": "preset", "schema_version": 1, "id": "x", "version": "1.0.0",
            "description": "x", "skills": [], "required_rules": [], "defaults": {},
            "detection_hints": [],
        }
        for field, value in (("dependencies", ["y"]), ("extends", "y"), ("include", ["y"])):
            with self.subTest(field=field):
                payload = dict(base)
                payload[field] = value
                with self.assertRaisesRegex(ValueError, "unknown keys"):
                    parse_preset(payload)
        cyclic = dict(base)
        cyclic["extends"] = "x"
        with self.assertRaises(ValueError):
            parse_preset(cyclic)

    def test_requires_eas_range_is_small_and_semver_bounded(self) -> None:
        self.assertEqual(validate_requires_eas(">=0.6.0,<0.7.0"), ">=0.6.0,<0.7.0")
        self.assertTrue(version_satisfies_range("0.6.0", ">=0.6.0,<0.7.0"))
        self.assertFalse(version_satisfies_range("0.5.9", ">=0.6.0,<0.7.0"))
        self.assertFalse(version_satisfies_range("0.7.0", ">=0.6.0,<0.7.0"))
        for value in ("^0.6", "0.6.*", ">=0.6.0,<0.7.0,!=0.6.5", ">=v0.6.0", "latest"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_requires_eas(value)

    def test_toml_duplicate_malformed_secret_and_unknown_profile_fields_fail(self) -> None:
        path = self.root / "project.toml"
        path.write_text('kind="project-profile"\nkind="project-profile"\n', encoding="utf-8")
        with self.assertRaises(ValueError):
            load_toml_mapping(path)
        path.write_text('kind = "unterminated\n', encoding="utf-8")
        with self.assertRaises(ValueError):
            load_toml_mapping(path)
        with self.assertRaisesRegex(ValueError, "secret-like"):
            parse_project_profile({
                "kind": "project-profile", "schema_version": 1, "id": "robot", "preset": "embedded",
                "values": {"domain": {"api_key": "nope"}},
            })
        with self.assertRaisesRegex(ValueError, "unknown keys"):
            parse_project_profile({
                "kind": "project-profile", "schema_version": 1, "id": "robot", "preset": "embedded",
                "local_override": True,
            })

    def test_paths_reject_traversal_casefold_and_symlink_escape(self) -> None:
        with self.assertRaises(ValueError):
            safe_join(self.root, "../outside.yaml")
        with self.assertRaises(ValueError):
            reject_casefold_collisions(["skills/A.yaml", "skills/a.yaml"])
        target = self.root / "outside"
        target.mkdir()
        inside = self.root / "package"
        inside.mkdir()
        link = inside / "link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable on this Windows test host")
        with self.assertRaisesRegex(ValueError, "symlink/reparse"):
            safe_join(inside, "link/secret.yaml")


class ResolverTests(unittest.TestCase):
    def test_exact_precedence_and_lineage(self) -> None:
        resolved = resolve_config(
            core_defaults={"selection": {"max_skills": 1}, "rules": {"required_rules": ["core.rule"]}},
            extension_defaults=[("embedded", {"selection": {"max_skills": 2}, "rules": {"required_rules": ["ext.rule"]}})],
            preset_defaults={"selection": {"max_skills": 3}, "skills": {"enabled": ["preset.skill"]}},
            project_values={"selection": {"context_budget_tokens": 4096}, "skills": {"enabled": ["project.skill"]}},
            cli_overrides={"selection.max_skills": 2},
        )
        self.assertEqual(resolved.values["selection"]["max_skills"], 2)
        self.assertEqual(resolved.lineage["selection.max_skills"], ["cli"])
        self.assertEqual(resolved.values["skills"]["enabled"], ["project.skill"])
        self.assertEqual(resolved.lineage["skills.enabled"], ["project"])
        self.assertEqual(resolved.values["rules"]["required_rules"], ["core.rule", "ext.rule"])

    def test_equal_extension_conflict_list_replacement_and_required_rule_union(self) -> None:
        with self.assertRaisesRegex(ValueError, "equal-precedence extension conflict"):
            resolve_config(extension_defaults=[
                ("a", {"selection": {"max_skills": 1}}),
                ("b", {"selection": {"max_skills": 2}}),
            ])
        resolved = resolve_config(
            extension_defaults=[("a", {"skills": {"enabled": ["one"]}, "rules": {"required_rules": ["a.rule"]}})],
            preset_defaults={"skills": {"enabled": ["two"]}, "rules": {"required_rules": ["b.rule"]}},
        )
        self.assertEqual(resolved.values["skills"]["enabled"], ["two"])
        self.assertEqual(resolved.values["rules"]["required_rules"], ["a.rule", "b.rule"])

    def test_null_unknown_deep_and_protected_cli_overrides_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "null tombstones"):
            resolve_config(project_values={"domain": {"mcu_family": None}})
        with self.assertRaisesRegex(ValueError, "unknown"):
            resolve_config(project_values={"domain": {"nested": {"x": 1}}})
        for path in ("lifecycle.soft_limit", "provider.name", "models.default", "write_lease.owner", "approval.ttl"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, "protected"):
                    validate_cli_overrides({path: 1})
        with self.assertRaisesRegex(ValueError, "not allowlisted"):
            validate_cli_overrides({"domain.target": "release"})


class PreflightBindingTests(unittest.TestCase):
    def test_preflight_can_require_same_capability_digest_without_changing_legacy_default(self) -> None:
        from runtime.contracts import ContextBudget, DelegationRequest
        from runtime.preflight import DelegationPreflight
        request = DelegationRequest(
            task="read repository", route_mode="delegate", role="scout", profile="cheap",
            provider="openai", child_agent_capable=True, write_owner=None, write_scope=[],
            parent_role="orchestrator", recursion_depth=0,
            context_budget=ContextBudget(max_input_tokens=1000, estimated_input_tokens=100),
            review_required=False, review_planned=False,
            capability_snapshot_digest="a" * 64,
        )
        preflight = DelegationPreflight.from_repository(ROOT)
        self.assertEqual(preflight.evaluate(request).decision, "PASS")
        mismatch = preflight.evaluate(request, required_capability_snapshot_digest="b" * 64)
        self.assertEqual(mismatch.decision, "REJECT")
        self.assertIn("capability_snapshot_mismatch", [reason.code for reason in mismatch.reasons])
        bound = preflight.evaluate(request, required_capability_snapshot_digest="a" * 64)
        self.assertEqual(bound.decision, "PASS")
        self.assertEqual(bound.to_execution_plan("a-1").capability_snapshot_digest, "a" * 64)


class DetectionTests(TempGitCase):
    def test_embedded_ros2_release_none_and_release_not_ready(self) -> None:
        embedded = self.git_project("embedded")
        (embedded / "robot.ioc").write_text("ProjectManager.ProjectName=robot", encoding="utf-8")
        (embedded / "FreeRTOSConfig.h").write_text("#define configUSE_PREEMPTION 1", encoding="utf-8")
        e = detect_project(embedded)
        self.assertEqual(e.status, "RECOMMENDED")
        self.assertEqual(e.recommended_preset, "embedded")
        self.assertFalse(e.release_ready)

        ros = self.git_project("ros")
        (ros / "package.xml").write_text("<package/>", encoding="utf-8")
        (ros / "CMakeLists.txt").write_text("find_package(rclcpp REQUIRED)\nament_package()", encoding="utf-8")
        r = detect_project(ros)
        self.assertEqual(r.recommended_preset, "ros2")
        self.assertFalse(r.release_ready)

        release = self.git_project("rel")
        (release / ".github" / "workflows").mkdir(parents=True)
        (release / ".github" / "workflows" / "release.yml").write_text("name: release", encoding="utf-8")
        (release / "CHANGELOG.md").write_text("# Changelog", encoding="utf-8")
        (release / "pyproject.toml").write_text('[project]\nname="x"\nversion="1.0.0"\n', encoding="utf-8")
        d = detect_project(release)
        self.assertEqual(d.recommended_preset, "release")
        self.assertFalse(d.as_dict()["release_ready"])

        empty = self.git_project("empty")
        n = detect_project(empty)
        self.assertEqual(n.status, "NONE")
        self.assertIsNone(n.recommended_preset)

    def test_competing_strong_evidence_is_ambiguous_and_never_activates(self) -> None:
        project = self.git_project("hybrid")
        (project / "robot.ioc").write_text("x", encoding="utf-8")
        (project / "package.xml").write_text("<package/>", encoding="utf-8")
        # Both strong indicators score 6, forcing bounded ambiguity.
        result = detect_project(project)
        self.assertEqual(result.status, "AMBIGUOUS")
        self.assertEqual(result.confidence, "UNKNOWN")
        self.assertIsNone(result.recommended_preset)
        self.assertTrue(result.contradictions)


class SkillSelectionTests(TempGitCase):
    def test_metadata_is_lazy_and_body_load_occurs_only_after_selection(self) -> None:
        copied = self.root / "resources"
        shutil.copytree(builtin_root(), copied)
        catalog = load_builtin_catalog(copied)
        skills = SkillCatalog(catalog)
        body = copied / "embedded" / "bodies" / "realtime-control.md"
        body.unlink()
        metadata = skills.metadata(["embedded.realtime-control"])
        self.assertEqual(metadata[0]["id"], "embedded.realtime-control")
        selected = skills.select(
            preset_id="embedded", role="implementer", task_tags=["stm32"], task_text="STM32 realtime loop"
        )
        self.assertTrue(selected)
        with self.assertRaisesRegex(ValueError, "body missing"):
            skills.load_selected(selected)

    def test_selection_is_bounded_deterministic_and_context_budgeted(self) -> None:
        catalog = load_builtin_catalog()
        root = catalog.preset_roots["embedded"]
        fake_ids = []
        for index in range(4):
            ident = "embedded.fake{}".format(index)
            fake_ids.append(ident)
            catalog.skills[ident] = SkillContract(
                kind="skill", schema_version=1, id=ident, version="0.6.0", summary="fake",
                roles=["implementer"], task_tags=["embedded"], triggers=["fake"],
                body="bodies/integration.md", references=[], context_cost=100,
            )
            catalog.skill_roots[ident] = root
        catalog.presets["embedded"] = PresetContract(
            kind="preset", schema_version=1, id="embedded", version="0.6.0", description="x",
            skills=fake_ids, required_rules=[], defaults={}, detection_hints=[],
        )
        skills = SkillCatalog(catalog)
        selected = skills.select(
            preset_id="embedded", role="implementer", task_tags=["embedded"], task_text="fake",
            max_selected=3, context_budget=250,
        )
        self.assertEqual([item.id for item in selected], fake_ids[:2])
        with self.assertRaises(ValueError):
            skills.select(preset_id="embedded", role="implementer", max_selected=4)


class SnapshotAndProjectTests(TempGitCase):
    def snapshot(self, project_id: str = "robot", preset: str = "embedded", value: int = 3):
        return build_snapshot(
            eas_version="0.6.0", project_id=project_id, active_preset=preset,
            sources=[{"kind": "test", "id": "source", "digest": "a" * 64}],
            resolved_values={"selection": {"max_skills": value}},
            lineage={"selection.max_skills": ["test"]}, selected_skills=[], selected_rules=[],
            detection={"status": "NONE", "evidence_revision": "b" * 64},
        )

    def test_snapshot_hash_is_deterministic_corruption_and_drift_fail_closed(self) -> None:
        project = self.git_project()
        first = self.snapshot()
        second = self.snapshot()
        self.assertEqual(first.digest, second.digest)
        bind_snapshot(project, first)
        self.assertEqual(read_snapshot(project).digest, first.digest)
        with self.assertRaisesRegex(RuntimeError, "drift"):
            bind_snapshot(project, self.snapshot(value=2))
        path = snapshot_path(project)
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["digest"] = "0" * 64
        path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            read_snapshot(project)

    def test_snapshot_explicit_migration_requires_expected_old_digest_when_requested(self) -> None:
        project = self.git_project()
        old = self.snapshot(value=1)
        new = self.snapshot(value=2)
        write_snapshot(project, old)
        with self.assertRaisesRegex(RuntimeError, "changed before migration"):
            migrate_snapshot(project, new, expected_old_digest="f" * 64)
        migrate_snapshot(project, new, expected_old_digest=old.digest)
        self.assertEqual(read_snapshot(project).digest, new.digest)

    def test_project_profile_init_is_non_overwriting_and_no_secret_policy_is_enforced(self) -> None:
        project = self.git_project()
        path = initialize_project_profile(project, "embedded")
        self.assertTrue(path.is_file())
        self.assertEqual(load_project_profile(project).preset, "embedded")
        before = path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "never overwrites"):
            initialize_project_profile(project, "ros2")
        self.assertEqual(path.read_bytes(), before)
        path.write_text(
            'kind="project-profile"\nschema_version=1\nid="robot"\npreset="embedded"\n[values.domain]\napi_key="secret"\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "secret-like"):
            load_project_profile(project)

    def test_tracked_profile_remains_authoritative_when_detection_conflicts(self) -> None:
        project = self.git_project()
        initialize_project_profile(project, "embedded")
        (project / "package.xml").write_text("<package/>", encoding="utf-8")
        (project / "CMakeLists.txt").write_text("find_package(rclcpp REQUIRED)\nament_package()", encoding="utf-8")
        status = ProjectCapabilityService(eas_version="0.6.0").project_status(project)
        self.assertEqual(status["profile"]["preset"], "embedded")
        self.assertEqual(status["detection"]["recommended_preset"], "ros2")
        self.assertEqual(status["detection_conflict"]["tracked_preset"], "embedded")

    def test_goal_binding_is_explicit_and_legacy_state_stays_version_2(self) -> None:
        project = self.git_project()
        legacy = GoalStore(project, "legacy")
        legacy_state = legacy.initialize()
        self.assertIsNone(legacy_state.capability_snapshot_digest)
        self.assertEqual(json.loads(legacy.state_path.read_text())["version"], 2)

        digest = "a" * 64
        with self.assertRaises(RuntimeError):
            legacy.initialize(capability_snapshot_digest=digest)
        migrated = legacy.bind_capability_snapshot(digest, legacy.load().revision)
        self.assertEqual(migrated.capability_snapshot_digest, digest)
        self.assertEqual(json.loads(legacy.state_path.read_text())["version"], 3)
        legacy.require_capability_snapshot(digest)
        with self.assertRaises(RuntimeError):
            legacy.require_capability_snapshot("b" * 64)

    def test_goal_capability_migration_refuses_while_assignment_active(self) -> None:
        project = self.git_project()
        store = GoalStore(project, "active")
        state = store.initialize()
        state.assignments.append(GoalAssignment(
            assignment_id="a-0001", role="scout", task_domain="x", state="pending", write_scope=[]
        ))
        state.next_sequence = 2
        store.save(state)
        with self.assertRaisesRegex(RuntimeError, "assignments are active"):
            store.bind_capability_snapshot("a" * 64, store.load().revision)


class CliCapabilitiesTests(TempGitCase):
    def run_cli(self, *args: str, cwd: Path = None):
        env = os.environ.copy()
        env["EAS_REPO"] = str(ROOT)
        env["EAS_HOME"] = str(self.root / "home")
        return subprocess.run(
            [PYTHON, "-m", "eas_cli", *args], cwd=str(cwd or ROOT), env=env,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", check=False,
        )

    def test_preset_cli_list_show_detect_check_and_project_status(self) -> None:
        project = self.git_project()
        listed = self.run_cli("preset", "list", "--json")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual({item["id"] for item in json.loads(listed.stdout)["presets"]}, {"embedded", "ros2", "release"})
        shown = self.run_cli("preset", "show", "embedded", "--json")
        self.assertEqual(json.loads(shown.stdout)["preset"]["id"], "embedded")
        detected = self.run_cli("preset", "detect", "--project", str(project), "--json")
        self.assertEqual(json.loads(detected.stdout)["detection"]["status"], "NONE")
        checked = self.run_cli("preset", "check", "embedded", "--project", str(project), "--json")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        status = self.run_cli("project", "status", "--project", str(project), "--json")
        self.assertEqual(json.loads(status.stdout)["snapshot"]["status"], "UNBOUND")

    def test_init_preset_creates_profile_and_snapshot_and_never_overwrites(self) -> None:
        project = self.git_project()
        first = self.run_cli("init", str(project), "--preset", "embedded")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        profile = project / ".eas" / "project.toml"
        self.assertTrue(profile.is_file())
        self.assertTrue(snapshot_path(project).is_file())
        before = profile.read_bytes()
        second = self.run_cli("init", str(project), "--preset", "ros2")
        self.assertEqual(second.returncode, 2, second.stdout + second.stderr)
        self.assertEqual(profile.read_bytes(), before)

    def test_protected_cli_override_is_rejected(self) -> None:
        project = self.git_project()
        result = self.run_cli(
            "preset", "check", "embedded", "--project", str(project),
            "--override", 'provider.name="other"', "--json",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("protected", result.stdout)


if __name__ == "__main__":
    unittest.main()
