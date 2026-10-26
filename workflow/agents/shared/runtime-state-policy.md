# Durable Runtime State

This policy defines the resumable control state for `sk-*` workflows. Apply it with
`orchestration-policy.md`. Durable product decisions remain in OpenSpec artifacts;
runtime state records only orchestration facts and references to those artifacts.

## Storage contract

Resolve the per-worktree root with `git rev-parse --git-path sk-workflow` and use:

```text
<runtime-root>/<change>/
├── events.jsonl  # authoritative append-only semantic history
├── state.json    # derived materialized projection
└── .state.lock   # helper-owned writer lock
```

Linked-worktree removal can delete this entire runtime root. Before cleanup, apply
`workspace-lifecycle.md`: quiesce writers, copy and verify the journal/projection
and evidence under `<common-dir>/sk-workflow-archive/<change>/<run-id>/`, and use
only that surviving `--runtime-dir` for subsequent cleanup/completion writes.
Keep historical paths in the journal intact; record the relocation map and current
artifact references. Never remove a worktree containing the sole copy of a run.

Use `runtime-state/sk_state.py` from this shared-policy directory. In the source
repository it is `workflow/agents/shared/runtime-state/sk_state.py`. The helper
requires Python 3.10 or newer and has no third-party runtime dependencies.

Resolve the interpreter once before the first helper command. Try `python3`, then
`python`, then the Windows launcher `py -3`; accept the first candidate for which
`import sys; sys.version_info >= (3, 10)` succeeds. Use that exact argv prefix as
`<python>` for the rest of the turn. If none succeeds, block with a Python 3.10+
installation requirement instead of editing the ledger manually.

Never edit `events.jsonl` or `state.json` directly. The global root owns workflow
state and invokes the helper. Only Full review may grant one named review
orchestrator a bounded nested-attempt writer lease under the protocol below; every
other child only returns compact results and artifact fingerprints. Quick and Micro
are root-writer-only.

For nested review, use one parked orchestrator bootstrap. First dispatch the review
orchestrator with an instruction to remain parked: it performs no review work,
dispatches no leaf, and writes no runtime state until it receives a lease envelope.
After successful dispatch returns the real host thread ID, the root records the task
and `start-attempt`, then runs `grant-review-lease` with a unique lease ID, the current stage, the running
orchestrator attempt ID, and a stable holder actor ID. The root then delivers the
runtime directory, current revision, stage, lease ID, and actor ID as the lease
envelope; only that delivery activates review work. The helper records
`review.lease.granted` in `writer_lease`; granting fails unless the run is Full and
the holder is a running `review-orchestrator` attempt in the review stage.

The child receives the runtime directory, revision, lease ID, and holder actor ID.
Every leased mutation uses `--actor-kind review-orchestrator --actor-id <holder>` and
CAS. The helper permits only nested task/attempt events, including batched task
creation, and the matching `review.lease.released` event in the leased stage. It rejects root writes, another
actor, another stage, and every stage/gate/check/artifact/blocker/control/completion
event while the lease is active. Each leased task and attempt records the holder's
`lease_holder_attempt_id`; a leased writer may start, finish, or attach a late result
only inside that lineage. Pre-existing sibling tasks and attempts remain root-owned
and cannot be mutated through the lease. Leaf children never write.

The holder runs `release-review-lease` before returning. The root then reloads and
validates before recording the orchestrator result. To detach, release first, let the
root record the detached join, and return the checkpoint. Foreground resume is a
transport action and writes no event; the root may then grant a new lease ID to the
same holder attempt. Persisted lineage remains valid across that release, detach,
and regrant; leases never survive a detached turn. If the holder host crashes while
a lease remains active, the root records
`release-review-lease --reason <evidence>`; the reason makes the exceptional root
recovery explicit. This only releases the writer lock, after which the root
reconciles and finishes or cancels the still-running holder and nested work.

The helper appends and fsyncs the event first, then writes and fsyncs a temporary
projection and atomically replaces `state.json`. `state.json` may therefore lag
after a crash but must never be ahead. `status` reports snapshot health; `repair`
preserves an incomplete JSONL tail and rebuilds the projection.

## State model

- `run` stores workflow identity and the policy revision pinned at start.
- `charter` stores its revision, route (`micro | quick | full`), assurance,
  authorization (`manual | checkpoints | yolo`), scope digest, requested/resolved
  workspace, destination, and visible budgets. It is authoritative across resume.
- `repositories` stores worktree, branch, and base identity per repository.
- `workflow.stages.<stage>.gates` stores user/authority decisions for that stage.
- `workflow.stages.<stage>.checks` stores verification outcomes, not approvals.
- `workflow.stages.<stage>.tasks.<task>.attempts` preserves every agent attempt. A
  task with `purpose` and `members` is a compact semantic batch: one `task.created`
  event materializes all successfully dispatched one-shot members with their host
  IDs and input fingerprints. Use it for Quick implementation/review batches and
  Full review leaf aggregation instead of a task/attempt event pair per leaf.
- Gates, checks, and attempts record the stage entry that produced them. A redo
  increments the entry; use a new gate ID, and only current-entry gates constrain
  current stage completion.
- `control` is a discriminated union: `ready`, `waiting_agents`, `waiting_user`,
  `blocked`, or `complete`.
- `artifacts` stores paths and SHA-256 fingerprints, never full artifact contents.
- `delivery` records the pending or completed terminal action and its evidence.
- `revision` equals the last applied event sequence.

Current projections use state schema v3 and new journal events use event schema v2.
The helper can replay legacy event-schema-v1 history and normalize it into a v3
projection. Do not infer a missing charter from conversation history.

Use logical attempt IDs as durable references. Host thread IDs such as Codex agent
paths are transport metadata inside an attempt and may not survive a new client.

## Mutation rules

Every mutation after `init` requires:

```text
--expected-revision <state revision>
--command-id <stable semantic operation ID>
```

The revision is an optimistic-concurrency precondition. Reuse the same command ID
only to retry the exact same operation after an uncertain result; the helper returns
the existing event without duplicating it. Never reuse it for changed data.

Record semantic transitions only:

- workflow/stage start and completion;
- gate request and decision;
- logical task/attempt or compact batched-task dispatch/result;
- verification check and artifact fingerprint;
- explicit detach, user wait, blocker, and final completion.

Foreground host waiting, including the first wait and every continuation after a
partial result or timeout, is transport-only. `wait-agents --join foreground`
validates the active set and returns the unchanged projection; it does not append an
event or increment the revision. Do not record status reads, mailbox polling,
commentary, raw prompts, full child returns, tool calls, or logs. Notifications and
UI status remain observability, not workflow evidence.

Older journals may contain `workflow.waiting_for_agents` with `join=foreground`;
replay continues to accept those events, but the current CLI never emits another
one. Only `join=detached` is a new durable transition.

## Command sequence

Initialize once:

```bash
<python> <shared>/runtime-state/sk_state.py init \
  --runtime-dir <runtime-root>/<change> \
  --change <change> --workflow sk-team \
  --policy-revision <skills commit-or-fingerprint> \
  --repository-json '<JSON object>' \
  --route <micro|quick|full> \
  --assurance <standard|elevated> \
  --authorization <manual|checkpoints|yolo> \
  --scope-sha256 <digest> \
  --workspace <current|worktree|auto> \
  --workspace-resolved <pending|current|worktree> \
  --destination <local|commit|pr|merge|deploy>
```

Add `--workspace-path` after resolution and `--destination-target` for PR, merge,
or deploy. The route supplies default attempt/review/remediation budgets; explicit
budget flags may override them when the charter says so. Direct legacy invocations
of `sk-team-feature`/`sk-team-quick` remain parseable but should resolve a charter
and initialize `sk-team` for new runs.

Use the following semantic commands as the workflow advances:

```text
enter-stage       complete-stage
request-gate      decide-gate
create-task       start-attempt       finish-attempt
record-late-result
record-check      record-artifact
wait-agents       wait-user
block             resolve-blocker     complete
grant-review-lease    release-review-lease
change-authorization  change-scope
resolve-workspace     change-destination
escalate-route        record-terminal
```

Run `<python> <shared>/runtime-state/sk_state.py <command> --help` for exact options.
Use `status` for a JSON projection plus `snapshot_status`, `history` for JSONL
events, and `validate` before resume, phase approval, archive, or handoff.

Tasks and checks are required by default. A successful stage requires every
required task and required check from its current entry to have succeeded or
passed. Use `--optional` only for explicitly non-blocking work; optional failures
remain visible but do not prevent successful stage closure. Micro may close a stage
with no task, attempt, join, or lease when the root performed and verified the
work itself.

After all successful host dispatches in a batch return real thread IDs, record one
`create-task --purpose <purpose>` with one `--member-json` envelope per child. Each
member requires its own immutable `input_fingerprint`. Record each observed result
with `finish-attempt`; the supplied input fingerprint must match dispatch, and every
successful result requires a result SHA-256. If an artifact path exists locally,
the helper verifies its bytes against that digest before append. Legacy long-lived
work may still use task/attempt commands, but new v2 attempt dispatch/result events
have the same mandatory fingerprint rules.

Call `wait-agents --join foreground` only to validate the complete running attempt
set before entering the host wait primitive. It never writes runtime
state, including after partial completion. `wait-agents --join detached` is the only
durable agent-wait transition; result recording drains its references and restores
`ready` when the detached set finishes.

Use `wait-agents --join detached --detach-reason <code>` only for a detach reason
allowed by `orchestration-policy.md`.

## Gates, checks, attempts, and stops

- A **gate** is typed as `ceremony`, `authority_decision`, `sensitive_action`, or
  `terminal_action`. The charter may auto-decide ceremony; it never manufactures
  authority for the other three.
- A **check** is observed evidence such as TDD Red, lint, review, or acceptance.
- An **attempt** is one execution of one logical task by one agent thread.
- A **batch** is a task with a purpose and successfully dispatched one-shot members.
  Its members count against the attempt budget; review and remediation batches also
  count against their respective budgets. Exhausted budgets reject new dispatches.

Do not represent a gate as a check, infer approval from a passing check, or overwrite
an old attempt during retry/remediation. A late result for a terminal/cancelled
attempt uses `record-late-result` and never reopens the attempt or stage.

Every user wait or blocker carries a stable reason code from
`workflow-charter-policy.md`. Ceremony gates in YOLO are immediately recorded with
`decision_source=policy`; authority/sensitive/terminal gates remain pending. Before
`complete`, `record-terminal` must store a successful receipt matching the charter's
destination and target.

## Resume and migration

On resume, run `status` and follow this fail-closed matrix. A repairable row requires
a valid non-empty journal; `status` proves that condition by successfully replaying
the journal and reporting a positive `journal_events` count.

| `snapshot_status` | Journal condition | Required action |
|---|---|---|
| `valid` | valid non-empty journal | Run `validate`, then use the projection. |
| `stale` or `diverged` | valid non-empty journal | Run `repair`, then `validate`. |
| `missing` | valid non-empty journal | Run `repair`, then `validate`. |
| `legacy_v1` | no committed journal | Run `migrate-v1`, then `validate`. |
| `legacy_v1` | valid non-empty journal | Run `repair`, then `validate`. |
| `legacy_v2` | no committed journal | Run `migrate-v2`, then `validate`. |
| `legacy_v2` | valid non-empty journal | Run `repair`, then `validate`. |
| `orphaned`, or `missing`/`diverged` without history | no valid non-empty journal | Fail closed with `recover-journal-or-reinitialize`; recover the journal or explicitly reinitialize and reconfirm approvals, constraints, stage, tasks, and results. |
| `unsupported_schema` | any | Fail closed with `require-compatible-helper`; do not repair or mutate the projection. |

The complete status vocabulary is valid | stale | diverged | missing | orphaned | legacy_v1 | legacy_v2 | unsupported_schema.
Do not infer state from an orphaned projection or manually edit either
file. After validation, reconcile running attempt host IDs with the
host mailbox and record newly observed results before dispatching new work. An
active writer lease is never silently cleared: prove holder loss, use
`release-review-lease --reason <evidence>`, then reconcile its lineage.

For a legacy `schema_version: 1` ledger, run `migrate-v1` with the workflow name and
current policy revision. Migration preserves the original as `state.v1.json`, starts
the semantic journal with `workflow.migrated_from_v1`, and normalizes legacy
foreground/background wait state. If `phase: background_work_active` does not retain
the real stage in its checkpoint, reconcile the mailbox and pass that proven stage as
`--legacy-stage`; never guess it. A legacy state combining unresolved blockers and
running agents must be reconciled before migration because v2 gives control to only
one condition at a time. Validate before continuing. Never interpret a newer
unsupported schema or event version; stop with `require-compatible-helper`, preserve
the projection byte-for-byte, and require a compatible helper.

For a legacy `schema_version: 2` projection without a committed journal, run
`migrate-v2`. Migration preserves `state.v2.json`, creates the semantic
`workflow.migrated_from_v2` event, derives a conservative charter from the legacy
workflow, and initializes pending delivery. Review the derived charter before
continuing; use explicit charter transition commands for any correction. When valid
history already exists, use `repair` so replay—not the stale projection—remains the
authority.

The machine-readable contracts are `runtime-state/state.schema.json` and
`runtime-state/event.schema.json`.
