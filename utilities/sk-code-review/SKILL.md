---
name: sk-code-review
version: 2.0.0
description: Review uncommitted changes with fresh context. Runs linters, checks SOLID/KISS/DRY principles, verifies language-specific best practices. Skips automated checks, focuses on patterns linters miss.
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

Review all uncommitted changes in the current repository with a fresh perspective. Runs linters, checks SOLID/KISS/DRY principles, and verifies language-specific best practices.

**IMPORTANT: Context Reset.** Treat this as a fresh review session. Ignore any prior conversation context. Your only focus is analyzing the uncommitted changes objectively.

---

## Step 1: Check for Project Context

Check if there are active project specifications or design documents:

```bash
find . -maxdepth 3 -name "design.md" -o -name "*.spec.md" -o -name "PROPOSAL.md" 2>/dev/null | head -10
```

**If design documents exist:**
- Use AskUserQuestion to ask the user if they want to review changes in context of a specific document
- Options: list found documents + "No, review without context"
- If user selects a document, read it for context

**If no documents or user declines:** Proceed without additional context.

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

Detect the project stack to apply language-specific rules:

```bash
# Detect languages
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.java" -o -name "*.kt" \) -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/venv/*" -not -path "*/__pycache__/*" -not -path "*/.pytest_cache/*" 2>/dev/null | head -100 | xargs -I {} basename {} | sed 's/.*\.//' | sort | uniq -c | sort -rn

# Detect tooling configs
ls -la .eslintrc* eslint.config.* .prettierrc* prettier.config.* pyproject.toml setup.cfg ruff.toml .flake8 .golangci.yml Cargo.toml 2>/dev/null
```

Record: Primary language(s), detected linters/formatters.

---

## Step 3: Detect Changes

Check for uncommitted changes:

```bash
git status --porcelain
```

**If no changes:**
Output: "No uncommitted changes to review." and stop.

**If changes exist:** Continue to next step.

---

## Step 4: Run Linters and Static Analysis

Run linters and formatters if detected to catch automated issues first:

### JavaScript/TypeScript
```bash
if [ -f package.json ]; then
  npm run lint 2>/dev/null || yarn lint 2>/dev/null || pnpm lint 2>/dev/null || echo "No lint script"

  if [ -f tsconfig.json ]; then
    npx tsc --noEmit 2>/dev/null || echo "TypeScript check skipped"
  fi
fi
```

### Python
```bash
if command -v ruff &> /dev/null; then
  ruff check . 2>/dev/null
  ruff format --check . 2>/dev/null
elif [ -f pyproject.toml ] || [ -f setup.cfg ]; then
  black --check . 2>/dev/null
  flake8 . 2>/dev/null
fi

if [ -f pyproject.toml ] && grep -q "mypy" pyproject.toml 2>/dev/null; then
  mypy . 2>/dev/null
fi
```

### Go
```bash
if [ -f go.mod ]; then
  gofmt -l . 2>/dev/null
  go vet ./... 2>/dev/null
  if command -v golangci-lint &> /dev/null; then
    golangci-lint run 2>/dev/null
  fi
fi
```

### Rust
```bash
if [ -f Cargo.toml ]; then
  cargo fmt -- --check 2>/dev/null
  cargo clippy 2>/dev/null
fi
```

**Note:** Record any linter violations. These are BLOCKERS.

---

## Step 5: Gather Full Diff

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

## Step 6: Analyze Changes

### 6.1 Universal Checks (always apply)

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

### 6.2 SOLID Principles Check

#### Single Responsibility Principle (SRP)
- Each class/module has ONE reason to change
- No "god objects" that do everything
- Functions are focused on a single task
- File length reasonable (<300-400 lines)

#### Open/Closed Principle (OCP)
- New functionality extends rather than modifies existing code
- Abstract classes/interfaces used appropriately

#### Liskov Substitution Principle (LSP)
- Derived classes can substitute base classes without issues
- No unexpected behavior in subclasses

#### Interface Segregation Principle (ISP)
- Interfaces are client-specific, not fat interfaces
- No dependency on unused methods

#### Dependency Inversion Principle (DIP)
- High-level modules depend on abstractions, not low-level details
- Dependency injection used appropriately

---

### 6.3 KISS, DRY, YAGNI Check

#### KISS (Keep It Simple, Stupid)
- Code solves the problem simply without over-engineering
- No unnecessary design patterns
- No speculative abstraction "just in case"

#### DRY (Don't Repeat Yourself)
- No duplication of logic >3 lines
- Magic values extracted to constants
- Common logic extracted to functions/utilities

#### YAGNI (You Ain't Gonna Need It)
- No speculative functionality added
- No unused parameters or variables
- No "future-proofing" without clear requirements

---

### 6.4 Maintainability (conditional)

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
- SOLID violations
- Deep nesting (>3 levels)
- Functions with >4 parameters

---

### 6.5 Language-Specific Best Practices

#### Python-Specific
- **PEP 8 Compliance**: 4 spaces, 88-100 char lines
- **Import Organization** (3 groups: stdlib, third-party, local)
- Absolute imports preferred over relative
- No wildcard imports (`from module import *`)
- Type hints for public APIs
- f-strings for formatting
- `pathlib` over `os.path`
- `is None` / `is not None` for None checks
- `@dataclass` for data containers

#### TypeScript/JavaScript-Specific
- No `any` types (use `unknown` with guards)
- Strict null checks
- `===`/`!==` over `==`/`!=`
- Optional chaining (`?.`) and nullish coalescing (`??`)
- Async/await (not raw promises)
- `const`/`let` (no `var`)
- Event listeners cleaned up

#### Go-Specific
- Explicit error handling (`err != nil`)
- Errors wrapped with context
- Context propagation for cancellation
- Small interfaces (interface segregation)
- Resource cleanup with `defer`
- No unused imports

#### Rust-Specific
- Handle `Result` and `Option` properly
- `?` operator for error propagation
- Ownership and borrowing correct
- No unwrap in production code

---

### 6.6 Import and Module Organization

- Imports grouped logically (stdlib → third-party → local)
- No unused imports
- No circular dependencies
- No deep relative paths (`../../../../`)
- Barrel exports consistent
- Clear separation of concerns
- Public API boundaries clear

---

### 6.7 Architecture Review

Always check, regardless of code-style.md:

- **Layer boundary violations**: Controller importing Repository directly?
- **Dependency direction**: Lower layers importing higher layers?
- **Circular dependency risk**: New imports creating cycles?
- **Abstraction leaks**: Implementation details exposed in APIs?
- **SOLID violations**: Architecture patterns violated?

---

## Step 7: Generate Report

Output a structured review report:

```
## Code Review Report

### Summary
[1-2 sentence overview of the changes and overall assessment]

### Files Changed
- `path/to/file1.ts` - [brief description of changes]
- `path/to/file2.ts` - [brief description of changes]

---

### Linter/Static Analysis Results
[Linter output if run]

---

### SOLID Principles

| Principle | Status | Notes |
|-----------|--------|-------|
| Single Responsibility | ✅/⚠️/❌ | [Notes if issues] |
| Open/Closed | ✅/⚠️/❌ | [Notes if issues] |
| Liskov Substitution | ✅/⚠️/❌ | [Notes if issues] |
| Interface Segregation | ✅/⚠️/❌ | [Notes if issues] |
| Dependency Inversion | ✅/⚠️/❌ | [Notes if issues] |

---

### KISS/DRY/YAGNI

- **KISS**: ✅/⚠️/❌ - [Notes]
- **DRY**: ✅/⚠️/❌ - [Notes if duplication found]
- **YAGNI**: ✅/⚠️/❌ - [Notes if speculative code]

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

### Language-Specific Issues

#### Python
- [PEP 8/import/typing issues]

#### TypeScript/JavaScript
- [Type safety/modern syntax issues]

#### Go
- [Error handling/conventions issues]

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
- Linter issues: N
- Critical issues: N
- Warnings: N
- Suggestions: N
```

**Section rules:**
- Omit empty sections (except Summary and Summary Stats)
- Omit "Style Guide Compliance" entirely if no code-style.md loaded
- Omit language-specific sections if not applicable
- Use severity levels: CRITICAL (must fix), WARNING (should fix), SUGGESTION (could improve)

---

## Guardrails

- **Read-only mode** - NEVER make any changes to files. This is strictly a review.
- **No commits** - Do not create, amend, or modify any commits
- **No git operations** - Only read git state, never modify it
- **Objective review** - Focus on the code, not on validating prior decisions
- **Fresh perspective** - Ignore any prior conversation context about these changes
- **Don't duplicate linters** - Skip checks that are automated by tooling
- **Focus on patterns** - Prioritize SOLID/KISS/DRY over generic style
- **Language-specific** - Apply appropriate best practices for detected stack
