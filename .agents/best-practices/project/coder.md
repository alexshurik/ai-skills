# Project Coder Profile — skills

> Normative project layer. Contains Enforced and Approved rules only.
> See `evidence.md` for non-normative observations and legacy patterns.

## Authoritative commands

- [ENF-PYTHON-QUALITY] Run `./scripts/check-python.sh` for pinned Ruff format,
  Ruff lint/complexity, MyPy, 70-line structure, and runtime coverage gates.
  Source: `pyproject.toml`, `scripts/check-python.sh`.
- [ENF-FULL-GATE] Run `./tests/run.sh` for repository-safe full verification.
  Source: `tests/run.sh`.

## Approved architecture and conventions

- [APP-RUNTIME-OWNERS] Keep `runtime-state/sk_state.py` as the stable executable and
  import facade. Persistence, event validation, reduction, projection validation,
  migration, and CLI composition belong to cohesive `_sk_runtime` modules.
  Source: `workflow/agents/shared/runtime-state-policy.md` and the approved
  runtime-state-v2 remediation.
- [APP-RUNTIME-DEPS] Installed runtime code supports Python 3.10+ and uses only the
  standard library. Development tools remain in the uv dev dependency group.
  Source: `README.md#requirements`, `pyproject.toml`.

## Enforced implementation rules

- [ENF-PYTHON-SCOPE] Apply Python gates to the paths in `tool.ruff.include` and
  `tool.mypy.files`; expand that scope deliberately when adding a maintained Python
  component. Verify with `./scripts/check-python.sh`.
- [ENF-FUNCTION-LENGTH] Keep production and runtime-state test functions at or below
  70 physical lines. Verify with `scripts/check-python-structure.py`.

## Conflicts and escalation

- Follow the cited source. If normative sources conflict, stop and request
  resolution. Never use sample frequency as the tie-breaker.
