# Modular Project Steering

Use this contract for `sk-onboard` and its lightweight first-use check. Steering
records project facts and approved decisions; skill execution procedures remain in
the installed skills. Keep detailed rules in their existing authoritative owners.

## Check — inspect without changing the project

Read the applicable repository guidance (`AGENTS.md`, `CLAUDE.md`, native rule
files, and their referenced documents), existing steering indexes, project
profiles, and manifests for the active components. Look for established locations
such as `.agents/steering/`, `.kiro/steering/`, `.claude/rules/`, `.cursor/rules/`,
and repository-defined equivalents. Respect nested/path-scoped guidance. Do not
read every module or sample the whole codebase just to check readiness.

Report the existing entrypoint, useful missing coverage, and one of:

- **Ready:** guidance routes agents to the relevant existing documents.
- **Missing:** no usable project guidance was found.
- **Partial:** guidance exists, but useful routing or applicable modules are missing.
- **Stale:** a recorded source/output hash changed or a referenced path is broken.

A custom structure can be Ready without any `.agents/steering/` directory. The
absence of an optional module or a freshness receipt is not itself a defect;
report freshness as unknown when it has not been verified. Do not declare existing
human guidance obsolete merely because our templates differ.

`check` writes no files, starts no explorers, and never invokes setup. Return a
concrete offer when useful: existing documents to reuse, proposed destinations,
and missing topics to investigate. Do not draft unsupported rules in the offer.

### First-use callers

Run the check once per repository/workspace in the root session, before modifying
source or capturing review evidence. Pass its result through nested workflows so
they do not repeat the offer. If the workspace or relevant guidance changes,
revalidate affected paths before reuse without repeating an already answered offer.
Missing steering does not block the original task.
Offer setup/refresh once; only an explicit onboarding request or acceptance starts
the write workflow. Silence, a development charter, and YOLO are not acceptance of
additional project setup. A read-only review only reports the offer and continues.

If the user declines, remember that in the session. Where Git-local metadata
writes are allowed, the caller may persist `offer: declined` in
`$(git rev-parse --git-path sk-workflow)/onboarding/preferences.json`; read this
preference before future offers. Do not create a tracked preference file. An
explicit `sk-onboard` request overrides the suppressed offer. Without writable
Git metadata, session memory is sufficient.

## Plan destinations before discovery

Prefer explicit user destinations, then the project's existing document owners,
then the defaults below. Retain an existing `.claude/docs/project-map.md` or
`.claude/rules/codebase-navigation.md` owner unless migration was requested. Pass
the resolved output paths and reuse/merge decisions to both discovery skills.
Create only modules with useful sourced content; do not scaffold empty topics.

| Concern | Default for a new owner | Read when |
|---------|-------------------------|-----------|
| Routing | `.agents/steering/index.md` | Starting work; select applicable rows |
| Project overview, vocabulary, constraints | Existing README/docs; optionally `.agents/steering/project.md` | Domain context is needed |
| Detailed discovery map | `.agents/docs/project-map.md` | Looking up components, APIs, or integrations |
| Navigation and boundary owners | `.agents/steering/architecture.md` | Locating code, adding modules, changing dependencies |
| Test setup and command sources | Existing contributor docs; optionally `.agents/steering/testing.md` | Choosing or running checks |
| Implementation and review rules | `.agents/best-practices/project/{coder,reviewer}.md` | Implementing or reviewing within their scope |
| Observations and unresolved proposals | `.agents/best-practices/project/evidence.md` | Investigating a convention; never as normative rules |

Keep the index short. Each row names a repository-relative document, its purpose,
task/role trigger, and path/component scope. Paths in the table are relative to the
repository root; Markdown links must resolve relative to the containing file.
For monorepos route only to relevant components, including cross-component owners
when the task spans them. Do not add an instruction to read the whole directory.

## Derive and merge

Use `project-conventions-guide.md` and `convention-evidence-model.md` for rule
authority. Cite repository sources for project facts; mark inferences as such.
Unknown purpose, terminology, or constraints remain unknown. Existing source
patterns are observations, not approved architectural decisions.

Resolve relevant bundled profiles through `index.yaml` and `resolver.md`. Use them
to identify useful gaps and propose applicable recommendations. A bundled rule
does not become an Approved project rule just because the skill contains it.
Present individual proposed adoptions with source, scope, and effect; promote only
explicitly selected items, preserving the decision and provenance in the project.
Do not copy the entire profile library or put machine-specific installation paths
in project steering. Keep normative coder/reviewer IDs aligned.

Reuse existing README, ADR, testing, and convention documents by reference. Add
missing guidance without duplicating their rule text or command inventories.
Preserve human edits and stable IDs. A changed generated-output hash is a reason to
inspect and merge, not overwrite. For a material conflict, prepare the conflicting
alternatives and ask for that decision; continue independent non-conflicting work.
An explicit onboarding request authorizes non-conflicting setup and pointer
updates; do not ask again for that work or implicitly approve new recommendations.

## Connect the entrypoint

Add or update one small, marked block in the applicable repository entrypoint.
For a new host-neutral setup, use `AGENTS.md` and this shape with resolved paths:

```markdown
<!-- sk-onboard:steering:start -->
Read `.agents/steering/index.md` before working in this project.
Load only the documents whose task, role, and path scope apply to the current work.
<!-- sk-onboard:steering:end -->
```

Preserve unrelated text. Reuse an equivalent existing pointer; never add a duplicate
block. Inspect edits inside a managed block before merging them. If the entrypoint
is generated, update its maintained source/template and regenerate through the
project command. If that owner is unknown, report the unresolved connection.
Add a short pointer in an existing native host entrypoint when that host needs it;
create one only for the requested host. Do not create full parallel rule sets or
claim that arbitrary Markdown links automatically load their targets.

## Validate the result

Verify local links and routing targets exist, role/path triggers select only the
needed documents, manual guidance survives, and no Observed/Legacy item became a
normative rule. Check that a second run with unchanged inputs adds no modules,
duplicate pointers, or new approval requests. Report unresolved connections and
conflicts separately from completed work; do not claim full setup if either blocks
the requested routing. Do not persist task-specific commit/deploy permissions.
