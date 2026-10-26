# Context-Efficient Agent Orchestration

This is the shared orchestration contract for `sk-*` workflows. It separates
conversation context from repository authority: agents receive a bounded task and
paths to durable evidence, not a copy of the caller's transcript.

Use `scope-governance.md` for Scope Delta approval, finding/remediation authority,
OpenSpec documents, and deferred-item lifecycle. Use `runtime-state-policy.md` for
the semantic event journal, materialized state, transitions, and migration. Use
`workflow-charter-policy.md` for route, authorization, workspace, assurance, and
finish semantics.

## Core invariants

1. One agent thread owns **one bounded deliverable** with explicit acceptance
   criteria and an output artifact or verdict.
2. A new phase, redo, remediation, subsystem, or review cycle starts a clean thread.
3. Full evidence lives in durable artifacts or Git-local runtime artifacts. Agent
   messages carry compact decisions and artifact paths.
4. The root owns the global spawn, retry, concurrency budget, and runtime-state
   writes. The exact bounded nested-review writer lease is the only child-writer
   exception, is available only in Full review, and records only permitted nested
   task/attempt events through the helper. No child ever edits the workflow journal
   or projection directly, and every child outside that lease is read-only with
   respect to runtime state.
5. Nesting is limited to **depth 2**. A child may spawn helpers only when its task
   envelope grants a named subgraph and exact child count. Depth 3+ is prohibited.
6. A leaf agent may not spawn. Review lenses are always leaves.
7. One runtime run owns one objective and one charter. A new independent objective
   starts a new run and never inherits YOLO or terminal authority.

## Required task envelope

Every delegated task includes:

```text
Deliverable: <one bounded result>
Worktree: <absolute path>
Authority: <proposal/design/ADR/guidance paths>
Scope: <paths, base/fingerprint, and explicit exclusions>
Constraints: <C-* statement, user/normative authority, and source artifact/gate>
Preferences: <non-binding caller suggestions or none>
Acceptance: <observable completion criteria>
Output: <artifact path or read-only verdict>
Return: FINAL or BLOCKED, required actions, and artifact paths; max 50 lines
Delegation budget: none | depth-2 <named children and maximum count>
```

Only a traceable user decision, approved artifact, or repository policy may appear
under `Constraints`. Persist a new material user choice before dispatch or cite the
stage gate that records it. Caller assumptions, convenience goals, and preferred
implementation techniques belong under `Preferences`; they cannot eliminate a
solution class or override approved authority. If a preference would materially
change architecture, scope, or a public contract, route it through the applicable
decision gate instead of presenting it as a constraint.

Do not paste full files, diffs, logs, static-analysis output, prior handoffs, or the
whole original conversation when the child can read an artifact path.

## Codex context policy

- For every independent phase, redo, remediation, reviewer, and helper, call
  `spawn_agent` with `fork_turns="none"`.
- Use `fork_turns="1"` through `"3"` only when a recent material user choice has not
  yet been persisted. Persist it immediately so later children can return to clean
  context.
- Never use `fork_turns="all"` as a default. It is allowed only when the user
  explicitly requests full-conversation continuation after the expected cost is
  disclosed.
- Omit model and reasoning overrides by default. A clean child inherits the parent
  model and reasoning effort; clean context is not a model downgrade.
- When Codex code mode is available, batch independent deterministic read-only tool
  calls and emit only bounded summaries. Collaboration tools stay outside code mode.

Hosts without `fork_turns` use their equivalent isolated delegation mechanism. If a
host cannot guarantee isolation, disclose that limitation rather than claiming an
isolated context.

## Nesting and communication

Normal graph:

```text
root
├── clean phase agent
└── clean review orchestrator (optional depth-2 budget)
    ├── clean lens
    └── clean lens
```

- Children communicate compact status through the host mailbox and full data through
  the shared filesystem.
- A leaf returns only `FINAL` or `BLOCKED`; routine progress messages are forbidden.
- A nested child returns its summary and artifact paths to its immediate parent. The
  parent validates and aggregates them before returning to the root.
- Direct sibling/root messages are reserved for cancellation, a corrected scope, or
  a blocker the immediate parent cannot handle.
- `send_message` may steer a running child when scope genuinely changes.
- Allow **one short follow-up** in the same child only for clarification within the
  same bounded deliverable. A new deliverable always gets a clean child.

## Artifact locations

- Durable user-facing work remains under `openspec/changes/<name>/` and is archived
  with the change.
- Heavy runtime evidence, logs, checkpoints, and workflow state live under:

  ```text
  $(git rev-parse --git-path sk-workflow)/<name>/
  ```

  This resolves correctly for normal repositories and linked worktrees and stays
  outside the reviewed Git diff. Before removing a linked worktree, preserve its
  runtime directory using `workspace-lifecycle.md`; Git may remove administrative
  state with the worktree. Keep disposable previews/scratch output in recorded
  run-local paths instead of the project root.
- Every runtime artifact has a content fingerprint. Parent summaries name the exact
  artifact path and fingerprint they used.
- `events.jsonl` is the authoritative append-only history of semantic workflow
  transitions. `state.json` is its derived compact projection. The global root owns
  both and mutates them only through `runtime-state/sk_state.py`. The sole exception
  is the bounded nested-review writer lease defined by `runtime-state-policy.md`;
  it records Full review leaf attempts inside the bounded lineage.
- Stages own their gates, checks, and tasks; tasks own immutable attempt history and
  may compactly materialize a successfully dispatched one-shot batch in one event.
  `control` records `ready`, `waiting_agents`, `waiting_user`, `blocked`, or
  `complete`. Neither file is a raw transcript or duplicate host tool-call log.

## Wave and join policy

1. Resolve the available concurrency budget once.
2. Fill every available slot from the pending wave before waiting.
3. Maintain explicit `pending`, `running`, `done`, and `blocked` sets.
4. Keep the required wave and its aggregation in the same active parent turn. When
   a result makes the next required task eligible, dispatch it immediately before
   optional analysis or status prose. A parked orchestrator is a bootstrap state
   only: activate it as soon as its lease envelope exists, and treat an unactivated
   or completed-but-unaggregated required child as a workflow defect, not normal
   waiting.
5. When the host exposes an event-driven mailbox wait such as Codex `wait_agent`,
   keep every required child in a **foreground join** with the active parent turn.
   After successful dispatch, record one compact batched task (or a long-lived
   task attempt). Validate its running IDs with `wait-agents --join foreground`;
   that command is read-only and does not append a journal event.
   Call the primitive with the **longest timeout** allowed by the active host,
   higher-priority instructions, and communication policy. Never hard-code a short
   polling loop or a universal maximum timeout.
6. If the wait returns only because of a transport timeout or partial completion,
   re-enter the foreground join without writing a wait event. The first foreground
   wait and all continuations are transport-only: none is a workflow retry, phase
   transition, budget, or semantic event. Waiting inside one tool call adds no
   periodic transcript entries; only a model-visible wake-up and its compact result
   add parent context.
7. Do not end the parent turn while a required child is running merely because an
   elapsed-time or empty-wakeup threshold was reached. End the join when all required
   results arrive, the user cancels or replaces the work, or the host forces the turn
   to end.
8. After a wake-up with updates, process every available mailbox result and fill
   newly freed slots before waiting again. If user input steers the active turn,
   handle it under the host's normal steering rules and resume the join when the
   required work remains in scope.
9. Do not call `list_agents` after routine transport timeouts. Use it only for
   inconsistent state, cancellation, or a suspected missing completion.
10. On a concurrency-limit error, remember the effective capacity and wait for a slot;
   do not retry the same spawn repeatedly.
11. Completed agents are never polled again. Periodic “still running” progress
    chatter and unsolicited `send_message` nudges are forbidden.

If the host has no event-driven mailbox wait, do not invent an unbounded polling
loop. Use a finite polling deadline only when the host, user, or higher-priority
policy provides one. Otherwise detach with a compact checkpoint instead of spending
repeated model steps on status checks.

Detach required work only when the user explicitly requests background execution,
the host forces the parent turn to end, a higher-priority deadline requires it, or
the wait primitive is unavailable or repeatedly fails. Preserve the real workflow
stage; record `wait-agents --join detached` with the active attempt IDs and an
allowed `detach_reason`. Return a compact `BACKGROUND WORK ACTIVE` handoff that says
aggregation requires a future turn. Product or desktop notifications are
observability only: never treat them as a correctness mechanism or assume they will
start a new parent turn.

On resume, validate the semantic journal and projection before interpreting host
status. Reconcile running attempt IDs with the mailbox and record
observed results before new dispatch. Migrate schema-v1 ledgers using `migrate-v1` and schema-v2
projections using `migrate-v2`; each preserves the old file. Schema-v1 migration
normalizes `phase: background_work_active` and legacy wait-budget state to a detached
attempt join and requires mailbox aggregation before any new stage, verdict, or
approval. Never treat a legacy UI Done state as proof of aggregation.

## Result contract

The complete evidence stays in artifacts. The model-visible return is a compact
decision envelope, normally no more than 50 lines or about 2,500 tokens:

```markdown
## FINAL | BLOCKED
- Deliverable: ...
- Verdict/status: ...
- Required actions: ...
- Critical evidence: ...
- Artifacts: `path` (`fingerprint`)
- Blockers: ...
```

The caller may display a full artifact when the user asks, but it does not relay raw
artifacts or logs by default.
