# Webapp auth shell regression eval

This directory is a behavioral regression suite for the global skills. Its
project-specific names and examples are test data only: `skills-manifest.yaml`
does not install `evals/` into any platform skill tree.

## What is automated

The suite keeps three distinct stages:

1. `run-codex-eval.sh` creates isolated fixtures and captures fresh-context
   responses plus machine-readable run provenance.
2. A human performs semantic scoring against the assertions in `eval.json`.
   Keyword matching alone is not proof that a finding has the correct owner,
   severity, and evidence.
3. `validate-result.py` validates the recorded result schema, unique IDs, safe
   output paths, output hashes, evidence links, score arithmetic, and declared
   provenance. It does not independently judge response quality.

The committed `results/2026-07-24.json` predates provenance capture. It is retained
as an explicitly non-reproducible historical snapshot and must not be presented as
a current model benchmark.

## Historical fixture prerequisite

The broad review fixture is built from the immutable `ee6100b..5aa47ea` range in
the historical backend repository. That source is not vendored here, so the full
agent run is not self-contained. The supplied repository must contain both commits:

```bash
TEMP_ROOT="$(mktemp -d /tmp/sk-auth-eval.XXXXXX)"
./build-historical-fixture.sh \
  /path/to/historical-backend \
  "$TEMP_ROOT/fixture" \
  ee6100b \
  5aa47ea
```

The builder archives committed objects into a new repository and applies the
historical range as uncommitted changes. It never reads uncommitted content from
the source working tree. Smaller companion cases under `cases/` cover authority
precedence, import evidence, baseline separation, and lesson routing.

## Run the agent harness

The harness launches eight isolated Codex sessions from five neutral prompt
templates. Pin the model explicitly and use an output directory outside the
repository:

```bash
./run-codex-eval.sh \
  /path/to/historical-backend \
  /tmp/sk-auth-run \
  <model-id>
```

Each session receives the intended skill source and one fixture only. It does not
receive `eval.json`, expected assertions, previous responses, or the retrospective.
Responses are stored outside the fixtures. `run-manifest.json` records the model,
Codex CLI version, skills commit and dirty state, fixture commits, response hashes,
and isolation declarations. The harness intentionally stops before semantic
scoring.

## Record and validate semantic scoring

For each required assertion in `eval.json`, record a boolean outcome, the run that
supports it, and specific evidence. New reproducible results must identify a clean
skills commit, pinned model, and Codex CLI version.

Validate result integrity without requiring a passing score:

```bash
python3 ../validate-result.py eval.json results/2026-07-24.json
```

Use the regression gate when every assertion is expected to pass:

```bash
python3 ../validate-result.py \
  eval.json \
  results/2026-07-24.json \
  --require-pass
```

## Structural checks

```bash
../../tests/test-eval-fixtures.sh
```

The repository-wide suite also verifies that project-specific regression
vocabulary does not leak into normative workflow and best-practice prompts.
