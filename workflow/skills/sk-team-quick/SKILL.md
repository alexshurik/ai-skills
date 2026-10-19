---
name: sk-team-quick
description: Quick workflow for bounded fixes, features, and coherent UI polish that need one implementer plus one fresh combined review.
license: MIT

# Claude Code
allowed-tools: Task, Read, Write, Edit, Glob, Grep, Bash
---

# sk-team-quick - Quick Fix Workflow

<sk-team-quick>

You orchestrate a small, well-defined change using **two bounded threads**. Keep
the TDD and independent-review guarantees of the full workflow without carrying a
long conversation through four role invocations.

When invoked through `sk-team`, inherit its charter and do not ask the workflow
choices again. When invoked directly, resolve one compact charter with route fixed
to Quick before editing.

## Required policy

Read before starting:

```text
~/.claude/agents/shared/workflow-charter-policy.md
~/.claude/agents/shared/orchestration-policy.md
~/.claude/agents/shared/handoff-protocol.md
~/.claude/agents/shared/scope-governance.md
~/.claude/agents/references/review-approval-gate.md
or, from the skills repository:
workflow/agents/shared/workflow-charter-policy.md
workflow/agents/shared/orchestration-policy.md
workflow/agents/shared/handoff-protocol.md
workflow/agents/shared/scope-governance.md
workflow/agents/shared/runtime-state-policy.md
workflow/agents/references/review-approval-gate.md
```

Installed adapters may expose the same files under their agent reference roots.
The shared policy controls context inheritance, artifacts, nesting, waiting, and
compact returns.

For Codex, every new thread uses `fork_turns="none"`. Omit model and reasoning
overrides so both threads inherit the parent's selected model and effort. Give each
thread a task envelope with one deliverable, inputs, output path, constraints,
verification, and final-return contract. A thread returns only `FINAL` or `BLOCKED`.

## Scope gate

Use quick mode for a bug fix, typo, bounded feature, coherent multi-screen UI polish,
or other change with clear intended behavior and no unresolved high-cost design
decision. Several related views do not make a task Full when they use established
owners, contracts, and design language.

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
  SUMMARY.md       # only for a named consumer/repository requirement
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
   fix approach, risks, verification plan, required scope, explicit non-goals, and
   the authority source for every material constraint. Treat caller assumptions and
   implementation preferences as non-binding.
   State `Scope Delta: None`; if not none, return the item for user decision and
   escalation instead of editing.
4. In Manual or Checkpoints, return BLOCKED with a compact execution checkpoint and
   the design.md path. In YOLO, continue directly to Stage B unless diagnosis exposed
   a typed material scope/product/safety stop.

Stage B — after the caller sends the recorded execution decision, or immediately
after Stage A in YOLO:
1. For a bug, write a regression test first and prove RED for the right reason.
2. Implement the smallest approved fix.
3. For user-visible UI, render the first coherent screen early at representative
   compact/desktop widths, pass the macro visual gate, and iterate before broad
   verification. Preserve literal visual constraints and record exact-source final
   evidence.
4. Prove GREEN with focused checks, then run the broad safe/applicable gate once for
   the final input closure.
5. Write implementation.md with changed paths, design deviations, exact commands
   and statuses, skipped checks, and log artifact paths.
6. Return FINAL with at most 50 lines / 2500 tokens; do not paste diffs or logs.

No delegation unless the task envelope explicitly grants a bounded depth-2 helper.
```

In Manual or Checkpoints mode, surface the compact design checkpoint and wait for
the user's Execution decision before the follow-up. In YOLO, record the ceremony
decision from policy inside the same developer turn; do not force a return-and-
follow-up round unless design exposed a material scope/product/safety stop. If the
user changes scope or rejects the
approach, end this thread and start a clean successor from the request, design path,
and a short feedback artifact; do not accumulate redesign history.

## Thread 2 — independent review and acceptance

After implementation returns, the root first opens the coherent exact-source compact
and desktop renders and performs the macro visual preflight. If hierarchy, grouping,
density, alignment, rhythm, responsive priority, or product fit fails, return to the
same implementation scope before any broad readiness battery. Only after that pass,
capture one review snapshot and fingerprint. Validate the Developer's exact-input
broad receipt and run only missing, stale, or untrusted readiness rows; do not create
a duplicate root-owned full-suite run. Red required formatter/lint/type/build/tests/
diff evidence returns to implementation. Spawn a fresh clean reviewer/acceptance
thread. It must not delegate or rerun the full gate/tool battery. Its bounded
deliverable is:

```text
Objective: independently decide whether the approved quick fix is safe and meets
its intended behavior at review snapshot <fingerprint>.

Inputs:
- request and approved design.md;
- implementation.md;
- review evidence artifact path and fingerprint;
- relevant repository guidance and project profiles.

Use one combined reviewer only because the change passed the quick scope gate. Mark
each owner dimension PASS, FINDINGS, or NOT APPLICABLE:
1. architecture-design — boundaries/ownership, dependency/import direction,
   abstractions/navigation, structure, API/schema/model shape, packaging;
2. correctness-safety — approved behavior, edge/state/failure paths, recovery,
   concurrency/idempotency, trust/security, compatibility, tests, instructions;
3. engineering-quality — root-produced provenance, stack idioms, readability,
   complexity, duplication, dead code, error handling, test-code quality.
4. ui-ux — only when the snapshot has user-visible frontend impact; independently
   open the exact-source app or screenshots and inspect the changed journey at one
   representative desktop and one project-appropriate compact/mobile width. Perform
   the shared screenshot-first comprehension pass at original/native resolution and
   cover the complete effective scroll extent. Source inspection alone is UNVERIFIED.
   For browser chrome, safe-area, fixed navigation, dynamic viewport, keyboard, or
   `visualViewport` changes, use the actual target browser/device or the closest
   WebKit/mobile approximation and state the residual gap.
   Record both `CONTRACT: PASS | FAIL | UNVERIFIED` and
   `VISUAL: PASS | FAIL | UNVERIFIED`; overall UI approval requires both PASS.
   Contract conformance cannot excuse weak hierarchy, grouping, density, alignment,
   rhythm, responsive priority, or product fit.

Then verify intended behavior, regression coverage, applicable tests, documented
edge cases, and TODO/FIXME/HACK/XXX in changed files.

Classify every finding with severity, `required_fix | user_decision | backlog |
baseline`, `required_outcome`, and `remedy_authority`. Keep stack detection strict:
report whole-function/profile concerns, but unchanged debt does not become mandatory
remediation.

Write:
- REVIEW.md with dimension-by-dimension evidence and findings;
- VERIFICATION.md with ACCEPTED or NEEDS WORK and behavior evidence;
- SUMMARY.md only for a named consumer or repository requirement, not merely because
  the fix was accepted.

Begin `REVIEW.md` with the review-map fingerprint, source fingerprint, and
`Status: PASS | FINDINGS | UNVERIFIED`. Explicitly disposition every collector
structural/route-ownership lead and every non-OK static-analysis row; missing leads
make the review UNVERIFIED.

Return FINAL with verdict, artifact paths, blocking findings, exact verification
statuses, skipped/UNVERIFIED checks, and snapshot fingerprint. Keep the return to
50 lines / 2500 tokens; full evidence stays in artifacts.
```

This combines execution, not judgment: every required dimension remains explicit. If any
dimension requires specialist parallel analysis, the change is no longer quick;
escalate to the full workflow and its three independent core reviewers plus
conditional UI/UX.

## Remediation and finality

Quick has one full review round. The combined reviewer returns its complete finding
set across all dimensions in that round. Before remediation, show mandatory fixes, scope decisions, and
backlog; resolve every `user_decision` and freeze the exact allowlist containing only
`required_fix` plus approved IDs, together with each remedy authority/route. Never
pass “fix all findings”. Send Developer only `within_approved_design` items. Any
architecture, scope, or investigation route exits quick mode before source edits and
continues through the full workflow's owning gate.

One targeted remediation verification uses a fresh snapshot, fresh targeted gates
for changed inputs plus exact-input receipt reuse, and the valid parent full review,
immutable pre/post fingerprints, complete remediation delta, verified unchanged
hashes, no expansion, and every impacted dimension. Old evidence never proves
changed content. A material expansion or unprovable delta exits quick mode to the
full workflow while consuming the round.

A normative design/ADR amendment is never a targeted quick verification: exit quick mode
and run a full core-lens review plus conditional UI/UX against the new authority fingerprint.

If an allowlisted defect remains or remediation introduced a critical regression,
YOLO may run the charter's single bounded recovery with focused gates and the same
owning verification; this is not another full review round. Other modes return one
decision-focused blocker. If recovery still fails, return `budget.exhausted` with
exact IDs and offer escalation to `sk-team-feature`. New non-critical findings after
frozen triage go to `DEFERRED.md`; they cannot open another loop. Transport-only
waits never consume review or recovery budgets.

Only `ACCEPTED` from a fresh independent review of the current snapshot can finish
the workflow. Surface its compact decision. Manual mode may request its final
ceremony approval; Checkpoints and YOLO continue to the selected finish without a
redundant question. Archive with a recoverable move to
`openspec/completed/<fix-name>/` according to the charter. Never replace the user's
current request or existing unrelated artifact.

Immediately before finish, recapture evidence with the same base/policy, rebuild a
current review map, and run `review-gate.sh --mode quick` with
`combined=<REVIEW.md>`, the dispositions artifact, static summary when applicable,
and the approved/current maps. The gate must pass. It performs no broad rerun; source
drift returns to review, while missing reports/leads/tasks/tool dispositions remain
UNVERIFIED. Do not archive, commit/merge-for-finish, or mark the runtime complete on
a failed gate.

For user-visible UI, before finish the root personally opens the final exact-source
compact and desktop renders, verifies the current fingerprint, and records
Engineering, Visual, and Acceptance status. Do not rerun the broad suite merely to
perform this aggregation; reuse its exact-input receipt.

Before archive, resolve every `DEFERRED.md` candidate. Promote only user-selected
items to the repository's tracker or `openspec/backlog/<slug>.md`; preserve rejected/
deferred decisions in the archived change and do not implement them automatically.

## Communication and waiting

- Launch all independent work available in the current wave before waiting.
- Follow the shared foreground-join policy for every required child. Use the longest
  host-permitted event-driven wait and re-enter it after transport-only timeouts.
- Do not convert empty wake-ups into retry, phase, or workflow-budget counters.
- Record successfully dispatched one-shot children as one compact batched task; use
  a long-lived task attempt only when retry lineage matters. Foreground wait
  validation is read-only, and transport-only timeouts never write semantic events.
- Detach only for a shared-policy reason and record a detached attempt join with
  `detach_reason`; never rely on a notification to resume aggregation.
- Do not call `list_agents` after a routine timeout; use it only for reconciliation.
- Drain all available completion messages before launching or waiting again.
- Do not emit child progress chatter or repeat spawn attempts while slots are full.
- The mailbox carries compact status and decisions; the filesystem carries full
  reports, evidence, diffs, and logs.

## Start

Resolve/inherit the charter, validate the scope gate, resolve the workspace once,
initialize artifacts and schema-v3 runtime state with `--workflow sk-team`, enter
the first stage, then run Thread 1. Use typed stage gates for authorization and
checks for evidence. After acceptance, perform the selected finish and record the
matching terminal receipt; the charter's destination is authority for that action.

</sk-team-quick>
