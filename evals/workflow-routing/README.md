# Adaptive workflow-routing golden eval

This suite checks the decisions made by `sk-team`, not the wording used to explain
them. Each fresh model session receives one neutral scenario, the public workflow
policy inputs, and a strict response schema. Expected decisions stay in
`goldens.json`, which the runner never copies into a fixture or includes in a
prompt.

The decision record covers:

- Micro, Quick, and Full routing;
- authorization, assurance, workspace, and destination resolution;
- approval behavior and typed stops;
- route-appropriate rendered-UI gates;
- upward route escalation and material Scope Delta handling;
- expected agent topology; and
- focused checks, one broad-suite receipt, and exact-input receipt reuse.

## Validate the suite

```bash
python3 validate.py eval.json
```

The validator checks the manifest, case/golden correspondence, response schema,
enum values, cross-field invariants, required coverage, and source policy paths.

## Run fresh-context Codex sessions

Use an empty output directory outside the repository and pin the model:

```bash
./run-codex-eval.sh /tmp/sk-workflow-routing-run <model-id>
```

The harness creates one isolated Git fixture and one ephemeral Codex session per
case. A fixture contains only the declared public policy inputs and the response
schema. It does not contain the eval manifest, other cases, prior responses, or
goldens. `run-manifest.json` records source and output provenance.

Score the structured responses afterward:

```bash
python3 validate.py eval.json \
  --responses /tmp/sk-workflow-routing-run/responses
```

Scoring compares only the normalized decision fields. No rationale or exact prose
is part of the golden.

## What this suite does not prove

Routing goldens catch policy regressions such as turning clear multi-screen polish
into Full, forgetting YOLO authority, creating a worktree unnecessarily, or rerunning
an unchanged broad suite. They do not prove that generated code or UI is good.

Release confidence therefore has three layers:

1. `tests/run.sh` validates packaging, schemas, runtime transitions, and deterministic
   workflow contracts.
2. This suite runs fresh-context policy decisions against hidden goldens.
3. Product fixtures such as `evals/webapp-auth-shell/` exercise implementation and
   rendered outcomes; real workflow telemetry should additionally track agent count,
   unjustified user stops, broad-suite runs, remediation rounds, and elapsed tool
   time per completed objective.

Add a golden only for a stable behavioral decision. Prefer anonymized real failures,
minimal counterexamples, and paired near-boundary cases. Keep expected fields out of
the prompt, pin the model and source revision for live runs, and review intentional
golden changes as policy changes rather than ordinary snapshot updates.
