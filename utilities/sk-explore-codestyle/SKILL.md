---
name: sk-explore-codestyle
description: Derive project-specific coder, reviewer, and evidence profiles from enforced tooling, approved repository guidance, and representative source samples without promoting legacy frequency into rules.
---

# Derive Project Convention Profiles

Generate the canonical cross-platform project profile at:

```text
.agents/best-practices/project/
├── coder.md
├── reviewer.md
└── evidence.md
```

## Required reference

Read completely before analysis:

```text
~/.claude/agents/best-practices/project-conventions-guide.md
~/.claude/agents/best-practices/convention-evidence-model.md
```

When running from the skills repository, use:

```text
shared/best-practices/project-conventions-guide.md
shared/best-practices/convention-evidence-model.md
```

Use the guide's Enforced / Approved / Observed / Legacy authority model and
three-artifact output exactly.

## Workflow

### 1. Detect stack and components

Inspect manifests, lockfiles, source extensions, and monorepo layout. Record:

- languages and frameworks;
- independently deployable components;
- package/build runners;
- test locations.

Analyze active components separately when their tooling or conventions differ.

### 2. Collect Enforced evidence

Read formatter, linter, type checker, build, test, pre-commit, and CI configuration.
Record exact settings and commands through the pinned project runner.

Classify a rule as Enforced only when the tool actually checks it. Do not claim
tool authority over architecture, ownership, business vocabulary, or abstraction
quality that it cannot inspect.

### 3. Collect Approved evidence

Read current repository authority:

- `AGENTS.md`, `CLAUDE.md`, contribution/convention docs;
- accepted ADRs;
- approved active specifications;
- existing project profiles.

Record source paths and sections. Detect contradictions or stale/superseded rules.
Ask the user to resolve material conflicts; do not choose by sample frequency.

### 4. Sample source as non-normative evidence

Select 8–15 representative, non-generated files across transport/entry points,
business/application logic, persistence/integrations, models, tests, and shared
modules.

Count patterns and counterexamples for:

- naming and file organization;
- docstrings/comments;
- imports and public boundaries;
- typing/validation;
- error handling;
- testing/fixtures/mocks;
- framework idioms.

Classify these as Observed unless an Enforced or Approved source independently
authorizes them. Classify contradicted, deprecated, inconsistent, or unclear
patterns as Legacy/uncertain.

Never promote dependency aliases, local/dynamic imports, wrappers, forwarding
helpers, top-level constants, one-purpose files, utility placement, or custom
cross-cutting integrations from frequency alone.

### 5. Handle existing profiles

If `.agents/best-practices/project/` already exists, show a concise diff plan and
ask whether to:

- refresh and merge classifications;
- replace after preserving explicit Approved decisions;
- cancel.

Do not silently overwrite human-approved rules. Preserve stable IDs when the source
and meaning remain the same.

### 6. Generate the three artifacts

Write:

1. `coder.md` with Enforced and Approved instructions only.
2. `reviewer.md` with checks referencing the same normative IDs.
3. `evidence.md` with Observed and Legacy/uncertain evidence, counts,
   counterexamples, confidence, and promotion questions.

Each normative item must include:

- `ENF-*` or `APP-*` ID;
- source path/section or exact config;
- scope;
- verification command when mechanically enforced.

Each non-normative item must include:

- `OBS-*` or `LEG-*` ID;
- sampled paths/count and counterexamples;
- confidence;
- contradiction or promotion question.

### 7. Add compatibility pointers

The `.agents` profile is canonical. Do not create a second full rules database.

If `.claude/rules/code-style.md` exists or the user requests Claude compatibility,
replace or create only a short pointer to the canonical `coder.md` and
`evidence.md`, preserving unrelated Claude guidance.

Do not rewrite `AGENTS.md` or `CLAUDE.md` beyond an approved pointer update.

### 8. Validate and report

Before returning, verify:

- `coder.md` contains no `OBS-*` or `LEG-*` instruction;
- `reviewer.md` contains exactly the normative IDs it checks;
- every normative ID has an authoritative source;
- every sample-only pattern remains in `evidence.md`;
- exact safe format/lint/type/test commands are present;
- contradictions and promotion questions are visible.

Return:

- detected stack/components;
- Enforced and Approved counts;
- Observed and Legacy counts;
- unresolved conflicts/questions;
- files created/updated;
- exact validation commands.

## Guardrails

- Modify only project convention artifacts and approved compatibility pointers.
- Never modify application source during exploration.
- Treat code as evidence, not authority.
- Do not approve a pattern because all sampled files use it.
- Do not duplicate detailed rules across platform-specific files.
- Keep generated profiles concise and source-cited.
