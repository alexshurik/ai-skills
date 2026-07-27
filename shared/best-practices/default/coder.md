# Default Coder Profile

Universal coding rules applied to every project. Language-specific rules are loaded from language profiles and take precedence where they conflict.

## Keep It Simple

Solve the problem at hand directly. Resist the urge to introduce
configuration, registries, or pluggable strategies until the second
distinct caller appears. Three similar lines beat a premature abstraction.

See language-specific profiles for idiomatic examples.

## Follow Project Authority

Use this precedence:

```text
approved specification / ADR / repository guidance
  > enforced tooling
  > approved project profile
  > observed neighboring code
```

- Load `.agents/best-practices/project/coder.md` when present. It contains only
  Enforced and Approved project rules.
- Treat `.agents/best-practices/project/evidence.md` and neighboring code as
  evidence, not automatic instructions.
- Run the project's formatter/linter/type/build commands through its pinned runner.
- When a frequent pattern conflicts with a higher authority, follow the authority.
  Stop for clarification when the conflict affects architecture or public behavior.
- In greenfield code without project authority, use language/framework profiles as
  defaults and make material choices explicit.

## Write Readable Code

- Clear, intention-revealing variable names — **no single-letter names**, even for counters
- Short functions: < 20 lines ideal, **70 lines hard max** — split longer functions into sub-methods
- Functions have **< 4 parameters** — use an options/config object if more
- File/module docstrings follow Enforced or Approved project/language guidance;
  sample absence/presence alone does not create a rule
- **No dead code, commented-out code, or debug statements** left in
- **Comments only for complex/non-obvious logic** — if the code needs a comment to be understood, first try to simplify the code. If it's genuinely complex (tricky algorithm, workaround, business rule), then comment WHY, not WHAT. Don't litter code with obvious comments.
- **Blank line grouping**: separate logical blocks within a function with blank lines — group related statements together, split unrelated ones.
- **Break long comprehensions/chains** across multiple lines for readability

See language-specific profiles for code examples.

## File Size and Module Structure

- **Files > 300 lines with multiple unrelated functions/classes** — split into a package/module folder with separate files grouped by responsibility
- One large class in a file is fine — the rule targets files that became a dumping ground for loosely related functions
- Prefer a folder-module over a single 500-line file

## Keep Complexity Low

- **Cyclomatic complexity < 10** per function — if higher, split into smaller functions
- **Max 3 levels of nesting** — use early returns / guard clauses to flatten conditionals
- Extract complex conditions into named variables or functions
- Large switch/if-elif chains — use lookup tables/maps
- Each level of logic — its own step or function. Don't nest loop inside conditional inside resource block.

See language-specific profiles for guard clause and lookup table examples.

## Declarative Over Imperative

- Prefer built-in collection operations (map, filter, reduce, comprehensions) over raw for-loops
- Pipeline-style composition over nested loops
- Extract multi-step imperative logic into named sub-methods

See language-specific profiles for declarative pattern examples.

## No Hardcoded Values

- URLs, API endpoints, base paths — config/env vars
- Timeouts, retry counts, and limits live with their approved configuration/policy owner
- Extract a constant when it represents stable policy or has multiple meaningful
  uses; keep one-use validation/algorithm values with their owner
- Credentials, API keys — **NEVER** hardcode

## Imports Always at Top of File

- Keep imports at module scope by default
- Retain a local/dynamic import only for an Approved framework/lazy-loading reason
  or a cycle reproduced in a clean process; name the exact reason and add import
  regression coverage when the workaround is material
- Group imports with blank lines between groups:
  1. Standard library
  2. Third-party
  3. Local/project
- No wildcard imports, no duplicate imports, no unused imports

## Handle Errors Consistently

Follow project's error handling pattern:
- **Narrow try-catch/try-except**: wrap ONLY the code that can throw, not the whole function
- **Specific exceptions**: catch the exact type, not a generic base exception
- If generic catch IS needed (top-level handler), justify with a comment

See language-specific profiles for error handling examples.

## Boolean Naming

- Boolean variables and functions use `is`/`has`/`should`/`can` prefixes

## Anti-Slop: Clean Code, Not AI Boilerplate

AI-generated code has recognizable bad patterns. Actively avoid them:

- **No blank lines at top of file** — files start with code or imports on line 1
- **No excessive comments** — don't annotate every constant, every function call, every assignment. A file where every other line is a comment is slop. Comments are for WHY, not WHAT.
- **No trivial wrapper functions** — don't create a function that just calls another function with the same arguments. Call it directly.
- **No copy-paste with minor edits** — if multiple functions/methods are 90% identical, extract the common logic into a shared helper or base class.
- Keep exception/error types with their owning domain or established hierarchy.
  Do not create a one-class micro-file without project authority or real reuse.

## Project Structure Awareness

Before creating or placing files, study the existing project layout:

- **Utilities are portable** — place code in a shared utility only when multiple
  ownership areas need the same portable behavior. Framework/application
  integrations belong to the approved infrastructure owner, not generic utilities.
- **One source of truth for config** — if the project already has a settings/config module, don't create a parallel one. Add to what exists.
- **Root path in settings** — if scripts or modules need the project root path, store it once in settings and import it everywhere. Don't compute the root path in multiple places.
- **Growing files into packages** — when a single file (models, schemas, config, constants) grows beyond 300 lines or contains multiple unrelated concerns, convert it to a package directory re-exporting the public API.
- **Long handler/action methods** — any method that builds, renders, processes, or orchestrates and exceeds 50 lines should be broken into smaller named sub-methods. The main method should read like a table of contents.
