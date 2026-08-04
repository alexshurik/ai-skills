# Review Aggregation and Verdict Policy

Read and apply `~/.claude/agents/shared/scope-governance.md` or its
source-repository equivalent. This file determines review validity and severity;
scope governance determines whether a finding has remediation authority. Never
infer one from the other.

## Required lenses

Run these lenses for code changes:

1. contract/security;
2. architecture/layers;
3. abstraction/navigation;
4. structure;
5. imports;
6. stack rules.

Run instruction quality when the scope contains repository guidance,
specifications/ADRs, project profiles, skills, agent prompts/references, or their
packaging/generation scripts. Otherwise record N/A.

A lens is valid when it ran as a parallel subagent or disclosed inline section and
returned parseable findings/N/A. Error, timeout, empty output, or silent omission is
UNVERIFIED.

A lens is also invalid when its lens scope manifest omits a review-map path, assigns
no reading depth, or gives no defensible reason for metadata-only/excluded treatment.
`targeted-content` must include changed intervals, enclosing declarations, relevant
base context, and required call sites; a material lead expands to full content.
Complete scope is mandatory; uniform full-file reading by every lens is not.

The structure/coverage lens is additionally invalid unless its neutral
`coverage-ledger.json` passes deterministic validation against `review-map.json`.
Every human-authored readable text path and readable deleted base file must be
`full-content` and `reviewed`; metadata-only treatment is limited to validated locks,
binaries, symlinks, unavailable content, and generated/vendor output. The neutral
ledger may guide another lens but is not evidence for its verdict: specialists must
verify relevant raw repository/base content independently.

For a full review, the structure/coverage thread runs first and the remaining lens
verdicts run as independent clean targeted threads over the same immutable snapshot.
No lens may spawn. A targeted rerun can diagnose remediation, but final approval
requires a new full snapshot reviewed by every applicable lens.

## Finding classification

- **Change-caused:** introduced, modified, or materially worsened by the diff.
- **Touched structural regression:** pre-existing issue expanded or relied on by
  the change.
- **Baseline/out-of-scope:** unchanged and not worsened.

Only the first two are eligible to affect the current change; finding disposition
still decides remediation/release authority. Always render baseline separately.

For every finding also assign the scope-governance fields `disposition`,
`scope_basis`, `risk_if_deferred`, and `blocks_release`. Detection remains strict:
a reviewer may report any evidence-backed concern. Only `required_fix` creates
automatic remediation authority; `user_decision`, `backlog`, and `baseline` do not.

## Severity

- **BLOCKER:** exploitable security issue, secret exposure, data loss/corruption,
  incorrect authorization/contract, broken initialization, or CI-blocking error.
- **MAJOR:** wrong ownership/dependency direction, misleading business model,
  meaningful change-caused abstraction/structure/import debt, missing critical
  tests, or high quantitative risk. An unapproved scope expansion is a planning/
  triage defect; the proposed expanded implementation is not automatically required.
- **MINOR:** bounded maintainability/reliability issue that does not invalidate the
  design.
- **NITPICK:** optional preference; do not block.

Normalize quantitative findings:

| Finding | Severity |
|---|---|
| high/critical vulnerable dependency | BLOCKER |
| moderate vulnerable dependency | MAJOR |
| hardcoded credential | BLOCKER |
| CI linter/type/build failure | BLOCKER |
| circular dependency | MAJOR |
| cyclomatic/cognitive complexity >15 | MAJOR |
| cyclomatic/cognitive complexity >10 | MINOR |
| meaningful duplication >5 lines | MAJOR |
| high-confidence dead/unused dependency | MINOR |

Assign security severity from a demonstrated attack path, likelihood, impact, the
approved trust model, and compensating controls. Proven auth bypass, secret exposure,
arbitrary transaction substitution/repeat spend, or corruption remains BLOCKER.
Uncertainty is `NEEDS_INVESTIGATION`/UNVERIFIED; optional defense-in-depth or an
expanded threat model is not an automatic BLOCKER.

## Aggregation

1. Validate every applicable lens result.
2. Validate review-map/coverage-ledger path equality and fingerprints.
3. Merge findings matching file, overlapping line, and concern.
4. Keep highest severity and concatenate distinct evidence/recommendations.
5. Preserve source lenses, change class, scope basis, disposition, deferral risk,
   and release-blocking flag.
6. Group `required_fix`, `user_decision`, `backlog`, and `baseline` before sorting
   BLOCKER → MAJOR → MINOR → NITPICK within each group.
7. Keep tool provenance and full log paths in the Git-local technical report; keep
   only the compact decision/evidence links in the durable OpenSpec artifact.

Do not deduplicate different concerns merely because they point at the same line.
For example, wrong layer ownership and one-use navigation cost remain independent.

## Approval invariant

Return **APPROVED** only when:

- every applicable lens ran and is valid;
- no `required_fix` remains;
- complete changed/untracked scope was reviewed;
- deterministic review-map and full-coverage ledger validation passed;
- the static-analysis provenance table is present;
- no required gate dimension is UNVERIFIED;
- baseline findings are separated and visible.

Return **TRIAGE REQUIRED** when no `required_fix` remains but one or more
`user_decision` items has no recorded decision. Backlog/baseline items never block.
Once the user defers/rejects/promotes those items, update the durable triage without
rerunning lenses if no source or normative artifact changed.

Otherwise return **CHANGES REQUESTED**. When the cause is missing execution rather
than a code defect, say `CHANGES REQUESTED — review incomplete`.

## Required verdict shape

```markdown
## CODE REVIEW COMPLETE

**Decision:** APPROVED | TRIAGE REQUIRED | CHANGES REQUESTED

### Scope
- Base/head:
- Tracked changed:
- Untracked:
- Deleted/renamed:

### Pass execution
| Lens | Mode | Status |
|---|---|---|
| Contract/security | parallel/inline | OK/FINDINGS/UNVERIFIED/N/A |
| Architecture/layers | ... | ... |
| Abstraction/navigation | ... | ... |
| Structure | ... | ... |
| Imports | ... | ... |
| Stack rules | ... | ... |
| Instruction quality | ... | ... |

### Mandatory in-scope fixes
[`required_fix` findings]

### Scope additions requiring decision
[`user_decision` findings]

### Deferred/backlog candidates
[`backlog` findings]

### Baseline/out-of-scope
[`baseline` findings]

### Deep analysis provenance
[Compact table, summary, and full-log artifact paths]

### Decision rationale
[Why the invariant passes/fails]
```

Return a compact handoff with verdict, fingerprint, report paths, lens statuses,
required finding IDs/titles, missing verification, and next step. Keep the full
findings, baseline section, and provenance in artifacts and show them on request.
