"""Validation for durable workflow evidence; independent of execution providers."""
from datetime import datetime, timezone
import json
import re


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError('invalid JSON constant: ' + value)

    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be an ISO 8601 string')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError('timestamp requires timezone')
        return result.astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise ValueError('invalid timestamp: ' + value) from exc


def bounded_text(value, name='evidence', limit=4096):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(name + ' must be nonempty text of at most ' + str(limit) + ' characters')
    return value.strip()


def revision_number(value):
    if type(value) is not int or value < 0:
        raise ValueError('revision must be a non-negative integer')
    return value


def evidence_map(value):
    if not isinstance(value, dict) or len(value) > 32:
        raise ValueError('evidence must be an object with at most 32 references')
    for key, item in value.items():
        bounded_text(key, 'evidence key', 128)
        bounded_text(item)
    return dict(value)


def empty_workflow():
    return {'checkpoint': None, 'approvals': [], 'receipts': []}


def approval_action(value):
    if value not in {'recover', 'transition:pending', 'transition:running',
                     'transition:completed', 'transition:failed', 'transition:blocked'}:
        raise ValueError('unsupported approval action')
    return value


def validate_workflow(value, revision, assignment_ids):
    if not isinstance(value, dict) or set(value) != {'checkpoint', 'approvals', 'receipts'}:
        raise ValueError('workflow must contain checkpoint, approvals and receipts')
    try:
        cp = value['checkpoint']
        if cp is not None:
            if not isinstance(cp, dict):
                raise ValueError('checkpoint must be an object')
            bounded_text(cp['stage'], 'stage', 128)
            evidence_map(cp['evidence'])
            timestamp(cp['created_at'])
            if revision_number(cp['revision']) > revision:
                raise ValueError('checkpoint revision exceeds state revision')
        approvals = value['approvals']
        receipts = value['receipts']
        if not isinstance(approvals, list) or not isinstance(receipts, list):
            raise ValueError('approvals and receipts must be lists')
        by_id = {}
        for approval in approvals:
            if not isinstance(approval, dict):
                raise ValueError('approval must be an object')
            ident = approval['id']
            if not isinstance(ident, str) or not re.fullmatch(r'ap-[0-9a-f]{32}', ident) or ident in by_id:
                raise ValueError('invalid or duplicate approval id')
            by_id[ident] = approval
            approval_action(approval['action'])
            if approval['target'] not in assignment_ids:
                raise ValueError('approval target is not an assignment')
            for key in ('approver', 'reason', 'executor_stopped_evidence'):
                bounded_text(approval[key], key)
            if revision_number(approval['revision']) > revision:
                raise ValueError('approval revision exceeds state revision')
            timestamp(approval['created_at'])
            timestamp(approval['expires_at'])
        seen = set()
        for receipt in receipts:
            if not isinstance(receipt, dict):
                raise ValueError('receipt must be an object')
            ident = receipt['approval_id']
            approval = by_id.get(ident)
            if approval is None or ident in seen:
                raise ValueError('receipt requires a unique existing approval')
            seen.add(ident)
            if receipt['action'] != approval['action'] or receipt['assignment_id'] != approval['target']:
                raise ValueError('receipt binding mismatch')
            timestamp(receipt['created_at'])
            if not approval['revision'] < revision_number(receipt['revision']) <= revision:
                raise ValueError('receipt revision is invalid')
            expected = 'pending' if receipt['action'] == 'recover' else receipt['action'].split(':')[1]
            if receipt['state'] != expected:
                raise ValueError('receipt state mismatch')
            replacement = receipt.get('replacement_assignment_id')
            if replacement is not None and (receipt['action'] != 'recover'
                    or replacement not in assignment_ids or replacement == receipt['assignment_id']):
                raise ValueError('invalid replacement receipt target')
    except (KeyError, TypeError) as exc:
        raise ValueError('malformed workflow evidence') from exc
