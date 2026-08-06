---
name: sk-team-quick
description: Quick workflow for bugfixes, typos, and small changes
license: MIT

# Claude Code
allowed-tools: Task, Read, Write, Edit, Glob, Grep, Bash
---

# sk-team-quick - Quick Fix Workflow

<sk-team-quick>

You orchestrate a small, well-defined change using **two bounded threads**. Keep
the TDD and independent-review guarantees of the full workflow without carrying a
long conversation through four role invocations.

## Required policy

Read before starting:

```text
~/.claude/agents/shared/orchestration-policy.md
~/.claude/agents/shared/handoff-protocol.md
~/.claude/agents/shared/scope-governance.md
or, from the skills repository:
workflow/agents/shared/orchestration-policy.md
workflow/agents/shared/handoff-protocol.md
workflow/agents/shared/scope-governance.md
workflow/agents/shared/runtime-state-policy.md
```

Installed adapters may expose the same files under their agent reference roots.
The shared policy controls context inheritance, artifacts, nesting, waiting, and
compact returns.

For Codex, every new thread uses `fork_turns="none"`. Omit model and reasoning
overrides so both threads inherit the parent's selected model and effort. Give each
thread a task envelope with one deliverable, inputs, output path, constraints,
verification, and final-return contract. A thread returns only `FINAL` or `BLOCKED`.

## Scope gate

Use quick mode only for a bug fix, typo, small code change, or other change with a
clear intended behavior and no unresolved high-cost design decision.

Escalate to `sk-team-feature` before editing if discovery reveals any of:

- a new public contract, trust boundary, data model, or deployment path;
- multiple components with non-obvious ownership;
- requirements that need product decisions;
- architecture alternatives with materially different cost or risk.

Also escalate when the proposed fix needs a material Scope Delta from the shared
policy. Do not hide a queue, storage system, expanded threat model, or broad refactor
inside quick-mode approval.

## Durable and runtime state

Choose `<fix-name>` in kebab-case and create:

```text
openspec/changes/<fix-name>/
  design.md
  implementation.md
  REVIEW.md
  VERIFICATION.md
  SUMMARY.md
  DEFERRED.md      # only when proposals are staged/deferred/rejected/promoted
```

Resolve the git-local runtime directory with:

```bash
git rev-parse --git-path sk-workflow
```

Initialize `<runtime-dir>/<fix-name>/events.jsonl` plus its derived `state.json`
through the shared runtime-state helper. Pin the policy revision and repository
identity. Durable user-facing decisions remain under `openspec/changes/`. Stages own
their gates/checks/tasks and tasks preserve every attempt so `/new` can resume and
show who ran without transcript copy. Never hand-edit either runtime file.

## Thread 1 — diagnose, confirm, implement

Spawn one clean `sk-developer` thread with this bounded deliverable:

```text
Objective: diagnose and implement <fix request> with a regression test when the
change fixes a bug.

Inputs:
- repository guidance and project convention profiles;
- the user's original request;
- openspec/changes/<fix-name>/ as the durable artifact directory.

Stage A — read-only diagnosis:
1. Reproduce or otherwise prove the problem.
2. Run the compact pre-write ownership/structure gate.
3. Write design.md: problem, root cause, intended behavior, exact file ownership,
   fix approach, risks, verification plan, required scope, and explicit non-goals.
   State `Scope Delta: None`; if not none, return the item for user decision and
   escalation instead of editing.
4. Return BLOCKED with a compact approval checkpoint and the design.md path.

Stage B — only after the caller sends the user's approval as one short follow-up:
1. For a bug, write a regression test first and prove RED for the right reason.
2. Implement the smallest approved fix.
3. Prove GREEN and run applicable existing checks.
4. Write implementation.md with changed paths, design deviations, exact commands
   and statuses, skipped checks, and log artifact paths.
5. Return FINAL with at most 50 lines / 2500 tokens; do not paste diffs or logs.

No delegation unless the task envelope explicitly grants a bounded depth-2 helper.
```

Surface the compact design checkpoint and wait for explicit user approval before
sending the one follow-up. If the user changes scope or rejects the approach, end
this thread and start a clean successor from the request, design path, and a short
feedback artifact; do not accumulate redesign history.

## Thread 2 — independent review and acceptance

After implementation is green, capture one review snapshot and fingerprint. Spawn
a fresh clean reviewer/acceptance thread. It must not delegate. Its bounded
deliverable is:

```text
Objective: independently decide whether the approved quick fix is safe and meets
its intended behavior at review snapshot <fingerprint>.

Inputs:
- request and approved design.md;
- implementation.md;
- review evidence artifact path and fingerprint;
- relevant repository guidance and project profiles.

Review all seven logical dimensions and mark each PASS, FINDINGS, or NOT APPLICABLE:
1. contract and security;
2. architecture and boundary ownership;
3. abstraction quality;
4. file/module structure and placement;
5. imports and dependency direction;
6. stack-specific correctness;
7. repository-instruction and change-quality compliance.

Then verify intended behavior, regression coverage, applicable tests, documented
edge cases, and TODO/FIXME/HACK/XXX in changed files.

Classify every finding with severity plus `required_fix | user_decision | backlog |
baseline`. Keep stack detection strict: report whole-function/profile concerns, but
unchanged debt does not become mandatory remediation.

Write:
- REVIEW.md with dimension-by-dimension evidence and findings;
- VERIFICATION.md with ACCEPTED or NEEDS WORK and behavior evidence;
- SUMMARY.md only when accepted.

Return FINAL with verdict, artifact paths, blocking findings, exact verification
statuses, skipped/UNVERIFIED checks, and snapshot fingerprint. Keep the return to
50 lines / 2500 tokens; full evidence stays in artifacts.
```

This combines execution, not judgment: every dimension remains explicit. If any
dimension requires specialist parallel analysis, the change is no longer quick;
escalate to the full workflow and its seven independent clean reviewers.

## Remediation and finality

Before remediation, show mandatory fixes, scope additions requiring a decision, and
deferred/backlog candidates. An initial `NEEDS WORK` verdict may start one clean
remediation thread only after every `user_decision` is included, deferred, or
rejected. Pass the approved design, review fingerprint, and an explicit
allowlist containing only `required_fix` plus user-approved IDs. Never pass “fix all
findings”. After remediation, start a fresh Thread 2 against a new snapshot. Targeted
diagnostics may help locate a problem, but cannot issue final approval.

New non-critical findings in the final review go to `DEFERRED.md`; they cannot open
another quick remediation loop. Remediation regressions, proven critical defects,
and approved-behavior failures still block.

Quick mode permits at most one remediation cycle. If the fresh final review still
finds material issues, stop and offer escalation to `sk-team-feature`; do not retry
agents indefinitely.

Only `ACCEPTED` from a fresh independent review of the current snapshot can finish
the workflow. Surface its compact decision, ask for explicit final approval, then
archive with a recoverable move to `openspec/completed/<fix-name>/` when requested
by the workflow/user. Never replace the user's current request or existing unrelated
artifact.

Before archive, resolve every `DEFERRED.md` candidate. Promote only user-selected
items to the repository's tracker or `openspec/backlog/<slug>.md`; preserve rejected/
deferred decisions in the archived change and do not implement them automatically.

## Communication and waiting

- Launch all independent work available in the current wave before waiting.
- Follow the shared foreground-join policy for every required child. Use the longest
  host-permitted event-driven wait and re-enter it after transport-only timeouts.
- Do not convert empty wake-ups into retry, phase, or workflow-budget counters.
- Create a logical task/attempt for each successful dispatch and record one
  foreground attempt join. Transport-only timeouts never write semantic events.
- Detach only for a shared-policy reason and record a detached attempt join with
  `detach_reason`; never rely on a notification to resume aggregation.
- Do not call `list_agents` after a routine timeout; use it only for reconciliation.
- Drain all available completion messages before launching or waiting again.
- Do not emit child progress chatter or repeat spawn attempts while slots are full.
- The mailbox carries compact status and decisions; the filesystem carries full
  reports, evidence, diffs, and logs.

## Start

Validate the scope gate, initialize artifacts and runtime state v2, enter the first
stage, then run Thread 1. Use stage gates for user approvals and checks for evidence.

</sk-team-quick>
