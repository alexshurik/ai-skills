# Review Tooling and Provenance

Use this reference for tool resolution, execution, and provenance. Never let a
missing or failed tool become a silent pass.

## Resolve the project runner

Prefer the target repository's pinned environment:

| Signal | Runner |
|---|---|
| `uv.lock` / `[tool.uv]` | `uv run` |
| `poetry.lock` | `poetry run` |
| `pdm.lock` | `pdm run` |
| `Pipfile.lock` | `pipenv run` |
| local `.venv`/`venv` only | activate it |
| `pnpm-lock.yaml` | `pnpm exec` / project scripts |
| `yarn.lock` | `yarn` |
| npm project | `npm exec` / project scripts |
| Go | `go` |
| Rust | `cargo` |

Pre-commit and CI commands are authoritative when they use the locked project
environment. Do not run a random global version against project config. An unknown
rule/option usually means the wrong tool version.

## Run applicable project gates

Run through the resolved runner:

- safe/default test suite;
- formatter check;
- linter;
- type checker;
- build;
- project architecture/import checks.

Use repository guidance for safe test selection. Do not run live, paid,
credential-backed, destructive, or production-facing suites without explicit
authorization.

Record exact command, version when available, exit code, scope, and result.

## Run deep analysis

Run the canonical battery once before lens dispatch:

```text
shared/static-analysis/run-static-analysis.sh \
  --artifact-dir <snapshot-dir>/static-analysis --summary-only <changed paths>
```

Pass the complete changed/untracked scope where supported. Some dependency or
repository scanners necessarily inspect the full repository; classify their
findings against changed-line evidence afterward.

Persist full tool output under the artifact directory. Capture the compact `STATIC
ANALYSIS PROVENANCE` table, `SUMMARY`, and log paths in the review provenance
artifact. Give lenses those artifact paths, not raw scanner output.

## Relevant tools by dimension

Use configured project tools first. Probe optional tools without installing:

| Dimension | Typical tools |
|---|---|
| SAST/security | semgrep, bandit, gosec |
| secrets | gitleaks, trufflehog |
| supply chain/dependencies | guarddog, pip-audit, npm audit, cargo-deny |
| types | mypy, pyright, TypeScript compiler |
| complexity | lizard, radon, complexipy, gocognit, clippy |
| duplication | jscpd |
| dead/unused code | vulture, knip, deptry, cargo-machete |
| dependency cycles | import-linter, dependency-cruiser, madge, architecture tests |
| frontend quality | eslint, stylelint, accessibility/performance/bundle gates |

Only propose tools relevant to the detected stack. In full review, ask before
installing. In quick mode or nested execution, continue with available tools and
report missing dimensions; never install automatically.

## Status semantics

- **OK:** tool executed correctly and found no blocking issue.
- **FINDINGS:** tool executed correctly and reported findings.
- **UNVERIFIED:** tool did not run, failed to execute, used an incompatible
  environment, or produced unusable output.
- **N/A:** dimension is genuinely inapplicable and the reason is recorded.

CI/pre-commit history is supporting evidence, not proof that this review executed
the dimension.

## Baseline classification

Use changed-file and changed-line evidence:

- finding on an introduced/modified line → change-caused;
- file-level metric newly crossing or worsening a threshold → change-caused;
- pre-existing problem materially expanded/relied on → touched structural regression;
- unchanged line/file/metric → baseline/out-of-scope.

Do not hide baseline debt. Report it separately and exclude it from the feature
verdict unless the change worsens or depends on it.
