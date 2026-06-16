# Python Coder Profile

Python-specific coding rules. Applied on top of the default coder profile.

## PEP Compliance

Follow PEP 8, PEP 257, PEP 484 strictly.

### Type Hints (PEP 484)

- **All function signatures** must have type hints for parameters and return type
- Annotate variables where the type is non-obvious (e.g., empty collections, union types)
- Use `collections.abc` for abstract container types (`Sequence`, `Mapping`, `Iterable`), not `typing` equivalents (deprecated since Python 3.9)
- Use built-in generics (`list[str]`, `dict[str, int]`, `tuple[int, ...]`) instead of `typing.List`, `typing.Dict`, `typing.Tuple`
- Use `X | Y` union syntax instead of `typing.Union[X, Y]` and `X | None` instead of `typing.Optional[X]`
- Target Python 3.11+ (3.9/3.10 are EOL or near it); modern generic syntax (`list[str]`) works natively. `from __future__ import annotations` is only needed for older interpreters

```python
# Good
from collections.abc import Sequence

def process_items(
    items: list[str],
    handler: Callable[[str], None],
    options: Mapping[str, int] | None = None,
) -> Sequence[str]:
    ...

# Bad — uses deprecated typing generics
from typing import List, Optional, Dict

def process_items(
    items: List[str],
    handler: Callable[[str], None],
    options: Optional[Dict[str, int]] = None,
) -> List[str]:
    ...
```

### Modern Typing Constructs

Reach for the type system to make illegal states unrepresentable, not just to annotate signatures.

- **`Protocol`** for structural typing — define behavior contracts without inheritance; pairs with "accept the interface, not the concrete class."
- **`TypedDict`** for dict-shaped payloads (JSON, config) where a dataclass/model is too heavy.
- **`Literal`** for closed sets of constant values; **`enum.Enum`** / **`StrEnum`** (3.11+) when the set carries identity/behavior.
- **`Self`** (3.11+) for fluent/builder return types and `copy`-style methods.
- **`typing.assert_never`** at the end of an exhaustive `match`/`if` chain so a newly-added variant becomes a *type* error, not a silent fallthrough.

```python
from enum import StrEnum
from typing import Literal, Protocol, Self, assert_never

class Drawable(Protocol):
    def draw(self) -> None: ...

class Color(StrEnum):
    RED = "red"
    GREEN = "green"

def describe(c: Color) -> str:
    match c:
        case Color.RED:
            return "warm"
        case Color.GREEN:
            return "cool"
    assert_never(c)  # type error if a Color member is added but unhandled

class Query:
    def where(self, cond: str) -> Self:  # returns the subclass type, not just Query
        ...
```

### Structural Pattern Matching

Use `match`/`case` (3.10+) for dispatch over a closed set of shapes (enums, tagged unions, AST-like nodes) — clearer than an `if/elif` ladder, and combines with `assert_never` for exhaustiveness. Don't reach for it on a single equality check (`if x == 1:` is plenty).

```python
# Good — destructure and dispatch
match event:
    case Click(x, y):
        handle_click(x, y)
    case KeyPress(key):
        handle_key(key)
    case _:
        assert_never(event)
```

### Style Basics (ruff-autofixed)

These are enforced and auto-fixed by ruff; write them right the first time, don't dwell on them:

- **f-strings** for interpolation — never `%` or `.format()`.
- **`pathlib.Path`** for filesystem paths — never `os.path.join` / `os.path.exists`.
- **`is None`** / **`is not None`** for identity — never `==` / `!=` against `None`.

### Resource Management

Use **`with` statements** for all resources that need cleanup: files, connections, locks, database sessions.

```python
# Good
with open("data.json") as f:
    data = json.load(f)

# Bad
f = open("data.json")
data = json.load(f)
f.close()
```

### Iteration Patterns (ruff-autofixed)

Use **`enumerate()`** instead of a manual counter, and **`zip()`** for parallel iteration instead of `range(len(...))` indexing. Both are flagged/fixed by ruff.

### Data Containers

Use **`@dataclass`** for internal value objects. Use **Pydantic `BaseModel`** for data crossing system boundaries (API schemas, config, serialization).

```python
# Good — internal data container
from dataclasses import dataclass

@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float

# Good — external data with validation
from pydantic import BaseModel

class UserRequest(BaseModel):
    name: str
    email: str
```

### Comprehensions

Use list/dict/set comprehensions where they improve readability. Never nest more than two levels.

```python
# Good
active_emails = [user.email for user in users if user.is_active]

user_map = {user.id: user.name for user in users}

# Bad — nested too deep, extract into a function
result = [
    cell.value
    for row in sheet.rows
    for section in row.sections
    for cell in section.cells
    if cell.is_valid
]
```

## Docstrings (PEP 257)

Use Google-style docstrings. Opening and closing `"""` go on their own lines for multi-line docstrings. Single-line docstrings are fine on one line.

```python
def calculate_total(
    items: list[LineItem],
    *,
    tax_rate: float = 0.0,
) -> Decimal:
    """
    Calculate the total price including tax.

    Sums all item prices and applies the tax rate. Returns zero
    if the item list is empty.

    Args:
        items: Line items to sum.
        tax_rate: Tax multiplier (0.0 = no tax, 0.2 = 20%).

    Returns:
        Total price as Decimal, rounded to 2 decimal places.

    Raises:
        ValueError: If tax_rate is negative.
    """
    ...
```

One-liner for simple functions:

```python
def is_active(user: User) -> bool:
    """Check whether the user account is active."""
    return user.status == "active"
```

## Import Organization

Three groups separated by blank lines, each group sorted alphabetically:

1. Standard library
2. Third-party packages
3. Local/project imports

```python
import json
import logging
from pathlib import Path

import httpx
from pydantic import BaseModel

from myapp.models import User
from myapp.utils import validate_email
```

Rules:
- **All imports at the top of the file** — never inside functions, methods, or conditionals
- Only exception: avoiding circular imports (must be commented `# avoid circular import`)
- Absolute imports preferred over relative
- No wildcard imports (`from module import *`)
- No duplicate imports

## Exception Handling

- **No bare `except:`** — always specify the exception type
- **No `except Exception:`** unless at a top-level entry point (and justified with a comment)
- Catch the most specific exception type possible
- Group related exceptions: `except (TypeError, ValueError):`

```python
# Good
try:
    data = json.loads(raw_input)
except json.JSONDecodeError as exc:
    raise ValidationError(f"Invalid JSON: {exc}") from exc

# Bad — bare except catches SystemExit, KeyboardInterrupt
try:
    data = json.loads(raw_input)
except:
    data = {}

# Bad — too broad
try:
    data = json.loads(raw_input)
except Exception:
    data = {}
```

## Mutable Default Arguments

Never use mutable objects as default parameter values. Use `None` and create inside the function.

```python
# Good
def append_item(item: str, target: list[str] | None = None) -> list[str]:
    if target is None:
        target = []
    target.append(item)
    return target

# Bad — shared mutable default
def append_item(item: str, target: list[str] = []) -> list[str]:
    target.append(item)
    return target
```

## Async Correctness

- **Structured concurrency**: prefer `asyncio.TaskGroup` (3.11+) over bare `asyncio.gather`. A `TaskGroup` cancels siblings on first failure and propagates errors as an `ExceptionGroup`; bare `gather` leaks the other tasks unless you remember `return_exceptions` + manual cleanup.
- **Never swallow `CancelledError`**. If you must catch it (e.g. to run cleanup), re-raise. Eating it breaks cancellation and timeouts.
- **`async with` / `async for`** for async context managers and iterators — never drive an async resource with a sync `with`/`for`.
- **Never call sync-blocking I/O in a coroutine** (`requests`, `time.sleep`, blocking DB drivers, large file reads). It stalls the whole event loop. Use async libraries (`httpx.AsyncClient`, `asyncio.sleep`) or offload to `asyncio.to_thread(...)`.

```python
# Good — TaskGroup: structured, cancels siblings on failure
async with asyncio.TaskGroup() as tg:
    user_t = tg.create_task(fetch_user(uid))
    posts_t = tg.create_task(fetch_posts(uid))
user, posts = user_t.result(), posts_t.result()

# Good — re-raise cancellation after cleanup
try:
    await do_work()
except asyncio.CancelledError:
    await cleanup()
    raise

# Bad — bare gather leaks siblings on failure; blocking call stalls the loop
results = await asyncio.gather(fetch_user(uid), fetch_posts(uid))
time.sleep(1)               # use: await asyncio.sleep(1)
data = requests.get(url)    # use: async with httpx.AsyncClient() ...
```

## Security Idioms

State these in code, not just in the linter — bandit catches some, but write them right by default.

- **No `subprocess(..., shell=True)` with interpolated input.** Pass an argument list and let the OS avoid shell parsing.
- **Never deserialize untrusted data with `pickle` or `yaml.load`.** Use `yaml.safe_load`; for cross-process data use JSON.
- **Parameterized SQL only.** Pass values as query parameters — never build SQL with f-strings or `%`/`+` concatenation.

```python
# Good
subprocess.run(["git", "clone", repo_url], check=True)
config = yaml.safe_load(raw)
cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# Bad — shell injection / arbitrary code execution / SQL injection
subprocess.run(f"git clone {repo_url}", shell=True)
config = yaml.load(raw, Loader=yaml.Loader)
cur.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

## Logging, Not print

In library and application code use the `logging` module (or `structlog`), never `print`. `print` has no levels, no structured fields, and can't be routed or silenced. Reserve `print` for CLI user-facing output only.

```python
# Good
import logging

logger = logging.getLogger(__name__)
logger.info("processed %d items", len(items))

# Bad — no level, no routing, not a log record
print(f"processed {len(items)} items")
```

## Timezone-Aware Datetimes

Never construct naive datetimes for anything that represents a real moment. `datetime.now()` and `datetime.utcnow()` return naive objects that silently misbehave across timezones and DST. Always pass `tz=`.

```python
from datetime import datetime, UTC

# Good — aware
now = datetime.now(tz=UTC)

# Bad — naive; utcnow() is deprecated in 3.12+
now = datetime.now()
now = datetime.utcnow()
```

## Packaging Hygiene

- **Use `uv` for dependency/build management** (2026 default): `uv sync`, `uv run`, `uv add`; commit `uv.lock` for reproducible installs. `pyproject.toml` is the single project manifest.
- **No `sys.path.insert` / `sys.path.append` hacks** — fix packaging with `pyproject.toml` (editable install via `uv pip install -e .` / `pip install -e .`)
- **No `sys.path` manipulation between imports** — if truly unavoidable, all path changes go before all imports
- **No `from src.` imports** — `src` is not a package name; use the real project package name
- **Entry points over scripts** — define CLI commands in `pyproject.toml` `[project.scripts]` instead of standalone scripts that hack the Python path
