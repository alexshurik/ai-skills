# Review Aggregation and Verdict Policy

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

## Finding classification

- **Change-caused:** introduced, modified, or materially worsened by the diff.
- **Touched structural regression:** pre-existing issue expanded or relied on by
  the change.
- **Baseline/out-of-scope:** unchanged and not worsened.

Only the first two determine the change verdict. Always render baseline separately.

## Severity

- **BLOCKER:** exploitable security issue, secret exposure, data loss/corruption,
  incorrect authorization/contract, broken initialization, or CI-blocking error.
- **MAJOR:** wrong ownership/dependency direction, misleading business model,
  unapproved scope expansion, meaningful abstraction/structure/import debt,
  missing critical tests, or high quantitative risk.
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

Security findings default to BLOCKER. Downgrade only with explicit limited impact
and a real compensating control.

## Aggregation

1. Validate every applicable lens result.
2. Merge findings matching file, overlapping line, and concern.
3. Keep highest severity and concatenate distinct evidence/recommendations.
4. Preserve source lenses and change/baseline classification.
5. Sort BLOCKER → MAJOR → MINOR → NITPICK, then by concern and path.
6. Keep tool provenance verbatim.

Do not deduplicate different concerns merely because they point at the same line.
For example, wrong layer ownership and one-use navigation cost remain independent.

## Approval invariant

Return **APPROVED** only when:

- every applicable lens ran and is valid;
- no change-caused or touched-regression BLOCKER/MAJOR remains;
- complete changed/untracked scope was reviewed;
- the static-analysis provenance table is present;
- no required gate dimension is UNVERIFIED;
- baseline findings are separated and visible.

Otherwise return **CHANGES REQUESTED**. When the cause is missing execution rather
than a code defect, say `CHANGES REQUESTED — review incomplete`.

## Required verdict shape

```markdown
## CODE REVIEW COMPLETE

**Decision:** APPROVED | CHANGES REQUESTED

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

### Required changes
[Change-caused and touched-regression findings]

### Baseline/out-of-scope
[Visible but excluded from feature verdict]

### Deep analysis provenance
[Verbatim table and summary]

### Decision rationale
[Why the invariant passes/fails]
```

End with:
**"Caller: surface the full findings, baseline section, provenance, and verdict to
the user verbatim — do not summarize."**
