# Context-Efficient Agent Orchestration

This is the shared orchestration contract for `sk-*` workflows. It separates
conversation context from repository authority: agents receive a bounded task and
paths to durable evidence, not a copy of the caller's transcript.

Use `scope-governance.md` for Scope Delta approval, finding/remediation authority,
OpenSpec documents, and deferred-item lifecycle.

## Core invariants

1. One agent thread owns **one bounded deliverable** with explicit acceptance
   criteria and an output artifact or verdict.
2. A new phase, redo, remediation, subsystem, or review cycle starts a clean thread.
3. Full evidence lives in durable artifacts or Git-local runtime artifacts. Agent
   messages carry compact decisions and artifact paths.
4. The root owns the global spawn, retry, and concurrency budget.
5. Nesting is limited to **depth 2**. A child may spawn helpers only when its task
   envelope grants a named subgraph and exact child count. Depth 3+ is prohibited.
6. A leaf agent may not spawn. Review lenses are always leaves.

## Required task envelope

Every delegated task includes:

```text
Deliverable: <one bounded result>
Worktree: <absolute path>
Authority: <proposal/design/ADR/guidance paths>
Scope: <paths, base/fingerprint, and explicit exclusions>
User constraints: <material choices not already persisted>
Acceptance: <observable completion criteria>
Output: <artifact path or read-only verdict>
Return: FINAL or BLOCKED, required actions, and artifact paths; max 50 lines
Delegation budget: none | depth-2 <named children and maximum count>
```

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
  outside the reviewed Git diff.
- Every runtime artifact has a content fingerprint. Parent summaries name the exact
  artifact path and fingerprint they used.
- `state.json` stores resumable phase/approval fingerprints, review/remediation/acceptance
  counts, spawned/running/completed IDs, `execution_status`, the current foreground
  `join` set, any `detach_reason`, blockers, and next action. It is not a raw
  transcript or a duplicate host tool-call log.

## Wave and join policy

1. Resolve the available concurrency budget once.
2. Fill every available slot from the pending wave before waiting.
3. Maintain explicit `pending`, `running`, `done`, and `blocked` sets.
4. When the host exposes an event-driven mailbox wait such as Codex `wait_agent`,
   keep every required child in a **foreground join** with the active parent turn.
   Before waiting, set `execution_status` to `foreground_join`, persist the required
   agent IDs in `join`, and clear `detach_reason`.
   Call the primitive with the **longest timeout** allowed by the active host,
   higher-priority instructions, and communication policy. Never hard-code a short
   polling loop or a universal maximum timeout.
5. If the wait returns only because of a transport timeout, re-enter the foreground
   join. A transport timeout is not a workflow retry, phase transition, or budget
   event. Waiting inside one tool call adds no periodic transcript entries; only a
   model-visible wake-up and its compact result add parent context.
6. Do not end the parent turn while a required child is running merely because an
   elapsed-time or empty-wakeup threshold was reached. End the join when all required
   results arrive, the user cancels or replaces the work, or the host forces the turn
   to end.
7. After a wake-up with updates, process every available mailbox result and fill
   newly freed slots before waiting again. If user input steers the active turn,
   handle it under the host's normal steering rules and resume the join when the
   required work remains in scope.
8. Do not call `list_agents` after routine transport timeouts. Use it only for
   inconsistent state, cancellation, or a suspected missing completion.
9. On a concurrency-limit error, remember the effective capacity and wait for a slot;
   do not retry the same spawn repeatedly.
10. Completed agents are never polled again. Periodic “still running” progress
    chatter and unsolicited `send_message` nudges are forbidden.

If the host has no event-driven mailbox wait, do not invent an unbounded polling
loop. Use a finite polling deadline only when the host, user, or higher-priority
policy provides one. Otherwise detach with a compact checkpoint instead of spending
repeated model steps on status checks.

Detach required work only when the user explicitly requests background execution,
the host forces the parent turn to end, a higher-priority deadline requires it, or
the wait primitive is unavailable or repeatedly fails. Preserve the real workflow
`phase`; set `execution_status` to `background_detached` and persist the running IDs,
wave, snapshot fingerprint, artifact paths, `detach_reason`, and next action. Return
a compact `BACKGROUND WORK ACTIVE` handoff that says aggregation requires a future
turn. Product or desktop notifications are observability only: never treat them as
a correctness mechanism or assume they will start a new parent turn.

On resume, normalize legacy ledgers that used `phase: background_work_active` or
legacy wait-budget counters. Recover the last real workflow phase from the validated
checkpoint, preserve all agent/artifact IDs, set `execution_status` to
`background_detached`, set `detach_reason` to `legacy_wait_budget`, and require
mailbox aggregation before any new phase, verdict, or approval. Never treat a legacy
UI Done state as proof of aggregation.

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
