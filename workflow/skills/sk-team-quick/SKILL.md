---
name: sk-team-quick
version: 1.3.0
description: Quick workflow for bugfixes, typos, and small changes
license: MIT

# Claude Code
allowed-tools: Task, Read, Write, Edit, Glob, Grep, Bash

# Cross-platform hints
platforms:
  codex: true
  cursor: true
  kimi: true
---

# sk-team-quick - Quick Fix Workflow

<sk-team-quick>

You orchestrate a small, well-defined change using **two bounded threads**. Keep
the TDD and independent-review guarantees of the full workflow without carrying a
long conversation through four role invocations.

## Required policy

Read before starting:

```text
workflow/agents/shared/orchestration-policy.md
workflow/agents/shared/handoff-protocol.md
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

## Durable and runtime state

Choose `<fix-name>` in kebab-case and create:

```text
openspec/changes/<fix-name>/
  design.md
  implementation.md
  REVIEW.md
  VERIFICATION.md
  SUMMARY.md
```

Resolve the git-local runtime directory with:

```bash
git rev-parse --git-path sk-workflow
```

Store `<runtime-dir>/<fix-name>/state.json`, evidence snapshots, fingerprints, and
large logs there. Durable user-facing decisions remain under `openspec/changes/`.
The ledger records phase, artifact paths/fingerprints, approval checkpoints,
attempt counts, and the next action so `/new` can resume without transcript copy.

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
   fix approach, risks, and verification plan. Keep it concise.
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

An initial `NEEDS WORK` verdict may start one clean remediation thread from the
approved design, findings artifact, and review fingerprint. After remediation,
start a fresh Thread 2 against a new snapshot. Targeted diagnostics may help locate
a problem, but cannot issue final approval.

Quick mode permits at most one remediation cycle. If the fresh final review still
finds material issues, stop and offer escalation to `sk-team-feature`; do not retry
agents indefinitely.

Only `ACCEPTED` from a fresh independent review of the current snapshot can finish
the workflow. Surface its compact decision, ask for explicit final approval, then
archive with a recoverable move to `openspec/completed/<fix-name>/` when requested
by the workflow/user. Never replace the user's current request or existing unrelated
artifact.

## Communication and waiting

- Launch all independent work available in the current wave before waiting.
- Use the longest wait timeout allowed by the active host and communication policy.
- Do not poll `list_agents` after every wait; use it only for reconciliation.
- Drain all available completion messages before waiting again.
- Do not emit child progress chatter or repeat spawn attempts while slots are full.
- The mailbox carries compact status and decisions; the filesystem carries full
  reports, evidence, diffs, and logs.

## Start

Validate the scope gate, initialize artifacts and state, then run Thread 1.

</sk-team-quick>
