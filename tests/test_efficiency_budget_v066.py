from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.lifecycle import GoalStore, LifecycleGate
from runtime.workflow import Workflow

CORRUPT = "Encrypted function output content could not be decrypted or decoded"


class EfficiencyBudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = LifecycleGate(ROOT)

    def test_v066_budget_and_concurrency_contract(self) -> None:
        self.assertEqual(self.gate.policy.soft_limit, 6)
        self.assertEqual(self.gate.policy.hard_limit, 8)
        self.assertEqual(self.gate.policy.max_parallel_writers, 1)
        self.assertEqual(self.gate.policy.conservative_cap, 2)
        self.assertEqual(self.gate.policy.balanced_cap, 3)
        self.assertEqual(self.gate.policy.read_heavy_cap, 4)

    def test_committed_reuse_is_persisted_without_spawning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            store = GoalStore(project, "reuse-efficiency")
            store.initialize()
            first, assignment = self.gate.evaluate_and_commit(
                store, role="scout", task_domain="gateway", write_scope=[]
            )
            self.assertEqual(first.action, "SPAWN")
            self.assertIsNotNone(assignment)
            self.gate.transition_atomic(store, "a-0001", "completed")
            before_total = len(store.load().assignments)
            reused, child = self.gate.evaluate_and_commit(
                store, role="scout", task_domain="Gateway", write_scope=[]
            )
            self.assertEqual(reused.action, "REUSE")
            self.assertIsNone(child)
            state = store.load()
            self.assertEqual(len(state.assignments), before_total)
            self.assertEqual(state.efficiency["spawned_assignments"], 1)
            self.assertEqual(state.efficiency["reuse_decisions"], 1)
            self.assertEqual(state.efficiency["peak_active_children"], 1)

    def test_reactivation_and_approved_retry_transitions_are_counted_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            store = GoalStore(project, "transition-efficiency")
            store.initialize()
            self.gate.evaluate_and_commit(store, role="scout", task_domain="repo", write_scope=[])
            self.gate.transition_atomic(store, "a-0001", "completed")
            self.gate.transition_atomic(store, "a-0001", "running")
            metrics = store.load().efficiency
            self.assertEqual(metrics["resume_attempts"], 1)
            self.assertEqual(metrics["retry_attempts"], 0)

            self.gate.transition_atomic(store, "a-0001", "completed")
            self.gate.evaluate_and_commit(
                store, role="scout", task_domain="other", write_scope=[]
            )
            self.gate.transition_atomic(store, "a-0002", "running")
            flow = Workflow(self.gate)
            approval = flow.approve(
                store, "transition:failed", "a-0002", store.load().revision,
                "parent", "record failed attempt", "artifact:stopped",
            )
            self.gate.transition_atomic(store, "a-0002", "failed", approval["id"])
            retry_approval = flow.approve(
                store, "transition:running", "a-0002", store.load().revision,
                "parent", "retry after bounded fix", "artifact:stopped",
            )
            first = self.gate.transition_atomic(store, "a-0002", "running", retry_approval["id"])
            replay = self.gate.transition_atomic(store, "a-0002", "running", retry_approval["id"])
            self.assertEqual(first.assignment_id, replay.assignment_id)
            metrics = store.load().efficiency
            self.assertEqual(metrics["resume_attempts"], 2)
            self.assertEqual(metrics["retry_attempts"], 1)

    def test_running_to_pending_retry_transition_is_counted_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            store = GoalStore(project, "pending-retry-efficiency")
            store.initialize()
            self.gate.evaluate_and_commit(store, role="scout", task_domain="repo", write_scope=[])
            self.gate.transition_atomic(store, "a-0001", "running")
            flow = Workflow(self.gate)
            approval = flow.approve(
                store, "transition:pending", "a-0001", store.load().revision,
                "parent", "retry same assignment", "artifact:stopped",
            )
            first = self.gate.transition_atomic(store, "a-0001", "pending", approval["id"])
            replay = self.gate.transition_atomic(store, "a-0001", "pending", approval["id"])
            self.assertEqual(first.assignment_id, replay.assignment_id)
            metrics = store.load().efficiency
            self.assertEqual(metrics["resume_attempts"], 0)
            self.assertEqual(metrics["retry_attempts"], 1)

    def test_corruption_retry_and_replacement_metrics_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            store = GoalStore(project, "recovery-efficiency")
            store.initialize()
            self.gate.evaluate_and_commit(store, role="scout", task_domain="api", write_scope=[])
            flow = Workflow(self.gate)
            flow.transport(store, "a-0001", "failure", CORRUPT, store.load().revision)
            approval = flow.approve(
                store, "recover", "a-0001", store.load().revision,
                "parent", "resume once", "artifact:stopped",
            )
            receipt = flow.recover(store, "a-0001", approval["id"])
            replay = flow.recover(store, "a-0001", approval["id"])
            self.assertEqual(receipt, replay)
            self.assertEqual(store.load().efficiency["resume_attempts"], 1)
            self.assertEqual(store.load().efficiency["retry_attempts"], 1)
            flow.transport(store, "a-0001", "resume-failed", CORRUPT, store.load().revision)
            handoff = {
                "summary": "continue", "evidence": ["artifact:test"], "files": [],
                "commands": [], "risks": ["stream"], "next_action": "retry in replacement",
            }
            approval2 = flow.approve(
                store, "recover", "a-0001", store.load().revision,
                "parent", "replace once", "artifact:stopped",
            )
            result = flow.replace_child(store, "a-0001", approval2["id"], handoff)
            replay2 = flow.replace_child(store, "a-0001", approval2["id"], handoff)
            self.assertEqual(result, replay2)
            metrics = store.load().efficiency
            self.assertEqual(metrics["replacement_assignments"], 1)
            self.assertEqual(metrics["spawned_assignments"], 2)
            self.assertEqual(metrics["resume_attempts"], 1)
            with self.assertRaises(ValueError):
                flow.recover(store, "a-0001", approval2["id"])

    def test_legacy_goal_efficiency_is_partial_without_mutating_on_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            store = GoalStore(project, "legacy-efficiency")
            store.initialize()
            self.gate.evaluate_and_commit(store, role="scout", task_domain="repo", write_scope=[])
            payload = json.loads(store.state_path.read_text(encoding="utf-8"))
            payload.pop("efficiency", None)
            store.state_path.write_text(json.dumps(payload), encoding="utf-8")
            before = store.state_path.read_bytes()
            metrics = self.gate.efficiency(store.load())
            self.assertFalse(metrics["tracking_complete"])
            self.assertEqual(metrics["assignment_count"], 1)
            self.assertEqual(metrics["spawned_assignments"], 1)
            self.assertEqual(metrics["reuse_decisions"], 0)
            self.assertEqual(before, store.state_path.read_bytes())

    def test_efficiency_summary_is_read_only_and_provider_usage_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            store = GoalStore(project, "eff-summary")
            store.initialize()
            self.gate.evaluate_and_commit(store, role="scout", task_domain="repo", write_scope=[])
            before = store.state_path.read_bytes()
            first = self.gate.efficiency(store.load())
            second = self.gate.efficiency(store.load())
            self.assertEqual(first, second)
            self.assertEqual(before, store.state_path.read_bytes())
            self.assertEqual(first["assignment_count"], 1)
            self.assertEqual(first["spawned_assignments"], 1)
            self.assertEqual(first["reused_or_resumed"], 0)
            self.assertEqual(first["provider_usage"], {
                "tokens": None, "cost": None, "latency_ms": None,
            })


class EfficiencyCliTests(unittest.TestCase):
    def run_cli(self, args, project: Path):
        env = dict(os.environ)
        env["EAS_REPO"] = str(ROOT)
        env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        return subprocess.run(
            [sys.executable, "-m", "eas_cli"] + list(args), cwd=str(project), env=env,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", check=False,
        )

    def test_goal_efficiency_cli_json_and_human_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            self.assertEqual(self.run_cli(["goal", "init", "demo"], project).returncode, 0)
            self.assertEqual(self.run_cli([
                "goal", "gate", "demo", "--role", "scout", "--domain", "repo", "--commit"
            ], project).returncode, 0)
            state_path = project / ".git" / "eas" / "goals" / "demo.json"
            before = state_path.read_bytes()
            machine = self.run_cli(["goal", "efficiency", "demo", "--json"], project)
            self.assertEqual(machine.returncode, 0, machine.stderr + machine.stdout)
            payload = json.loads(machine.stdout)
            self.assertEqual(payload["command"], "goal-efficiency")
            self.assertEqual(payload["spawned_assignments"], 1)
            self.assertIsNone(payload["provider_usage"]["tokens"])
            human = self.run_cli(["goal", "efficiency", "demo"], project)
            self.assertEqual(human.returncode, 0, human.stderr + human.stdout)
            self.assertIn("Efficiency", human.stdout)
            self.assertIn("spawned=1", human.stdout)
            self.assertEqual(before, state_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
