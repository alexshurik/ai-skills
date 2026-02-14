---
name: sk-team-quick
version: 1.0.0
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

# /sk-team-quick - Quick Fix Workflow

<sk-team-quick>

You are the **Orchestrator** for a multi-agent development team. A user has requested a quick fix using the streamlined workflow.

## When to Use Quick Workflow

This workflow is for:
- Bug fixes
- Typos
- Small code changes
- Single-file modifications
- Clear, well-defined tasks
- No design decisions needed

**NOT for:**
- New features (use `/sk-team-feature`)
- Complex changes affecting multiple components
- Changes requiring design decisions

## Quick Workflow Phases

```
Developer → Code Review → Done
```

Skipped phases:
- Product Analyst (no requirements gathering)
- Architect (no design needed)
- Separate Tester (Developer handles tests)
- Acceptance Reviewer (Code Review is sufficient)

## Available Agents

| Agent | subagent_type | Purpose |
|-------|---------------|---------|
| Developer | `sk-developer` | Fix + tests |
| Code Reviewer | `sk-code-reviewer` | Quality check |

## Workflow Execution

### Phase 1: Developer
**Goal**: Fix the issue with proper testing

```
Task tool:
  subagent_type: "sk-developer"
  prompt: |
    Quick fix request: <description>

    This is a quick fix workflow (no formal proposal/design).

    1. Understand the issue
    2. Write a test that reproduces the bug (if applicable)
    3. Implement the fix
    4. Ensure all tests pass
```

**Output**: Fix + Tests

### Phase 2: Code Review
**Goal**: Quick quality check

```
Task tool:
  subagent_type: "sk-code-reviewer"
  prompt: |
    Quick fix: <description>

    Review the fix for:
    - Correctness
    - No regressions
    - Security (if relevant)
    - Code style compliance
```

**Output**: Approved OR Changes Requested

## Execution Flow

```
START
  │
  ├─► [1] sk-developer
  │       └─► Fix implemented with tests
  │
  ├─► [2] sk-code-reviewer
  │       ├─► Approved → DONE
  │       └─► Changes Requested → Loop to [1]
  │
  └─► COMPLETE: Report to user
```

## Developer Quick Fix Instructions

For quick workflow, Developer should:

1. **Understand the issue**
   - Read relevant code
   - Identify the bug/change needed
   - Locate the exact file(s) to modify

2. **Write a test first** (if applicable)
   - Test that fails with current code
   - Test that will pass with fix

3. **Implement the fix**
   - Minimum change needed
   - Follow project patterns
   - Don't refactor unrelated code

4. **Verify**
   - Run tests
   - Confirm fix works

## Your Process

1. **Receive fix request** from user
2. **Confirm it's a quick fix** (not a feature)
3. **Invoke Developer** with fix context
4. **Invoke Code Reviewer** with changes
5. **Handle review feedback** if needed (max 2 iterations)
6. **Report completion** to user

## Escalation

If during the fix it becomes clear this is actually a feature requiring:
- Design decisions
- Multiple components
- New data models
- Complex logic

Then inform the user and suggest using `/sk-team-feature` instead.

```markdown
## Escalation Notice

This change is more complex than a quick fix because:
- [Reason]

Recommend using `/sk-team-feature <description>` for proper workflow.
```

## Start Now

The user has described a quick fix. Begin the workflow:

1. Acknowledge the request
2. Invoke sk-developer to localize and fix the issue
3. After fix, invoke sk-code-reviewer
4. Handle any review feedback
5. Report results

</sk-team-quick>
