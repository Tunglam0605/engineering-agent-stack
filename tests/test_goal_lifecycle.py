from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.lifecycle import GoalAssignment, GoalState, GoalStore, LifecycleGate


class LifecycleGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = LifecycleGate(ROOT)

    @staticmethod
    def assignment(index: int, role: str, domain: str, state: str = "completed", scope=None, change_set=None):
        return GoalAssignment(
            assignment_id="a-{:04d}".format(index),
            role=role,
            task_domain=domain,
            state=state,
            write_scope=list(scope or []),
            change_set=change_set,
        )

    def test_resume_before_spawn_reuses_same_role_domain_scope(self) -> None:
        state = GoalState("goal-reuse", assignments=[self.assignment(1, "scout", "gateway")], next_sequence=2)
        decision = self.gate.evaluate(state, role="scout", task_domain="Gateway", write_scope=[])
        self.assertEqual(decision.action, "REUSE")
        self.assertEqual(decision.reuse_assignment_id, "a-0001")
        self.assertIsNone(decision.proposed_assignment_id)

    def test_soft_and_hard_goal_budgets_are_executable_and_justified(self) -> None:
        soft = GoalState(
            "goal-soft",
            assignments=[self.assignment(i, "scout", "domain-{}".format(i)) for i in range(1, 9)],
            next_sequence=9,
        )
        blocked = self.gate.evaluate(soft, role="researcher", task_domain="external-api", write_scope=[])
        self.assertEqual(blocked.action, "ESCALATE")
        allowed = self.gate.evaluate(
            soft,
            role="researcher",
            task_domain="external-api",
            write_scope=[],
            reconciled=True,
            override_reason="remaining evidence is independent and not covered by existing children",
        )
        self.assertEqual(allowed.action, "SPAWN")
        self.assertEqual(
            allowed.justification["override_reason"],
            "remaining evidence is independent and not covered by existing children",
        )

        hard = GoalState(
            "goal-hard",
            assignments=[self.assignment(i, "scout", "domain-{}".format(i)) for i in range(1, 13)],
            next_sequence=13,
        )
        rejected = self.gate.evaluate(hard, role="researcher", task_domain="new-source", write_scope=[])
        self.assertEqual(rejected.action, "REJECT")
        exception = self.gate.evaluate(
            hard,
            role="reviewer",
            task_domain="release",
            write_scope=[],
            change_set="release-1",
            exception_kind="required-release-review",
            override_reason="release policy requires one independent review",
        )
        self.assertEqual(exception.action, "SPAWN")
        self.assertEqual(exception.justification["exception_kind"], "required-release-review")
        self.assertEqual(
            exception.justification["override_reason"],
            "release policy requires one independent review",
        )

    def test_fresh_context_requires_reason_and_cannot_duplicate_active_assignment(self) -> None:
        completed = GoalState(
            "goal-fresh", assignments=[self.assignment(1, "scout", "gateway")], next_sequence=2
        )
        with self.assertRaisesRegex(ValueError, "fresh_context requires override_reason"):
            self.gate.evaluate(
                completed, role="scout", task_domain="gateway", write_scope=[], fresh_context=True
            )
        decision = self.gate.evaluate(
            completed,
            role="scout",
            task_domain="gateway",
            write_scope=[],
            fresh_context=True,
            override_reason="previous evidence is stale after a material repository change",
        )
        self.assertEqual(decision.action, "SPAWN")
        self.assertEqual(decision.proposed_assignment_id, "a-0002")

        active = GoalState(
            "goal-active",
            assignments=[self.assignment(1, "scout", "gateway", state="running")],
            next_sequence=2,
        )
        blocked = self.gate.evaluate(
            active,
            role="scout",
            task_domain="gateway",
            write_scope=[],
            fresh_context=True,
            override_reason="stale",
        )
        self.assertEqual(blocked.action, "ESCALATE")
        self.assertIn("same role/domain/scope", blocked.reasons[0])

    def test_parallel_reader_and_writer_capacity_are_enforced(self) -> None:
        readers = GoalState(
            "goal-readers",
            assignments=[self.assignment(i, "scout", "d{}".format(i), state="running") for i in range(1, 4)],
            next_sequence=4,
        )
        decision = self.gate.evaluate(readers, role="researcher", task_domain="docs", write_scope=[])
        self.assertEqual(decision.action, "ESCALATE")
        self.assertIn("reader capacity", decision.reasons[0])

        writers = GoalState(
            "goal-writers",
            assignments=[self.assignment(1, "implementer", "api", state="running", scope=["src/api"])],
            next_sequence=2,
        )
        decision = self.gate.evaluate(
            writers, role="debugger", task_domain="worker", write_scope=["src/worker"]
        )
        self.assertEqual(decision.action, "ESCALATE")
        self.assertIn("writer capacity", decision.reasons[0])

    def test_terminal_reuse_and_reactivation_cannot_bypass_capacity(self) -> None:
        state = GoalState(
            "goal-resume-cap",
            assignments=[
                self.assignment(1, "scout", "target", state="completed"),
                self.assignment(2, "scout", "a", state="running"),
                self.assignment(3, "scout", "b", state="running"),
                self.assignment(4, "researcher", "c", state="running"),
            ],
            next_sequence=5,
        )
        decision = self.gate.evaluate(state, role="scout", task_domain="target", write_scope=[])
        self.assertEqual(decision.action, "ESCALATE")

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            store = GoalStore(project, "goal-transition-cap")
            persisted = GoalState(
                "goal-transition-cap", assignments=list(state.assignments), next_sequence=5
            )
            store.save(persisted)
            with self.assertRaisesRegex(ValueError, "reader capacity reached"):
                self.gate.transition_atomic(store, "a-0001", "running")
            self.assertEqual(store.load().assignments[0].state, "completed")

    def test_architect_and_reviewer_reuse_budgets(self) -> None:
        architect_state = GoalState(
            "goal-architect",
            assignments=[self.assignment(1, "architect", "boot-contract")],
            next_sequence=2,
        )
        second = self.gate.evaluate(
            architect_state, role="architect", task_domain="transport-contract", write_scope=[]
        )
        self.assertEqual(second.action, "ESCALATE")
        changed = self.gate.evaluate(
            architect_state,
            role="architect",
            task_domain="transport-contract",
            write_scope=[],
            material_change=True,
            override_reason="public interface assumptions materially changed",
        )
        self.assertEqual(changed.action, "SPAWN")

        reviewer_state = GoalState(
            "goal-review",
            assignments=[self.assignment(1, "reviewer", "initial", change_set="patch-a")],
            next_sequence=2,
        )
        reuse = self.gate.evaluate(
            reviewer_state,
            role="reviewer",
            task_domain="fix-verification",
            write_scope=[],
            change_set="patch-a",
        )
        self.assertEqual(reuse.action, "REUSE")
        self.assertEqual(reuse.reuse_assignment_id, "a-0001")

    def test_atomic_state_events_and_justification_persist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            store = GoalStore(project, "goal-store")
            initialized = store.initialize()
            self.assertEqual(initialized.revision, 1)
            decision, assignment = self.gate.evaluate_and_commit(
                store,
                role="implementer",
                task_domain="cli",
                write_scope=["eas_cli/"],
                override_reason="bounded CLI implementation",
            )
            self.assertEqual(decision.action, "SPAWN")
            self.assertIsNotNone(assignment)
            assert assignment is not None
            self.assertEqual(assignment.assignment_id, "a-0001")
            self.gate.transition_atomic(store, "a-0001", "running")
            loaded = store.load()
            self.assertEqual(loaded.assignments[0].state, "running")
            self.assertGreaterEqual(loaded.revision, 3)
            self.assertFalse(store.state_path.with_suffix(".json.tmp").exists())
            self.assertFalse(store.lock_path.exists())
            events = [json.loads(line) for line in store.event_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(
                [item["event"] for item in events],
                ["goal_initialized", "assignment_spawned", "assignment_transition"],
            )
            self.assertEqual(
                events[1]["payload"]["decision"]["justification"]["override_reason"],
                "bounded CLI implementation",
            )

    def test_concurrent_reader_commits_preserve_unique_assignments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            GoalStore(project, "race-readers").initialize()

            def commit(domain: str):
                gate = LifecycleGate(ROOT)
                store = GoalStore(project, "race-readers")
                decision, assignment = gate.evaluate_and_commit(
                    store, role="scout", task_domain=domain, write_scope=[]
                )
                return decision.action, None if assignment is None else assignment.assignment_id

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(commit, ["one", "two"]))
            self.assertEqual(sorted(action for action, _ in results), ["SPAWN", "SPAWN"])
            ids = sorted(assignment_id for _, assignment_id in results if assignment_id)
            self.assertEqual(ids, ["a-0001", "a-0002"])
            loaded = GoalStore(project, "race-readers").load()
            self.assertEqual(len(loaded.assignments), 2)
            self.assertEqual(sorted(item.assignment_id for item in loaded.assignments), ids)

    def test_concurrent_writer_commits_cannot_bypass_single_writer_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            GoalStore(project, "race-writers").initialize()

            def commit(domain_scope):
                domain, scope = domain_scope
                gate = LifecycleGate(ROOT)
                store = GoalStore(project, "race-writers")
                decision, assignment = gate.evaluate_and_commit(
                    store, role="implementer", task_domain=domain, write_scope=[scope]
                )
                return decision.action, None if assignment is None else assignment.assignment_id

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(commit, [("one", "src/one"), ("two", "src/two")]))
            self.assertEqual(sorted(action for action, _ in results), ["ESCALATE", "SPAWN"])
            loaded = GoalStore(project, "race-writers").load()
            self.assertEqual(len(loaded.assignments), 1)
            self.assertEqual(loaded.assignments[0].state, "pending")

    def test_stale_state_cas_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            store = GoalStore(project, "cas")
            store.initialize()
            first = store.load()
            stale = store.load()
            first.next_sequence = 2
            store.save(first)
            stale.next_sequence = 3
            with self.assertRaisesRegex(RuntimeError, "changed concurrently"):
                store.save(stale)

    def test_goal_ids_write_scopes_and_corrupt_state_are_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            for bad in ("../escape", "Release", "con", "COM1"):
                with self.subTest(goal_id=bad):
                    with self.assertRaisesRegex(ValueError, "goal_id"):
                        GoalStore(project, bad)
            store = GoalStore(project, "corrupt")
            store.directory.mkdir(parents=True)
            store.state_path.write_text(
                json.dumps({
                    "version": 1, "goal_id": "corrupt", "next_sequence": 1,
                    "revision": 0, "created_at": "x", "updated_at": "x", "assignments": None,
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "assignments must be a list"):
                store.load()
        with self.assertRaisesRegex(ValueError, "repository-relative"):
            self.gate.evaluate(
                GoalState("safe-goal"), role="implementer", task_domain="x", write_scope=["C:/outside"]
            )


class GoalCliTests(unittest.TestCase):
    def run_cli(self, args, project: Path):
        env = dict(os.environ)
        env["EAS_REPO"] = str(ROOT)
        env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        return subprocess.run(
            [sys.executable, "-m", "eas_cli"] + list(args),
            cwd=str(project),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=False,
        )

    def test_goal_cli_init_gate_reuse_transition_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            init = self.run_cli(["goal", "init", "demo", "--json"], project)
            self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
            self.assertEqual(json.loads(init.stdout)["goal_id"], "demo")

            spawn = self.run_cli([
                "goal", "gate", "demo", "--role", "scout", "--domain", "gateway", "--commit", "--json"
            ], project)
            self.assertEqual(spawn.returncode, 0, spawn.stderr + spawn.stdout)
            body = json.loads(spawn.stdout)
            self.assertEqual(body["action"], "SPAWN")
            self.assertEqual(body["assignment_id"], "a-0001")

            transition = self.run_cli([
                "goal", "transition", "demo", "a-0001", "completed", "--json"
            ], project)
            self.assertEqual(transition.returncode, 0, transition.stderr + transition.stdout)

            reuse = self.run_cli([
                "goal", "gate", "demo", "--role", "scout", "--domain", "gateway", "--json"
            ], project)
            self.assertEqual(reuse.returncode, 0, reuse.stderr + reuse.stdout)
            self.assertEqual(json.loads(reuse.stdout)["action"], "REUSE")

            status = self.run_cli(["goal", "status", "demo", "--json"], project)
            self.assertEqual(status.returncode, 0, status.stderr + status.stdout)
            summary = json.loads(status.stdout)
            self.assertEqual(summary["total"], 1)
            self.assertEqual(summary["budget_state"], "within_budget")
            self.assertGreaterEqual(summary["revision"], 3)

            git_status = subprocess.run(
                ["git", "status", "--porcelain"], cwd=str(project), text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(git_status.returncode, 0, git_status.stderr)
            self.assertEqual(git_status.stdout, "")

    def test_goal_gate_returns_distinct_escalate_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            self.run_cli(["goal", "init", "capacity"], project)
            for index in range(3):
                spawn = self.run_cli([
                    "goal", "gate", "capacity", "--role", "scout", "--domain", "d{}".format(index), "--commit"
                ], project)
                self.assertEqual(spawn.returncode, 0, spawn.stdout + spawn.stderr)
            blocked = self.run_cli([
                "goal", "gate", "capacity", "--role", "researcher", "--domain", "extra", "--json"
            ], project)
            self.assertEqual(blocked.returncode, 4)
            self.assertEqual(json.loads(blocked.stdout)["action"], "ESCALATE")

    def test_corrupt_goal_state_returns_cli_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            init = self.run_cli(["goal", "init", "broken"], project)
            self.assertEqual(init.returncode, 0)
            git_dir = project / ".git" / "eas" / "goals"
            (git_dir / "broken.json").write_text("{bad json", encoding="utf-8")
            result = self.run_cli(["goal", "status", "broken"], project)
            self.assertEqual(result.returncode, 2)
            self.assertIn("ERROR:", result.stdout)
            self.assertNotIn("Traceback", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
