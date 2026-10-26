---
name: sk-team-status
description: Show status of current team workflow
license: MIT

# Claude Code
allowed-tools: Read, Glob, Grep, Bash

---

# sk-team-status - Workflow Status

<sk-team-status>

You are the **Orchestrator** checking the status of ongoing team workflows.

Read `~/.claude/agents/shared/runtime-state-policy.md` or
`workflow/agents/shared/runtime-state-policy.md` from the skills repository before
inspecting runtime state.

## Your Task

Scan for active workflows and report their status clearly.

## Status Check Process

### 1. Find Active Changes

Resolve the Git-local workflow state root first:

```bash
git rev-parse --git-path sk-workflow
```

Also inspect `sk-workflow-archive/<change>/<run-id>/` under the absolute Git common
directory for completed/cleanup-pending runs moved out of removed worktrees. Use the shared
`workspace-lifecycle.md` relocation map and cleanup receipt to resolve historical
artifact paths without editing journal history. Report retained/blocked resources
and the recorded next action; status inspection never performs cleanup. Deduplicate
by run ID using the verified relocation record, not directory timestamps.

Read the installed/source `runtime-state-policy.md`. For each runtime directory run
the shared helper `status`; when the projection reports `valid`, also run `validate`.
`events.jsonl` is the authority and `state.json` is its derived projection. Validate
recorded repository identity, artifact paths, and fingerprints. File presence alone
is not proof of approval.

Report schema/revision, the complete charter (route, assurance, authorization,
scope digest, requested/resolved workspace, destination, budgets), delivery receipt,
current stage, stage gates/checks, logical tasks with every attempt, and `control`.
When `control.kind` is `waiting_agents`, report durable
attempt IDs, their host thread IDs, foreground/detached join mode, reason code, and
any detach reason. Do not wait or poll from a status request. UI status and
notifications are observability, not proof that the parent aggregated a result.

Report the complete `snapshot_status` vocabulary:
valid | stale | diverged | missing | orphaned | legacy_v1 | legacy_v2 | unsupported_schema.
Include `journal_events` and `recommended_action`. Use `validate` for valid; use
`repair` for stale/diverged/missing only with a valid non-empty journal; use
`migrate-v1` for legacy_v1 without committed history (or `repair` when
valid history already exists), and `migrate-v2` for legacy_v2 under the same rule.
For orphaned or missing/diverged without history,
fail closed with `recover-journal-or-reinitialize`: require journal recovery or
explicit reinitialization and reconfirmation. For `unsupported_schema`, fail closed
with `require-compatible-helper` and preserve the projection byte-for-byte. Never
infer state from an orphaned projection or mutate runtime state as part of a read-only
status request.

```bash
# List all change directories
ls -la openspec/changes/ 2>/dev/null
```

### 2. Check Artifacts for Each Change

For each change directory found:

```bash
# Check what exists
ls openspec/changes/<name>/ 2>/dev/null
```

### 3. Determine Current Phase

Prefer the validated ledger. Use the table only to recover safe facts when state is
missing or stale; label inferred approval as `UNCONFIRMED` and report exactly what
must be reconfirmed rather than copying a previous chat into the new session.

| Artifacts Present | Phase | Status |
|-------------------|-------|--------|
| None | - | Not started |
| proposal.md only | Discovery | Complete - Planning next |
| proposal.md, design.md, tasks.md | Planning | Complete - Doc Review or test-risk route next |
| Above + DOC_REVIEW.md | Doc Review | Complete - test-risk route next |
| Above + independent failing tests | Testing | Complete - Implementation next |
| Above + implementation (tests pass) | Implementation | Complete - Review next |
| Above + `CODE_REVIEW.md` APPROVED | Review | Complete - Acceptance next |
| Above + `CODE_REVIEW.md` TRIAGE REQUIRED | Review | User scope decision next |
| Above + `VERIFICATION.md` ACCEPTED | Acceptance | Complete - Retrospective next |
| Above + `RETROSPECTIVE.md` | Retrospective | Complete - Archive approval next |

### 4. Check Test Status

If implementation exists, resolve the repository's approved/pinned test command
from `AGENTS.md`, project guidance, CI, and package/tooling configuration. Run only
that safe command. If no authoritative command can be established, report test
status as `UNVERIFIED` instead of assuming `npm test`.

### 5. Generate Report

```markdown
# Team Workflow Status

## Active Workflows

### 1. <feature-name>
- **Phase**: <current phase>
- **Path / assurance**: <Micro | Quick | Full> / <Standard | Elevated>
- **Control**: <Manual | Checkpoints | YOLO>
- **Workspace**: <requested> → <resolved path>
- **Finish**: <Local | Commit | PR | Merge | Deploy and target>
- **Budgets**: attempts <used>/<limit>; reviews <used>/<limit>; remediations <used>/<limit>
- **Engineering**: passed | failed | pending | unverified
- **Visual**: passed | failed | pending | unverified | not_applicable
- **Acceptance**: accepted | needs_work | blocked | pending
- **Completed phases**: Discovery, Planning
- **Current phase**: Testing
- **Artifacts**:
  - [x] proposal.md - Requirements defined
  - [x] design.md - Architecture complete
  - [x] tasks.md - Tasks broken down
  - [ ] Tests - Pending
  - [ ] Implementation - Pending
  - [ ] CODE_REVIEW.md - Pending
  - [ ] DEFERRED.md - Optional; candidate/deferred/rejected/promoted scope proposals
  - [ ] VERIFICATION.md - Pending
  - [ ] RETROSPECTIVE.md - Pending
- **Derived next action**: Classify the test-risk route; invoke sk-tester only for
  high-risk/explicit separate testing, otherwise invoke Developer for integrated
  Red→Green
- **Runtime state**: `<git-local-path>/` (schema/revision; valid | stale | diverged | missing | orphaned | legacy_v1 | legacy_v2 | unsupported_schema)
- **Run state**: ready | waiting agents/user | blocked with typed reason | complete
- **Tasks/attempts**: logical task, attempt ordinal, host thread, result/artifact
- **Gates/checks**: stage-owned decisions and verification evidence
- **Deferred candidates**: none | <IDs requiring triage>
- **Snapshot/fingerprints**: <current durable artifact fingerprints>
- **Delivery**: pending | succeeded/failed receipt and evidence
- **Cleanup**: removed/retained/blocked/not_applicable resources, reasons, surviving evidence
- **Resume**: invoke `sk-team` using the current host's skill syntax

### 2. <another-feature>
...

## Summary
| Status | Count |
|--------|-------|
| In Discovery | 0 |
| In Planning | 1 |
| In Testing | 0 |
| In Implementation | 1 |
| In Review | 0 |
| In Acceptance | 0 |
| In Retrospective | 0 |
| Ready to Archive | 0 |
| Complete | 2 |
| **Total Active** | **4** |

## Quick Actions
- `sk-team <description>` - Recommend and run the right-sized workflow
- `sk-team-feature <description>` - Force the Full route
- `sk-team-quick <description>` - Force the Quick route
- Continue workflow: describe what to do next
```

## If No Active Workflows

```markdown
# Team Workflow Status

No active workflows found in `openspec/changes/`.

## Start a Workflow

### Adaptive (recommended)
```
sk-team <description>
```
Example: `sk-team Add user authentication with OAuth`

### Full Feature Development
```
sk-team-feature <description>
```
Example: `sk-team-feature Add user authentication with OAuth`

### Quick Bugfix
```
sk-team-quick <description>
```
Example: `sk-team-quick Fix typo in login error message`

## Team Agents Available
| Agent | Purpose |
|-------|---------|
| sk-product-analyst | Requirements (WHAT & WHY) |
| sk-architect | Design (HOW) |
| sk-tester | Risk-routed independent TDD tests |
| sk-developer | Implementation |
| sk-review-orchestrator | Code quality |
| sk-doc-reviewer | Documentation review |
| sk-acceptance-reviewer | Business validation |
```

## Additional Checks

### Stale Workflows
If artifacts exist but workflow seems stuck:
- proposal.md exists but no design.md
- Tests exist but no implementation
- Implementation exists but no approved CODE_REVIEW.md
- CODE_REVIEW.md has unresolved `user_decision` items or DEFERRED.md has candidates
- VERIFICATION.md exists but no RETROSPECTIVE.md

Report these as potentially stale and suggest resuming.

### Incomplete Phases
Check for incomplete artifacts:
- Empty files
- Missing required sections
- Partial implementations

## Start Now

Scan for active workflows and report their status.

</sk-team-status>
