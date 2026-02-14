---
name: sk-code-review
version: 1.0.0
description: Review uncommitted changes with fresh context. Skips automated checks, focuses on patterns linters miss.
license: MIT

# Claude Code
disable-model-invocation: true
allowed-tools: Bash, Glob, Grep, Read, AskUserQuestion

# Cross-platform hints
platforms:
  codex: true
  cursor: true
  kimi: true
---

# Code Review for Uncommitted Changes

Review all uncommitted changes in the current repository with a fresh perspective.

**IMPORTANT: Context Reset.** Treat this as a fresh review session. Ignore any prior conversation context. Your only focus is analyzing the uncommitted changes objectively.

---

## Step 1: Check for OpenSpec Context

Check if there are active OpenSpec changes that might provide context:

```bash
openspec list --json 2>/dev/null || echo "NO_OPENSPEC"
```

**If proposals exist:**
- Use AskUserQuestion to ask the user if they want to review changes in context of a specific proposal
- Options: list active proposal names + "No, review without proposal context"
- If user selects a proposal, read `openspec/changes/<name>/proposal.md` and `openspec/changes/<name>/tasks.md` for context

**If no proposals or user declines:** Proceed without proposal context.

---

## Step 1.5: Load Project Code Style

Check for project-specific code style rules:

### Search for rules files

```bash
ls -la .claude/rules/code-style.md .claude/CLAUDE.md .cursorrules .cursor/rules/*.mdc AGENTS.md .clinerules .github/copilot-instructions.md 2>/dev/null
```

### If code-style.md exists

Read the file and parse these key sections:

**1. "Automated by Tooling" section:**
- Extract the table of automated checks
- Store as `SKIP_IN_REVIEW` list (formatting, imports, basic naming, types)
- These will NOT be checked manually

**2. "Project Patterns" section:**
- Extract each subsection (Naming, Module Org, Error Handling, Async, Testing, Commits)
- Store as `FOCUS_IN_REVIEW` list
- These WILL be the focus of pattern compliance

### If code-style.md does NOT exist

Use AskUserQuestion:
- Header: "Code style"
- Question: "No code style rules found. Generate them first for better review quality?"
- Options:
  1. "Yes, generate (Recommended)" - description: "Stop and generate code style rules first"
  2. "No, continue" - description: "Proceed with generic review"

If user selects "Yes, generate":
- Output: "Run `/sk-explore-codestyle` first to generate project-specific code style rules, then run `/sk-code-review` again."
- Stop execution.

If user selects "No, continue":
- Proceed with generic review (no automated skips, no pattern focus)

---

## Step 2: Detect Changes

Check for uncommitted changes:

```bash
git status --porcelain
```

**If no changes:**
Output: "No uncommitted changes to review." and stop.

**If changes exist:** Continue to next step.

---

## Step 3: Gather Full Diff

Get the complete diff of all changes:

```bash
git diff HEAD
```

Also get list of untracked files:

```bash
git status --porcelain | grep "^??" | cut -c4-
```

For untracked files, read their contents to include in the review.

---

## Step 4: Analyze Changes

### 4.1 Universal Checks (always apply)

#### Correctness
- Logic errors
- Edge cases not handled
- Incorrect assumptions
- Off-by-one errors
- Null/undefined handling

#### Security
- Injection vulnerabilities (SQL, command, XSS)
- Authentication/authorization issues
- Secrets or credentials in code
- Unsafe deserialization
- Path traversal

#### Performance
- N+1 queries
- Unnecessary allocations
- Missing indexes (if schema changes)
- Blocking operations in async code
- Memory leaks

#### Testing
- Missing test coverage for new code
- Tests that don't test the right thing
- Brittle tests

---

### 4.2 Maintainability (conditional)

**SKIP if in SKIP_IN_REVIEW list:**
- Formatting (if Prettier/Black/gofmt/etc. detected)
- Import ordering (if ESLint import/order, Ruff I, goimports detected)
- Basic naming conventions (if linter enforces camelCase/PascalCase)
- Type correctness (if TypeScript/mypy/etc. detected)

**ALWAYS check (linters don't catch these):**
- Code duplication
- Complex logic that needs simplification
- Unclear intent / poor abstraction
- Magic numbers without explanation
- Dead code introduction

---

### 4.3 Project Patterns (if code-style.md loaded)

Check FOCUS_IN_REVIEW patterns:

#### Naming Patterns
- Does new code follow domain naming conventions?
- Handler/Service/Repository naming consistent?
- Boolean naming (is/has/can) matches project pattern?

#### Module Organization
- Are layer boundaries respected?
- Is code in the right directory/module?
- Are imports following the dependency direction?

#### Error Handling
- Using project's error class hierarchy?
- Error wrapping/context consistent?
- Logging pattern matches project?

#### Async/Concurrency
- Using project's async pattern?
- Resource cleanup present?
- Cancellation handled if applicable?

#### Testing
- Test structure matches project pattern?
- Using project's mock/fixture approach?

---

### 4.4 Architectural Review

Always check, regardless of code-style.md:

- **Layer boundary violations**: Controller importing Repository directly?
- **Dependency direction**: Lower layers importing higher layers?
- **Circular dependency risk**: New imports creating cycles?
- **Abstraction leaks**: Implementation details exposed in APIs?

---

## Step 5: Generate Report

Output a structured review report:

```
## Code Review Report

### Summary
[1-2 sentence overview of the changes and overall assessment]

### Files Changed
- `path/to/file1.ts` - [brief description of changes]
- `path/to/file2.ts` - [brief description of changes]

---

### Critical Issues
[Issues that must be fixed before committing]

> **[CRITICAL]** `file.ts:42` - [description]
> ```
> [relevant code snippet]
> ```
> **Why:** [explanation]
> **Fix:** [suggested fix]

---

### Warnings
[Issues that should be addressed but aren't blocking]

> **[WARNING]** `file.ts:15` - [description]
> **Why:** [explanation]
> **Suggestion:** [how to improve]

---

### Suggestions
[Optional improvements for code quality]

> **[SUGGESTION]** `file.ts:88` - [description]
> **Rationale:** [why this would be better]

---

### Looks Good
[Positive observations about the changes, if any]

---

### Style Guide Compliance
[Only include if code-style.md was loaded]

**Automated (verified by tooling):**
- Formatting: Handled by [tool]
- Imports: Handled by [tool]
- Types: Handled by [tool]

**Project Patterns:**
- Naming follows conventions
- Module organization correct
- Error handling differs from pattern (line X)
  - Expected: `throw new DomainError(...)`
  - Found: `throw new Error(...)`
- Layer violation: Controller imports Repository directly
  - Expected: Controller -> Service -> Repository
  - Found: Controller -> Repository

**Legend:** Follows | Deviation (discuss) | Violation (fix)

---

### Summary Stats
- Files changed: N
- Lines added: +N
- Lines removed: -N
- Critical issues: N
- Warnings: N
- Suggestions: N
```

**Section rules:**
- Omit empty sections (except Summary and Summary Stats)
- Omit "Style Guide Compliance" entirely if no code-style.md loaded
- Use severity levels: CRITICAL (must fix), WARNING (should fix), SUGGESTION (could improve)

---

## Guardrails

- **Read-only mode** - NEVER make any changes to files. This is strictly a review.
- **No commits** - Do not create, amend, or modify any commits
- **No git operations** - Only read git state, never modify it
- **Objective review** - Focus on the code, not on validating prior decisions
- **Fresh perspective** - Ignore any prior conversation context about these changes
- **Don't duplicate linters** - Skip checks that are automated by tooling
- **Focus on patterns** - Prioritize project-specific patterns over generic style
