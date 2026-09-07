# Context Management Pattern

## Goal

Keep the parent context authoritative while avoiding repeated transmission of irrelevant repository history, logs and source text.

## Rules

- Send task-specific context, not the entire parent conversation.
- Prefer file/symbol references to copied source when the worker can read the repository.
- Return findings, evidence, confidence and handoff—not a transcript.
- Do not dump full logs when the failing lines and command are sufficient.
- Bound reviewer input to the plan/diff/evidence required for the review.

## Preferred worker result

```text
finding
location / evidence
impact
confidence
recommended handoff
validation gap (if any)
```
