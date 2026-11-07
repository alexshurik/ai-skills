# Forward evaluation evidence

Date: 2026-11-07. Six independent clean-context cases passed the parent evaluator's
withheld rubric. These are actual generated artifacts, not merely corpus-integrity
tests. Code review and acceptance remain separate and pending.

Each evaluator received one copied fixture, its raw request and the listed current
source instructions. Evaluators were not given goldens, sibling outputs, parent
history or implementation diagnoses. They produced artifacts without modifying
fixture application code, installing tools or invoking external services. The
parent read the outputs, compared source and input hashes, and assessed the
withheld criteria. Referenced prompt hashes still matched current source afterward.

| Case | Observed result | Criteria |
| --- | --- | --- |
| `layered-reservations` | Reserve/cancel outcomes retain the layered service, public ports and one SQL transaction. Design and task evidence cover both criteria and D/I/T/R work. A cohesive seven-file milestone is not split by a file-count quota. | AC-1/2 |
| `small-local-fix` | One local outcome retains `metrics.py`, adds the approved empty result, preserves arithmetic and marks state/transactions N/A. No VSA, new ADR, wrapper, separate Tester or extra full review is introduced. | AC-1/2 |
| `native-decisions-archive` | Existing `docs/decisions` remains the owner. New decision 0043 follows indexed legacy 0042. Accepted and legacy decision bodies retain their hashes; affected links resolve after archive. | AC-3 |
| `decision-owner-fallback` | With no existing permanent owner, one `docs/adr` record and index are created. The design points to that record, the change is archived, and affected navigation resolves. | AC-3 |
| `enforcement-evidence` | Actual coder/reviewer/evidence profiles preserve stable IDs. Approved Decimal/manual review is distinct from mechanical enforcement; optional audit, stale lint evidence, partial core provenance and unknown dev merge policy remain explicit. | AC-4 |
| `bandit-context` | All five raw issues retain severity/confidence. Two contextual non-defects, two required security fixes and one missing-context investigation remain distinct. The intentionally unsafe fixture is not approved; raw FINDINGS are not rewritten. | AC-5b |

The parent also checked legacy ADR body hashes and affected relative links, fixture
source preservation, coder/reviewer normative-ID agreement and prompt-input
freshness. The Bandit case's correct non-approval is a successful evaluation result,
not a claim that its fixture is safe.

Deterministic Lizard regressions cover 21 logged/in-memory cases, including clean
threshold text, real warnings, forced-zero findings, failures and inconsistent
reports. The final locked `uv run --frozen bash tests/run.sh` passed. Its receipt
and exact input closure are recorded in [implementation.md](implementation.md).

Full generated artifacts, raw logs, input manifests and parent assessments live in
the Git-local `organize-vsa-and-workflow/forward-evals/<case>/` evidence directory
of the parent Deli Check migration. The source corpus and withheld assessment
criteria are committed under `evals/scenario-workflow/`; reproducing a behavioral
case requires a fresh evaluator, not just running the corpus-integrity test.

| Case report | SHA-256 |
| --- | --- |
| layered-reservations | `d1c0bd8e2bf42ac9becbf4dcaf99ff21a20fc65a887dde05f49a2f62c57728b0` |
| native-decisions-archive | `30c60ef433504aa58f27682cd9cb66138a77116c0ef321fb8e3b1ed0ef919d15` |
| decision-owner-fallback | `37e12538dc2dce552c65633762819640eba20fe83bb37ffbd00b9d8d8c131357` |
| enforcement-evidence | `bfcb57c08d561d892d72e011ef5e0d6618f2d8b1901f9a8d683397d96bcd2292` |
| bandit-context | `fd990fe2edf5c17d72c8e38824c268aa2ad930ea17f3c4709f8575b7b17071d9` |
| small-local-fix | `19797ddfccdd1fed4a2322f6384eea4ba02461eb0441fd2edde44b6b3a577d02` |
