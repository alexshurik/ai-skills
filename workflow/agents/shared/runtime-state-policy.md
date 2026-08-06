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
repository it is `workflow/agents/shared/runtime-state/sk_state.py`.

Never edit `events.jsonl` or `state.json` directly. The root is the only logical
writer and invokes the helper. Children return compact results and artifact
fingerprints; they never mutate global workflow state.

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
python3 <shared>/runtime-state/sk_state.py init \
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
```

Run `python3 <shared>/runtime-state/sk_state.py <command> --help` for exact options.
Use `status` for a JSON projection plus `snapshot_status`, `history` for JSONL
events, and `validate` before resume, phase approval, archive, or handoff.

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

On resume:

1. run `status`;
2. run `validate` when `snapshot_status` is `valid`;
3. if it is `stale` or `missing`, run `repair` and validate again;
4. reconcile `control` and running attempt host IDs with the host mailbox;
5. record newly observed results before dispatching new work.

For a legacy `schema_version: 1` ledger, run `migrate-v1` with the workflow name and
current policy revision. Migration preserves the original as `state.v1.json`, starts
the semantic journal with `workflow.migrated_from_v1`, and normalizes legacy
foreground/background wait state. Validate before continuing. Never interpret a
newer unsupported schema or event version; stop and require a compatible helper.

The machine-readable contracts are `runtime-state/state.schema.json` and
`runtime-state/event.schema.json`.
