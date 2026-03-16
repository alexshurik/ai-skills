---
name: sk-code-review
version: 3.0.0
description: Deep code review with best practices research, advanced analysis tools (complexity, maintainability, code smells, security), SOLID/KISS/DRY principles, and language-specific checks. Caches research in .claude/rules/best-practices/.
license: MIT

# Claude Code
disable-model-invocation: true
allowed-tools: Bash, Glob, Grep, Read, AskUserQuestion, WebSearch, WebFetch, Write

# Cross-platform hints
platforms:
  codex: true
  cursor: true
  kimi: true
---

# Code Review for Uncommitted Changes

Deep code review with best practices research and advanced analysis tools. Researches framework/domain best practices before reviewing, runs deep analysis tools (complexity, maintainability, code smells, security), checks SOLID/KISS/DRY principles, and verifies language-specific best practices.

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

## Step 3.5: Research Best Practices

Research best practices for the detected framework and domain. Results are cached for reuse.

### Detect Framework

```bash
# JavaScript/TypeScript frameworks
if [ -f package.json ]; then
  cat package.json | grep -E '"(next|nuxt|@nestjs|express|@sveltejs|remix|astro|@angular|vue|react)"' 2>/dev/null
fi

# Python frameworks
if [ -f pyproject.toml ] || [ -f requirements.txt ] || [ -f setup.py ]; then
  grep -iE '(fastapi|django|flask|starlette|tornado|sanic)' pyproject.toml requirements.txt setup.py 2>/dev/null
fi

# Go frameworks
if [ -f go.mod ]; then
  grep -E '(gin-gonic|echo|fiber|chi|gorilla)' go.mod 2>/dev/null
fi

# Rust frameworks
if [ -f Cargo.toml ]; then
  grep -iE '(actix|axum|rocket|warp|tide)' Cargo.toml 2>/dev/null
fi
```

### Detect Domain from Changed Files

Scan changed file paths (from `git status --porcelain`) for domain signals:

| Path patterns | Domain |
|--------------|--------|
| `auth/`, `login`, `session`, `oauth`, `jwt`, `token` | authentication |
| `pay/`, `billing`, `stripe`, `checkout` | payment-processing |
| `middleware/`, `interceptor` | middleware |
| `migration/`, `schema`, `model` | database |
| `websocket`, `realtime`, `sse` | realtime |
| `cache/`, `redis` | caching |
| `queue/`, `worker`, `job` | background-jobs |
| `upload/`, `storage`, `s3` | file-storage |
| `email/`, `notification`, `sms` | notifications |
| `search/`, `elastic`, `algolia` | search |

**If no framework AND no domain detected → skip this step.**

### Check Cache

```bash
ls .claude/rules/best-practices/ 2>/dev/null
```

**If `.claude/rules/best-practices/[name].md` exists:**

Use AskUserQuestion:
- Header: "Best Practices Cache"
- Question: "Found cached best practices for [name] (researched [DATE]). What would you like to do?"
- Options:
  1. "Use cached" - description: "Use existing best practices for review"
  2. "Research fresh" - description: "Conduct new research and update cache"
  3. "Use cached + supplement for [domain]" - description: "Keep framework practices, add domain research" (only if domain detected)

**If cache does not exist → proceed to research.**

### Conduct Research

Use 3-5 WebSearch queries + 5-8 WebFetch calls:

**For framework:**
1. **WebSearch:** `"[framework] best practices [current_year]"` → **WebFetch** top 2-3 results
2. **WebSearch:** `"[framework] common mistakes anti-patterns"` → **WebFetch** top 1-2 results
3. **WebSearch:** `"[framework] security best practices"` → **WebFetch** top 1-2 results
4. **WebSearch:** `"[framework] performance optimization"` → **WebFetch** top 1 result

**For domain:**
5. **WebSearch:** `"[framework_or_language] [domain] best practices security"` → **WebFetch** top 2 results

**Extract:**
- Concrete, actionable patterns (not vague advice)
- Anti-patterns with WHY they're bad and WHAT to do instead
- Security rules with specific examples
- Performance pitfalls with measurable impact

### Save to Cache

```bash
mkdir -p .claude/rules/best-practices
```

Write `.claude/rules/best-practices/[name].md`:

```markdown
# Best Practices: [Framework/Domain Name]

> Last researched: [YYYY-MM-DD]
> Sources: [list of URLs]

## Key Patterns
- [Pattern]: [brief explanation]

## Anti-Patterns (flag in review)
- [Anti-pattern]: [why bad] → [what instead]

## Security Considerations
- [Rule with example]

## Performance Considerations
- [Rule with impact]
```

### Load for Review

Read cached file(s) and use as **Supplementary Review Criteria** during Step 6 analysis.

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

## Step 4.5: Run Deep Analysis Tools

Run advanced code quality analysis beyond linters. Only run tools that are **already installed**.

**Priority:** security → complexity/maintainability → code smells → duplication → dependency audit

### Multi-Language Tools

```bash
# Semgrep — security & pattern analysis (17+ languages)
if command -v semgrep &> /dev/null; then
  semgrep --config auto --severity ERROR --severity WARNING --quiet --json . 2>/dev/null | head -500
fi

# jscpd — copy-paste / code duplication (any language)
if command -v jscpd &> /dev/null; then
  jscpd --reporters console --threshold 5 --min-lines 5 --min-tokens 50 . 2>/dev/null
fi

# lizard — cyclomatic complexity, function length, params (17+ languages)
if command -v lizard &> /dev/null; then
  lizard . --CCN 10 -w -L 50 -a 5 2>/dev/null | head -200
fi
```

### JavaScript/TypeScript

```bash
if [ -f package.json ]; then
  npm audit --json 2>/dev/null | head -200

  if command -v madge &> /dev/null; then
    madge --circular --extensions ts,tsx,js,jsx src/ 2>/dev/null
  fi

  if command -v depcheck &> /dev/null; then
    depcheck . 2>/dev/null
  fi

  if grep -q "sonarjs" package.json .eslintrc* eslint.config.* 2>/dev/null; then
    npx eslint --format json ./src 2>/dev/null | head -500
  fi
fi
```

### Python

```bash
if [ -f pyproject.toml ] || [ -f setup.py ] || [ -f requirements.txt ]; then
  if command -v bandit &> /dev/null; then
    bandit -r . -f json --severity-level medium 2>/dev/null | head -500
  fi

  if command -v radon &> /dev/null; then
    radon cc -j -n C . 2>/dev/null | head -200
    radon mi -j -s . 2>/dev/null | head -200
    radon hal -j . 2>/dev/null | head -200
  fi

  if command -v vulture &> /dev/null; then
    vulture . --min-confidence 80 2>/dev/null | head -100
  fi

  if command -v pip-audit &> /dev/null; then
    pip-audit 2>/dev/null | head -100
  fi

  if command -v pylint &> /dev/null; then
    pylint --disable=all --enable=R0801,R0912,R0913,R0914,R0915,R0911,C0901 --output-format=json . 2>/dev/null | head -300
  fi
fi
```

### Go

```bash
if [ -f go.mod ]; then
  if command -v gosec &> /dev/null; then
    gosec -fmt json ./... 2>/dev/null | head -300
  fi

  if command -v gocognit &> /dev/null; then
    gocognit -over 10 -top 20 -avg ./... 2>/dev/null
  fi

  if command -v golangci-lint &> /dev/null; then
    golangci-lint run --enable gocritic,gocognit,gocyclo --out-format json ./... 2>/dev/null | head -500
  fi
fi
```

### Rust

```bash
if [ -f Cargo.toml ]; then
  if command -v cargo-deny &> /dev/null; then
    cargo deny check 2>/dev/null | head -200
  elif command -v cargo-audit &> /dev/null; then
    cargo audit 2>/dev/null | head -200
  fi

  cargo clippy --message-format=json -- -W clippy::cognitive_complexity 2>/dev/null | head -300
fi
```

### Severity Mapping

| Category | Condition | Severity |
|----------|-----------|----------|
| Security (semgrep/bandit/gosec) | any finding | **BLOCKER** |
| Vulnerable deps (audit tools) | high/critical CVE | **BLOCKER** |
| Vulnerable deps (audit tools) | moderate CVE | **MAJOR** |
| Cyclomatic complexity | >15 CCN | **MAJOR** |
| Cyclomatic complexity | >10 CCN | **MINOR** |
| Cognitive complexity | >15 | **MAJOR** |
| Cognitive complexity | >10 | **MINOR** |
| Maintainability Index | <20 | **MAJOR** |
| Maintainability Index | <40 | **MINOR** |
| Code duplication (jscpd) | >5 lines | **MAJOR** (DRY) |
| Circular deps (madge) | any cycle | **MAJOR** |
| Dead code (vulture) | >80% confidence | **MINOR** |
| Code smells (pylint/sonarjs) | structural issues | **MAJOR** |
| Unused deps (depcheck) | any | **MINOR** |

**Note:** Skip tools that take >30 seconds. Record unavailable tools for the report.

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

**Important:** If Step 3.5 produced Supplementary Review Criteria from best practices research, apply those criteria throughout this analysis in addition to the standard checks below.

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

### Best Practices Review
[Only include if research was conducted in Step 3.5]
Source: .claude/rules/best-practices/[name].md (researched [DATE])

#### Patterns Compliance
- [x] [Pattern 1]: followed
- [ ] [Pattern 2]: violation in file.ts:42
  - **Problem:** [what's wrong]
  - **Best practice:** [correct approach + source]

#### Anti-Patterns Detected
- [Anti-pattern]: found in file.ts:42 — [description + recommendation]

---

### Deep Analysis Results
[Only include if tools were run in Step 4.5]

#### Security
| Tool | Findings | Details |
|------|----------|---------|
| [tool] | [N] issues | [summary] |

#### Complexity & Maintainability
| Tool | Metric | Result | Status |
|------|--------|--------|--------|
| [tool] | [metric] | [value] | OK/MAJOR/MINOR |

#### Code Smells
| Tool | Findings | Details |
|------|----------|---------|
| [tool] | [N] issues | [summary] |

#### Tools Not Available
Consider installing for better coverage: [list]

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
- Deep analysis findings: N (X blocker, Y major, Z minor)
- Best practices: [Researched/Cached/Skipped]
- Critical issues: N
- Warnings: N
- Suggestions: N
```

**Section rules:**
- Omit empty sections (except Summary and Summary Stats)
- Omit "Style Guide Compliance" entirely if no code-style.md loaded
- Omit "Best Practices Review" if no research was conducted
- Omit "Deep Analysis Results" if no tools were run
- Omit language-specific sections if not applicable
- Use severity levels: CRITICAL (must fix), WARNING (should fix), SUGGESTION (could improve)

---

## Guardrails

- **Read-only for source code** - NEVER make any changes to source code files. This is strictly a review.
- **Write only to cache** - The Write tool may ONLY be used for `.claude/rules/best-practices/` files
- **No commits** - Do not create, amend, or modify any commits
- **No git operations** - Only read git state, never modify it
- **Objective review** - Focus on the code, not on validating prior decisions
- **Fresh perspective** - Ignore any prior conversation context about these changes
- **Don't duplicate linters** - Skip checks that are automated by tooling
- **Focus on patterns** - Prioritize SOLID/KISS/DRY over generic style
- **Language-specific** - Apply appropriate best practices for detected stack
- **Research-informed** - When best practices are available, cite specific patterns and sources
- **Tool-evidence based** - Include deep analysis tool output to back up findings
- **Don't skip tools** - Run all available deep analysis tools before manual review
