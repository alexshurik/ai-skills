---
name: sk-review-imports
description: Review local and dynamic imports, dependency cycles, clean-process reproduction, lazy-loading authority, and import regression coverage.
tools: Read, Glob, Grep, Bash
version: 1.0.0
---

# Import Evidence Review

Review import placement and dependency-cycle claims independently from style and
general architecture.

## Inputs

- complete changed/untracked file scope;
- full files and diff;
- change-evidence local/dynamic import candidates;
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
  - file: path/to/file
    line: 55
    finding: "Local import is justified by an unreproduced cycle claim"
    severity: MAJOR
    classification: change-caused
    recommendation: "Move it to module scope or provide clean-process reproduction and an import regression test"
    evidence: "Both relevant import orders completed successfully"
```

Include a compact evidence table for every candidate: reason, reproduction command,
result, exact cycle, and regression test.
