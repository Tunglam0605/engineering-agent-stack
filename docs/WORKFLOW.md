# Durable workflow and recovery

v0.5.0 stores parent-stage checkpoints, approval attestations and consumption receipts in the same atomic snapshot as assignments. State lives in Git metadata (`.git/eas/goals`, or the worktree's resolved Git directory), so goal operations do not dirty source files. Python 3.9 remains supported.

## Checkpoint and inspect

```sh
eas goal init shipping
eas goal gate shipping --role scout --domain api --commit
eas goal status shipping --json
eas goal checkpoint shipping --stage verify --evidence '{"tests":"report:42","review":"ticket:43"}' --revision 2
eas goal plan shipping --json
```

Use the actual revision returned by status/plan, not a previously cached value. Stage names are limited to 128 characters. Evidence is a JSON object with at most 32 references, 128-character keys and 4096-character nonempty string values. Store references instead of logs, transcripts or secrets. A checkpoint records where the parent should resume investigation; it never rewinds assignments, restores files or authorizes dispatch.

Pending/running assignments are suspect after 3600 seconds without an update or 86400 seconds of attempt age, as configured in `config/routing-policy.yaml`. Read-only status/plan computes suspicion without mutation. Timeout takes precedence when both thresholds apply. Suspects remain active and reserve capacity. The gate escalates while any assignment is suspect. A same-state transition can serve as a heartbeat before suspicion, but cannot clear suspicion afterward.

## Reconcile an interrupted executor

First establish that the previous executor has stopped using explicit external evidence: for example, a process exit observation or a provider termination receipt. Silence, a stale timestamp, a timeout, an absent JSONL spawn event or a checkpoint alone is insufficient evidence.

```sh
eas goal plan shipping --json
eas goal approve shipping --action recover --target a-0001 --revision 3 --approver operator --reason "Interrupted executor reconciled" --executor-stopped-evidence "Provider termination receipt ticket:44"
eas goal recover shipping a-0001 --approval ap_REPLACE_WITH_RETURNED_ID --json
eas goal status shipping --json
eas goal export shipping > shipping-trace.json
```

Replace the example revision and approval ID with the returned values. Approval issuance itself advances the revision by one; the approval binds to that resulting snapshot, its action and assignment. Any intervening durable mutation invalidates unused approval. Approval expires after 900 seconds. A rejection requires a fresh plan and fresh explicit attestation, not an automatic retry with new approval.

Recovery atomically consumes approval, returns the same assignment to pending and starts a new attempt clock. Original assignment creation time, role, domain, scope, ID and goal assignment count remain unchanged. Recovery is permitted before a suspicion threshold when the operator has stopped-executor evidence. Terminal assignments use an approved transition instead. No process is killed and no provider call or task dispatch occurs.

A consumed approval returns its original receipt on retry without another mutation, even if execution has since advanced. Receipts are historical acknowledgements, not fresh dispatch authorizations. An orchestrator must track dispatch separately; neither a recovery receipt nor `REUSE` grants permission to start duplicate executors. Check current status before continuing.

## Risky lifecycle transitions

Pass `--approval ID` to `eas goal transition`. The approval action is `transition:STATE`. Approval with stopped-executor evidence is required for active-to-failed/blocked transitions, changes out of failed/blocked, running-to-pending reset, and every transition of a suspect assignment. Reactivation still checks capacity and same-scope conflicts. Ordinary nonsuspect pending/running completion remains supported without approval.

Approval fields are explicit local operator attestations. EAS checks their presence, binding, expiry and consumption; it does not authenticate the named person or independently verify the evidence. Filesystem access to the metadata directory is the trust boundary. Protect it accordingly. This policy covers stack-controlled goal operations, not unrelated shell commands, `eas uninstall`, native provider APIs or arbitrary edits to metadata.

## Durability and export

Each mutation holds the existing per-goal exclusive lock, checks revision/CAS, flushes and fsyncs a temporary snapshot, and atomically replaces state. POSIX also fsyncs the containing directory. Filesystem/platform guarantees still apply; this is not replicated storage. Corrupt state fails closed. v1 snapshots are validated and migrated to v2 only on mutation. Do not downgrade a checkout that needs to mutate v2 goal state.

The `.lock` file is never automatically stolen, even if its recorded PID appears absent. After a crash, independently establish the owning EAS process has exited before manually removing only that goal's lock. A leftover `.json.tmp` is not a recovery source. Preserve corrupt state for investigation; do not reconstruct or roll back from checkpoints or JSONL.

`export` always emits JSON (`format=eas-goal-trace`, `version=1`). `state` is authoritative durable state, including checkpoint and approvals/receipts. `observations` contains readable JSONL records; `observations_transactional=false` is permanent. `observations_complete` only reports whether the available file could be fully read and parsed. Even true does not prove all events were delivered. Missing or malformed observational data yields warnings without replacing durable state. Checkpoint/recovery evidence is in the snapshot and need not have a corresponding JSONL event.

Keep exported traces private when evidence references contain operational details. All enforcement is opt-in stack-controlled behavior. EAS does not transparently intercept native spawning, terminate executors, authenticate approval identities or promise exactly-once external execution.

## Transport and session recovery (v0.6.3)

EAS cannot intercept Codex App reconnects or repair upstream encrypted stream decoding.
The parent must report observed failures through these orchestration contracts. Classification
recognizes stream disconnection, reconnect counters, closed/reset connections or transports,
and encrypted function-output decoding corruption. Unrecognized failures remain `AGENT_FAILURE`.
This is a failure category, not proof that reasoning caused an unrecognized error.

```sh
eas goal plan shipping --json
eas goal transport shipping a-0001 --event failure --revision 4 --evidence "Reconnecting 5/5" --json
```

Use the current revision from plan. `TRANSIENT_TRANSPORT` and `TRANSPORT_CORRUPTION` enter
`resume-ready`; `AGENT_FAILURE` escalates to the parent. A reconnect notification does not
release capacity, reset budgets, or create a child. Unresolved recovery blocks ordinary dispatch
and direct transitions back to active/completed states. Record stopped-executor evidence using
the existing `approve --action recover`, then `recover` to enter `resuming`. The parent may
resume the existing native child only after reconciling its executor; EAS issues no native calls.
After verifying the outcome, record `transport --event resume-success` or `resume-failed`
with the current revision and bounded evidence. Success enters `healthy`.

A failed transient resume permits another resume, up to two total in the assignment lineage.
Failed corruption recovery, or the second failed transient resume, enters `replacement-ready`.
Further resume attempts are rejected and require parent escalation. The parent may use the
single bounded replacement fallback only with a valid handoff and a fresh stopped-executor
approval. Missing evidence or a lifecycle rejection leaves the barrier in place; work returns
to the parent. Budget counters survive successful resumes and replacement. Any replacement
failure escalates; there is no recursive respawn loop.

After escalation, the parent can approve `transition:failed` or `transition:blocked` with
stopped-executor evidence. That terminal reconciliation enters `resolved` and releases the
goal-wide barrier for unrelated work. The failed role/domain/scope stays with the parent:
ordinary reactivation or a new assignment for that same task cannot reset its recovery budget.
Replaced and resolved assignments cannot be revived through ordinary transitions.

```json
{"summary":"Inspect API behavior","evidence":["artifact:checks.txt"],"files":["src/api.py"],"commands":["python -m unittest"],"risks":["Prior output was corrupt"],"next_action":"Recheck API from files and evidence"}
```

Save this bounded checkpoint/handoff as `handoff.json`, approve recovery after establishing that
the previous executor stopped, then run:

```sh
eas goal replace-child shipping a-0001 --approval ap_REPLACE_WITH_RETURNED_ID --handoff handoff.json --json
```

Replacement atomically retires the old assignment and reserves one new pending assignment with
the same role/domain/write scope/change set. It counts toward ordinary fanout and role budgets;
no exception or approval rule is weakened. Its handoff and inherited counters are durable.
The historical receipt is idempotent and has `dispatch_authorized: false`; it is not a token
to repeatedly dispatch. The parent still runs delegation preflight and tracks native dispatch.

The handoff/result packet requires exactly `summary`, `evidence`, `files`, `commands`, `risks`,
and `next_action`. Text fields allow 4096 characters; lists allow 32 entries of 1024 characters;
the serialized JSON allows 16384 characters total. Oversized packets fail, rather than silently
dropping required evidence. Reference large logs by path/artifact. Do not inject full transcripts.
The CLI limits handoff files to 65536 bytes before parsing. The existing explicit trace export
is an operator diagnostic and remains separate from child handoffs.

The existing routing policy now limits total active children to two by default, configurable
only within 1..4 through `limits.default_max_active_children`. Reader/writer, same-scope, review,
approval and fanout constraints still apply. At capacity, wait for completion/reconciliation,
integrate returned evidence, then re-evaluate the next bounded batch. No background scheduler
or queue is added. Seven defined roles never imply seven simultaneous children.

Recovery fields are optional for legacy snapshots. Use v0.6.3 or later to mutate snapshots with
transport recovery evidence: older code does not understand those barriers or budgets.
