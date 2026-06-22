# Default Coder Profile

Universal coding rules applied to every project. Language-specific rules are loaded from language profiles and take precedence where they conflict.

## Keep It Simple

Solve the problem at hand directly. Resist the urge to introduce
configuration, registries, or pluggable strategies until the second
distinct caller appears. Three similar lines beat a premature abstraction.

See language-specific profiles for idiomatic examples.

## Follow Project Patterns

**The project's own conventions OUTRANK the generic examples in these profiles.** The
code snippets here show idiomatic defaults; they are the fallback for greenfield code,
NOT a license to impose a style the repo doesn't use. On any conflict, match the repo.

- If a project profile is loaded (`.agents/best-practices/project/coder.md`, highest
  precedence), it is authoritative — follow it over any example below.
- The project's own formatter + linter are the final arbiter of style. Run them on
  the code you write and conform (see your agent's format/lint step). Do not hand-pick
  a style the linter would rewrite.
- Look at neighbouring files before introducing ANY new convention — and do not add a
  pattern the surrounding code doesn't already use (e.g. don't add module/file
  docstrings, decorators, or naming flavors that appear nowhere else).

Match existing code style:

- Naming (camelCase, snake_case, PascalCase — match what's there)
- File organization and import order
- Error handling (exceptions, Result types, error returns — match the project)
- Async style (async/await vs callbacks vs promises) — match the project

## Write Readable Code

- Clear, intention-revealing variable names — **no single-letter names**, even for counters
- Short functions: < 20 lines ideal, **70 lines hard max** — split longer functions into sub-methods
- Functions have **< 4 parameters** — use an options/config object if more
- **No file-level docstrings** at the top of the file — they add noise and become stale
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
- Timeouts, retry counts, limits — named constants
- Magic numbers/strings used more than once — extract to constants
- Credentials, API keys — **NEVER** hardcode

## Imports Always at Top of File

- **ALL imports at the top of the file** — never inside functions, methods, or conditional blocks
- Only exception: avoiding circular imports (must be commented why)
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
- **Exception/error classes in their own file** — don't mix exception class definitions with client/business logic.

## Project Structure Awareness

Before creating or placing files, study the existing project layout:

- **Utilities are portable** — utility modules (datetime helpers, string formatters, async wrappers, HTTP helpers) should live in a dedicated utilities directory. They must NOT import from the main project — imagine they could be copied to any other project as-is.
- **One source of truth for config** — if the project already has a settings/config module, don't create a parallel one. Add to what exists.
- **Root path in settings** — if scripts or modules need the project root path, store it once in settings and import it everywhere. Don't compute the root path in multiple places.
- **Growing files into packages** — when a single file (models, schemas, config, constants) grows beyond 300 lines or contains multiple unrelated concerns, convert it to a package directory re-exporting the public API.
- **Long handler/action methods** — any method that builds, renders, processes, or orchestrates and exceeds 50 lines should be broken into smaller named sub-methods. The main method should read like a table of contents.
