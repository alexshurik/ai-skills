---
name: sk-team-status
version: 1.0.0
description: Show status of current team workflow
license: MIT

# Claude Code
allowed-tools: Read, Glob, Grep, Bash

# Cross-platform hints
platforms:
  codex: true
  cursor: true
  kimi: true
---

# sk-team-status - Workflow Status

<sk-team-status>

You are the **Orchestrator** checking the status of ongoing team workflows.

## Your Task

Scan for active workflows and report their status clearly.

## Status Check Process

### 1. Find Active Changes

Resolve the Git-local workflow state root first:

```bash
git rev-parse --git-path sk-workflow
```

Read each `<runtime-root>/<name>/state.json` before inferring anything from files.
Validate its recorded worktree, base, artifact paths, and fingerprints. A valid
ledger is authoritative for phase approvals, retry budgets, and next action; file
presence alone is not proof of approval.

Report review/remediation/acceptance counts, spawned/running/completed IDs,
`execution_status`, the foreground join set, and any `detach_reason` from the ledger.
These are resumable orchestration state, not a second transcript or a quality verdict.

If `execution_status` is `background_detached`, report the running IDs, wave,
snapshot, artifact paths, detach reason, and exact aggregation action. Do not wait or
poll from a status request. Treat UI status and notifications as observability, not
proof that the parent has aggregated the mailbox result.

If `execution_status` is `foreground_join`, report the outstanding join IDs and real
workflow phase without converting the status request into a detach. For a legacy
ledger with `phase: background_work_active` or empty-wait counters, report that it
requires normalization under the shared policy before aggregation can continue.

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
| proposal.md, design.md, tasks.md | Planning | Complete - Doc Review or Testing next |
| Above + DOC_REVIEW.md | Doc Review | Complete - Testing next |
| Above + test files (failing) | Testing | Complete - Implementation next |
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
- **Next Action**: Invoke sk-tester for TDD red phase
- **State ledger**: `<git-local-path>/state.json` (valid | stale | missing)
- **Workflow state**: review/remediation/acceptance counts; agents, join, detach reason
- **Deferred candidates**: none | <IDs requiring triage>
- **Snapshot/fingerprints**: <current durable artifact fingerprints>
- **Resume**: invoke `sk-team-feature` using the current host's skill syntax

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
- `sk-team-feature <description>` - Start new feature
- `sk-team-quick <description>` - Quick fix
- Continue workflow: describe what to do next
```

## If No Active Workflows

```markdown
# Team Workflow Status

No active workflows found in `openspec/changes/`.

## Start a Workflow

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
| sk-tester | TDD tests |
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
