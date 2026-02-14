---
name: sk-plan-mode
version: 1.0.0
description: Structured planning workflow with file-based plan storage. Separates research from execution through 4 phases. Wait for explicit user approval before making changes.
license: MIT

# Claude Code
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
disable-model-invocation: true

# Cross-platform hints
platforms:
  codex: true
  cursor: true
  kimi: true
---

# /sk-plan-mode - Structured Planning Workflow

Activate Plan Mode to separate research from execution. Creates a detailed plan file that requires explicit user approval before any changes are made.

## Overview

Plan Mode provides a **4-phase planning workflow** inspired by Claude Code's plan mode:

```
UNDERSTANDING → DESIGN → REVIEW → FINAL PLAN → WAIT FOR APPROVAL → EXECUTE
```

## When to Use Plan Mode

- **Multi-step implementation** - Feature requires changes to many files
- **Complex refactoring** - Need to understand codebase before changing
- **Safety-critical changes** - Want to review plan before execution
- **Exploration first** - Research codebase thoroughly before modifications

## Quick Start

```
/sk-plan-mode Refactor authentication to use OAuth2
```

Or manually:
```
Enter Plan Mode. Analyze the database layer and create a migration plan.
```

---

## 🔒 Plan Mode Rules

### STRICTLY FORBIDDEN (without explicit approval):
- ❌ Writing, editing, or deleting any files **EXCEPT the plan file**
- ❌ Running shell commands that modify the system
- ❌ Installing/uninstalling packages  
- ❌ Creating git commits, branches, or tags
- ❌ Making any destructive operations

### ALLOWED (read-only operations):
- ✅ Reading files
- ✅ Searching (grep, glob)
- ✅ Running read-only commands (`ls`, `cat`, `git status`, `git log`, etc.)
- ✅ Asking clarifying questions
- ✅ Writing to the plan file only

---

## 📋 The 4 Phases of Planning

### Phase 1: Initial Understanding 🕵️
**Goal**: Gain comprehensive understanding of the user's request

**Actions**:
1. Read relevant files in the codebase
2. Identify key components, dependencies, and constraints
3. Ask clarifying questions to the user
4. Document findings in the plan file

**Output**: Background context with filenames and code paths

---

### Phase 2: Design 🏗️
**Goal**: Design an implementation approach

**Actions**:
1. Analyze different implementation options
2. Consider trade-offs and edge cases
3. Define the recommended approach
4. Document technical details

**Output**: Detailed implementation plan with rationale

---

### Phase 3: Review 🔍
**Goal**: Ensure alignment with user's intentions

**Actions**:
1. Verify plan addresses all requirements
2. Identify potential risks or issues
3. Add any missing details
4. Confirm file paths and changes

**Output**: Validated plan with risk assessment

---

### Phase 4: Final Plan 📝
**Goal**: Write the final plan to the plan file

**Actions**:
1. Include ONLY the recommended approach (not alternatives)
2. Make the plan concise but detailed enough to execute
3. List all critical files to be modified
4. Mark plan as complete

**Output**: Final plan in structured format

---

## 📁 Plan File Location

Create the plan file at one of these locations (in order of preference):
1. `.kimi/plan.md` (if `.kimi/` directory exists or can be created)
2. `PLAN.md` in the project root
3. `.plan.md` (hidden file in project root)

Use this exact template for the plan file:

```markdown
# 📋 Plan: [Task Title]

## Summary
Brief description of what this plan accomplishes.

## Background (Phase 1)
- **Request**: What the user asked for
- **Key Files Identified**:
  - `path/to/file1` - purpose
  - `path/to/file2` - purpose
- **Constraints**: Any limitations or requirements discovered

## Implementation Plan (Phase 2)

### Changes Overview
| File | Action | Description |
|------|--------|-------------|
| `path/to/file` | Create/Edit/Delete | What will be changed |

### Detailed Steps
1. **Step 1**: Description
   - File: `path`
   - Changes: Specific modifications
   
2. **Step 2**: Description
   - File: `path`
   - Changes: Specific modifications

## Risk Assessment (Phase 3)
| Risk | Level | Mitigation |
|------|-------|------------|
| Risk description | Low/Medium/High | How to handle it |

## Checklist
- [ ] Phase 1: Understanding complete
- [ ] Phase 2: Design complete
- [ ] Phase 3: Review complete
- [ ] Phase 4: Final plan written
- [ ] Ready for approval

## Status: 🟡 IN PROGRESS / 🟢 READY FOR APPROVAL
```

---

## 🔄 Complete Workflow

### When User Requests Plan Mode

1. **Acknowledge Plan Mode**
   ```
   🛑 PLAN MODE ACTIVATED
   
   I will analyze your request and create a detailed plan.
   I will NOT make any changes until you explicitly approve.
   
   Creating plan file: `.kimi/plan.md`
   ```

2. **Execute 4 Phases**
   - Work through each phase systematically
   - Update the plan file after each phase
   - Use read-only tools only

3. **Signal Completion**
   When plan is complete, say EXACTLY:
   
   ```
   ✅ **PLAN COMPLETE - AWAITING APPROVAL**
   
   Plan file: `.kimi/plan.md`
   
   ## Summary
   [2-3 sentences about what the plan does]
   
   ## Key Changes
   - [ ] File 1 - Action
   - [ ] File 2 - Action
   - [ ] File 3 - Action
   
   ## Next Steps
   Please review the plan and reply with:
   
   1. **"Approved"** or **"Execute"** - to proceed with implementation
   2. **"Modify: [specific changes]"** - to adjust the plan
   3. **"Cancel"** - to abort
   4. **Edit the plan file directly** - to make your own changes
   
   ⏸️ Waiting for your approval...
   ```

4. **Wait for Explicit Approval**
   - Do NOT proceed until user says "Approved", "Yes", "Go", "Execute", or similar
   - Acceptable: "Approved", "Yes", "Go", "Execute", "Proceed", "Do it"
   - NOT acceptable: just "ok", "sounds good", thumbs up emoji (ask for explicit confirmation)

5. **Execute (Only After Approval)**
   - Read the plan file
   - Execute step by step
   - Use SetTodoList to track progress
   - Report after each major step

---

## ✏️ Editing the Plan

User can modify the plan by:
1. Replying with "Modify: [changes]" - you'll update the plan file
2. Editing the plan file directly - you'll read it before execution
3. Asking questions - you'll clarify and update plan

Always re-read the plan file before execution if user made edits.

---

## 🎯 Examples

### Example 1: Database Migration

**User**: `/sk-plan-mode Migrate from PostgreSQL to MongoDB`

**Response**:
```
🛑 PLAN MODE ACTIVATED

I will analyze the current database layer and create a migration plan.
I will NOT make any changes until you explicitly approve.

Creating plan file: `.kimi/plan.md`
```

**After Phase 1-4**:
```
✅ **PLAN COMPLETE - AWAITING APPROVAL**

Plan file: `.kimi/plan.md`

## Summary
Migrate user and order data from PostgreSQL to MongoDB with zero downtime
dusing the strangler fig pattern.

## Key Changes
- [ ] `src/models/user.ts` - Add MongoDB schema alongside PostgreSQL
- [ ] `src/models/order.ts` - Add MongoDB schema alongside PostgreSQL
- [ ] `src/db/migrate.ts` - Create data migration script
- [ ] `docker-compose.yml` - Add MongoDB service
- [ ] `.env.example` - Add MongoDB connection string

## Next Steps
Please review the plan and reply with "Approved" to proceed.
```

### Example 2: API Refactoring

**User**: `/sk-plan-mode Refactor REST API to GraphQL`

**Response**:
```
🛑 PLAN MODE ACTIVATED

I will analyze the current REST API and create a GraphQL migration plan.
```

---

## 🚫 Common Mistakes to Avoid

### ❌ BAD: Executing without approval
```
User: "Set up notifications"
Assistant: *immediately creates files*
```

### ❌ BAD: Assuming approval from vague response
```
User: "ok"
Assistant: *starts executing*
```

### ❌ BAD: Not creating a plan file
```
Assistant: *keeps plan only in memory*
```

### ❌ BAD: Skipping phases
```
Assistant: *jumps straight to Phase 4 without understanding*
```

---

## ✅ Best Practices

### ✅ Create structured plan
- Use the template format
- Include all 4 phases
- Be specific about file paths

### ✅ Clear approval request
- Explicitly ask for "Approved"
- List acceptable responses
- Explain next steps

### ✅ Respect user edits
- Re-read plan if user modified it
- Confirm understanding of changes
- Ask for re-approval if needed

### ✅ Safe execution
- Follow plan exactly
- Report progress
- Ask if deviations needed

---

## Integration with Other Skills

Plan Mode works well with:
- `/sk-team-feature` - Use Plan Mode during the Architect phase
- `/sk-code-review` - Plan Mode first, then review the plan
- `/sk-explore-codebase` - Use before Plan Mode to understand structure

---

## Platform-Specific Notes

### Claude Code
Plan Mode is similar to Claude Code's built-in `/plan` command, but:
- Creates a visible plan file that users can edit
- 4 explicit phases instead of internal state
- Works across all platforms

### Kimi CLI
Use with slash command:
```
/skill:sk-plan-mode Migrate database
```

Or mention in conversation:
```
Enter Plan Mode. I want to refactor the auth system.
```

---

**REMEMBER: The user trusts you to NOT make changes until they say "Approved". Respect that trust.**
