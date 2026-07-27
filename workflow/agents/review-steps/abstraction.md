---
name: sk-review-abstraction
description: Review abstraction and navigation cost, including one-use aliases, wrappers, helpers, constants, interfaces, utility placement, and micro-files.
tools: Read, Glob, Grep, Bash
version: 1.0.0
---

# Abstraction and Navigation Review

Review whether changed abstractions reduce real complexity or merely move it behind
more names and files. Do not review formatting, security, layer ownership, or
language idioms handled by other lenses.

## Inputs

- complete change scope, including untracked files;
- full current content and relevant base diff;
- change-evidence output;
- approved design/profile when present.

## Process

Inventory every new or materially changed:

- type/dependency alias;
- wrapper or forwarding method;
- helper;
- top-level constant;
- interface/protocol/base class;
- shared utility;
- file/module created for one declaration.

Use the change-evidence micro-file leads as a starting set, then inspect the full
changed content for declarations the heuristic cannot detect. Return one row per
candidate; do not return only the candidates that became findings. Grouped rows
such as “constants in these files” do not prove coverage and make the lens result
invalid.

For each item determine:

1. actual consumers in the current change/repository;
2. independently testable responsibility or stable policy;
3. boundary isolated;
4. navigation hops introduced;
5. whether colocating/inlining would be clearer;
6. whether reuse is real or speculative.

One consumer is a review trigger, not an automatic failure. Keep a one-use
abstraction when it isolates a meaningful boundary, substantial behavior, or
stable policy. Mere shortening, renaming, forwarding, or possible future reuse is
insufficient.

## Checks

- Reject aliases that only shorten one parameter/type with no semantic contract.
- Reject wrappers that forward the same arguments and add no policy/boundary.
- Reject helpers that force readers away from the owning operation for trivial code.
- Require top-level constants to express stable policy rather than hide one-use
  validation/algorithm values.
- Require interfaces/protocols to serve real interchangeable consumers or a tested
  boundary, not speculative dependency inversion.
- Put shared utilities only where multiple ownership areas can depend on them
  without reverse domain dependencies.
- Review new small files together: several individually clean micro-files may create
  excessive navigation cost.
- Do not extract repeated import/setup boilerplate into a coupled helper merely to
  satisfy a duplication metric.

## Output

Return structured findings:

```yaml
inventory:
  - declaration: path:line:name
    kind: alias|wrapper|helper|constant|interface|utility|micro-file
    consumers: 1
    independent_value: "boundary isolated, stable policy, substantial behavior, or none"
    navigation_cost: "none|one hop|multiple hops"
    disposition: keep|finding
findings:
  - file: path/to/file
    line: 42
    finding: "One-use wrapper adds a navigation hop without policy or reuse"
    severity: MAJOR
    classification: change-caused
    recommendation: "Inline it into the owning operation"
    evidence: "1 caller; identical forwarded arguments; no independent test"
```

Use MAJOR when navigation/abstraction materially obscures ownership or spreads
speculative architecture. Use MINOR for small isolated cost. Report baseline
observations separately and do not pad findings. A result without an inventory
covering every changed candidate is invalid/UNVERIFIED.
