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

Use `runtime-state/sk_state.py` from this shared-policy directory. In the source
repository it is `workflow/agents/shared/runtime-state/sk_state.py`. The helper
requires Python 3.10 or newer and has no third-party runtime dependencies.

Resolve the interpreter once before the first helper command. Try `python3`, then
`python`, then the Windows launcher `py -3`; accept the first candidate for which
`import sys; sys.version_info >= (3, 10)` succeeds. Use that exact argv prefix as
`<python>` for the rest of the turn. If none succeeds, block with a Python 3.10+
installation requirement instead of editing the ledger manually.

Never edit `events.jsonl` or `state.json` directly. The global root owns workflow
state and invokes the helper. It may grant one named review orchestrator a bounded
nested-attempt writer lease under the protocol below; every other child only returns
compact results and artifact fingerprints.

For nested review, use one parked orchestrator bootstrap. First dispatch the review
orchestrator with an instruction to remain parked: it performs no review work,
dispatches no leaf, and writes no runtime state until it receives a lease envelope.
After successful dispatch returns the real host thread ID, the root records the task
and `start-attempt`, records `wait-agents --join foreground` for that attempt, and
runs `grant-review-lease` with a unique lease ID, the current stage, the running
orchestrator attempt ID, and a stable holder actor ID. The root then delivers the
runtime directory, current revision, stage, lease ID, and actor ID as the lease
envelope; only that delivery activates review work. The helper records
`review.lease.granted` in `writer_lease`; granting fails unless the holder is a
running `review-orchestrator` attempt in the current foreground join.

The child receives the runtime directory, revision, lease ID, and holder actor ID.
Every leased mutation uses `--actor-kind review-orchestrator --actor-id <holder>` and
CAS. The helper permits only nested `task.created`, `agent.attempt.started`,
`agent.result.recorded`, `agent.late_result.recorded`, and the matching
`review.lease.released` event in the leased stage. It rejects root writes, another
actor, another stage, and every stage/gate/check/artifact/blocker/control/completion
event while the lease is active. Each leased task and attempt records the holder's
`lease_holder_attempt_id`; a leased writer may start, finish, or attach a late result
only inside that lineage. Pre-existing sibling tasks and attempts remain root-owned
and cannot be mutated through the lease. Starting a leaf attempt extends the existing
join; recording its result drains that leaf. Leaf children never write.

The holder runs `release-review-lease` before returning. The root then reloads and
validates before recording the orchestrator result. To detach, release first, let the
root record the detached join, and return the checkpoint. On resume the root restores
the foreground join and grants a new lease ID to the same holder attempt. Persisted
task/attempt lineage remains valid across that release, detach, and regrant; leases
never survive a detached turn.

The helper appends and fsyncs the event first, then writes and fsyncs a temporary
projection and atomically replaces `state.json`. `state.json` may therefore lag
after a crash but must never be ahead. `status` reports snapshot health; `repair`
preserves an incomplete JSONL tail and rebuilds the projection.

## State model

- `run` stores workflow identity and the policy revision pinned at start.
- `repositories` stores worktree, branch, and base identity per repository.
- `workflow.stages.<stage>.gates` stores user/authority decisions for that stage.
- `workflow.stages.<stage>.checks` stores verification outcomes, not approvals.
- `workflow.stages.<stage>.tasks.<task>.attempts` preserves every agent attempt.
- Gates, checks, and attempts record the stage entry that produced them. A redo
  increments the entry; use a new gate ID, and only current-entry gates constrain
  current stage completion.
- `control` is a discriminated union: `ready`, `waiting_agents`, `waiting_user`,
  `blocked`, or `complete`.
- `artifacts` stores paths and SHA-256 fingerprints, never full artifact contents.
- `revision` equals the last applied event sequence.

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
- logical task creation and agent attempt start/result;
- verification check and artifact fingerprint;
- foreground join, explicit detach, user wait, blocker, and final completion.

Do not record transport-only `wait_agent` timeouts, status reads, mailbox polling,
commentary, raw prompts, full child returns, tool calls, or logs. Notifications and
UI status remain observability, not workflow evidence.

## Command sequence

Initialize once:

```bash
<python> <shared>/runtime-state/sk_state.py init \
  --runtime-dir <runtime-root>/<change> \
  --change <change> --workflow <sk-team-feature|sk-team-quick> \
  --policy-revision <skills commit-or-fingerprint> \
  --repository-json '<JSON object>'
```

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
```

Run `<python> <shared>/runtime-state/sk_state.py <command> --help` for exact options.
Use `status` for a JSON projection plus `snapshot_status`, `history` for JSONL
events, and `validate` before resume, phase approval, archive, or handoff.

Tasks and checks are required by default. A successful stage requires every required
task and required check from its current entry to have succeeded or passed. Use
`--optional` on `create-task` or `record-check` only for explicitly non-blocking work;
optional failures remain visible but do not prevent successful stage closure.

For a required agent wave, create tasks and start attempts after successful host
dispatch, then issue one `wait-agents --join foreground` event for the semantic
join. Re-entering `wait_agent` after a transport timeout does not touch runtime
state. When results arrive, issue `finish-attempt` for each observed result and
let the reducer remove that attempt from the join. The final joined result returns
`control` to `ready` automatically; there is no manual ready/reset command that can
bypass an outstanding join, gate, or blocker.

Use `wait-agents --join detached --detach-reason <code>` only for a detach reason
allowed by `orchestration-policy.md`.

## Gates, checks, and attempts

- A **gate** is an authorization decision such as test-plan or remediation approval.
- A **check** is observed evidence such as TDD Red, lint, review, or acceptance.
- An **attempt** is one execution of one logical task by one agent thread.

Do not represent a gate as a check, infer approval from a passing check, or overwrite
an old attempt during retry/remediation. A late result for a terminal/cancelled
attempt uses `record-late-result` and never reopens the attempt or stage.

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
| `orphaned`, or `missing`/`diverged` without history | no valid non-empty journal | Fail closed with `recover-journal-or-reinitialize`; recover the journal or explicitly reinitialize and reconfirm approvals, constraints, stage, tasks, and results. |
| `unsupported_schema` | any | Fail closed with `require-compatible-helper`; do not repair or mutate the projection. |

The complete status vocabulary is valid | stale | diverged | missing | orphaned | legacy_v1 | unsupported_schema.
Do not infer state from an orphaned projection or manually edit either
file. After validation, reconcile `control` and running attempt host IDs with the
host mailbox and record newly observed results before dispatching new work.

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

The machine-readable contracts are `runtime-state/state.schema.json` and
`runtime-state/event.schema.json`.
