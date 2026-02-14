---
name: sk-explore-codestyle
version: 1.0.0
description: Analyze project code and generate universal code style guidelines. Detects stack, extracts linter rules, identifies patterns linters don't catch.
license: MIT

# Claude Code
disable-model-invocation: true
allowed-tools: Bash, Glob, Grep, Read, Write, Edit, AskUserQuestion

# Cross-platform hints
platforms:
  codex: true
  cursor: true
  kimi: true
---

# Generate Code Style Guidelines

Analyze the current project and generate comprehensive code style guidelines. Works with any language/framework. Focuses on patterns that linters DON'T catch.

---

## Step 1: Detect Project Stack

### 1.1 Detect Languages

Scan for source files:

```bash
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.java" -o -name "*.kt" -o -name "*.rb" -o -name "*.php" -o -name "*.cs" -o -name "*.swift" -o -name "*.scala" \) -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/vendor/*" -not -path "*/dist/*" 2>/dev/null | head -200 | xargs -I {} basename {} | sed 's/.*\.//' | sort | uniq -c | sort -rn
```

### 1.2 Detect Framework

Check manifest files for framework detection:

| File | Look for |
|------|----------|
| `package.json` | react, vue, angular, next, nest, express, fastify |
| `pyproject.toml` | django, flask, fastapi, pytest |
| `go.mod` | gin, echo, fiber, chi |
| `Cargo.toml` | actix, axum, tokio, rocket |
| `Gemfile` | rails, sinatra, rspec |
| `composer.json` | laravel, symfony |
| `*.csproj` | aspnet, blazor |

### 1.3 Detect Build System

Check for:
- `Makefile`, `justfile`, `Taskfile.yml`
- `gradle`, `maven` (pom.xml)
- `package.json` scripts
- `pyproject.toml` scripts

Record: Language(s), Framework (if any), Build system.

---

## Step 2: Discover Tooling

Search for linter, formatter, and pre-commit configs by language:

### JavaScript/TypeScript
- `.eslintrc*`, `eslint.config.*`, `biome.json`
- `.prettierrc*`, `prettier.config.*`
- `tsconfig.json`, `jsconfig.json`

### Python
- `pyproject.toml` (check `[tool.ruff]`, `[tool.black]`, `[tool.mypy]`, `[tool.pylint]`)
- `ruff.toml`, `.flake8`, `.pylintrc`, `mypy.ini`, `setup.cfg`

### Go
- `go.mod`, `.golangci.yml`

### Rust
- `Cargo.toml`, `clippy.toml`, `rustfmt.toml`

### Ruby
- `Gemfile`, `.rubocop.yml`

### Java/Kotlin
- `checkstyle.xml`, `pmd.xml`, `detekt.yml`
- `spotless` config in gradle

### PHP
- `composer.json`, `.php-cs-fixer.php`, `phpstan.neon`

### C#
- `.editorconfig`, `Directory.Build.props`, `.globalconfig`

### General
- `.editorconfig`
- `.pre-commit-config.yaml`
- `.husky/`

Read found configs to understand existing rules.

---

## Step 3: Extract Key Linter Rules

For each found linter, extract rules that AUTOMATE checks:

### What to Extract

| Tool | Key Rules | What's Automated |
|------|-----------|------------------|
| ESLint | `import/order`, `@typescript-eslint/*` | Import order, type usage |
| Prettier/Biome | All formatting | Formatting, semicolons, quotes |
| Ruff | `I` (isort), `F`, `E` | Imports, basic errors |
| Black | All | Formatting |
| mypy/pyright | Type checking | Type annotations |
| golangci-lint | `gofmt`, `goimports` | Formatting, imports |
| rustfmt | All | Formatting |
| clippy | Lints | Common mistakes |
| RuboCop | Layout, Style | Formatting, naming basics |
| Checkstyle | Naming, format | Java conventions |
| detekt | Style | Kotlin patterns |
| PHP-CS-Fixer | All | Formatting |
| EditorConfig | Indent, charset | Basic formatting |

**Goal:** Build a list of "automated checks" to SKIP during manual review.

---

## Step 4: Check for Existing Rules Files

Search for ALL AI rules files:

```bash
ls -la .claude/rules/code-style.md .claude/CLAUDE.md .cursorrules .cursor/rules/*.mdc AGENTS.md .clinerules .github/copilot-instructions.md CONVENTIONS.md CONTRIBUTING.md 2>/dev/null
```

**If `.claude/rules/code-style.md` exists:**
Use AskUserQuestion:
- Header: "Existing rules"
- Question: "Code style rules already exist. How should I proceed?"
- Options:
  1. "Merge (Recommended)" - Merge new findings with existing rules
  2. "Replace" - Replace existing rules entirely
  3. "Cancel" - Stop and keep existing rules

If "Cancel" selected, stop execution.
If "Merge" selected, read existing file first.

**If OTHER rules files exist (.cursorrules, AGENTS.md, etc.):**
- Read them for additional context
- Note their patterns in the generated doc
- Suggest the user consider consolidating

---

## Step 5: Sample Representative Files

Select **8-12 files** from different areas:

### Core/Lib (2-3 files)
- Main business logic
- Look in: `src/`, `lib/`, `core/`, `app/`

### Entry Points (1-2 files)
- `main.*`, `index.*`, `app.*`, `server.*`
- CLI entry, web entry

### Services/Handlers (2-3 files)
- Business layer
- Look in: `services/`, `handlers/`, `controllers/`, `api/`

### Data/Models (1-2 files)
- Types, schemas, entities
- Look in: `models/`, `types/`, `entities/`, `schemas/`

### Tests (2 files)
- One unit test, one integration test
- Look in: `tests/`, `__tests__/`, `*_test.*`, `*.spec.*`

### Utils (1 file)
- Utility/helper functions
- Look in: `utils/`, `helpers/`, `common/`

**Selection criteria:**
- Moderate size (50-500 lines)
- Not generated or vendored
- Representative of project patterns

Read these files to analyze patterns.

---

## Step 6: Analyze Patterns

Extract patterns across these dimensions:

### Naming (beyond what linters catch)
- Domain-specific prefixes/suffixes
- Handler/Service/Repository naming
- Boolean naming patterns (is/has/should/can)
- Event/callback naming (on/handle/emit)

### Module Organization
- Layer structure (controllers -> services -> repos)
- Feature-based vs layer-based organization
- Barrel/index file patterns
- Public API boundaries

### Error Handling
- Custom error class hierarchy
- Error propagation patterns
- Error wrapping/context
- Logging patterns with errors
- Result/Either/Option patterns

### Dependency Management
- DI approach (constructor, parameter, container)
- Interface usage for abstraction
- Import boundaries between modules

### Concurrency/Async
- async/await vs callbacks vs Promises
- Resource cleanup (finally, defer, using)
- Cancellation patterns
- Concurrency limits

### Testing Patterns
- Test naming conventions
- Fixture/factory patterns
- Mock patterns (jest.mock, testify, unittest.mock)
- Test organization (describe/it, class-based)

### Git/Commit Patterns
Check recent commits for patterns:
```bash
git log --oneline -20 2>/dev/null | head -10
```
- Conventional commits (feat:, fix:, chore:)?
- Ticket references?
- Scope patterns?

---

## Step 7: Generate Document

Create `.claude/rules/` directory if needed:

```bash
mkdir -p .claude/rules
```

Write `.claude/rules/code-style.md` with this structure (target: under 200 lines):

```markdown
# Code Style Guidelines

> Auto-generated [DATE]. Target: <200 lines for LLM context efficiency.

## Project Stack

- **Language:** [detected primary language(s)]
- **Framework:** [if any, or "None"]
- **Build:** [build system]
- **Package Manager:** [npm/yarn/pnpm/pip/cargo/etc.]

---

## Automated by Tooling (skip in review)

These checks are handled by linters/formatters. Don't waste review time on them.

| Category | Tool | What it handles |
|----------|------|-----------------|
| Formatting | [Prettier/Black/etc.] | Indentation, line length, braces |
| Import order | [ESLint/Ruff/etc.] | Import sorting and grouping |
| Basic naming | [linter if configured] | camelCase, PascalCase enforcement |
| Type errors | [TypeScript/mypy/etc.] | Type correctness |

---

## Project Patterns (focus in review)

### Naming Beyond Linters

[Only patterns NOT enforced by linters]
- Handlers: `handle{Action}` or `on{Event}`
- Services: `{Domain}Service`
- Repositories: `{Entity}Repository`
- Booleans: `is{State}`, `has{Thing}`, `can{Action}`
- [Add project-specific patterns]

### Module Organization

[Describe the project's module structure]
- Layer pattern: Controllers -> Services -> Repositories
- Feature folders: `features/{name}/`
- Shared code: `shared/` or `common/`
- [Add project-specific structure]

### Error Handling

[Describe how errors are handled]
- Custom error classes: `{Domain}Error extends BaseError`
- Error wrapping: Always wrap with context
- Logging: Log at catch site with structured data
- [Add project-specific patterns]

### Async/Concurrency

[Describe async patterns]
- Pattern: async/await throughout
- Cleanup: Use try/finally for resources
- Cancellation: [AbortController / context / etc.]
- [Add project-specific patterns]

### Testing

[Describe test conventions]
- Framework: [Jest/pytest/etc.]
- Structure: `describe('{Unit}', () => { it('should...') })`
- Mocks: [pattern used]
- Fixtures: [pattern used]
- [Add project-specific patterns]

### Commits

[If conventional commits detected]
- Format: `type(scope): description`
- Types: feat, fix, chore, docs, refactor, test
- Scope: [module or feature name]

---

## Other Rules Files

[If other rules files were found]
- `.cursorrules` - [brief summary if exists]
- `AGENTS.md` - [brief summary if exists]
- Consider consolidating into this file.

---

*Generated from analysis of [N] source files. Follow existing code patterns when in doubt.*
```

---

## Step 8: Update CLAUDE.md

Check if `.claude/CLAUDE.md` exists:

```bash
ls -la .claude/CLAUDE.md 2>/dev/null
```

**If exists:**
Check if it references code-style. If not, append:

```markdown

## Code Style

See [rules/code-style.md](rules/code-style.md) for code style guidelines.
```

**If doesn't exist:**
Create `.claude/CLAUDE.md`:

```markdown
# Project Guidelines

## Code Style

See [rules/code-style.md](rules/code-style.md) for code style guidelines.
```

---

## Step 9: Report Summary

Output a summary:

```
## Code Style Generation Complete

### Project Stack
- Language: [primary] (+ [secondary])
- Framework: [name or None]
- Build: [system]

### Tooling Detected
- Linter: [tools]
- Formatter: [tools]
- Type checker: [tools]

### Automated Checks (will skip in reviews)
- Formatting
- Import order
- [other automated checks]

### Key Patterns Identified
- Naming: [brief]
- Modules: [brief]
- Errors: [brief]
- Tests: [brief]
- Commits: [conventional/freeform]

### Files Created/Updated
- `.claude/rules/code-style.md` - [created/updated]
- `.claude/CLAUDE.md` - [created/updated]

### Other Rules Files Found
- [list any .cursorrules, AGENTS.md, etc.]

The rules will be automatically loaded in future Claude Code sessions.
Run `/sk-code-review` to review code with these patterns.
```

---

## Guardrails

- **Never modify source code** - Only read source files for analysis
- **Respect existing configs** - Base guidelines on what's already configured
- **Ask before overwriting** - Always ask if code-style.md already exists
- **Descriptive, not prescriptive** - Document what IS, not what SHOULD BE
- **Minimal CLAUDE.md changes** - Only add a reference line, don't restructure
- **Compact output** - Keep generated doc under 200 lines for LLM efficiency
- **Don't duplicate linters** - Focus on what linters DON'T catch
