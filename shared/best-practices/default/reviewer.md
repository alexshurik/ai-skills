# Default Reviewer Profile

Universal **stack-level** review rules — the fallback applied to every project
when no more specific language/framework profile is loaded. Language-specific
rules are layered on top from language profiles.

Scope boundaries (to avoid double-coverage across review passes):
- **Structural principles** (SOLID, KISS/DRY/YAGNI, layer boundaries, design
  patterns, performance, design.md compliance) are owned by the **architecture
  review pass** — they are NOT repeated here.
- **Severity mapping, focus/priority order, and feedback style** are owned by
  the **orchestrator** — they are NOT repeated here.
- This profile covers code-quality, error-handling, declarative-style, and
  test-coverage checks that apply at the per-file / per-function level.

## Code Quality Checklist

### Readability
- [ ] Clear, intention-revealing variable/function names
- [ ] No abbreviations or single-letter variables -- including counters (no `i`, `j`, `k`)
- [ ] Boolean names use is/has/should/can prefixes
- [ ] Function length < 20 lines (ideal), < 70 lines (hard max)
- [ ] Functions longer than 70 lines MUST be split into smaller sub-methods
- [ ] No deeply nested conditionals (>3 levels is a smell)
- [ ] Early returns reduce nesting
- [ ] No file-level docstrings at the top of the file -- they add noise and become stale
- [ ] Comments only for complex/non-obvious logic -- if code needs a comment, first try to simplify it. If genuinely complex (tricky algorithm, workaround, business rule), comment WHY, not WHAT
- [ ] Blank line grouping -- related statements grouped together, unrelated ones separated. Code reads like "paragraphs"
- [ ] Long comprehensions/chains broken across multiple lines for readability

### Maintainability
- [ ] Functions have < 4 parameters (use object/params object if more)
- [ ] Default parameters used instead of null checks **where the language permits** (note: Python must NOT use mutable defaults — the language profile overrides this)
- [ ] Consistent coding style throughout
- [ ] No dead code or commented-out code
- [ ] No debug statements left in production code

### Cyclomatic Complexity
- [ ] Functions have complexity < 10
- [ ] Large switch/if-elif chains use lookup tables
- [ ] Extract complex conditions to named variables/functions

### Declarative over Imperative
- [ ] Prefer declarative constructs (map, filter, reduce, comprehensions) over raw for-loops
- [ ] If a for-loop does a transformation -- use map/select/comprehension
- [ ] If a for-loop filters -- use filter/where/comprehension
- [ ] If a for-loop accumulates -- use reduce/fold
- [ ] Multi-step imperative logic: extract each step into a named sub-method
- [ ] Avoid deeply nested loops -- extract inner logic into separate functions
- [ ] Prefer pipeline-style composition over nested loops
- [ ] Method should read like a high-level description of WHAT it does, not HOW

## Error Handling Checklist

### Try-Catch Scope
- [ ] Try blocks wrap ONLY the code that can actually throw -- no extra logic inside
- [ ] Setup/cleanup code is OUTSIDE the try block
- [ ] Each try-catch handles ONE logical operation, not multiple unrelated ones
- [ ] If a try block is longer than 5-10 lines, consider splitting or extracting the throwable part

### Specific Exception Handling
- [ ] Catch blocks specify the EXACT exception type(s) the code can throw
- [ ] No generic catch-all without justification
- [ ] Multiple specific catch blocks preferred over one generic catch
- [ ] If a generic catch IS needed (e.g., top-level handler), it MUST be justified with a comment

## Test Quality and Coverage Checklist

- [ ] Tests cover new/changed code (gate on **changed-line coverage**, ~80%, not a global % target — a global target gets gamed with assertion-free tests)
- [ ] Edge cases and error paths tested
- [ ] A bug fix is accompanied by a regression test that reproduces the bug
- [ ] Tests assert **behavior, not implementation** (observable outcomes, not internal call sequences) — won't break on a behavior-preserving refactor
- [ ] **Narrow assertions** — only the fields relevant to the behavior, not whole-object equality
- [ ] Assertions are meaningful (not `toBeTruthy()`/`assert True`); test names describe behavior + expected outcome
- [ ] **Deterministic** — no wall-clock/`sleep`/real-network in unit tests; seeded randomness; order-independent; isolated state
- [ ] **No logic in tests** (no loops/conditionals); not over-mocked; no mocking of types you don't own
- [ ] Integration tests for external dependencies; contract tests where stubs stand in for real services
- [ ] (Optional, max rigor) diff-scoped mutation testing confirms tests actually detect faults, not just execute lines
