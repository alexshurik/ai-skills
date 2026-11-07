---
name: sk-onboard
version: 1.1.0
description: Check, create, or refresh modular project steering, reusing existing guidance and deriving project maps and authoritative convention profiles.
argument-hint: "[optional: check|quick|full]"
license: MIT
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Write
  - Task
  - Skill
---

# Project Onboarding and Steering

Connect project knowledge and approved rules through a small routing index. Reuse
existing documentation and preserve human guidance. A direct setup request
authorizes non-conflicting generation and entrypoint updates; adoption of new
recommendations requires an explicit decision on those items.

## Required reference

Read the relevant mode in `project-steering-guide.md` before acting:

```text
~/.claude/agents/best-practices/project-steering-guide.md
or, from this source repository:
shared/best-practices/project-steering-guide.md
```

Installed adapters rewrite the installed locator for their host. For `check`, read
only the Check section and return; the remaining sections govern setup/refresh.

## Modes

- **`check`:** inspect existing guidance and report readiness plus a concrete
  setup/refresh offer. No writes, delegation, or full discovery. Safe for first-use
  callers and read-only reviews; missing steering never blocks their task.
- **`quick`:** create or refresh useful routing, high-level project context,
  navigation, and project profiles. Skip detailed endpoint/schema extraction.
- **`full` (default):** also perform detailed domain and API discovery. Detailed maps
  are reference material, not instructions to load on every task.

Re-running quick/full refreshes only affected artifacts. An existing steering
layout is supported; no migration is required to use this skill.

## Setup and refresh

### 1. Inspect and plan

Apply the shared Check contract, then resolve destinations before discovery. Show
a compact plan of existing owners to reuse, missing modules to create, and the
entrypoint block to add/update. If invoked after an accepted first-use offer,
inherit its decisions instead of asking again. Respect explicit module/component
scope and surface only unresolved material choices.

Use `.agents/steering/index.md` for a new routing owner. Existing README/ADRs and
native steering files can remain authoritative. Preserve existing map/navigation
paths; new defaults are `.agents/docs/project-map.md` and
`.agents/steering/architecture.md`. Project convention profiles remain in
`.agents/best-practices/project/`, including existing component-specific profiles.
Resolve permanent ADR ownership/navigation with §6 of
`~/.claude/agents/shared/scope-governance.md` (source:
`workflow/agents/shared/scope-governance.md`). Reuse and link the decision index;
onboarding alone does not require a new ADR or relocation of legacy records.

### 2. Reuse verified discovery

Compute a reusable **project fingerprint** from the selected mode/components,
resolved destinations, skill/reference content, and consumed repository inputs:
manifests, tooling, guidance, and source paths/content hashes including dirty files.
Record repository revision for provenance, but do not invalidate every module
merely because HEAD moved. Record the discovered directory inventory too, so new
or deleted relevant source files invalidate the appropriate discovery subset.

Use the Git-local `sk-workflow/onboarding/` ledger for input and output hashes.
Track input subsets per discovery artifact. Exclude generated outputs from their
own source fingerprints; track manual guidance within them separately. When input
and required output hashes match, reuse the artifact. A mode upgrade must satisfy
the new coverage before reuse. A changed output requires inspection/merge to
preserve edits. Never reuse merely because a file exists. Without Git metadata,
verify in the session without creating tracked runtime files.

### 3. Discover only missing or invalidated coverage

Run `sk-discover-project` for the project map, and `sk-explore-codebase` for
navigation and convention profiles. Pass the mode, component scope, resolved
output paths, existing owners, and merge decisions explicitly. Share common facts
and prior verified evidence rather than exploring the repository twice. The
discovery skills retain their bounded explorer and foreground-join contracts.

For a thin or empty project, generate only supported facts and approved/tooling
rules. Ask only for information needed for the requested setup; record other gaps
without inventing purpose, terminology, architecture, or a test command.

### 4. Assemble modular steering

Apply the shared Derive and merge contract. Index existing documents wherever they
cover the concern. Add a brief project overview or testing module only when useful
information lacks an owner; do not duplicate the detailed map or command sources.
Keep architecture navigation separate from role-specific coder/reviewer rules and
non-normative evidence. Include task/role triggers and component/path scope in each
index row, so an implementation task does not load every review rule or API map.

Use relevant bundled best-practice profiles to propose missing decisions. Keep
unaccepted recommendations out of normative modules. Present only concrete items
requiring a decision, with their source and scope; preserve already approved rules.

### 5. Connect and verify

Apply the shared Connect the entrypoint and Validate contracts. Add a short managed
pointer to the resolved index without rewriting unrelated `AGENTS.md` or native
guidance. For generated entrypoints, update their maintained source. Verify links,
selective loading, preserved edits, authority classifications, and repeat-run
stability. Record successful input/output hashes after writing the final artifacts.

Report detected stack/components, reused/created/merged paths, the entrypoint and
loading rules, verification performed, and unresolved decisions or connections.
Do not claim that creating files alone makes them load automatically.
