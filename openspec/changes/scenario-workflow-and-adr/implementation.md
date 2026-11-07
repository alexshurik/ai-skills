# Implementation evidence — scenario workflow and durable decisions

Status: implementation, engineering checks and six forward behavioral cases complete;
independent code review and acceptance pending.
Date: 2026-11-07. Scope Delta: **None**.
Authority: [proposal](proposal.md), [approved design](design.md), [tasks](tasks.md),
and the parent execution envelope. Initial base: `8a096e0ca6f3c9a386d0058391f60478f8ae6f01`.
Review base after integrating the separately published UI review-gate fix:
`1a1d8007787800992f743da3b7f832cef12c47c4`.

## Delivered outcomes

| Criteria | Maintained owner and result |
|---|---|
| AC-1/AC-2 | `architecture-gates.md` owns the scenario record; `shared/templates/tasks.md` owns complete outcome milestones. Architect, discovery, design template, Full workflow, and documentation review use those contracts. Each milestone retains user criteria plus design/development/testing/review work. Existing phases and risk routing remain. |
| AC-3 | `scope-governance.md` §6 owns permanent ADR resolution, supersession, legacy preservation, and archive navigation. Architect/onboarding/Full/Quick callers and public artifact lists use it. New decisions stop defaulting to change-local storage. |
| AC-4 | `convention-evidence-model.md` separates authority from command/scope/invocation/blocking/freshness/manual gaps. The profile guide provides one enforcement record in coder.md with reviewer references; codestyle and architecture callers use it. Existing rule IDs/classes remain. |
| AC-5a | The static runner classifies Lizard's completed summary, clean marker, warning evidence, and exit status. Failure takes precedence. The provenance columns, status vocabulary, CLI, and top-level exit behavior remain. Other analyzers are unchanged. |
| AC-5b | The Python reviewer preserves raw Bandit findings and assesses each issue in context. Direct tool-severity escalation and blanket exclude/threshold examples were removed. Existing authority/disposition obligations remain. |

The source diff contains 22 modified maintained files, one new corpus integrity test,
three normalized Lizard reports, and the non-installed behavioral corpus (six cases,
37 raw files, case manifest, withheld rubrics, and evaluation instructions).
No application, runtime/event schema, generated inventory, or global installation
was changed. No commit or push was performed.

## Engineering verification

**PASS:** `uv run --frozen bash tests/run.sh` → exit 0, `OK: all skill tests`.
The wrapper supplies the repository's locked Python environment to every test.
It includes format/lint/type/structure checks, runtime coverage, source metadata and
reference closure, all platform renders, generated-file checks, workflow/eval and
review-provenance contracts, and installer/migration tests in temporary destinations.
Runtime coverage was 81%, above the existing 80% gate. Managed documents were current;
no generator output needed regeneration.

Focused evidence:

| Command | Result and purpose |
|---|---|
| `bash tests/test-static-analysis-artifacts.sh` before parser edit | Expected Red, exit 1: actual clean Lizard 1.21.2 report was falsely FINDINGS. |
| Same command after implementation | Green, exit 0: 21 semantic cases in both logged and in-memory modes. Includes clean, genuine findings at exits 0/1, positive warning count, missing tool, execution/usage/error/timeout/unsupported-exit failures, and incomplete/contradictory/unrecognized output. Raw logs and non-Lizard controls remain checked. |
| `python3 tests/test-review-approval-gate.py` | Green: Lizard OK needs no disposition, findings require one, and UNVERIFIED cannot approve even with a disposition. The consumer implementation is unchanged. |
| `python3 tests/test-scenario-workflow-eval.py` | Green: six case IDs, raw file hashes, source references, path confinement, rubric completeness, and preserved-body hashes. This is corpus integrity only. |
| Focused source, rendered-platform, documentation, scope, context, workflow-efficiency/charter checks | Green; full command evidence is also included in the final suite log. |
| Skill Creator `quick_validate.py` for Full/Quick/Help/codestyle source folders | Green. Codestyle was rechecked after its final edit. |
| `git diff --check` and Bash syntax checks | Green. |

The initial full-suite attempts exposed two in-scope issues, which were fixed with
focused Green: raw fixture formatting/cache inventory, and preservation of the
existing “merely available” workflow contract wording. A later attempt used the host
Python without `jsonschema`; the locked Python gate had passed. Running the whole
suite through `uv run --frozen` corrected the runner environment. Every repeat has
its specific invalidation reason in `full-suite-*-inputs.json`; no unchanged green
broad gate was rerun. No unrelated baseline failure remains.

The auxiliary Skill Creator validator needs PyYAML, absent from host Python. It was
run read-only with the existing backend virtualenv interpreter (PyYAML 6.0.3).
No package was added to this repository or installed globally for that check.
Repository checks used uv 0.9.10, CPython 3.14.0, Ruff 0.16.1, and MyPy 1.20.2 from
`uv.lock`. The shell regression also runs on macOS Bash 3.2.57.

## Fingerprints and full evidence

Git-local evidence root:

```text
/Users/alex/Project/skills/.git/worktrees/skills-vsa-worktree/sk-workflow/scenario-workflow-and-adr/
```

| Evidence | Value/path relative to that root |
|---|---|
| Approved design SHA256 | `979efcc4bffc00530e5606014edddd85e0dd2874920d1a9295e77e29cbd1d1e1` |
| Changed source fingerprint (66 paths; excludes OpenSpec reports) | `1da0353dea15a242be6f46b887fe19d0a1dbaba96a886b4f9d636d661019c08f` — `changed-source.json` |
| Full passing gate input fingerprint | `ede05a3c9067be756c617b9471f144e4bd143e65f0591ff0905d92ab164d24f8` |
| Immutable final gate receipt | `gate-receipt.json` — command, environment, config/lockfile hashes, complete covered path hashes, exit, log SHA256 |
| Passing full log | `logs/full-suite-final.log` — SHA256 `f8598b8bd3269a9cf7a0212d85f4b1724912fc1306b9634c71ba5f703312869c` |
| Red and focused scanner Green | `logs/lizard-red.log`, `logs/lizard-final.log`, `lizard-capture.json` |
| Pre-write and before/after evidence | `prewrite.md`, `before.json`, `prewrite-evidence.json`, `implementation-evidence.json`, `changed-source.json` |
| Auxiliary validators | `logs/quick-validate-existing-python.log`, `logs/quick-validate-codestyle-final.log` |
| Fixed failures and invalidations | `logs/full-suite.log`, `logs/full-suite-2.log`, `logs/full-suite-3.log`; matching inputs/exit files; `logs/fixture-format-fix.log`, `logs/fixture-integrity-fix.log`, `logs/efficiency-fix.log` |

All final covered source hashes were rechecked against the passing receipt.
OpenSpec task/report updates are outside its executable/source gate input closure.
Root owns runtime state; this task wrote evidence files only, not events/state.

## Structure and boundary conformance

- The Lizard helper is colocated with its sole execution/classification owner.
  The runner grows 277 → 318 lines and still owns one battery/provenance concern.
  No parser framework, library, or generic abstraction was added.
- The artifact policy grows 290 → 319 lines; ADR lifecycle belongs to its existing
  durable-artifact/archive responsibility. The approval-gate regression file grows
  270 → 311 lines and retains its existing consumer-test responsibility.
- Discovery shrinks 491 → 483 lines, below its 500-line catalog budget. Full workflow
  remains 462 lines and Architect 272 lines. Source prompt-budget checks pass.
- New small files are normalized reports or raw evaluator inputs, not runtime
  wrappers. Corpus helpers validate paths/hashes and are used for all six cases.
- No local/dynamic runtime import or new runtime entry point was added. The test adds
  one module-level consumer import through the existing approval-test setup.
- No UI is changed. Visual evidence is **N/A**; platform prompt rendering is engineering
  evidence, not a visual product verdict.
- No design deviation, public-contract change, or unapproved Scope Delta occurred.

## Independent evaluation and remaining acceptance

The root ran all six cases in fresh evaluator contexts and temporary repositories.
Evaluators received only the selected request, listed current source prompts and
raw fixtures. Rubrics, prior diagnoses and intended answers were withheld.
[EVALUATION.md](EVALUATION.md) records the actual outputs, independent rubric
assessments and evidence hashes. All six passed. Their prompt/source input hashes
still match after the upstream integration.

| Raw case ID | Required forward evidence |
|---|---|
| `layered-reservations` | Actual design/tasks for two outcomes; criteria through all four milestone work kinds; existing layers, atomic state, and public dependencies preserved; cohesive >5-file task retained. |
| `native-decisions-archive` | Resulting permanent decision and archived change; affected links resolve; old IDs/body hashes preserved; no duplicated body or competing owner; repeated discovery reuses the index. |
| `decision-owner-fallback` | One permanent fallback owner only when needed; archive-safe navigation; new accepted body unchanged by archive. |
| `enforcement-evidence` | Actual three profiles distinguish manual authority, unused configuration, optional CI, proven release blocking, unknown dev policy, and stale receipts. |
| `bandit-context` | Per-issue judgments distinguish decorative/random-secret and trusted/untrusted execution cases; missing plugin context stays unverified; raw report/source hashes unchanged. |
| `small-local-fix` | One compact complete outcome; retained local owner; no domain migration, extra mechanism, or mandatory full-review loop. |

Milestone M1-T/M2-T/M3-T/M4-T2 are complete. All M*-R items and F-3 remain pending
for independent review and acceptance.

## Upstream integration verification

The root fast-forwarded this isolated worktree to the new `main` commit before
review. The sole conflict joined independent UI-verdict and Lizard-provenance
tests in `tests/test-review-approval-gate.py`. Both groups and their entrypoints
are retained; AST comparisons prove their function bodies unchanged. All other
70 existing task paths retained their exact bytes. Upstream changes remain
baseline, outside the five requested improvements.

Because the integrated review-gate inputs changed, the root ran the full locked
suite once more: `uv run --frozen bash tests/run.sh`, exit 0. Inputs were unchanged
during execution. The new full log SHA256 is
`ded9410f7a746693f101c06a2d255cb0b285f4745cc9b869124c511ca5862c48`.
The authoritative current receipt is `skills-upstream-integration/full-suite-receipt.json`
under the parent backend worktree's Git-local runtime. The earlier receipt above
remains historical evidence. The changed test file also has fresh targeted static
analysis; unchanged task paths reuse the prior raw analysis.
