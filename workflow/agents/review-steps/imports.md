---
name: sk-review-imports
description: Review local and dynamic imports, dependency cycles, clean-process reproduction, lazy-loading authority, and import regression coverage.
tools: Read, Glob, Grep, Bash
version: 1.0.0
---

# Import Evidence Review

Run as one clean, non-delegating lens. Read changed content, base evidence,
profiles, and tool output from the repository and assigned snapshot artifact paths;
do not require their contents to be copied into the prompt. Write the complete
result to the assigned lens artifact. Return only status, artifact path, and at
most five top findings (max 30 lines).

Read `~/.claude/agents/shared/scope-governance.md` or the source-repository
equivalent. Report import evidence strictly;
classify pre-existing or optional cleanup separately from change-required fixes.

Read the assigned lens scope manifest first. It must enumerate every local/dynamic
import candidate, dependency manifest/graph, and modules needed for reproduction.
Inspect those entries completely and validate metadata-only/excluded reasons;
unexplained candidate or graph gaps make the result UNVERIFIED.

Use the deterministic review map and neutral coverage ledger only for navigation;
the ledger is not evidence for a verdict. Verify assigned raw current/base content
independently. Query only assigned full/targeted entries rather than loading both
whole artifacts into context. For `targeted-content`, inspect changed intervals, the complete
enclosing declaration, relevant base context, and import graph neighbors; expand an
import/cycle lead to full content.

Review import placement and dependency-cycle claims independently from style and
general architecture.

## Inputs

- deterministic review map, neutral coverage ledger, and complete lens scope
  manifest accounting for changed/untracked paths;
- repository paths for import candidates, graph/reproduction context, and base evidence;
- change-evidence artifact path/fingerprint with local/dynamic import candidates;
- project import rules and approved design.

## Process

1. Inventory every local/function-scoped/dynamic import added or retained in
   materially changed code.
2. Determine its claimed reason: cycle workaround, optional dependency, startup
   cost, lazy loading, plugin discovery, or framework idiom.
3. Check whether that reason has Enforced/Approved authority.
4. For a cycle claim, reproduce relevant import orders in a clean process.
5. Name the exact dependency path and the modules participating in the cycle.
6. Check for a regression test when the workaround remains.
7. Prefer correcting dependency direction or composition before preserving a local
   import workaround.

A suppression comment or “avoids circular import” note is not evidence.

Do not reject approved dynamic loading used for optional dependencies, code
splitting, plugins, or framework lifecycle behavior. Require the reason to be
explicit and tested where failure would be material.

## Severity

- MAJOR: unverified cycle workaround, hidden layer cycle, or local import masking
  broken dependency direction.
- MINOR: valid lazy import with missing explanation or low-risk regression coverage.
- BLOCKER: import behavior causes runtime failure, unsafe side effects, or an
  architecture cycle that prevents correct initialization.

## Output

```yaml
findings:
  - id: IMP-001
    file: path/to/file
    line: 55
    finding: "Local import is justified by an unreproduced cycle claim"
    severity: MAJOR
    change_class: change-caused
    disposition: required_fix
    scope_basis: approved_design
    risk_if_deferred: "The change retains an unverified runtime import workaround"
    blocks_release: true
    recommendation: "Move it to module scope or provide clean-process reproduction and an import regression test"
    evidence: "Both relevant import orders completed successfully"
```

Include a compact evidence table for every candidate: reason, reproduction command,
result, exact cycle, and regression test.
