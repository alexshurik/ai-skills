# Project Convention Evidence — skills

## Observed — non-normative

- [OBS-SHELL-ENTRYPOINTS] Pattern: repository workflows expose small Bash entrypoints
  around Python utilities and contract tests.
  Evidence: 8/10 sampled paths (`tests/run.sh`, four install scripts,
  `scripts/validate-skills.sh`, `scripts/generate-agents-md.sh`,
  `scripts/check-python.sh`); Python-only counterexamples:
  `scripts/skills_tool.py`, `scripts/manifest_inventory.py`. Confidence: high.
  Promotion question: none.
- [OBS-CONTRACT-TESTS] Pattern: component tests exercise real CLI boundaries and
  serialized artifacts in addition to imported helpers.
  Evidence: 4/4 sampled test areas (`tests/runtime_state/`,
  `test-rendered-platform-contracts.py`, `test-installers.sh`,
  `test-workflow-contracts.sh`). Confidence: high. Promotion question: none.

## Legacy or uncertain — do not copy by frequency

- [LEG-PYTHON-COMMAND] Pattern: some unchanged developer/test scripts invoke
  `python3` directly.
  Evidence: repository search outside installed runtime/install entrypoints.
  Conflict: the approved installed runtime resolver supports `python3`, `python`, and
  `py -3`. Containment: new install/runtime paths use `scripts/python-runtime.sh`;
  broader baseline conversion needs separate authority.

## Decisions needed

- None.
