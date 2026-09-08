from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest

from runtime.lifecycle import GoalStore, LifecycleGate
from runtime.workflow import Workflow

ROOT = Path(__file__).resolve().parents[1]
CORRUPT = 'Encrypted function output content could not be decrypted or decoded'


class TransportRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        project = Path(self.tmp.name)
        (project / '.git').mkdir()
        self.store = GoalStore(project, 'transport')
        self.store.initialize()
        self.gate = LifecycleGate(ROOT)
        self.flow = Workflow(self.gate)
        self.gate.evaluate_and_commit(self.store, role='scout', task_domain='api', write_scope=[])

    def event(self, event, message='stream disconnected before completion', target='a-0001'):
        return self.flow.transport(self.store, target, event, message, self.store.load().revision)

    def resume(self, target='a-0001'):
        approval = self.flow.approve(self.store, 'recover', target, self.store.load().revision,
                                     'parent', 'resume existing child', 'artifact:executor-stopped')
        return self.flow.recover(self.store, target, approval['id'])

    def test_classification(self):
        from runtime.reliability import classify_failure
        for message in ('stream disconnected before completion', 'Reconnecting 5/5',
                        'ConnectionResetError', 'transport closed', 'connection reset by peer'):
            self.assertEqual(classify_failure(message), 'TRANSIENT_TRANSPORT')
        self.assertEqual(classify_failure(CORRUPT), 'TRANSPORT_CORRUPTION')
        self.assertEqual(classify_failure('assertion failed'), 'AGENT_FAILURE')

    def test_transient_resume_success_and_no_duplicate_spawn(self):
        self.event('failure')
        self.event('failure')
        decision, child = self.gate.evaluate_and_commit(self.store, role='scout', task_domain='api', write_scope=[])
        self.assertEqual(decision.action, 'ESCALATE')
        self.assertIsNone(child)
        self.resume()
        self.event('resume-success', 'artifact:verified-stream')
        state = self.store.load()
        self.assertEqual(len(state.assignments), 1)
        self.assertEqual(state.assignments[0].recovery['resumes'], 1)
        self.assertEqual(state.assignments[0].recovery['phase'], 'healthy')

    def test_corruption_resume_then_single_replacement(self):
        self.event('failure', CORRUPT)
        self.resume()
        self.event('resume-failed', CORRUPT)
        handoff = dict(summary='Inspect API', evidence=['artifact:test'], files=['runtime/workflow.py'],
                       commands=['python -m unittest'], risks=['Unverified output'], next_action='Recheck API')
        approval = self.flow.approve(self.store, 'recover', 'a-0001', self.store.load().revision,
                                     'parent', 'replace corrupt executor', 'artifact:stopped')
        result = self.flow.replace_child(self.store, 'a-0001', approval['id'], handoff)
        self.assertEqual(result['assignment_id'], 'a-0002')
        self.assertEqual(self.flow.replace_child(self.store, 'a-0001', approval['id'], handoff), result)
        self.gate.transition_atomic(self.store, 'a-0002', 'completed')
        revival = self.flow.approve(self.store, 'transition:running', 'a-0001', self.store.load().revision,
                                    'parent', 'attempt retired revival', 'artifact:stopped')
        with self.assertRaisesRegex(ValueError, 'retired'):
            self.gate.transition_atomic(self.store, 'a-0001', 'running', revival['id'])
        self.gate.transition_atomic(self.store, 'a-0002', 'running')
        self.event('failure', CORRUPT, 'a-0002')
        self.assertEqual(self.store.load().assignments[1].recovery['phase'], 'escalated')

    def test_resume_budget_exhaustion(self):
        self.event('failure')
        for _ in range(2):
            self.resume()
            self.event('resume-failed')
        self.assertEqual(self.store.load().assignments[0].recovery['phase'], 'replacement-ready')
        with self.assertRaises(ValueError):
            self.resume()
        with self.assertRaises(ValueError):
            self.flow.replace_child(self.store, 'a-0001', 'missing', {})
        self.assertFalse(self.flow.plan(self.store)['dispatch_authorized'])

    def test_concurrency_barrier(self):
        self.gate.evaluate_and_commit(self.store, role='implementer', task_domain='code', write_scope=['src/'])
        decision, child = self.gate.evaluate_and_commit(self.store, role='researcher', task_domain='docs', write_scope=[])
        self.assertEqual(decision.action, 'ESCALATE')
        self.assertIsNone(child)
        self.gate.transition_atomic(self.store, 'a-0001', 'completed')
        decision, child = self.gate.evaluate_and_commit(self.store, role='researcher', task_domain='docs', write_scope=[])
        self.assertEqual(decision.action, 'SPAWN')

    def test_handoff_bounds(self):
        from runtime.reliability import bounded_handoff
        packet = dict(summary='done', evidence=['artifact:raw.log'], files=[], commands=[], risks=[], next_action='review')
        self.assertEqual(bounded_handoff(packet), packet)
        for bad in ({**packet, 'raw_log': 'dump'}, {**packet, 'summary': 'x' * 4097},
                    {**packet, 'evidence': ['x'] * 33}):
            with self.assertRaises(ValueError):
                bounded_handoff(bad)

    def test_corruption_observation_cannot_be_lost_during_reconnect(self):
        self.event('failure')
        self.event('failure', CORRUPT)
        self.assertEqual(self.store.load().assignments[0].recovery['reason'], 'TRANSPORT_CORRUPTION')

    def test_parallel_gate_reserves_only_two_children(self):
        def spawn(index):
            return self.gate.evaluate_and_commit(GoalStore(self.store.project, 'transport'),
                role='scout', task_domain='other-' + str(index), write_scope=[])[0].action
        with ThreadPoolExecutor(max_workers=4) as pool:
            actions = list(pool.map(spawn, range(4)))
        self.assertEqual(actions.count('SPAWN'), 1)
        self.assertEqual(len(self.store.load().assignments), 2)

    def test_pending_child_cannot_start_through_transition_during_reconnect(self):
        self.gate.evaluate_and_commit(self.store, role='scout', task_domain='other', write_scope=[])
        self.event('failure')
        with self.assertRaisesRegex(ValueError, 'barrier'):
            self.gate.transition_atomic(self.store, 'a-0002', 'running')

    def test_approved_terminal_resolution_releases_only_unrelated_work(self):
        self.event('failure', 'assertion failed')
        approval = self.flow.approve(self.store, 'transition:failed', 'a-0001', self.store.load().revision,
                                     'parent', 'parent owns escalation', 'artifact:stopped')
        self.gate.transition_atomic(self.store, 'a-0001', 'failed', approval['id'])
        self.assertEqual(self.store.load().assignments[0].recovery['phase'], 'resolved')
        self.assertEqual(self.gate.evaluate(self.store.load(), role='scout', task_domain='other', write_scope=[]).action, 'SPAWN')
        self.assertEqual(self.gate.evaluate(self.store.load(), role='scout', task_domain='api', write_scope=[]).action, 'ESCALATE')
        with self.assertRaises(ValueError):
            self.gate.transition_atomic(self.store, 'a-0001', 'running')

    def test_historical_task_reactivation_cannot_reset_resolved_budget(self):
        self.gate.transition_atomic(self.store, 'a-0001', 'completed')
        self.gate.evaluate_and_commit(self.store, role='scout', task_domain='api', write_scope=[],
                                      fresh_context=True, override_reason='independent evidence')
        self.event('failure', 'assertion failed', 'a-0002')
        approval = self.flow.approve(self.store, 'transition:failed', 'a-0002', self.store.load().revision,
                                     'parent', 'parent owns escalation', 'artifact:stopped')
        self.gate.transition_atomic(self.store, 'a-0002', 'failed', approval['id'])
        with self.assertRaisesRegex(ValueError, 'resolved'):
            self.gate.transition_atomic(self.store, 'a-0001', 'running')

    def test_barrier_cannot_be_bypassed_by_transition_or_stale_result(self):
        revision = self.store.load().revision
        self.event('failure')
        with self.assertRaises(ValueError):
            self.gate.transition_atomic(self.store, 'a-0001', 'completed')
        with self.assertRaises(RuntimeError):
            self.flow.transport(self.store, 'a-0001', 'resume-success', 'verified', revision)
        with self.assertRaises(ValueError):
            self.event('resume-success', 'verified')

    def test_configurable_cap_has_safe_bounds(self):
        from runtime.lifecycle import LifecyclePolicy
        import yaml
        root = Path(self.tmp.name)
        (root / 'config').mkdir()
        data = yaml.safe_load((ROOT / 'config/routing-policy.yaml').read_text())
        for value in (0, 5, True):
            data['limits']['default_max_active_children'] = value
            (root / 'config/routing-policy.yaml').write_text(yaml.safe_dump(data))
            with self.assertRaises(ValueError):
                LifecyclePolicy.from_repository(root)
