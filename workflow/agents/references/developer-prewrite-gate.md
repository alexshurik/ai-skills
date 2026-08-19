# Developer Pre-Write Gate

Run this gate before the first source edit. It verifies that tests and nearby code
will not pull implementation away from the approved architecture.

Apply `~/.claude/agents/shared/scope-governance.md` or its installed/source
equivalent. For remediation, require a finding-ID
allowlist and never treat the complete review report as implementation authority.

## Authority order

```text
approved specification / ADR / repository guidance
  > enforced tooling
  > approved project profile
  > observed neighboring code
```

Treat samples as evidence. When a common pattern conflicts with a higher authority,
do not copy it. Stop for clarification when the conflict changes architecture,
scope, or a public contract.

## Pre-write checklist

1. Load the approved boundary matrix and infrastructure non-goals.
2. Assign every planned edit to its owning concern: transport, use-case/domain
   policy, persistence, framework infrastructure, or configuration/bootstrap.
3. Confirm external or serialized input becomes a validated precise shape before
   business policy consumes it.
4. Before a custom cross-cutting wrapper, search the repository, official
   integration, and user-supplied references recorded by the design.
5. Inventory each new alias, helper, constant, wrapper, interface, or file.
6. Record current file sizes and responsibilities for materially touched files.
7. Inventory local/dynamic imports and their claimed reason.
8. Map every planned edit to an acceptance criterion, approved Scope Delta ID, or
   allowlisted `required_fix` finding.
9. For remediation, load each finding's `required_outcome` and `remedy_authority`,
   then compare the intended fix with the approved design fingerprint.

If the approved design lacks an owner for a material concern, return
`## NEEDS USER INPUT` or request Planning rework. Do not invent the owner while
coding.

## Remediation design-delta gate

Before a remediation source edit, describe the intended fix narrowly and compare it
with the approved owners, models, public contracts, dependencies, operational
mechanisms, infrastructure scope, and non-goals.

- Continue only when the finding is routed `within_approved_design` and the
  comparison has no material design delta.
- For `architecture_decision_required`, or when the comparison reveals a missing or
  invalidated design decision, return `BLOCKED — REPLAN_REQUIRED` to Architecture.
- For `scope_decision_required`, return `BLOCKED — REPLAN_REQUIRED` to Scope Triage.
- For `investigation_required`, perform no source edits and return the missing
  evidence needed for a bounded read-only investigation.

The permission to fix a mandatory defect is not permission to select a new
architecture. Do not turn an ungrounded caller preference into a design restriction,
or evade an unresolved design decision by repurposing an artifact with mismatched
semantics. Architecture must first approve its owner, scope, lifecycle, consistency,
growth, and recovery behavior.

## New-abstraction decision

Keep a one-use abstraction only when it isolates a meaningful boundary, stable
policy, substantial behavior, or independently testable responsibility. Otherwise
keep the declaration with its owner or inline it.

Do not create a shared utility without real consumers from distinct ownership
areas and a dependency direction that remains valid.

## Local/dynamic import evidence

Do not accept “avoids a circular import” as evidence by itself.

For a retained local/dynamic import:

1. reproduce the cycle in a clean process with the relevant import orders;
2. name the exact dependency path;
3. remove or relocate the dependency if the cycle is not reproducible;
4. add an import regression test when the workaround remains.

Language/framework idioms may provide other approved reasons for dynamic loading;
record that authority explicitly.

## Before/after structural evidence

After implementation, compare:

- line count before and after;
- responsibilities before and after;
- files crossing 300 lines;
- new small files and their responsibility;
- abstractions added and their actual consumers;
- local/dynamic imports added or removed.

These are review leads, not automatic findings. Explain every threshold crossing or
new responsibility in the handoff.

## Handoff evidence

Report:

- boundary ownership applied;
- reuse decision for any cross-cutting integration;
- trust-boundary models introduced or reused;
- new-abstraction inventory with keep/inline reasons;
- local-import reproduction results;
- before/after structure evidence;
- any design deviation and its approval source;
- remediation route and design-delta result for every allowlisted finding.
