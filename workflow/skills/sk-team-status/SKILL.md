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

# /sk-team-status - Workflow Status

<sk-team-status>

You are the **Orchestrator** checking the status of ongoing team workflows.

## Your Task

Scan for active workflows and report their status clearly.

## Status Check Process

### 1. Find Active Changes

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

| Artifacts Present | Phase | Status |
|-------------------|-------|--------|
| None | - | Not started |
| proposal.md only | Discovery | Complete - Planning next |
| proposal.md, design.md, tasks.md | Planning | Complete - Doc Review or Testing next |
| Above + DOC_REVIEW.md | Doc Review | Complete - Testing next |
| Above + test files (failing) | Testing | Complete - Implementation next |
| Above + implementation (tests pass) | Implementation | Complete - Review next |
| Above + approved review | Review | Complete - Acceptance next |
| VERIFICATION.md | Acceptance | WORKFLOW COMPLETE |

### 4. Check Test Status

If implementation exists:
```bash
npm test 2>&1 | tail -30
```

### 5. Generate Report

```markdown
# Team Workflow Status

## Active Workflows

### 1. <feature-name>
- **Phase**: <current phase>
- **Progress**: 4/6 phases
- **Artifacts**:
  - [x] proposal.md - Requirements defined
  - [x] design.md - Architecture complete
  - [x] tasks.md - Tasks broken down
  - [ ] Tests - Pending
  - [ ] Implementation - Pending
  - [ ] VERIFICATION.md - Pending
- **Next Action**: Invoke sk-tester for TDD red phase
- **Resume**: `/sk-team-feature` to continue

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
| Complete | 2 |
| **Total Active** | **4** |

## Quick Actions
- `/sk-team-feature <description>` - Start new feature
- `/sk-team-quick <description>` - Quick fix
- Continue workflow: describe what to do next
```

## If No Active Workflows

```markdown
# Team Workflow Status

No active workflows found in `openspec/changes/`.

## Start a Workflow

### Full Feature Development
```
/sk-team-feature <description>
```
Example: `/sk-team-feature Add user authentication with OAuth`

### Quick Bugfix
```
/sk-team-quick <description>
```
Example: `/sk-team-quick Fix typo in login error message`

## Team Agents Available
| Agent | Purpose |
|-------|---------|
| sk-product-analyst | Requirements (WHAT & WHY) |
| sk-architect | Design (HOW) |
| sk-tester | TDD tests |
| sk-developer | Implementation |
| sk-code-reviewer | Code quality |
| sk-doc-reviewer | Documentation review |
| sk-acceptance-reviewer | Business validation |
```

## Additional Checks

### Stale Workflows
If artifacts exist but workflow seems stuck:
- proposal.md exists but no design.md
- Tests exist but no implementation
- Implementation exists but no VERIFICATION.md

Report these as potentially stale and suggest resuming.

### Incomplete Phases
Check for incomplete artifacts:
- Empty files
- Missing required sections
- Partial implementations

## Start Now

Scan for active workflows and report their status.

</sk-team-status>
