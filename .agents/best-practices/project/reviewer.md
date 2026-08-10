# Project Reviewer Profile — skills

Review only the normative IDs from `coder.md`.

- [ENF-PYTHON-QUALITY] Verify `./scripts/check-python.sh` passes.
- [ENF-FULL-GATE] Verify `./tests/run.sh` passes.
- [APP-RUNTIME-OWNERS] Verify the facade stays thin and each `_sk_runtime` module
  has one cohesive owner.
- [APP-RUNTIME-DEPS] Verify installed runtime imports are standard-library only and
  `project.dependencies` stays empty.
- [ENF-PYTHON-SCOPE] Verify changed maintained Python paths are in the Ruff and MyPy
  scopes in `pyproject.toml`.
- [ENF-FUNCTION-LENGTH] Verify runtime production and test functions remain at or
  below 70 lines with `scripts/check-python-structure.py`.

Report Observed/Legacy evidence separately; it is not a violation unless a normative
rule prohibits the pattern.
