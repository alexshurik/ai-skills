# Webapp auth shell regression eval

This directory is a behavioral regression suite for the global skills. Its
project-specific names and examples are test data only: `skills-manifest.yaml`
does not install `evals/` into any platform skill tree.

## Historical fixture

Build an isolated working tree from immutable commits:

```bash
TEMP_ROOT="$(mktemp -d /tmp/sk-auth-eval.XXXXXX)"
./build-historical-fixture.sh \
  /path/to/deli-check-backend \
  "$TEMP_ROOT/fixture"
```

The builder archives the base commit, creates a new local repository, and applies
the historical range as uncommitted changes. It never reads uncommitted content
from the live backend repository.

## Evaluation method

1. Start a fresh agent context for each prompt in `prompts/`.
2. Give it the intended skill source and one isolated fixture only.
3. Do not include `eval.yaml`, expected assertions, prior agent output, or the
   retrospective in its context.
4. Store generated artifacts in that fixture; do not share them with later
   agents.
5. Score the returned artifacts/findings against all assertions in `eval.yaml`.
6. A review run cannot pass when an applicable coverage inventory or verification
   gate is missing, even if its final verdict says `APPROVED`.

Record run provenance, fresh-context isolation, evidence, and assertion outcomes
under `results/`. Validate a recorded result with:

```bash
python3 ../score-result.py eval.yaml results/2026-07-24.json
```

For a new Codex run, the optional harness builds isolated fixtures and launches
five separate ephemeral sessions. It does not contain or pass the assertion
rubric:

```bash
./run-codex-eval.sh /path/to/deli-check-backend /tmp/sk-auth-run
```

The harness stores responses outside every fixture. Semantic scoring remains an
explicit review step because matching keywords is not proof that a finding has
the correct owner, severity, and evidence.

`cases/` supplies small companion fixtures for behavior not independently
represented by the historical commit range. These cases test general workflow
properties such as authority precedence, import evidence, baseline separation,
and lesson routing; they are not normative skill instructions.

## Structural checks

```bash
../../tests/test-eval-fixtures.sh
```

The repository-wide suite also validates that project-specific regression
vocabulary does not leak into the normative workflow and best-practice prompts.
