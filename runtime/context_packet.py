from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional


@dataclass(frozen=True)
class ContextEvidence:
    evidence_id: str
    source: str
    content: str
    required: bool = False
    priority: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not self.evidence_id.strip():
            raise ValueError("evidence_id must be a non-empty string")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string")
        if not isinstance(self.content, str):
            raise ValueError("content must be a string")
        if type(self.required) is not bool:
            raise ValueError("required must be a boolean")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise ValueError("priority must be an integer")


@dataclass(frozen=True)
class ContextPacket:
    task: str
    retained_evidence_ids: List[str]
    retained_evidence_count: int
    context_size_chars: int
    token_proxy: int


def render_context_prompt(task: str, evidence: Iterable[ContextEvidence]) -> str:
    if not isinstance(task, str) or not task:
        raise ValueError("task must be a non-empty string")
    items = list(evidence)
    if not all(isinstance(item, ContextEvidence) for item in items):
        raise ValueError("evidence must contain only ContextEvidence")
    blocks = [task.rstrip(), "", "CONTROLLED CONTEXT EVIDENCE:"]
    for item in items:
        blocks.extend(
            ["", f"--- {item.source} [{item.evidence_id}] ---", item.content.rstrip()]
        )
    return "\n".join(blocks).rstrip() + "\n"


def _measure(task: str, evidence: Iterable[ContextEvidence]) -> int:
    return len(render_context_prompt(task, evidence))


def build_context_packet(
    *,
    task: str,
    evidence: List[ContextEvidence],
    max_evidence_items: int,
    max_chars: int,
) -> ContextPacket:
    if not isinstance(task, str) or not task:
        raise ValueError("task must be a non-empty string")
    if not isinstance(evidence, list) or not all(isinstance(item, ContextEvidence) for item in evidence):
        raise ValueError("evidence must be a list of ContextEvidence")
    if not isinstance(max_evidence_items, int) or isinstance(max_evidence_items, bool):
        raise ValueError("max_evidence_items must be an integer")
    if not isinstance(max_chars, int) or isinstance(max_chars, bool):
        raise ValueError("max_chars must be an integer")
    if max_evidence_items < 0 or max_chars < 0:
        raise ValueError("context packet limits must be non-negative")
    if _measure(task, []) > max_chars:
        raise ValueError("task exceeds context packet character budget after rendering")
    ids = [item.evidence_id for item in evidence]
    if len(ids) != len(set(ids)):
        raise ValueError("context evidence ids must be unique")

    required = sorted(
        (item for item in evidence if item.required),
        key=lambda item: (-item.priority, item.evidence_id),
    )
    optional = sorted(
        (item for item in evidence if not item.required),
        key=lambda item: (-item.priority, item.evidence_id),
    )
    if len(required) > max_evidence_items:
        raise ValueError("required evidence count exceeds context packet item limit")

    selected: List[ContextEvidence] = []
    for item in required:
        trial = selected + [item]
        if _measure(task, trial) > max_chars:
            raise ValueError("required evidence exceeds context packet bounds: " + item.evidence_id)
        selected.append(item)

    for item in optional:
        if len(selected) >= max_evidence_items:
            break
        trial = selected + [item]
        if _measure(task, trial) <= max_chars:
            selected.append(item)

    size = _measure(task, selected)
    return ContextPacket(
        task=task,
        retained_evidence_ids=[item.evidence_id for item in selected],
        retained_evidence_count=len(selected),
        context_size_chars=size,
        token_proxy=(size + 3) // 4,
    )


def build_full_context_packet(*, task: str, evidence: List[ContextEvidence]) -> ContextPacket:
    if not isinstance(task, str) or not task:
        raise ValueError("task must be a non-empty string")
    if not isinstance(evidence, list) or not all(isinstance(item, ContextEvidence) for item in evidence):
        raise ValueError("evidence must be a list of ContextEvidence")
    ids = [item.evidence_id for item in evidence]
    if len(ids) != len(set(ids)):
        raise ValueError("context evidence ids must be unique")
    size = _measure(task, evidence)
    return ContextPacket(
        task=task,
        retained_evidence_ids=list(ids),
        retained_evidence_count=len(evidence),
        context_size_chars=size,
        token_proxy=(size + 3) // 4,
    )


def compare_context_strategies(
    *,
    experiment_id: str,
    task_id: str,
    task: str,
    evidence: List[ContextEvidence],
    max_evidence_items: int,
    max_chars: int,
    quality_hook: Optional[Callable[[ContextPacket], float]] = None,
) -> List[dict]:
    full = build_full_context_packet(task=task, evidence=evidence)
    bounded = build_context_packet(
        task=task,
        evidence=evidence,
        max_evidence_items=max_evidence_items,
        max_chars=max_chars,
    )
    rows = []
    for strategy, packet in (("full", full), ("bounded", bounded)):
        rows.append(
            {
                "experiment_id": experiment_id,
                "task_id": task_id,
                "strategy": strategy,
                "measurement": {
                    "context_size_chars": packet.context_size_chars,
                    "token_proxy": packet.token_proxy,
                    "retained_evidence_count": packet.retained_evidence_count,
                    "quality_score": quality_hook(packet) if quality_hook else None,
                    "latency_ms": None,
                    "tokens": None,
                },
            }
        )
    return rows
