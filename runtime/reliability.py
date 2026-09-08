"""Bounded orchestration evidence, not a provider transport implementation."""
import json
import re

from .workflow_state import bounded_text

REASONS = {'TRANSIENT_TRANSPORT', 'TRANSPORT_CORRUPTION', 'AGENT_FAILURE'}
PHASES = {'healthy', 'resume-ready', 'resuming', 'replacement-ready', 'replaced', 'escalated', 'resolved'}


def classify_failure(message):
    text = bounded_text(message, 'failure evidence').casefold()
    if 'encrypted function output' in text and ('decrypt' in text or 'decod' in text):
        return 'TRANSPORT_CORRUPTION'
    if ( 'stream disconnected before completion' in text
            or re.search(r'reconnecting\s+\d+\s*/\s*\d+', text)
            or re.search(r'(connection|transport)[\s_-]*(?:closed|reset|aborted)', text)
            or 'econnreset' in text):
        return 'TRANSIENT_TRANSPORT'
    return 'AGENT_FAILURE'


def bounded_handoff(value):
    fields = {'summary', 'evidence', 'files', 'commands', 'risks', 'next_action'}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('handoff requires summary/evidence/files/commands/risks/next_action only')
    result = {}
    for key in fields:
        if key in {'summary', 'next_action'}:
            result[key] = bounded_text(value[key], key)
        else:
            if not isinstance(value[key], list) or len(value[key]) > 32:
                raise ValueError(key + ' requires at most 32 entries')
            result[key] = [bounded_text(item, key, 1024) for item in value[key]]
    if len(json.dumps(result, ensure_ascii=False)) > 16384:
        raise ValueError('handoff exceeds 16384 characters; reference raw logs by artifact/path')
    return result


def validate_recovery(value):
    if value is None:
        return
    if not isinstance(value, dict) or set(value) != {'reason', 'evidence', 'phase', 'resumes', 'replacements', 'handoff'}:
        raise ValueError('invalid recovery evidence fields')
    if value['reason'] not in REASONS or value['phase'] not in PHASES:
        raise ValueError('invalid recovery reason/phase')
    bounded_text(value['evidence'])
    for key, maximum in (('resumes', 2), ('replacements', 1)):
        if type(value[key]) is not int or not 0 <= value[key] <= maximum:
            raise ValueError('invalid recovery budget: ' + key)
    if value['handoff'] is not None:
        bounded_handoff(value['handoff'])
