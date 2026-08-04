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
  counts, spawned/running/completed IDs, wait counters, blockers, and
  next action. It is not a raw transcript or a duplicate host tool-call log.

## Wave and wait policy

1. Resolve the available concurrency budget once.
2. Fill every available slot from the pending wave before waiting.
3. Maintain explicit `pending`, `running`, `done`, and `blocked` sets.
4. Call `wait_agent` with the **longest timeout** allowed by the active host and
   communication policy. Never hard-code a 30-second polling loop.
5. Use **bounded autonomous waiting** by default. Before dispatch, persist a wait
   budget in workflow state: at most 15 minutes and 15 empty wake-ups for one wave,
   with at most 30 total idle wake-ups for the complete workflow. A host-supported
   single long wait is preferred over multiple short waits. A stricter host/user
   limit wins.
6. An empty wake-up increments both counters. Continue waiting automatically only
   while both budgets remain. Do not emit empty-wait commentary or use another tool
   merely to announce that children are still running.
7. After a wake-up with updates, process every available mailbox result, fill newly
   freed slots, and continue the wave within the remaining persisted budget.
8. Do not call `list_agents` after routine timeouts. Use it only for inconsistent
   state, cancellation, or a suspected missing completion.
9. On a concurrency-limit error, remember the effective capacity and wait for a slot;
   do not retry the same spawn repeatedly.
10. Completed agents are never polled again. Periodic “still running” progress
    chatter and unsolicited `send_message` nudges are forbidden.

`Autonomous`, `continue without approvals`, or `finish the workflow` authorizes this
finite wait budget; it never authorizes **unbounded polling**. Do not reset counters
after a timeout, completion, compaction, or new assistant turn. A user may explicitly
raise a budget after being told that every empty timeout causes another model step.
Prefer a host's automatic background-completion notification when it exists.

Skills cannot create a free event-driven barrier when the host does not expose one.
When either budget is exhausted, persist the running IDs, wave, snapshot fingerprint,
counter values, and next action, then return a compact `BACKGROUND WORK ACTIVE`
handoff. Children continue in background; the UI's Done state plus `continue` resumes
mailbox aggregation. This is a fallback for unusually long work, not the normal path.

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
