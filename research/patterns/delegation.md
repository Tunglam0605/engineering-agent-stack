# Delegation Pattern

## Default

Work directly when one agent can safely understand, execute and verify the task without significant context churn.

## Delegate when

- independent exploration can reduce the main context
- multiple read-heavy questions can run in parallel
- a specialist lens materially changes expected quality
- independent review is required
- the task has separable write scopes

## Do not delegate when

- the task is trivial or touches one obvious location
- orchestration overhead is larger than the work
- workers would need nearly the same full context as the parent
- writers would contend for the same files
- the only purpose is to "use more agents"

## Worker contract

A worker receives a bounded objective, scope, evidence expectations and stop condition. It reports findings upward rather than recursively expanding the workflow.
