# Review Aggregation and Verdict Policy

Use `scope-governance.md` for remediation authority. This policy determines review
validity and verdict; severity never grants scope.

## Lenses and ownership

A full review runs exactly three independent lenses in one wave:

1. **architecture-design** — shape and ownership: components/modules, dependency
   and import direction, responsibility placement, abstraction/navigation,
   file/module structure, API/schema/model compatibility, packaging/loaders;
2. **correctness-safety** — semantics and risk: approved behavior, state/edge/failure
   paths, recovery/migration/concurrency/idempotency, trust/security/data loss,
   semantic compatibility, test adequacy, executable instruction correctness;
3. **engineering-quality** — implementation and tool evidence: root-produced gates
   and static analysis, stack idioms, readability, complexity, duplication, dead
   code, error handling, and test-code quality.

A lens is valid only when its artifact is parseable, belongs to the current
snapshot, covers its manifest, inspects assigned raw current/base content, and
returns a complete finding set or explicit clean result. Timeout, empty output,
stale hash, unsafe exclusion, or missing required context is UNVERIFIED. No lens may
spawn. Inline mode must preserve three separately labelled passes.

The three scope-manifest union must validate against `review-map.json`. Uniform
full-file reading by every lens is not required. Unchanged content is reusable only
when its recorded hash is verified.

## Readiness

The root runs formatter, lint, type/build, tests, diff integrity, project gates, and
applicable static analysis once per snapshot before dispatch. Any red required gate
prevents review from starting. Engineering-quality consumes compact provenance and
must not rerun the full battery. Missing/failed required tooling is UNVERIFIED.

## Finding classification

- **Change-caused:** introduced, modified, or materially worsened by the change.
- **Touched-regression:** pre-existing defect expanded or relied on by the change.
- **Baseline:** unchanged and not worsened; visible but non-blocking.

Finding disposition remains separate from severity. Every finding includes
`required_outcome`, `disposition`, `scope_basis`, `remedy_authority`,
`risk_if_deferred`, and `blocks_release`. Only `required_fix` makes the outcome
automatically mandatory; it does not authorize a new remedy design. An explicitly
selected `user_decision` is separate authority. Unresolved `user_decision` yields
`TRIAGE REQUIRED`; backlog/baseline items never block.

Severity:

- **BLOCKER:** realistic auth/contract failure, secret exposure, corruption/data
  loss, unsafe destructive instruction, broken initialization, or mandatory gate;
- **MAJOR:** wrong ownership/direction/shape, material semantic risk, missing
  critical tests, or meaningfully worsened maintainability;
- **MINOR:** bounded reliability/maintainability defect;
- **NITPICK:** optional preference.

## Review rounds

### Round 1 — full

Run all three independent lenses together. Aggregate their complete finding sets,
resolve every `user_decision`, and freeze the exact remediation allowlist. A lens
may not hold back findings to generate later cycles.

### Targeted Round 2

Use a fresh snapshot. Require:

- a valid parent full review and immutable parent fingerprint;
- frozen allowlist and complete remediation delta;
- immutable pre/post fingerprints and verified unchanged hashes;
- no unexplained paths or scope expansion;
- root gates run once on the new snapshot;
- every finding-owning and impact-routed lens.

Impact routing follows lens ownership. Multiple lenses may apply; contract/schema
fixes route both shape and semantic owners when both changed. Old evidence is never
proof for changed content.

A material scope expansion, changed authority/base, dependency/trust/infrastructure
expansion, unexplained path, invalid parent, or unprovable delta forces a full
three-lens run while consuming Round 2.

A normative design/ADR amendment invalidates targeted mode and requires a full
three-lens review against the new authority fingerprint within the remaining round
budget.

### Exceptional Round 3

Allow only for an unresolved allowlisted defect, remediation regression, or newly
proven critical correctness/security defect. Use a fresh snapshot, root gates once,
and owning/impact-routed lenses; escalation conditions may require all three.

There is no automatic Round 4. After Round 3 return `NEEDS USER DECISION` with exact
blockers/options. Transport-only wait timeouts do not increment the round and round
counters do not reset within the workflow unless the user approves a new change
scope/workflow.

## Aggregation

1. Validate snapshot, scope union, provenance, and lens artifacts.
2. Merge only identical concerns at overlapping locations.
3. Preserve source lens, severity, change class, disposition, scope basis, required
   outcome, remedy authority, deferral risk, and release flag.
4. Group required fixes, user decisions, backlog, and baseline; sort by severity.
5. Keep full findings/logs Git-local and a compact durable verdict in OpenSpec.

## Approval invariant

Return `APPROVED` only when required gates are green, scope is complete, required
lenses are valid, no `required_fix` remains, baseline is separate, and there are
zero required UNVERIFIED dimensions.

No source remediation begins while an allowlisted finding still routes to
Architecture, Scope Triage, or Investigation. A route becomes Developer only after
its required authority and fingerprint are recorded.

Targeted-mode approval additionally requires valid parent full review, complete
routing, all affected lenses valid, resolved allowlist, complete/proven delta, and
no blocking regression or newly proven critical defect.

Return `TRIAGE REQUIRED` when only unresolved `user_decision` remains. Otherwise
return `CHANGES REQUESTED`; use `CHANGES REQUESTED — review incomplete` for missing
execution/evidence. After the round cap use `NEEDS USER DECISION`, never an
automatic fourth pass.

## Required verdict shape

```markdown
## CODE REVIEW COMPLETE

**Decision:** APPROVED | TRIAGE REQUIRED | CHANGES REQUESTED | NEEDS USER DECISION
**Mode:** full | targeted
**Round:** 1 | 2 | 3
**Parent:** none | <full-review fingerprint>
**Snapshot:** <fingerprint>

### Scope and routing
- Base/head and tracked/untracked/deleted/renamed counts
- Scope-manifest validation and routed lenses

### Lens execution
| Lens | Mode | Status |
|---|---|---|
| Architecture-design | parallel/inline/N/A | OK/FINDINGS/UNVERIFIED/N/A |
| Correctness-safety | ... | ... |
| Engineering-quality | ... | ... |

### Mandatory fixes / scope decisions / backlog / baseline
[Grouped findings]

### Readiness and provenance
[Compact commands/statuses and full-log paths]

### Decision rationale and next action
[Why the invariant passes/fails]
```
