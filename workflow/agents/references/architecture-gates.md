# Architecture Decision-Completeness Gates

Read this reference before writing a full feature design. Apply the compact
variant to quick fixes. Apply `~/.claude/agents/shared/scope-governance.md` or its
installed/source equivalent before making any proposal normative.

## Scope Delta

Separate request/acceptance work from proposed architecture additions. Assign every
material addition an `SD-*` ID with cost/blast radius and obtain an explicit decision
before adding it to design/tasks. `None` is a valid result. Unselected useful ideas
belong in `DEFERRED.md`; a general approach approval does not authorize hidden
infrastructure, threat-model expansion, or broad refactoring.

## Authority inventory

List the sources that constrain the design:

| Source | Authority | Applicable decisions |
|---|---|---|
| Approved specification / ADR / repository guide | Normative | Scope, ownership, contracts, policy |
| Enforced tooling | Normative within its scope | Mechanical format/type/build behavior |
| Approved project profile | Normative | Project-specific implementation/review rules |
| Existing code and samples | Evidence only | Candidate patterns and integration clues |

Do not make a repeated source pattern normative when a higher authority rejects or
has not approved it.

## Boundary matrix

Give every concern exactly one primary owner:

| Concern | Input / trust boundary | Primary owner | Boundary model | Forbidden locations |
|---|---|---|---|---|
| Transport mapping | External request/event | Transport adapter | Request/response shape | Domain persistence |
| Use-case policy | Validated intent | Application/domain service | Domain command/result | Transport/persistence adapter |
| Persistence mechanics | Domain record | Repository/adapter | Serialized record | Transport/use-case service |
| Framework infrastructure | Framework/runtime hook | Application core/integration | Framework config | Feature/domain utility |
| Configuration validation | Untrusted configuration | Settings/bootstrap boundary | Validated settings model | Scattered startup guards |

Adapt names to the target architecture. Do not force a layered design onto a
project that has an approved different structure; still name one owner per concern.

The design is incomplete while a key/codec/TTL, middleware/policy hook, external
payload, transaction, or configuration rule has no owner or multiple competing
owners.

## Business vocabulary

Check public API, service, command, event, and module names:

- describe the user operation or business capability at application/domain levels;
- keep storage, protocol, cache, table, token, and algorithm nouns in adapters or
  infrastructure unless they are genuine domain language;
- make state names meaningful without requiring knowledge of the storage engine.

Record rejected names when the mechanism-oriented alternative would be tempting.

## Reuse research

Before proposing custom cross-cutting infrastructure:

1. inspect an existing integration in the target repository;
2. inspect official documentation for the selected framework/library;
3. inspect user-supplied reference projects when provided;
4. record reuse, extension, or custom-build decision and why.

Apply this gate to middleware, auth/session integration, rate limiting, retries,
logging/tracing, serialization frameworks, and deployment/configuration delivery.
Do not require external research for ordinary domain logic.

## Trust-boundary models

Inventory data entering from requests, events, tokens, serialized stores,
configuration, files, queues, and external providers. Validate and convert it to a
precise model before business policy consumes it. Do not pass an untyped generic
mapping across a trust boundary when the language supports a precise shape.

## Abstraction budget

List each planned alias, wrapper, helper, constant, interface, or new file:

| Abstraction | Current consumers | Independently testable responsibility | Keep / inline |
|---|---:|---|---|

One caller is not an automatic rejection, but it requires substantial isolation,
a stable policy name, or a real boundary. Mere shortening or speculative reuse is
not enough.

## Module-growth forecast

For materially touched files record:

| File | Current lines | Responsibility before | Responsibility added | Split / keep rationale |
|---|---:|---|---|---|

A file over 300 lines or gaining a second responsibility requires an explicit
structural decision. Also reject fragmentation into trivial one-purpose files.
The number is a review trigger, not an automatic split rule.

## Infrastructure authority and non-goals

State:

- which runtime, deployment, secret/configuration, and observability systems are
  in scope;
- who owns them;
- which adjacent systems are explicitly not being changed;
- which public contracts or authorization boundaries remain unchanged.

Application work does not grant implicit authority to create a second deployment
or secret-delivery path.

## Full-feature output gate

Before task breakdown, confirm the design contains:

- required scope, approved Scope Delta IDs, and explicit non-goals;
- authority inventory;
- boundary matrix;
- business-vocabulary decisions;
- reuse decisions for custom cross-cutting concerns;
- trust-boundary model inventory;
- abstraction budget;
- module-growth forecast;
- infrastructure authority and non-goals.

If a material decision is missing, return `## NEEDS USER INPUT` or request upstream
planning clarification. Do not produce implementation tasks.

## Quick-fix compact gate

For a genuinely small fix, keep the design brief but still answer:

- which owner changes;
- whether a new boundary, abstraction, local import, or infrastructure path appears;
- whether the touched file gains a second responsibility;
- what is explicitly out of scope.
- whether `Scope Delta` is `None`; otherwise stop and escalate before editing.

Escalate to the full workflow if any answer requires a new high-cost design choice.
