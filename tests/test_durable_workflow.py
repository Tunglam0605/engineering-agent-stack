from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import os
import unittest
from unittest.mock import patch

from runtime.lifecycle import GoalStore, LifecycleGate
from runtime.workflow import Workflow

ROOT = Path(__file__).resolve().parents[1]


def process_recover(project, approval):
    return Workflow(LifecycleGate(ROOT)).recover(GoalStore(Path(project), 'durable'), 'a-0001', approval)


class DurableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        (self.project / '.git').mkdir()
        self.store = GoalStore(self.project, 'durable')
        self.store.initialize()
        self.gate = LifecycleGate(ROOT)
        self.flow = Workflow(self.gate)
        self.gate.evaluate_and_commit(self.store, role='scout', task_domain='api', write_scope=[])

    def stale(self):
        state = self.store.load()
        state.assignments[0].updated_at = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        self.store.save(state)

    def approve(self, action='recover', target='a-0001'):
        return self.flow.approve(self.store, action, target, self.store.load().revision,
                                 'operator', 'executor reconciled', 'process exited; ticket 42')

    def test_checkpoint_durable_and_cas(self):
        rev = self.store.load().revision
        cp = self.flow.checkpoint(self.store, 'verify', {'tests': 'report:42'}, rev)
        self.assertEqual(GoalStore(self.project, 'durable').load().workflow['checkpoint'], cp)
        with self.assertRaisesRegex(RuntimeError, 'revision'):
            self.flow.checkpoint(self.store, 'review', {}, rev)

    def test_recovery_requires_approval_and_retries_are_idempotent(self):
        self.stale()
        before = self.store.state_path.read_bytes()
        self.assertEqual(self.flow.plan(self.store)['suspect'][0]['reason'], 'stale')
        self.assertEqual(before, self.store.state_path.read_bytes())
        with self.assertRaises(ValueError):
            self.flow.recover(self.store, 'a-0001', 'missing')
        approval = self.approve()
        first = self.flow.recover(self.store, 'a-0001', approval['id'])
        revision = self.store.load().revision
        self.assertEqual(first, self.flow.recover(self.store, 'a-0001', approval['id']))
        self.assertEqual(revision, self.store.load().revision)
        self.assertEqual(len(self.store.load().assignments), 1)

    def test_approval_is_bound_to_revision_target_and_expiry(self):
        self.stale()
        approval = self.approve()
        with self.assertRaises(ValueError):
            self.flow.recover(self.store, 'a-9999', approval['id'])
        self.flow.checkpoint(self.store, 'verify', {}, self.store.load().revision)
        with self.assertRaisesRegex(ValueError, 'revision'):
            self.flow.recover(self.store, 'a-0001', approval['id'])

    def test_suspect_gate_cannot_reuse_or_spawn(self):
        self.stale()
        result, _ = self.gate.evaluate_and_commit(self.store, role='scout', task_domain='api', write_scope=[])
        self.assertEqual(result.action, 'ESCALATE')
        with self.assertRaises(ValueError):
            self.gate.transition_atomic(self.store, 'a-0001', 'running')

    def test_risky_transition_requires_explicit_evidence(self):
        with self.assertRaisesRegex(ValueError, 'approval'):
            self.gate.transition_atomic(self.store, 'a-0001', 'failed')
        approval = self.approve('transition:failed')
        self.gate.transition_atomic(self.store, 'a-0001', 'failed', approval_id=approval['id'])
        self.assertEqual(self.store.load().assignments[0].state, 'failed')

    def test_concurrent_recovery_consumes_once(self):
        self.stale()
        approval = self.approve()
        def recover(_):
            return self.flow.recover(GoalStore(self.project, 'durable'), 'a-0001', approval['id'])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(recover, range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(len(self.store.load().workflow['receipts']), 1)

    def test_corruption_fails_closed(self):
        for change in ({'goal_id': 'other'}, {'workflow': None}, {'created_at': 'bad'}):
            original = self.store.state_path.read_bytes()
            payload = json.loads(original)
            payload.update(change)
            self.store.state_path.write_text(json.dumps(payload), encoding='utf-8')
            with self.assertRaises(ValueError):
                self.flow.plan(self.store)
            self.store.state_path.write_bytes(original)

    def test_export_contains_durable_evidence_and_marks_observation_corruption(self):
        self.flow.checkpoint(self.store, 'verify', {'review': 'ticket:42'}, self.store.load().revision)
        payload = self.flow.export(self.store)
        self.assertEqual(payload['state']['workflow']['checkpoint']['stage'], 'verify')
        self.assertFalse(payload['observations_transactional'])
        with self.store.event_path.open('a') as f:
            f.write('{broken')
        payload = self.flow.export(self.store)
        self.assertFalse(payload['observations_complete'])
        self.assertTrue(payload['warnings'])

    def test_process_recovery_consumes_once_and_preserves_identity(self):
        self.stale()
        approval = self.approve()
        with ProcessPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(process_recover, str(self.project), approval['id']) for _ in range(2)]
            results = [job.result(timeout=30) for job in jobs]
        self.assertEqual(results[0], results[1])
        state = self.store.load()
        self.assertEqual(len(state.workflow['receipts']), 1)
        self.assertEqual(state.assignments[0].assignment_id, 'a-0001')
        self.assertEqual(state.next_sequence, 2)
        self.assertEqual(self.flow.plan(self.store)['suspect'], [])

    def test_timeout_is_only_suspicion_and_recovery_resets_attempt_clock(self):
        state = self.store.load()
        state.assignments[0].created_at = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self.store.save(state)
        before = self.store.state_path.read_bytes()
        plan = self.flow.plan(self.store)
        self.assertEqual(plan['suspect'][0]['reason'], 'timeout')
        self.assertEqual(before, self.store.state_path.read_bytes())
        self.assertEqual(self.gate.summary(self.store.load())['active'], 1)
        approval = self.approve()
        self.flow.recover(self.store, 'a-0001', approval['id'])
        self.assertEqual(self.flow.plan(self.store)['suspect'], [])

    def test_empty_evidence_and_expired_approval_cannot_release_capacity(self):
        self.stale()
        with self.assertRaises(ValueError):
            self.flow.approve(self.store, 'recover', 'a-0001', self.store.load().revision,
                              'operator', 'reconciled', '')
        approval = self.approve()
        payload = json.loads(self.store.state_path.read_text())
        payload['workflow']['approvals'][0]['expires_at'] = '2000-01-01T00:00:00Z'
        self.store.state_path.write_text(json.dumps(payload))
        with self.assertRaises(ValueError):
            self.flow.recover(self.store, 'a-0001', approval['id'])
        self.assertEqual(self.store.load().assignments[0].state, 'pending')

    def test_failed_reactivation_and_running_reset_require_approval(self):
        self.gate.transition_atomic(self.store, 'a-0001', 'running')
        with self.assertRaisesRegex(ValueError, 'approval'):
            self.gate.transition_atomic(self.store, 'a-0001', 'pending')
        approval = self.approve('transition:failed')
        self.gate.transition_atomic(self.store, 'a-0001', 'failed', approval_id=approval['id'])
        with self.assertRaisesRegex(ValueError, 'approval'):
            self.gate.transition_atomic(self.store, 'a-0001', 'running')

    def test_corrupt_nested_evidence_and_sequence_fail_closed(self):
        self.flow.checkpoint(self.store, 'verify', {'test': 'report:42'}, self.store.load().revision)
        original = self.store.state_path.read_bytes()
        for mutate in (
            lambda p: p.update(next_sequence=1),
            lambda p: p['assignments'][0].update(updated_at='no-time'),
            lambda p: p['workflow'].update(approvals={}),
            lambda p: p['workflow']['checkpoint'].update(evidence=['bad']),
        ):
            payload = json.loads(original)
            mutate(payload)
            self.store.state_path.write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                self.flow.plan(self.store)
        self.store.state_path.write_bytes(original)

    def test_cli_checkpoint_approval_recovery_and_export(self):
        env = dict(os.environ, EAS_REPO=str(ROOT), PYTHONPATH=str(ROOT))
        def cli(*args):
            result = subprocess.run([sys.executable, '-m', 'eas_cli', 'goal', *args,
                                     '--project', str(self.project), '--json'], env=env,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)
        cli('checkpoint', 'durable', '--stage', 'verify', '--evidence', '{"tests":"report:42"}',
            '--revision', str(self.store.load().revision))
        self.stale()
        plan = cli('plan', 'durable')
        approval = cli('approve', 'durable', '--action', 'recover', '--target', 'a-0001',
                       '--revision', str(plan['revision']), '--approver', 'operator',
                       '--reason', 'reconciled', '--executor-stopped-evidence', 'process exited')
        recovered = cli('recover', 'durable', 'a-0001', '--approval', approval['id'])
        self.assertEqual(recovered['assignment_id'], 'a-0001')
        exported = cli('export', 'durable')
        self.assertEqual(exported['state']['assignments'][0]['state'], 'pending')
        self.assertFalse(exported['observations_transactional'])

    def test_old_receipt_never_rewinds_later_execution(self):
        approval = self.approve()
        receipt = self.flow.recover(self.store, 'a-0001', approval['id'])
        self.gate.transition_atomic(self.store, 'a-0001', 'running')
        before = self.store.state_path.read_bytes()
        self.assertEqual(self.flow.recover(self.store, 'a-0001', approval['id']), receipt)
        self.assertEqual(self.store.state_path.read_bytes(), before)
        self.assertEqual(self.store.load().assignments[0].state, 'running')

    def test_concurrent_checkpoints_have_one_cas_winner(self):
        revision = self.store.load().revision
        def checkpoint(stage):
            try:
                return self.flow.checkpoint(GoalStore(self.project, 'durable'), stage, {}, revision)['stage']
            except RuntimeError:
                return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(checkpoint, ['verify', 'review']))
        self.assertEqual(results.count('conflict'), 1)
        self.assertEqual(self.store.load().revision, revision + 1)

    def test_crash_left_lock_is_not_stolen(self):
        self.store.lock_path.write_text('{"pid":999999999}')
        before = self.store.state_path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'locked'):
            with self.store.locked(timeout_seconds=0.05, poll_seconds=0.01):
                self.fail('stole a lock')
        self.assertTrue(self.store.lock_path.exists())
        self.assertEqual(self.store.state_path.read_bytes(), before)

    def test_failed_flush_or_replace_preserves_committed_snapshot(self):
        for boundary in ('runtime.lifecycle.os.fsync', 'runtime.lifecycle.Path.replace'):
            with self.subTest(boundary=boundary):
                before = self.store.state_path.read_bytes()
                with patch(boundary, side_effect=OSError('disk failure')):
                    with self.assertRaises(OSError):
                        self.flow.checkpoint(self.store, 'verify', {}, self.store.load().revision)
                self.assertEqual(self.store.state_path.read_bytes(), before)
                self.assertFalse(self.store.lock_path.exists())

    def test_legacy_snapshot_migrates_only_on_mutation(self):
        payload = json.loads(self.store.state_path.read_text())
        payload['version'] = 1
        del payload['workflow']
        self.store.state_path.write_text(json.dumps(payload))
        before = self.store.state_path.read_bytes()
        self.assertIsNone(self.flow.plan(self.store)['checkpoint'])
        self.assertEqual(self.store.state_path.read_bytes(), before)
        self.flow.checkpoint(self.store, 'verify', {}, payload['revision'])
        self.assertEqual(json.loads(self.store.state_path.read_text())['version'], 2)

    def test_duplicate_json_keys_and_non_utf8_state_fail_closed(self):
        original = self.store.state_path.read_bytes()
        for content in (b'{"revision":0,' + original[1:], b'\xff'):
            self.store.state_path.write_bytes(content)
            with self.assertRaises(ValueError):
                self.flow.plan(self.store)
        self.store.state_path.write_bytes(original)

    def test_transition_receipt_consumes_once_without_reactivation(self):
        approval = self.approve('transition:failed')
        self.gate.transition_atomic(self.store, 'a-0001', 'failed', approval_id=approval['id'])
        second = self.approve('transition:running')
        self.gate.transition_atomic(self.store, 'a-0001', 'running', approval_id=second['id'])
        before = self.store.state_path.read_bytes()
        result = self.gate.transition_atomic(self.store, 'a-0001', 'failed', approval_id=approval['id'])
        self.assertEqual(result.state, 'failed')
        self.assertEqual(before, self.store.state_path.read_bytes())

    def test_suspect_cannot_be_cleared_by_ordinary_completion(self):
        self.stale()
        with self.assertRaisesRegex(ValueError, 'approval'):
            self.gate.transition_atomic(self.store, 'a-0001', 'completed')
        self.assertEqual(self.gate.summary(self.store.load())['active'], 1)

    def test_nonsuspect_heartbeat_refreshes_inactivity_without_resetting_attempt(self):
        self.gate.transition_atomic(self.store, 'a-0001', 'running')
        state = self.store.load()
        old = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        state.assignments[0].updated_at = old
        self.store.save(state)
        self.gate.transition_atomic(self.store, 'a-0001', 'running')
        current = self.store.load().assignments[0]
        self.assertNotEqual(current.updated_at, old)
        self.assertEqual(current.created_at, state.assignments[0].created_at)

    def test_missing_v2_revision_refuses_reads_and_writes_without_byte_changes(self):
        state = self.store.load()
        payload = json.loads(self.store.state_path.read_text())
        del payload['revision']
        self.store.state_path.write_text(json.dumps(payload))
        before = self.store.state_path.read_bytes()
        for operation in (
            lambda: self.store.load(),
            lambda: self.flow.plan(self.store),
            lambda: self.flow.export(self.store),
            lambda: self.flow.checkpoint(self.store, 'verify', {}, 0),
            lambda: self.store.save(state),
        ):
            with self.assertRaises(ValueError):
                operation()
            self.assertEqual(self.store.state_path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
