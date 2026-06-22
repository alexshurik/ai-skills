# Python Reviewer Profile


<!-- Mirrors rules in coder.md as review checks. Keep in sync. -->
Python-specific review checklist and tooling. Applied on top of the default reviewer profile.

## Python Review Checklist

### Coder Rules (verify, don't re-derive)

All `coder.md` rules apply as review checks — confirm they hold rather than re-listing them: f-strings, `pathlib`, `is None`, `with`, `enumerate`/`zip`, `@dataclass`/Pydantic, `collections.abc`, built-in generics. The style-basics (formatting, None checks, iteration) are ruff-autofixed — only flag them if the linter is absent or disabled; spend review attention on the judgment items below. Also verify: **PEP 8** (4-space indent, 88-100 char lines), **PEP 484** hints on every public signature, **PEP 257** docstrings on public APIs, and `__all__` on library modules.

### Modern Typing and Control Flow
- [ ] `Protocol` used for structural contracts where inheritance would be forced
- [ ] `TypedDict` / `Literal` / `enum.Enum` / `StrEnum` used to model closed sets instead of bare `str`/`int`
- [ ] `Self` used for fluent/builder/copy return types (not the hard-coded class name)
- [ ] `typing.assert_never` closes exhaustive `match`/`if` chains over enums/unions
- [ ] `match`/`case` used for closed-set dispatch where it beats an `if/elif` ladder (not for single equality checks)

### Async Correctness (high-value gap)
- [ ] `asyncio.TaskGroup` (3.11+) preferred over bare `gather` for structured concurrency
- [ ] `CancelledError` never swallowed — caught only for cleanup, then re-raised
- [ ] `async with` / `async for` used for async context managers and iterators
- [ ] **No sync-blocking I/O in coroutines** — `requests`, `time.sleep`, blocking DB drivers (use async clients or `asyncio.to_thread`)

### Security Idioms (don't defer to bandit)
- [ ] No `subprocess(..., shell=True)` with interpolated input — argument lists only
- [ ] No `pickle` / `yaml.load` on untrusted data — `yaml.safe_load` / JSON
- [ ] Parameterized SQL only — never f-string / concatenated SQL

### Other Must-Haves
- [ ] `logging` (or `structlog`) used in library/app code, not `print`
- [ ] Timezone-aware datetimes — `datetime.now(tz=...)`, never naive `now()` / deprecated `utcnow()`

### Import Organization
- [ ] All imports at top of file — never inside functions (except `# avoid circular import`)
- [ ] Three groups with blank lines: stdlib, third-party, local
- [ ] Absolute imports preferred over relative
- [ ] No wildcard imports (`from module import *`)
- [ ] No duplicate or unused imports

### Exception Handling
- [ ] No bare `except:` — always specify exception type
- [ ] No `except Exception:` unless at top-level entry point (justified with comment)
- [ ] Specific exceptions: `ValueError`, `KeyError`, `TypeError`, `ConnectionError`, etc.
- [ ] `except (TypeError, ValueError):` for multiple related exceptions
- [ ] Exceptions re-raised with context: `raise NewError(...) from original`

### Anti-Patterns to Flag
- [ ] **Mutable default arguments** — `def f(items=[])` is a bug; use `None` and create inside
- [ ] **String concatenation in loops** — use `"".join()` or f-strings with list comprehension
- [ ] **Nested comprehensions > 2 levels** — extract into a named function
- [ ] **Broad exception handling** — `except Exception` swallowing errors silently
- [ ] **Global mutable state** — module-level mutable variables shared across calls
- [ ] **`time.sleep()` in async code** — use `asyncio.sleep()` instead
- [ ] **Blocking calls in async functions** — sync I/O, `requests` library in async context
- [ ] **Swallowed `CancelledError`** — caught without re-raising breaks cancellation/timeouts
- [ ] **Bare `gather` where a `TaskGroup` belongs** — sibling tasks leak on failure
- [ ] **`shell=True` / `pickle` / `yaml.load` / f-string SQL** — injection and RCE vectors

### Packaging
- [ ] No `sys.path.insert` / `sys.path.append` hacks
- [ ] No `sys.path` manipulation interleaved between imports
- [ ] No `from src.` imports — use the real package name
- [ ] Project root path defined once and imported, not computed in multiple places

## Static Analysis Tools

> **Run every tool below through the project runner**, not the bare binary shown in
> the examples — e.g. `uv run ruff check`, `uv run mypy --strict src/`,
> `uv run complexipy src/ -d low` when the repo uses uv (or `poetry run …`, a
> `.venv` activation, etc.). The bare `ruff`/`mypy`/`complexipy` in the snippets is
> illustrative; a global binary is usually the wrong version and will misfire on the
> project's pinned config. See "Running Static-Analysis Tools" in the default profile.

### ruff (Primary Linter)

All-in-one Python linter and formatter. Replaces flake8, isort, pycodestyle, pyflakes, and many plugins.

```bash
# Lint
ruff check .

# Lint with auto-fix
ruff check --fix .

# Format
ruff format .

# Check formatting without modifying
ruff format --check .
```

**Recommended rule sets** for `ruff.toml` or `pyproject.toml [tool.ruff.lint]`:

| Rule Set | Plugin | Purpose |
|----------|--------|---------|
| `E` | pycodestyle | Style errors |
| `F` | pyflakes | Logical errors, unused imports |
| `W` | pycodestyle | Style warnings |
| `B` | flake8-bugbear | Common bug patterns |
| `ANN` | flake8-annotations | Missing type annotations |
| `N` | pep8-naming | Naming conventions |
| `PL` | pylint | Pylint checks (args, branches, returns, statements) |
| `S` | flake8-bandit | Security issues |
| `I` | isort | Import sorting |
| `UP` | pyupgrade | Upgrade syntax to modern Python |
| `SIM` | flake8-simplify | Simplifiable code |
| `RUF` | ruff-specific | Ruff's own rules |
| `T20` | flake8-print | Stray print statements |
| `PERF` | perflint | Performance anti-patterns |
| `ASYNC` | flake8-async | Async/await issues |
| `C4` | flake8-comprehensions | Comprehension improvements |
| `C90` | mccabe | Cyclomatic complexity |

Optional but recommended:

| Rule Set | Plugin | Purpose |
|----------|--------|---------|
| `PIE` | flake8-pie | Misc. lint rules |
| `FURB` | refurb | Modernize code patterns |
| `ERA` | eradicate | Detect commented-out code |
| `PT` | flake8-pytest-style | Pytest best practices |
| `DTZ` | flake8-datetimez | Timezone-aware datetime usage |

### Type Checking (mypy / pyright / ty) — REQUIRED

ruff does NOT type-check. A separate static type checker verifies the PEP 484 hints
the coder profile mandates — this is the single most important Python gate after ruff.

```bash
# mypy in strict mode (CI gate)
mypy --strict src/

# or pyright (faster, used by Pylance)
pyright src/
```

A type error is a **MAJOR** finding (BLOCKER if it indicates a real runtime bug —
`None` where a value is required, wrong argument type). New code must type-check
clean; flag missing/`Any`-typed public signatures.

### bandit (Security Scanner)

Dedicated security analysis beyond what ruff `S` rules cover.

```bash
# Scan entire project
bandit -r src/ -f json

# Scan with specific severity
bandit -r src/ -ll  # medium and above

# Exclude test files
bandit -r src/ --exclude src/tests/
```

### radon (Complexity and Maintainability)

```bash
# Cyclomatic complexity — flag functions >= B grade
radon cc src/ -a -nb

# Maintainability index — flag files below A grade
radon mi src/ -nb

# Raw metrics (LOC, SLOC, comments)
radon raw src/ -s
```

### complexipy (Cognitive Complexity)

```bash
# Cognitive complexity — fast, Rust-based; -d low shows only functions over the threshold
complexipy src/ -d low
```

### vulture (Dead Code Detection)

```bash
# Find unused code
vulture src/

# With minimum confidence threshold (reduce false positives)
vulture src/ --min-confidence 80

# Generate allowlist for intentional unused code
vulture src/ --make-whitelist > whitelist.py
```

### pip-audit (Dependency Vulnerabilities)

```bash
# Audit installed packages
pip-audit

# Audit from requirements file
pip-audit -r requirements.txt

# JSON output for CI integration
pip-audit --format json

# With uv
uv run pip-audit
```

### deptry (Dependency Hygiene)

Finds issues pip-audit/vulture miss: missing deps (imported, not declared), transitive
deps (imported but only a transitive dependency), and unused declared deps.

```bash
deptry .   # DEP001 missing, DEP002 unused, DEP003 transitive
```

### pylint (Selective Checks)

Use selectively for checks ruff does not cover (e.g., design checks, some refactoring suggestions).

```bash
# Run specific checkers only
pylint src/ --disable=all --enable=R0401  # cyclic imports
pylint src/ --disable=all --enable=W0611  # unused imports (redundant with ruff F)

# Design checks
pylint src/ --disable=all --enable=design
```

## Severity Mapping for Python Findings

Extends the orchestrator's severity table with Python-specific entries.

| Finding | Severity |
|---------|----------|
| Bare `except:` | **BLOCKER** |
| `except Exception:` without justification | **MAJOR** |
| Mutable default argument | **BLOCKER** |
| `sys.path` hacks | **MAJOR** |
| Missing type hints on public function | **MAJOR** |
| `os.path` instead of `pathlib` | **MINOR** |
| `typing.List` instead of `list` | **MINOR** |
| String concatenation in loop | **MAJOR** (performance) |
| Blocking call in async function | **BLOCKER** |
| `time.sleep()` in async code | **BLOCKER** |
| Swallowed `CancelledError` | **BLOCKER** |
| `shell=True` with interpolated input | **BLOCKER** |
| `pickle` / `yaml.load` on untrusted data | **BLOCKER** |
| f-string / concatenated SQL | **BLOCKER** |
| Bare `gather` where `TaskGroup` fits (sibling leak) | **MAJOR** |
| Naive datetime for a real moment (`now()`/`utcnow()`) | **MAJOR** |
| `print` instead of `logging` in library/app code | **MINOR** |
| Closed set typed as bare `str`/`int` (no `Literal`/`Enum`) | **MINOR** |
| `from src.` import | **MAJOR** |
| Missing docstring on public API | **MINOR** |
| Wildcard import | **MAJOR** |
| bandit high severity | **BLOCKER** |
| bandit medium severity | **MAJOR** |
| bandit low severity | **MINOR** |
| radon CC grade D or worse (>15) | **MAJOR** |
| radon CC grade C (11-15) | **MINOR** |
| radon MI below 20 | **MAJOR** |
| vulture finding (confidence >= 80%) | **MINOR** |
| pip-audit critical/high CVE | **BLOCKER** |
| pip-audit moderate CVE | **MAJOR** |
