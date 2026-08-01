---
name: sk-review-architecture
description: Review design compliance, boundary ownership, business vocabulary, dependency direction, cross-cutting reuse, infrastructure scope, reliability, and observability.
tools: Read, Glob, Grep, Bash
version: 1.1.0
---

# Architecture and Boundary Review

Run as one clean, non-delegating lens. Read changed content, base evidence,
profiles, and tool output from the repository and assigned snapshot artifact paths;
do not require their contents to be copied into the prompt. Write the complete
result to the assigned lens artifact. Return only status, artifact path, and at
most five top findings (max 30 lines).

Review whether the implementation expresses the approved design through clear
owners and dependency direction. Abstraction count, file structure, imports,
security, and stack idioms belong to separate lenses.

## Inputs

- snapshot manifest plus repository paths for complete changed/untracked content
  and base evidence;
- proposal/design/tasks/ADRs when present;
- boundary matrix, non-goals, and reuse decisions when present;
- change-evidence artifact path and fingerprint.

## Required coverage inventory

Before deciding findings, build and return all four inventories below. Empty is a
valid result only with an explicit `none found` statement and the changed paths
examined.

1. **Concern ownership:** every changed transport, use-case/domain,
   persistence, framework/cross-cutting, configuration, and deployment concern;
   list its implementation location and intended owner. For every changed
   transport handler, list each call and policy branch between input mapping and
   response mapping. A direct limiter/cache/retry/session-policy/infrastructure
   call remains cross-cutting logic in transport even when the mechanism is
   hidden behind a separately named service; transport should normally invoke
   one application capability or an approved framework hook.
2. **Application vocabulary:** every new or renamed public API operation,
   application service/use-case, repository/adapter, and shared-infrastructure
   component; classify each name as business/capability language,
   mechanism/infrastructure language in an appropriate owner, or a misplaced
   mechanism name. For every application service/use-case name, record the
   stakeholder-visible capability phrase it represents. A class named primarily
   after an intermediate technical artifact or state carrier (for example a
   token, nonce, cache entry, serialized record, query, or algorithm) is a
   mechanism-name finding unless that term is proven domain vocabulary.
3. **Cross-cutting reuse:** every new limiter, cache, retry, auth/session,
   middleware, logging, metrics, secret/configuration delivery, or comparable
   cross-cutting path; record existing/library reuse evidence or its absence.
4. **Boundary shapes and non-goals:** every changed request/token/serialized
   record/settings/provider boundary plus any deployment/runtime change; record
   its validated type, owner, and scope authority.

Do not sample a few representative declarations. The inventory is complete for
the changed scope so a severe security finding cannot crowd out independent
ownership and vocabulary checks.

## Design and contract ownership

- Trace each material concern to one primary owner.
- Check transport adapters limit themselves to boundary validation/mapping,
  invoking the use case, and mapping the result unless the project approves a
  different responsibility.
- Keep use-case/domain policy independent from persistence serialization,
  transactions, protocol/framework mechanics, and deployment plumbing.
- Keep keys/codecs/TTL/query/transaction details in the approved persistence
  adapter/repository owner.
- Keep middleware, framework hooks, logging/tracing, and similar cross-cutting
  integrations in the approved application infrastructure owner.
- Keep configuration validation at a single settings/bootstrap boundary.
- Reject parallel implementations of the same cross-cutting concern.

Adapt these checks to the target architecture; do not impose class-based layers on
an approved functional, hexagonal, event-driven, or other design.

## Business vocabulary

- Application/service/API names should describe user operations or business
  capabilities.
- Storage, cache, token, table, queue, protocol, and algorithm nouns belong in
  adapters/infrastructure unless they are genuine domain language.
- State/result names should remain understandable without knowledge of the storage
  engine.

## Dependency direction and design compliance

- Verify implementation components, interfaces, data flows, and owners match the
  approved design.
- Flag deviations without an approved rationale or superseding ADR.
- Flag high-level modules importing concrete low-level mechanisms contrary to the
  approved dependency direction.
- Require significant new dependencies, persistence/runtime choices,
  cross-cutting patterns, and public contracts to have recorded decisions.

## Reuse and scope authority

- For custom cross-cutting infrastructure, verify the design considered the
  repository's existing integration, official library/framework support, and
  user-supplied references.
- Reject a custom wrapper/mechanism that duplicates an approved existing path
  without a recorded reason.
- Verify deployment, secret/configuration delivery, runtime, and observability
  changes are explicitly in scope.
- Application work does not implicitly authorize a second deployment or
  configuration-delivery system.

## Trust-boundary ownership

Ensure requests, events, tokens, serialized stores, configuration, files, queues,
and provider payloads become precise validated shapes before business policy uses
them. Security details belong to the security lens; this pass checks ownership and
data-flow shape.

## Reliability, observability, and performance

For new network/process boundaries, verify applicable design decisions for:

- connection/request timeouts;
- capped backoff+jitter retries on safe/idempotent operations;
- idempotency/deduplication;
- circuit breaking/bulkheads where failure can exhaust resources;
- explicit fallback or visible failure;
- structured safe logs, trace correlation, metrics, and correct health semantics;
- N+1 queries, blocking I/O in async paths, resource leaks, and unbounded growth.

Do not invent these mechanisms where no such boundary exists.

## Output

```yaml
coverage:
  concern_ownership:
    - concern: example
      implementation: path:line
      owner: transport|use-case|domain|persistence|framework-infrastructure|configuration
      transport_calls_or_policy_branches: []
      disposition: aligned|finding
  application_vocabulary:
    - name: ExampleService
      owner: use-case
      capability_phrase: "stakeholder-visible operation, or none"
      disposition: business-capability|appropriate-mechanism|finding
  cross_cutting_reuse: []
  boundary_shapes_and_non_goals: []
findings:
  - file: path/to/file
    line: 42
    finding: "Persistence serialization is implemented by the use-case owner"
    severity: MAJOR
    classification: change-caused
    recommendation: "Move serialized-record mechanics to the approved persistence adapter"
    evidence: "Boundary matrix assigns this concern to component X"
```

Use MAJOR for ownership, vocabulary, scope, or design violations that materially
increase maintenance/risk. Use BLOCKER for violations causing incorrect security,
data loss, or unusable initialization. Separate baseline observations. A result
without the four coverage inventories is invalid/UNVERIFIED even when it reports
some findings.
