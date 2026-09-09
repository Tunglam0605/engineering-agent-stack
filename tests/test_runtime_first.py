from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def runtime_contracts():
    try:
        from runtime.contracts import (  # type: ignore
            AgentStatus,
            ContextBudget,
            DelegationRequest,
            ExecutionTelemetry,
            WriteLease,
        )
        from runtime.context_packet import (  # type: ignore
            ContextEvidence,
            build_context_packet,
            compare_context_strategies,
        )
        from runtime.preflight import DelegationPreflight  # type: ignore
        from runtime.registry import AgentRegistry  # type: ignore
    except ModuleNotFoundError as exc:
        raise AssertionError("provider-neutral runtime contracts are missing") from exc
    return {
        "AgentRegistry": AgentRegistry,
        "AgentStatus": AgentStatus,
        "ContextBudget": ContextBudget,
        "ContextEvidence": ContextEvidence,
        "DelegationPreflight": DelegationPreflight,
        "DelegationRequest": DelegationRequest,
        "ExecutionTelemetry": ExecutionTelemetry,
        "WriteLease": WriteLease,
        "build_context_packet": build_context_packet,
        "compare_context_strategies": compare_context_strategies,
    }


class DelegationPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        api = runtime_contracts()
        self.ContextBudget = api["ContextBudget"]
        self.DelegationPreflight = api["DelegationPreflight"]
        self.DelegationRequest = api["DelegationRequest"]
        self.WriteLease = api["WriteLease"]
        self.preflight = self.DelegationPreflight.from_repository(ROOT)

    def request(self, **overrides):
        values = {
            "task": "Implement a bounded runtime contract",
            "route_mode": "delegate",
            "role": "implementer",
            "profile": "standard",
            "provider": "openai",
            "child_agent_capable": True,
            "write_owner": "child-1",
            "write_scope": ["runtime/"],
            "parent_role": "orchestrator",
            "recursion_depth": 0,
            "context_budget": self.ContextBudget(
                max_input_tokens=1200,
                estimated_input_tokens=600,
            ),
            "review_required": False,
            "review_planned": False,
        }
        values.update(overrides)
        return self.DelegationRequest(**values)

    def test_request_contract_rejects_type_coercion(self) -> None:
        with self.assertRaisesRegex(ValueError, "child_agent_capable must be a boolean"):
            self.request(child_agent_capable="false")
        with self.assertRaisesRegex(ValueError, "review_required must be a boolean"):
            self.request(review_required="false")
        with self.assertRaisesRegex(ValueError, "recursion_depth must be an integer"):
            self.request(recursion_depth="0")
        with self.assertRaisesRegex(ValueError, "max_input_tokens must be an integer"):
            self.ContextBudget(max_input_tokens=True, estimated_input_tokens=1)
        with self.assertRaisesRegex(ValueError, "scope must be a list of strings"):
            self.WriteLease(owner="child-2", scope="runtime/preflight.py")

    def test_pass_resolves_role_profile_and_provider_model(self) -> None:
        result = self.preflight.evaluate(self.request())

        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.resolved_model, "gpt-5.6-terra")
        self.assertEqual(result.resolved_effort, "medium")
        self.assertEqual(result.reasons, [])

        plan = result.to_execution_plan(assignment_id="assignment-1")
        self.assertEqual(plan.preflight.decision, "PASS")
        self.assertEqual(plan.route.role, "implementer")
        self.assertEqual(plan.compute.provider, "openai")
        self.assertEqual(plan.compute.model, "gpt-5.6-terra")
        self.assertEqual(plan.permissions.write_scope, ["runtime/"])
        self.assertEqual(plan.context_budget.estimated_input_tokens, 600)

    def test_rejects_role_route_capability_and_resolution_failures(self) -> None:
        cases = [
            ("missing role", {"role": "not-a-role"}, "role_not_found"),
            ("disabled role", {"role": "scout"}, "role_disabled"),
            ("direct route", {"route_mode": "direct"}, "route_not_delegated"),
            (
                "missing child capability",
                {"child_agent_capable": False},
                "child_agent_unavailable",
            ),
            ("unknown profile", {"profile": "turbo"}, "profile_not_found"),
            (
                "incompatible profile",
                {"profile": "cheap"},
                "role_profile_incompatible",
            ),
            (
                "unmapped provider",
                {"provider": "unconfigured-provider"},
                "model_resolution_unavailable",
            ),
        ]
        for label, overrides, expected_code in cases:
            with self.subTest(label=label):
                disabled = {"scout"} if label == "disabled role" else set()
                result = self.preflight.evaluate(
                    self.request(**overrides), disabled_roles=disabled
                )
                self.assertEqual(result.decision, "REJECT")
                self.assertIn(expected_code, [reason.code for reason in result.reasons])

    def test_rejects_recursion_self_recursion_and_write_conflicts(self) -> None:
        cases = [
            (
                "recursive delegation",
                {"recursion_depth": 1},
                [],
                "recursive_delegation_forbidden",
            ),
            (
                "self recursion",
                {"parent_role": "implementer"},
                [],
                "self_recursion_forbidden",
            ),
            (
                "missing write owner",
                {"write_owner": None},
                [],
                "write_owner_required",
            ),
            (
                "missing write scope",
                {"write_scope": []},
                [],
                "write_scope_required",
            ),
            (
                "overlapping write lease",
                {},
                [self.WriteLease(owner="child-2", scope=["runtime/preflight.py"])],
                "write_scope_conflict",
            ),
        ]
        for label, overrides, leases, expected_code in cases:
            with self.subTest(label=label):
                result = self.preflight.evaluate(
                    self.request(**overrides), active_write_leases=leases
                )
                self.assertEqual(result.decision, "REJECT")
                self.assertIn(expected_code, [reason.code for reason in result.reasons])

    def test_direct_preflight_rejects_malformed_active_write_lease_container(self) -> None:
        for value in (False, {}, "", 0):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "active_write_leases must be an iterable of WriteLease"):
                    self.preflight.evaluate(self.request(), active_write_leases=value)

    def test_rejects_write_scope_for_read_only_role(self) -> None:
        result = self.preflight.evaluate(
            self.request(
                role="scout",
                profile="cheap",
                write_owner="child-1",
                write_scope=["runtime/"],
            )
        )
        self.assertEqual(result.decision, "REJECT")
        self.assertIn("write_scope_forbidden", [reason.code for reason in result.reasons])

    def test_policy_risk_can_require_independent_review(self) -> None:
        result = self.preflight.evaluate(
            self.request(risk_class="high-risk", review_required=False, review_planned=False)
        )
        self.assertEqual(result.decision, "ESCALATE")
        self.assertIn("required_review_unplanned", [reason.code for reason in result.reasons])
        self.assertTrue(result.effective_review_required)

        approved = self.preflight.evaluate(
            self.request(risk_class="high-risk", review_required=False, review_planned=True)
        )
        self.assertEqual(approved.decision, "PASS")
        plan = approved.to_execution_plan(assignment_id="assignment-risk")
        self.assertTrue(plan.review.required)

    def test_codex_provider_uses_adapter_reasoning_override_without_copying_it(self) -> None:
        result = self.preflight.evaluate(
            self.request(
                role="scout",
                profile="cheap",
                provider="openai-codex",
                write_owner=None,
                write_scope=[],
            )
        )
        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.resolved_model, "gpt-5.6-luna")
        self.assertEqual(result.resolved_effort, "medium")

    def test_non_pass_preflight_cannot_build_execution_plan(self) -> None:
        rejected = self.preflight.evaluate(self.request(child_agent_capable=False))
        with self.assertRaisesRegex(ValueError, "PASS preflight"):
            rejected.to_execution_plan(assignment_id="rejected")

        escalated = self.preflight.evaluate(
            self.request(
                context_budget=self.ContextBudget(
                    max_input_tokens=100, estimated_input_tokens=200
                )
            )
        )
        with self.assertRaisesRegex(ValueError, "PASS preflight"):
            escalated.to_execution_plan(assignment_id="escalated")

    def test_rejects_invalid_recursion_depth_and_unsafe_write_scopes(self) -> None:
        cases = [
            (self.request(recursion_depth=-1), [], "invalid_recursion_depth"),
            (self.request(write_scope=["../docs"]), [], "invalid_write_scope"),
            (self.request(write_scope=["C:/repo/runtime"]), [], "invalid_write_scope"),
            (self.request(write_scope=["C:outside"]), [], "invalid_write_scope"),
            (self.request(write_scope=["D:relative/path"]), [], "invalid_write_scope"),
            (self.request(write_scope=["runtime/file."]), [], "invalid_write_scope"),
            (self.request(write_scope=["runtime/file "]), [], "invalid_write_scope"),
            (self.request(write_scope=["runtime/file:stream"]), [], "invalid_write_scope"),
            (self.request(write_scope=["/runtime"]), [], "invalid_write_scope"),
        ]
        for request, leases, expected in cases:
            with self.subTest(expected=expected, scope=request.write_scope):
                result = self.preflight.evaluate(request, active_write_leases=leases)
                self.assertEqual(result.decision, "REJECT")
                self.assertIn(expected, [reason.code for reason in result.reasons])

    def test_write_conflicts_are_conservative_across_case_and_separators(self) -> None:
        leases = [self.WriteLease(owner="other", scope=["runtime/preflight.py"])]
        for scope in ["Runtime", "runtime\\preflight.py"]:
            with self.subTest(scope=scope):
                result = self.preflight.evaluate(
                    self.request(write_scope=[scope]), active_write_leases=leases
                )
                self.assertEqual(result.decision, "REJECT")
                self.assertIn(
                    "write_scope_conflict", [reason.code for reason in result.reasons]
                )

    def test_escalates_exceeded_context_budget_and_missing_review(self) -> None:
        result = self.preflight.evaluate(
            self.request(
                context_budget=self.ContextBudget(
                    max_input_tokens=500,
                    estimated_input_tokens=700,
                ),
                review_required=True,
                review_planned=False,
            )
        )

        self.assertEqual(result.decision, "ESCALATE")
        self.assertEqual(
            [reason.code for reason in result.reasons],
            ["context_budget_exceeded", "required_review_unplanned"],
        )


class AgentRegistryTests(unittest.TestCase):
    def test_registry_emits_json_and_concise_text_without_inventing_telemetry(self) -> None:
        api = runtime_contracts()
        registry = api["AgentRegistry"]()
        status = api["AgentStatus"](
            assignment_id="child-1",
            task="Inspect runtime contracts",
            state="pending",
            role="scout",
            profile="cheap",
            provider="openai",
            model="gpt-5.6-luna",
            parent_assignment_id="root-1",
            write_owner=None,
            write_scope=[],
        )

        registry.add(status)
        payload = json.loads(registry.to_json())
        self.assertIsNone(payload["agents"][0]["telemetry"]["tokens"])
        self.assertIsNone(payload["agents"][0]["telemetry"]["latency_ms"])
        self.assertIn("child-1 pending scout/cheap openai:gpt-5.6-luna", registry.to_text())
        self.assertIn("tokens=? latency=? duration=?", registry.to_text())

    def test_registry_tracks_terminal_state_and_known_telemetry(self) -> None:
        api = runtime_contracts()
        registry = api["AgentRegistry"]()
        registry.add(
            api["AgentStatus"](
                assignment_id="child-1",
                task="Implement runtime contracts",
                state="running",
                role="implementer",
                profile="standard",
                provider="openai",
                model="gpt-5.6-terra",
                parent_assignment_id="root-1",
                write_owner="child-1",
                write_scope=["runtime/"],
            )
        )

        registry.transition(
            "child-1",
            "completed",
            telemetry=api["ExecutionTelemetry"](
                duration_ms=1250,
                tokens=900,
                latency_ms=1100,
            ),
        )

        payload = registry.as_dict()["agents"][0]
        self.assertEqual(payload["state"], "completed")
        self.assertEqual(payload["telemetry"]["tokens"], 900)
        self.assertEqual(payload["write"]["scope"], ["runtime/"])

    def test_registry_summary_counts_goal_fanout_and_roles(self) -> None:
        api = runtime_contracts()
        registry = api["AgentRegistry"]()
        for index, (role, state) in enumerate([
            ("scout", "completed"),
            ("scout", "running"),
            ("debugger", "completed"),
        ], start=1):
            registry.add(
                api["AgentStatus"](
                    assignment_id=f"child-{index}",
                    task="bounded task",
                    state=state,
                    role=role,
                    profile="cheap" if role == "scout" else "deep",
                    provider="openai",
                    model="model",
                    parent_assignment_id="root-1",
                    write_owner=None,
                    write_scope=[],
                )
            )
        summary = registry.summary(soft_limit=3, hard_limit=4)
        self.assertEqual(summary["total_assignments"], 3)
        self.assertEqual(summary["active_assignments"], 1)
        self.assertEqual(summary["terminal_assignments"], 2)
        self.assertEqual(summary["completed_assignments"], 2)
        self.assertEqual(summary["failed_assignments"], 0)
        self.assertEqual(summary["blocked_assignments"], 0)
        self.assertEqual(summary["by_role"], {"debugger": 1, "scout": 2})
        self.assertEqual(summary["budget_state"], "soft_limit")
        self.assertIn("budget=soft_limit", registry.summary_text(soft_limit=3, hard_limit=4))

    def test_registry_summary_requires_goal_for_multi_goal_snapshot(self) -> None:
        api = runtime_contracts()
        registry = api["AgentRegistry"]()
        for index, goal in enumerate(("goal-a", "goal-b"), start=1):
            registry.add(
                api["AgentStatus"](
                    assignment_id=f"child-{index}", task="bounded task", state="completed",
                    role="scout", profile="cheap", provider="openai", model="model",
                    parent_assignment_id=goal, write_owner=None, write_scope=[],
                )
            )
        with self.assertRaisesRegex(ValueError, "goal_id is required"):
            registry.summary()
        selected = registry.summary(goal_id="goal-a", soft_limit=1, hard_limit=2)
        self.assertEqual(selected["goal_id"], "goal-a")
        self.assertEqual(selected["total_assignments"], 1)
        self.assertEqual(selected["budget_state"], "soft_limit")
        with self.assertRaisesRegex(ValueError, "goal_id was not found"):
            registry.summary(goal_id="goal-missing")

    def test_registry_summary_rejects_invalid_limits(self) -> None:
        api = runtime_contracts()
        registry = api["AgentRegistry"]()
        for kwargs, message in [
            ({"soft_limit": True, "hard_limit": 12}, "soft_limit must be a positive integer"),
            ({"soft_limit": 8, "hard_limit": 0}, "hard_limit must be a positive integer"),
            ({"soft_limit": 12, "hard_limit": 8}, "hard_limit must be greater than or equal to soft_limit"),
        ]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, message):
                    registry.summary(**kwargs)

    def test_registry_rejects_unknown_states(self) -> None:
        api = runtime_contracts()
        with self.assertRaisesRegex(ValueError, "unsupported agent state"):
            api["AgentStatus"](
                assignment_id="child-1",
                task="Invalid",
                state="cancelled",
                role="scout",
                profile="cheap",
                provider=None,
                model=None,
                parent_assignment_id=None,
                write_owner=None,
                write_scope=[],
            )


    def test_registry_rejects_malformed_write_and_telemetry_shapes(self) -> None:
        api = runtime_contracts()
        with self.assertRaisesRegex(ValueError, "write_scope must be a list of strings"):
            api["AgentStatus"](
                assignment_id="child-1",
                task="Invalid write scope",
                state="pending",
                role="scout",
                profile="cheap",
                provider="openai",
                model="gpt-5.6-luna",
                parent_assignment_id=None,
                write_owner=None,
                write_scope="runtime/",
            )
        with self.assertRaisesRegex(ValueError, "tokens must be an integer"):
            api["ExecutionTelemetry"](tokens=True)

        registry_type = api["AgentRegistry"]
        bad = {
            "agents": [
                {
                    "assignment_id": "child-1",
                    "task": "Bad snapshot",
                    "state": "pending",
                    "role": "scout",
                    "profile": "cheap",
                    "provider": "openai",
                    "model": "gpt-5.6-luna",
                    "parent_assignment_id": None,
                    "write": False,
                    "telemetry": {},
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "write must be an object"):
            registry_type.from_dict(bad)


class ContextPacketTests(unittest.TestCase):
    def test_bounded_packet_retains_required_evidence_within_limits(self) -> None:
        api = runtime_contracts()
        evidence = [
            api["ContextEvidence"](
                evidence_id="acceptance",
                source="docs/ACCEPTANCE_WINDOWS.md",
                content="Stack acceptance and provider diagnostics are separate.",
                required=True,
                priority=100,
            ),
            api["ContextEvidence"](
                evidence_id="policy",
                source="policies/context-budget.md",
                content="Evidence required for correctness must not be suppressed.",
                required=True,
                priority=90,
            ),
            api["ContextEvidence"](
                evidence_id="noise",
                source="logs/full.txt",
                content="x" * 400,
                required=False,
                priority=1,
            ),
        ]

        packet = api["build_context_packet"](
            task="Compare bounded evidence against full context",
            evidence=evidence,
            max_evidence_items=2,
            max_chars=300,
        )

        self.assertEqual(packet.retained_evidence_count, 2)
        self.assertEqual(packet.retained_evidence_ids, ["acceptance", "policy"])
        self.assertLessEqual(packet.context_size_chars, 300)
        self.assertEqual(packet.token_proxy, (packet.context_size_chars + 3) // 4)

    def test_required_evidence_never_silently_drops_at_item_limit(self) -> None:
        api = runtime_contracts()
        evidence = [
            api["ContextEvidence"]("a", "a.txt", "A", required=True, priority=2),
            api["ContextEvidence"]("b", "b.txt", "B", required=True, priority=1),
        ]
        with self.assertRaisesRegex(ValueError, "required evidence count"):
            api["build_context_packet"](
                task="x", evidence=evidence, max_evidence_items=1, max_chars=100
            )

    def test_task_and_required_evidence_must_fit_total_char_budget(self) -> None:
        api = runtime_contracts()
        with self.assertRaisesRegex(ValueError, "task exceeds"):
            api["build_context_packet"](
                task="x" * 20, evidence=[], max_evidence_items=0, max_chars=5
            )
        evidence = [
            api["ContextEvidence"](
                "required", "required.txt", "x" * 80, required=True, priority=1
            )
        ]
        with self.assertRaisesRegex(ValueError, "required evidence exceeds"):
            api["build_context_packet"](
                task="task", evidence=evidence, max_evidence_items=1, max_chars=50
            )

    def test_context_packet_budget_counts_exact_rendered_prompt(self) -> None:
        from runtime import context_packet as cp

        evidence = [cp.ContextEvidence("r", "s", "123456789012345678", required=True)]
        self.assertTrue(hasattr(cp, "render_context_prompt"))
        with self.assertRaisesRegex(ValueError, "required evidence exceeds"):
            cp.build_context_packet(
                task="x", evidence=evidence, max_evidence_items=1, max_chars=40
            )
        packet = cp.build_context_packet(
            task="x", evidence=evidence, max_evidence_items=1, max_chars=200
        )
        rendered = cp.render_context_prompt("x", evidence)
        self.assertEqual(packet.context_size_chars, len(rendered))
        self.assertEqual(packet.token_proxy, (len(rendered) + 3) // 4)

    def test_context_packet_rejects_type_coercion(self) -> None:
        api = runtime_contracts()
        ContextEvidence = api["ContextEvidence"]
        with self.assertRaisesRegex(ValueError, "required must be a boolean"):
            ContextEvidence("x", "x.txt", "evidence", required="false")
        with self.assertRaisesRegex(ValueError, "content must be a string"):
            ContextEvidence("x", "x.txt", 123)
        with self.assertRaisesRegex(ValueError, "priority must be an integer"):
            ContextEvidence("x", "x.txt", "evidence", priority=True)
        for field, kwargs in [
            ("max_evidence_items", {"max_evidence_items": True, "max_chars": 10}),
            ("max_chars", {"max_evidence_items": 1, "max_chars": 10.5}),
        ]:
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, field + " must be an integer"):
                    api["build_context_packet"](task="x", evidence=[], **kwargs)

    def test_comparison_harness_records_unknown_runtime_telemetry_as_unknown(self) -> None:
        api = runtime_contracts()
        fixture_path = ROOT / "benchmarks" / "fixtures" / "context-packet-minimal.yaml"
        if not fixture_path.is_file():
            self.fail("minimal controlled context-packet fixture is missing")
        fixture = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
        evidence = [api["ContextEvidence"](**item) for item in fixture["evidence"]]

        comparison = api["compare_context_strategies"](
            experiment_id=fixture["experiment_id"],
            task_id=fixture["task_id"],
            task=fixture["task"],
            evidence=evidence,
            max_evidence_items=fixture["bounded_limits"]["max_evidence_items"],
            max_chars=fixture["bounded_limits"]["max_chars"],
            quality_hook=lambda packet: 1.0
            if set(fixture["required_evidence_ids"]).issubset(
                packet.retained_evidence_ids
            )
            else 0.0,
        )

        self.assertEqual([item["strategy"] for item in comparison], ["full", "bounded"])
        self.assertLess(
            comparison[1]["measurement"]["context_size_chars"],
            comparison[0]["measurement"]["context_size_chars"],
        )
        self.assertEqual(comparison[1]["measurement"]["quality_score"], 1.0)
        self.assertIsNone(comparison[1]["measurement"]["latency_ms"])
        self.assertIsNone(comparison[1]["measurement"]["tokens"])


class DelegationResolverCliTests(unittest.TestCase):
    def test_resolver_cli_only_emits_execution_plan_for_pass(self) -> None:
        import subprocess
        import tempfile

        script = ROOT / "scripts" / "resolve_delegation.py"
        base = {
            "task": "Implement bounded runtime change",
            "route_mode": "delegate",
            "role": "implementer",
            "profile": "standard",
            "provider": "openai-codex",
            "child_agent_capable": True,
            "write_owner": "child-1",
            "write_scope": ["runtime/"],
            "parent_role": "orchestrator",
            "recursion_depth": 0,
            "context_budget": {
                "max_input_tokens": 1200,
                "estimated_input_tokens": 600,
            },
            "review_required": False,
            "review_planned": False,
            "risk_class": "normal",
            "assignment_id": "child-1",
        }
        with tempfile.TemporaryDirectory() as tmp:
            for label, overrides, expected_code, expect_plan in [
                ("pass", {}, 0, True),
                ("reject", {"child_agent_capable": False}, 3, False),
                (
                    "escalate",
                    {
                        "context_budget": {
                            "max_input_tokens": 500,
                            "estimated_input_tokens": 700,
                        }
                    },
                    4,
                    False,
                ),
            ]:
                payload = dict(base)
                payload.update(overrides)
                path = Path(tmp) / f"{label}.yaml"
                path.write_text(yaml.safe_dump(payload), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(script), "--request", str(path), "--format", "json"],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, expected_code, result.stderr + result.stdout)
                body = json.loads(result.stdout)
                self.assertEqual(body["preflight"]["decision"], label.upper())
                self.assertEqual(body["execution_plan"] is not None, expect_plan)

    def test_resolver_rejects_string_booleans_and_wrong_scalar_types(self) -> None:
        import subprocess
        import tempfile

        script = ROOT / "scripts" / "resolve_delegation.py"
        base = {
            "task": "Implement bounded runtime change",
            "route_mode": "delegate",
            "role": "implementer",
            "profile": "standard",
            "provider": "openai-codex",
            "child_agent_capable": True,
            "write_owner": "child-1",
            "write_scope": ["runtime/"],
            "parent_role": "orchestrator",
            "recursion_depth": 0,
            "context_budget": {
                "max_input_tokens": 1200,
                "estimated_input_tokens": 600,
            },
            "review_required": False,
            "review_planned": False,
            "risk_class": "normal",
            "assignment_id": "child-1",
        }
        cases = [
            ({"child_agent_capable": "false"}, "child_agent_capable must be a boolean"),
            ({"review_required": "false"}, "review_required must be a boolean"),
            ({"recursion_depth": "0"}, "recursion_depth must be an integer"),
            ({"write_scope": "runtime/"}, "write_scope must be a list of strings"),
            ({"task": 123}, "task must be a non-empty string"),
            ({"active_write_leases": False}, "active_write_leases must be a list"),
            ({"active_write_leases": {}}, "active_write_leases must be a list"),
            ({"active_write_leases": ""}, "active_write_leases must be a list"),
            ({"active_write_leases": [{"owner": "other", "scope": "runtime/"}]}, "scope must be a list of strings"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for index, (overrides, message) in enumerate(cases):
                with self.subTest(overrides=overrides):
                    payload = dict(base)
                    payload.update(overrides)
                    path = Path(tmp) / f"invalid-{index}.yaml"
                    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(script), "--request", str(path), "--format", "json"],
                        cwd=str(ROOT),
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
                    self.assertIn(message, json.loads(result.stdout)["error"])


class AgentStatusCliTests(unittest.TestCase):
    def test_status_cli_renders_snapshot_as_text_and_json(self) -> None:
        import subprocess
        import tempfile

        snapshot = {
            "agents": [
                {
                    "assignment_id": "child-1",
                    "state": "running",
                    "task": "Inspect runtime",
                    "role": "scout",
                    "profile": "cheap",
                    "provider": "openai",
                    "model": "gpt-5.6-luna",
                    "parent_assignment_id": "root-1",
                    "write": {"owner": None, "scope": []},
                    "telemetry": {"duration_ms": None, "tokens": None, "latency_ms": None},
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "status.json"
            path.write_text(json.dumps(snapshot), encoding="utf-8")
            script = ROOT / "scripts" / "agent_status.py"
            text = subprocess.run(
                [sys.executable, str(script), "--input", str(path), "--format", "text"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(text.returncode, 0, text.stderr)
            self.assertIn("child-1 running scout/cheap openai:gpt-5.6-luna", text.stdout)
            machine = subprocess.run(
                [sys.executable, str(script), "--input", str(path), "--format", "json"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(machine.returncode, 0, machine.stderr)
            payload = json.loads(machine.stdout)
            self.assertIsNone(payload["agents"][0]["telemetry"]["tokens"])

            summary = subprocess.run(
                [
                    sys.executable, str(script), "--input", str(path),
                    "--format", "json", "--summary", "--soft-limit", "1", "--hard-limit", "2",
                ],
                cwd=str(ROOT), capture_output=True, text=True, check=False,
            )
            self.assertEqual(summary.returncode, 0, summary.stderr)
            summary_payload = json.loads(summary.stdout)
            self.assertEqual(summary_payload["summary"]["budget_state"], "soft_limit")
            self.assertEqual(summary_payload["summary"]["by_role"], {"scout": 1})
            self.assertEqual(summary_payload["summary"]["goal_id"], "root-1")


class ContextBenchmarkPreparationTests(unittest.TestCase):
    def test_full_and_bounded_topologies_materialize_different_real_prompts(self) -> None:
        import subprocess
        import tempfile

        script = ROOT / "scripts" / "prepare_benchmark_task.py"
        manifests = {}
        with tempfile.TemporaryDirectory() as tmp:
            for topology in ("full-context", "bounded-context-packet"):
                destination = Path(tmp) / topology
                result = subprocess.run(
                    [
                        sys.executable,
                        str(script),
                        "--task-id",
                        "context-packet-synthetic-001",
                        "--experiment-id",
                        "context-packet-full-vs-bounded",
                        "--model",
                        "gpt-5.6-terra",
                        "--reasoning-effort",
                        "medium",
                        "--profile",
                        "standard",
                        "--topology",
                        topology,
                        "--destination",
                        str(destination),
                    ],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                manifests[topology] = yaml.safe_load(
                    (destination / "manifest.yaml").read_text(encoding="utf-8")
                )

        full = manifests["full-context"]
        bounded = manifests["bounded-context-packet"]
        self.assertIn("noisy-transcript.txt", full["prompt"])
        self.assertNotIn("noisy-transcript.txt", bounded["prompt"])
        self.assertIn("docs/ACCEPTANCE_WINDOWS.md", bounded["prompt"])
        self.assertIn("policies/context-budget.md", bounded["prompt"])
        self.assertGreater(
            full["context_measurement"]["context_size_chars"],
            bounded["context_measurement"]["context_size_chars"],
        )
        self.assertEqual(full["context_strategy"], "full")
        self.assertEqual(bounded["context_strategy"], "bounded")

    def test_context_topology_is_rejected_for_unrelated_task(self) -> None:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "prepare_benchmark_task.py"),
                    "--task-id",
                    "scout-symbol-001",
                    "--experiment-id",
                    "scout-luna-vs-terra",
                    "--model",
                    "gpt-5.6-luna",
                    "--reasoning-effort",
                    "medium",
                    "--profile",
                    "cheap",
                    "--topology",
                    "bounded-context-packet",
                    "--destination",
                    str(Path(tmp) / "bad"),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("context topology", result.stdout)


class CodexAdapterResolutionTests(unittest.TestCase):
    def test_config_example_uses_adapter_model_provider(self) -> None:
        scripts_dir = str(ROOT / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import generate_codex_adapter as generator

        profiles = {
            "profiles": {
                "standard": {
                    "candidate_models": {
                        "openai": "openai-model",
                        "test-provider": "provider-specific-model",
                    },
                    "reasoning": "medium",
                }
            }
        }
        role_map = {"model_provider": "test-provider"}
        rendered = generator.render_config_example({}, profiles, role_map)
        self.assertIn('default_subagent_model = "provider-specific-model"', rendered)
        self.assertNotIn('default_subagent_model = "openai-model"', rendered)


class LifecyclePolicyTests(unittest.TestCase):
    def test_lifecycle_policy_is_bounded_and_resume_first(self) -> None:
        policy = yaml.safe_load((ROOT / "config" / "routing-policy.yaml").read_text(encoding="utf-8"))
        self.assertEqual(policy["lifecycle"]["reuse_strategy"], "resume-before-spawn")
        self.assertEqual(policy["limits"]["default_max_parallel_readers"], 4)
        self.assertEqual(policy["limits"]["default_max_parallel_writers"], 1)
        self.assertEqual(policy["limits"]["soft_max_child_assignments_per_goal"], 6)
        self.assertEqual(policy["limits"]["hard_max_child_assignments_per_goal"], 8)
        self.assertEqual(policy["limits"]["default_max_architect_assignments_per_goal"], 1)
        self.assertEqual(policy["limits"]["default_max_reviewer_assignments_per_change_set"], 1)
        self.assertEqual(policy["limits"]["max_same_role_domain_scope_active"], 1)

        parent = (ROOT / "adapters" / "codex" / "AGENTS.md.example").read_text(encoding="utf-8")
        for phrase in (
            "Reuse before spawn",
            "6 child assignments",
            "8 child assignments",
            "one consultation per goal",
            "one independent reviewer per meaningful change-set",
        ):
            self.assertIn(phrase, parent)

        validator = (ROOT / "scripts" / "validate_agents.py").read_text(encoding="utf-8")
        self.assertIn("isinstance(item, str) and item.strip() for item in match_keys", validator)

    def test_validator_reports_malformed_reuse_match_keys_without_traceback(self) -> None:
        import shutil
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            (fixture / "scripts").mkdir()
            (fixture / "config").mkdir()
            (fixture / "schemas").mkdir()
            (fixture / "adapters" / "codex").mkdir(parents=True)
            shutil.copytree(ROOT / "agents" / "core", fixture / "agents" / "core")
            shutil.copy2(ROOT / "scripts" / "validate_agents.py", fixture / "scripts" / "validate_agents.py")
            shutil.copy2(ROOT / "config" / "model-profiles.yaml", fixture / "config" / "model-profiles.yaml")
            shutil.copy2(ROOT / "config" / "project-identity.yaml", fixture / "config" / "project-identity.yaml")
            shutil.copy2(ROOT / "schemas" / "agent-contract.yaml", fixture / "schemas" / "agent-contract.yaml")
            shutil.copy2(ROOT / "adapters" / "codex" / "role-profiles.yaml", fixture / "adapters" / "codex" / "role-profiles.yaml")
            shutil.copy2(ROOT / "adapters" / "codex" / "AGENTS.md.example", fixture / "adapters" / "codex" / "AGENTS.md.example")

            policy = yaml.safe_load((ROOT / "config" / "routing-policy.yaml").read_text(encoding="utf-8"))
            policy["lifecycle"]["reuse_match_keys"] = [{"bad": "shape"}]
            (fixture / "config" / "routing-policy.yaml").write_text(
                yaml.safe_dump(policy, sort_keys=False), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(fixture / "scripts" / "validate_agents.py")],
                cwd=str(fixture), capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn("reuse_match_keys must be a list of non-empty strings", result.stdout)
            self.assertNotIn("Traceback", result.stderr + result.stdout)


class RuntimeSchemaTests(unittest.TestCase):
    def test_runtime_schemas_define_bounded_required_fields(self) -> None:
        expected = {
            "delegation-request.yaml": {
                "task", "route_mode", "role", "profile", "provider",
                "child_agent_capable", "write_owner", "write_scope",
                "parent_role", "recursion_depth", "context_budget",
                "review_required", "review_planned", "risk_class", "assignment_id",
            },
            "delegation-preflight.yaml": {"decision", "reasons"},
            "resolved-execution-plan.yaml": {
                "assignment_id",
                "task",
                "route",
                "compute",
                "permissions",
                "recursion",
                "review",
                "context_budget",
                "preflight",
            },
            "agent-status.yaml": {
                "assignment_id",
                "state",
                "task",
                "role",
                "profile",
                "provider",
                "model",
                "parent_assignment_id",
                "write",
                "telemetry",
            },
            "context-packet-benchmark.yaml": {
                "experiment_id",
                "task_id",
                "strategy",
                "measurement",
            },
        }
        for filename, required in expected.items():
            with self.subTest(filename=filename):
                path = ROOT / "schemas" / filename
                if not path.is_file():
                    self.fail("missing schema: " + filename)
                schema = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertTrue(required.issubset(set(schema["required_fields"])))


if __name__ == "__main__":
    unittest.main()
