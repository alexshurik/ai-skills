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

Record the exact config path, selected setting/rule, command, scope, and exception.
Do not claim a tool enforces architecture or vocabulary it cannot inspect.

### Approved candidates

Read current:

- `AGENTS.md`, `CLAUDE.md`, contribution/convention docs;
- accepted ADRs and approved active specifications;
- project-level rule files.

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

Count patterns and counterexamples. Sampling can describe naming, docstrings,
imports/layout, typing, error handling, tests, framework idioms, and file grouping.
It cannot approve them.

Classify a sample as Legacy/uncertain when it conflicts with an Enforced/Approved
source, is inconsistent, is deprecated, or has unclear ownership.

Never promote dependency aliases, local/dynamic imports, wrappers, one-use helpers,
top-level constants, micro-files, shared utility placement, or custom cross-cutting
integrations from frequency alone.

## Rule record

Each item must include:

```text
ID: ENF-<topic> | APP-<topic> | OBS-<topic> | LEG-<topic>
Classification: Enforced | Approved | Observed | Legacy/uncertain
Source: exact file/section/config or sampled paths
Evidence: setting or N/M count plus counterexamples
Scope: affected language/package/component
Confidence: high | medium | low
Instruction/check: only for Enforced or Approved
```

Use stable IDs so `coder.md` and `reviewer.md` cannot drift independently.

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
  Source: `<path/section>` · Scope: `<scope>`

## Enforced implementation rules
- [ENF-topic] <imperative instruction>
  Source: `<config setting>` · Verify: `<cmd>`

## Conflicts and escalation
- Follow the cited source. If two normative sources conflict, stop and request
  resolution. Never use sample frequency as the tie-breaker.
```

## `reviewer.md` template

```markdown
# Project Reviewer Profile — <repository>

Review only the normative IDs from `coder.md`.

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
- every normative item has a source and stable ID;
- reviewer IDs match coder IDs;
- sample counts and counterexamples remain in `evidence.md`;
- uncertain patterns are questions, not instructions;
- exact safe format/lint/type/test commands are recorded;
- the user is shown what was generated or changed.
