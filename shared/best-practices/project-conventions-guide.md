# Deriving Project Convention Profiles

Generate `.agents/best-practices/project/` so implementation and review follow
approved project-specific rules without turning legacy frequency into authority.
Read `convention-evidence-model.md` before deriving any rule.

## Outputs

Create three artifacts:

- `coder.md` — Enforced and Approved instructions only;
- `reviewer.md` — checks tied to the same normative rule IDs;
- `evidence.md` — Observed and Legacy/uncertain patterns, contradictions, and
  promotion questions.

The project profile is the highest-precedence profile layer, so non-normative
observations must never be written into `coder.md` or `reviewer.md`.

## When to generate or refresh

Generate when `coder.md` is absent. Offer refresh when tooling, repository
guidance, accepted ADRs, or major code organization changes.

Handle three repository states:

1. **Established:** config, guidance, and source exist — classify all evidence.
2. **Thin tooling:** guidance/source exist — Approved rules remain normative;
   samples remain Observed.
3. **Greenfield:** there is no meaningful source sample — ask about naming,
   typing, error handling, tests, module organization, and boundary ownership.
   Record answers as Approved; do not fabricate Observed conventions.

Show generated artifacts for confirmation. Human confirmation may promote explicit
items from Observed to Approved; it does not automatically approve the whole sample.

## Evidence collection

### Enforced candidates

Read actual configuration and authoritative commands:

- formatter, linter, type checker, build, test, pre-commit, and CI config;
- package manager and locked runner;
- language/framework manifests.
- for UI repositories, required static design guards, component/browser tests,
  maintained visual-regression commands, and their CI/pre-commit/workflow invocation.

Collect the model's authority and enforcement evidence separately, including
invocation sources, receipts and remote required-check policy when available.
Do not claim a tool enforces architecture or vocabulary it cannot inspect. Mark
unavailable or stale evidence honestly, including for UI/visual checks.

### Approved candidates

Read current:

- `AGENTS.md`, `CLAUDE.md`, contribution/convention docs;
- accepted ADRs and approved active specifications;
- project-level rule files.
- for UI repositories, current design-system guidance, approved composition owners,
  domain presentation canons, responsive/state contracts, vocabulary decisions, and
  registered visual exceptions.

Resolve contradictions. A newer or explicitly superseding decision wins only when
the repository says so. Otherwise request clarification.

### Observed and Legacy candidates

Sample 8–15 representative, non-generated files across:

- entry points and transport adapters;
- business/application logic;
- persistence/integration code;
- data models;
- tests;
- shared modules.

For a UI component, include the application shell/scroll owner, representative page
frames and headers, the same recurring domain entity in more than one context, one
specialized interaction, responsive/state tests, and maintained rendered evidence
when present. Treat all source-only patterns as Observed until an Enforced or
Approved source authorizes them.

Count patterns and counterexamples. Sampling can describe naming, docstrings,
imports/layout, typing, error handling, tests, framework idioms, and file grouping.
It cannot approve them.

Classify a sample as Legacy/uncertain when it conflicts with an Enforced/Approved
source, is inconsistent, is deprecated, or has unclear ownership.

Never promote dependency aliases, local/dynamic imports, wrappers, one-use helpers,
top-level constants, micro-files, shared utility placement, or custom cross-cutting
integrations from frequency alone.

## Rule record

Use `convention-evidence-model.md` for field semantics and stable IDs. Present a
compact authority record and a separate enforcement record for each normative rule.
Keep the full record once in `coder.md`; `reviewer.md` references that ID/anchor.
Observed/Legacy items in `evidence.md` retain the model's sample evidence fields.

For an applicable approved UI composition rule, also record the concern's primary
owner, forbidden competing locations, and any exception ID with exact scope,
rationale, authority owner/source, and expiry or review trigger.

## `coder.md` template

```markdown
# Project Coder Profile — <repository>

> Normative project layer. Contains Enforced and Approved rules only.
> See `evidence.md` for non-normative observations and legacy patterns.

## Authoritative commands
- [ENF-tooling] Format: `<cmd>` · Lint: `<cmd>` · Types: `<cmd>` · Tests: `<cmd>`
  Source: `<path/section>`

## Approved architecture and conventions
- [APP-topic] <imperative instruction>
  Authority: `<path/section>` · Scope/exceptions: `<scope>`
  Enforcement: `<manual/tool evidence and gaps; link full record below>`

## Enforced implementation rules
- [ENF-topic] <imperative instruction>
  Authority: `<config setting>` · Scope/exceptions: `<scope>`
  Enforcement: `<link to record below>`

## Enforcement evidence by rule ID
- [ENF-topic / APP-topic] Check: `<command, runner/config, checked scope/exclusions>`
  Invocation: `<local/CI sources and observed/configured/unknown status>`
  Blocking: `<local behavior; CI job behavior; merge policy, each with evidence>`
  Freshness: `<checked date, revision/input receipt or stale/unexecuted>`
  Gaps: `<manual checks, uncovered requirements, owner or unknown>`

## Conflicts and escalation
- Follow the cited source. If two normative sources conflict, stop and request
  resolution. Never use sample frequency as the tie-breaker.
```

## `reviewer.md` template

```markdown
# Project Reviewer Profile — <repository>

Review only the normative IDs from `coder.md`; link their authority and enforcement
records instead of duplicating them. Unknown blocking/freshness remains unknown.

- [ENF-topic] Verify `<mechanically enforced behavior>` with `<cmd>`.
- [APP-topic] Verify `<approved architecture/convention>` against `<source>`.

Report Observed/Legacy evidence separately when relevant; do not treat it as a
violation unless an Enforced/Approved rule prohibits the pattern.
```

## `evidence.md` template

```markdown
# Project Convention Evidence — <repository>

## Observed — non-normative
- [OBS-topic] Pattern: `<description>`
  Evidence: N/M files (`paths`) · Counterexamples: `<paths>` · Confidence: `<level>`
  Promotion question: `<question or none>`

## Legacy or uncertain — do not copy by frequency
- [LEG-topic] Pattern: `<description>`
  Evidence: `<paths/count>` · Conflict: `<ENF/APP source or uncertainty>`
  Containment/migration: `<note if known>`

## Decisions needed
- [ ] Promote/reject `<OBS-ID>` with an explicit repository source.
```

## Quality gate

Before returning:

- every coder/reviewer item is Enforced or Approved;
- every normative item has a source and stable ID plus separate enforcement evidence;
- available/configured checks, actual runs, CI failure, and merge blocking are not
  conflated; gaps, unknowns, and stale evidence remain explicit;
- reviewer IDs match coder IDs;
- sample counts and counterexamples remain in `evidence.md`;
- uncertain patterns are questions, not instructions;
- exact safe format/lint/type/test commands are recorded;
- the user is shown what was generated or changed.
