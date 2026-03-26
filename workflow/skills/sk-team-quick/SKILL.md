---
name: sk-team-quick
version: 1.1.0
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
Setup → Mini-Architect → Developer → Code Review → Mini-Acceptance → Done
```

Skipped phases:
- Product Analyst (no requirements gathering)
- Separate Tester (Developer handles tests)
- Doc Reviewer (lightweight design note is sufficient)

## Available Agents

| Agent | subagent_type | Purpose |
|-------|---------------|---------|
| Architect | `sk-architect` | Brief design note |
| Developer | `sk-developer` | Fix + tests |
| Code Reviewer | `sk-code-reviewer` | Quality check |
| Acceptance Reviewer | `sk-acceptance-reviewer` | Verify fix + write docs |

## Workflow Execution

### Phase 0: Setup
**Goal**: Prepare documentation structure

1. Generate a fix name in kebab-case from the user's description (e.g. `fix-null-pointer-in-parser`)
2. Create directory: `openspec/changes/<fix-name>/`

```bash
mkdir -p openspec/changes/<fix-name>
```

### Phase 1: Mini-Architect
**Goal**: Brief design note — what to change and why

```
Agent tool:
  subagent_type: "sk-architect"
  prompt: |
    ## QUICK FIX MODE

    This is a quick fix workflow — lightweight design only.

    **Fix request:** <description>
    **Docs directory:** openspec/changes/<fix-name>/

    ### What to do:
    1. Explore the codebase to understand the problem
    2. Write a brief `openspec/changes/<fix-name>/design.md` with:
       - **Problem**: What is broken / what needs to change
       - **Root cause**: Why it happens (if bug)
       - **Fix approach**: What to change and in which files
       - **Risks**: Anything that could go wrong (if any)
    3. Return a summary of your findings

    ### Quick fix rules — MUST FOLLOW:
    - Do NOT ask the user any questions — work autonomously
    - Do NOT create tasks.md — this is a quick fix
    - Do NOT write component diagrams, API design, data model sections
    - Keep design.md SHORT — aim for 20-40 lines max
    - Focus only on: problem, root cause, fix approach, risks
```

**Output**: Brief design.md + summary to orchestrator

### Phase 2: Developer
**Goal**: Fix the issue with proper testing

```
Agent tool:
  subagent_type: "sk-developer"
  prompt: |
    Quick fix request: <description>

    **Design note:** Read `openspec/changes/<fix-name>/design.md` for the architect's analysis of the problem and recommended approach.

    1. Read the design note
    2. Understand the issue
    3. Write a test that reproduces the bug (if applicable)
    4. Implement the fix following the architect's approach
    5. Ensure all tests pass
```

**Output**: Fix + Tests

### Phase 3: Code Review
**Goal**: Quick quality check

```
Agent tool:
  subagent_type: "sk-code-reviewer"
  prompt: |
    Quick fix: <description>

    Design note at: openspec/changes/<fix-name>/design.md

    Review the fix for:
    - Correctness
    - No regressions
    - Security (if relevant)
    - Code style compliance
```

**Output**: Approved OR Changes Requested

### Phase 4: Mini-Acceptance
**Goal**: Verify fix and produce documentation

```
Agent tool:
  subagent_type: "sk-acceptance-reviewer"
  prompt: |
    ## QUICK FIX MODE

    This is a quick fix workflow — lightweight acceptance only.

    **Fix request:** <description>
    **Design note:** openspec/changes/<fix-name>/design.md
    **Docs directory:** openspec/changes/<fix-name>/

    ### What to do:
    1. Read the design note to understand what was supposed to be fixed
    2. Review the implemented code changes
    3. Run all tests and verify they pass
    4. Scan for TODO/FIXME/HACK/XXX in changed files
    5. Write `openspec/changes/<fix-name>/VERIFICATION.md`:
       - Verdict: ACCEPTED or NEEDS WORK
       - What was verified and evidence
       - Test results summary
       - Issues found (if any)
    6. Write `openspec/changes/<fix-name>/SUMMARY.md`:
       - Problem: what was broken
       - Fix: what was changed
       - Files modified: list
       - Tests: what was added/verified

    ### Quick fix rules — MUST FOLLOW:
    - Do NOT build traceability chains (no proposal.md exists)
    - Do NOT write API_CHANGELOG.md or OPERATIONAL_TASKS.md
    - Keep both documents SHORT — aim for 15-30 lines each
    - Focus on: was the fix correct? do tests pass? any regressions?
```

**Output**: VERIFICATION.md + SUMMARY.md

## Execution Flow

```
START
  │
  ├─► [0] Setup: generate fix name, create openspec/changes/<fix-name>/
  │
  ├─► [1] sk-architect (quick mode)
  │       └─► Brief design.md written
  │
  ├─► [2] sk-developer
  │       └─► Fix implemented with tests
  │
  ├─► [3] sk-code-reviewer
  │       ├─► Approved → continue
  │       └─► Changes Requested → Loop to [2] (max 2 iterations)
  │
  ├─► [4] sk-acceptance-reviewer (quick mode)
  │       ├─► ACCEPTED → archive and DONE
  │       └─► NEEDS WORK → Loop to [2] (max 1 iteration)
  │
  └─► COMPLETE: Archive docs, report to user
```

## Developer Quick Fix Instructions

For quick workflow, Developer should:

1. **Read the design note**
   - Check `openspec/changes/<fix-name>/design.md`
   - Understand the architect's recommended approach

2. **Write a test first** (if applicable)
   - Test that fails with current code
   - Test that will pass with fix

3. **Implement the fix**
   - Follow the architect's approach
   - Minimum change needed
   - Follow project patterns
   - Don't refactor unrelated code

4. **Verify**
   - Run tests
   - Confirm fix works

## Your Process

1. **Receive fix request** from user
2. **Confirm it's a quick fix** (not a feature)
3. **Setup**: generate fix name, create `openspec/changes/<fix-name>/`
4. **Invoke Architect** (quick mode) for brief design note
5. **Invoke Developer** with design note context
6. **Invoke Code Reviewer** with changes
7. **Handle review feedback** if needed (max 2 iterations)
8. **Invoke Acceptance Reviewer** (quick mode) for verification + summary
9. **Handle acceptance feedback** if needed (max 1 iteration)
10. **Archive docs**: `mv openspec/changes/<fix-name> openspec/completed/<fix-name>`
11. **Report completion** to user with summary

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
2. Generate fix name and create `openspec/changes/<fix-name>/`
3. Invoke sk-architect (quick mode) for design note
4. Invoke sk-developer with design context
5. After fix, invoke sk-code-reviewer
6. Handle any review feedback
7. Invoke sk-acceptance-reviewer (quick mode) for verification
8. Archive docs to `openspec/completed/<fix-name>/`
9. Report results

</sk-team-quick>
