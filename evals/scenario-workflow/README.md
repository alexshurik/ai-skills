# Scenario workflow behavioral cases

This non-installed corpus exercises planning, decision navigation, convention
profiles, and scanner review. It does not run or record an independent evaluator.
`tests/test-scenario-workflow-eval.py` checks corpus integrity only; a passing
integrity check is not behavioral acceptance.

The workflow root selects a case from `cases.json`, copies only its `fixture_root`
contents to an isolated temporary repository, and records the before hashes. Give
a fresh evaluator the selected request, its listed current source prompts and their
needed references, and the temporary fixture path. Preserve the approved mode and
side-effect bounds in the request. If a source prompt needs recorded approval, the
request's explicit approval is the authority; do not invent additional decisions.

Withhold `goldens.json`, this file's evaluation notes, other cases, prior outputs,
and implementation diagnoses. The implementer must not act as its own independent
evaluator. Root controls any delegation budget. Do not install skills globally,
contact live services, or modify the source repository from a case run.

Ask the evaluator to persist its actual design/tasks/profiles/review or archived
fixture tree, plus a concise evidence receipt. Record source prompt hashes, raw
fixture hashes, evaluator identity/session, output paths/hashes, and unavailable
checks under the root's designated Git-local evidence directory. Judge actual
artifacts against the withheld rubric afterward; instruction text matches or the
presence of expected filenames alone do not prove behavior.

- Planning cases: trace user criteria through each outcome's design, development,
  testing, and review work; inspect dependency/state claims against raw files.
- ADR cases: inspect the before/after tree, affected incoming/outgoing Markdown
  targets, record IDs/body hashes, and duplicate bodies. Repeat owner discovery
  after archive without a second owner/index. Test native and missing owners.
- Enforcement: reconcile every claim with configuration, branch-specific policy
  exports, receipts, current inputs, and missing evidence.
- Bandit: compare each issue's source context and disposition while preserving the
  raw report and application files. Unavailable caller context must remain visible.

Record observed failures and pending cases explicitly. Rerun only cases invalidated
by a relevant source/case change. A new rubric alone cannot certify an earlier run.
