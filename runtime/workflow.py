"""Stack-controlled checkpoint and recovery transactions, never native dispatch."""
from datetime import datetime, timedelta, timezone
import uuid

from .lifecycle import ACTIVE_STATES, GoalStore, LifecycleGate, _utc_now
from .workflow_state import approval_action, bounded_text, evidence_map, revision_number, strict_json, timestamp
from .reliability import bounded_handoff, classify_failure


class Workflow:
    def __init__(self, gate: LifecycleGate):
        self.gate = gate

    @staticmethod
    def check_revision(state, expected):
        revision_number(expected)
        if state.revision != expected:
            raise RuntimeError('goal revision changed; re-read plan before retrying')

    def checkpoint(self, store: GoalStore, stage, evidence, revision):
        stage = bounded_text(stage, 'stage', 128)
        evidence = evidence_map(evidence)
        with store.locked():
            state = store._load_unlocked()
            self.check_revision(state, revision)
            checkpoint = {'stage': stage, 'evidence': evidence, 'created_at': _utc_now(),
                          'revision': state.revision + 1}
            state.workflow['checkpoint'] = checkpoint
            store._save_unlocked(state)
            return checkpoint

    def plan(self, store: GoalStore):
        state = store.load()
        return {'goal_id': state.goal_id, 'revision': state.revision,
                'checkpoint': state.workflow['checkpoint'], 'suspect': self.gate.suspects(state),
                'recovery': {a.assignment_id: a.recovery for a in state.assignments if a.recovery},
                'recovery_requires': ['revision-scoped approval', 'prior executor stopped evidence'],
                'dispatch_authorized': False}

    def approve(self, store: GoalStore, action, target, revision, approver, reason,
                executor_stopped_evidence):
        action = approval_action(action)
        approver = bounded_text(approver, 'approver')
        reason = bounded_text(reason, 'reason')
        evidence = bounded_text(executor_stopped_evidence, 'executor_stopped_evidence')
        with store.locked():
            state = store._load_unlocked()
            self.check_revision(state, revision)
            if target not in {item.assignment_id for item in state.assignments}:
                raise ValueError('approval target is not an assignment')
            now = datetime.now(timezone.utc)
            approval = {'id': 'ap-' + uuid.uuid4().hex, 'action': action, 'target': target,
                        'revision': state.revision + 1, 'approver': approver, 'reason': reason,
                        'executor_stopped_evidence': evidence, 'created_at': now.isoformat(),
                        'expires_at': (now + timedelta(seconds=self.gate.policy.approval_ttl_seconds)).isoformat()}
            state.workflow['approvals'].append(approval)
            store._save_unlocked(state)
            return approval

    @staticmethod
    def receipt(state, approval_id, action, target):
        for receipt in state.workflow['receipts']:
            if receipt['approval_id'] == approval_id:
                if receipt['action'] != action or receipt['assignment_id'] != target:
                    raise ValueError('approval receipt action/target mismatch')
                return dict(receipt)
        return None

    @staticmethod
    def require_approval(state, approval_id, action, target):
        approval = next((a for a in state.workflow['approvals'] if a['id'] == approval_id), None)
        if approval is None:
            raise ValueError('explicit approval with prior executor stopped evidence is required')
        if approval['action'] != action or approval['target'] != target:
            raise ValueError('approval action/target mismatch')
        if approval['revision'] != state.revision:
            raise ValueError('approval revision no longer matches state')
        if timestamp(approval['expires_at']) <= datetime.now(timezone.utc):
            raise ValueError('approval has expired')
        bounded_text(approval['executor_stopped_evidence'], 'executor_stopped_evidence')
        return approval

    @staticmethod
    def record_receipt(state, approval_id, action, assignment):
        receipt = {'approval_id': approval_id, 'action': action,
                   'assignment_id': assignment.assignment_id, 'state': assignment.state,
                   'revision': state.revision + 1, 'created_at': _utc_now()}
        state.workflow['receipts'].append(receipt)
        return dict(receipt)

    def recover(self, store: GoalStore, assignment_id, approval_id):
        with store.locked():
            state = store._load_unlocked()
            receipt = self.receipt(state, approval_id, 'recover', assignment_id)
            if receipt:
                if 'replacement_assignment_id' in receipt:
                    raise ValueError('approval already used for replacement')
                return receipt
            self.require_approval(state, approval_id, 'recover', assignment_id)
            item = next((a for a in state.assignments if a.assignment_id == assignment_id), None)
            if item is None or item.state not in ACTIVE_STATES:
                raise ValueError('recovery requires an active assignment; use approved transition for terminal state')
            if self.gate.resolved_task(state, item.role, item.task_domain, item.write_scope):
                raise ValueError('resolved failed task remains with parent; cannot reset recovery budget')
            if item.recovery:
                recovery = item.recovery
                if recovery['phase'] != 'resume-ready' or recovery['resumes'] >= 2 or recovery['replacements']:
                    raise ValueError('resume budget exhausted or recovery is not resume-ready; escalate to parent')
                recovery['resumes'] += 1
                recovery['phase'] = 'resuming'
            # Operator evidence permits reconciliation even before the suspicion threshold.
            item.state = 'pending'
            item.updated_at = _utc_now()
            item.attempt_started_at = item.updated_at
            receipt = self.record_receipt(state, approval_id, 'recover', item)
            store._save_unlocked(state)
            return receipt

    def transport(self, store, assignment_id, event, evidence, revision):
        """Record parent-observed failures/results; never resume or spawn natively."""
        evidence = bounded_text(evidence)
        if event not in {'failure', 'resume-success', 'resume-failed'}:
            raise ValueError('unsupported transport event')
        with store.locked():
            state = store._load_unlocked()
            self.check_revision(state, revision)
            item = next((a for a in state.assignments if a.assignment_id == assignment_id), None)
            if item is None or item.state not in ACTIVE_STATES:
                raise ValueError('transport observation requires an active assignment')
            recovery = item.recovery
            if event == 'failure':
                reason = classify_failure(evidence)
                if recovery and recovery['phase'] != 'healthy':
                    # Reconnecting notifications do not start a new attempt or reset budgets.
                    if reason == 'TRANSPORT_CORRUPTION' and recovery['reason'] == 'TRANSIENT_TRANSPORT':
                        recovery.update(reason=reason, evidence=evidence)
                        store._save_unlocked(state)
                    return dict(recovery)
                recovery = dict(recovery or {'resumes': 0, 'replacements': 0, 'handoff': None})
                recovery.update(reason=reason, evidence=evidence, phase='resume-ready')
                if reason == 'AGENT_FAILURE' or recovery['replacements'] or recovery['resumes'] >= 2:
                    recovery['phase'] = 'escalated'
            else:
                if not recovery or recovery['phase'] != 'resuming':
                    raise ValueError('resume result requires an outstanding resume')
                recovery = dict(recovery)
                recovery['evidence'] = evidence
                if event == 'resume-success':
                    recovery['phase'] = 'healthy'
                else:
                    reason = classify_failure(evidence)
                    if reason == 'AGENT_FAILURE':
                        recovery.update(reason=reason, phase='escalated')
                    else:
                        if reason == 'TRANSPORT_CORRUPTION':
                            recovery['reason'] = reason
                        recovery['phase'] = ('replacement-ready' if recovery['reason'] == 'TRANSPORT_CORRUPTION'
                                             or recovery['resumes'] >= 2 else 'resume-ready')
            item.recovery = recovery
            store._save_unlocked(state)
            return dict(recovery)

    def replace_child(self, store, assignment_id, approval_id, handoff):
        handoff = bounded_handoff(handoff)
        with store.locked():
            state = store._load_unlocked()
            receipt = self.receipt(state, approval_id, 'recover', assignment_id)
            if receipt:
                if 'replacement_assignment_id' not in receipt:
                    raise ValueError('approval already used for resume')
                return {'assignment_id': receipt['replacement_assignment_id'], 'dispatch_authorized': False}
            self.require_approval(state, approval_id, 'recover', assignment_id)
            item = next((a for a in state.assignments if a.assignment_id == assignment_id), None)
            if (item is None or item.state not in ACTIVE_STATES or not item.recovery
                    or item.recovery['phase'] != 'replacement-ready' or item.recovery['replacements']):
                raise ValueError('single replacement requires failed resume; otherwise escalate to parent')
            # Evaluate against the retired executor, in memory, before committing anything.
            item.state = 'failed'
            item.recovery['phase'] = 'replaced'
            decision = self.gate.evaluate(state, role=item.role, task_domain=item.task_domain,
                                          write_scope=item.write_scope, change_set=item.change_set)
            if decision.action != 'SPAWN':
                raise ValueError('replacement blocked by lifecycle policy: ' + '; '.join(decision.reasons))
            from .lifecycle import GoalAssignment
            child = GoalAssignment(assignment_id=decision.proposed_assignment_id, role=item.role,
                                   task_domain=item.task_domain, state='pending', write_scope=list(item.write_scope),
                                   change_set=item.change_set,
                                   recovery={**item.recovery, 'phase': 'healthy', 'replacements': 1, 'handoff': handoff})
            state.assignments.append(child)
            state.next_sequence += 1
            # Existing recover receipt format binds approval to its original assignment.
            receipt = self.record_receipt(state, approval_id, 'recover', item)
            state.workflow['receipts'][-1].update(state='pending', replacement_assignment_id=child.assignment_id)
            store._save_unlocked(state)
            return {'assignment_id': child.assignment_id, 'dispatch_authorized': False}

    def export(self, store: GoalStore):
        with store.locked():
            state = store._load_unlocked()
            observations = []
            warnings = []
            complete = True
            try:
                lines = store.event_path.read_text(encoding='utf-8').splitlines()
            except (OSError, UnicodeError) as exc:
                lines = []
                complete = False
                warnings.append('Observational JSONL unavailable: ' + str(exc))
            for number, line in enumerate(lines, 1):
                try:
                    record = strict_json(line)
                    if (not isinstance(record, dict) or record.get('goal_id') != state.goal_id
                            or not isinstance(record.get('payload'), dict)):
                        raise ValueError('invalid observation record')
                    timestamp(record['time'])
                    bounded_text(record['event'], 'event')
                    observations.append(record)
                except (ValueError, KeyError, TypeError) as exc:
                    complete = False
                    warnings.append('Invalid observational JSONL line {}: {}'.format(number, exc))
            return {'format': 'eas-goal-trace', 'version': 1, 'state': state.as_dict(),
                    'state_authoritative': True, 'observations': observations,
                    'observations_transactional': False, 'observations_complete': complete,
                    'observations_completeness_scope': 'readable records only; missing events cannot be detected',
                    'warnings': warnings}
