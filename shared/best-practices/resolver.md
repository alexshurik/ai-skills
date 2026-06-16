<resolve_best_practice_profiles>
## Best-Practice Profile Resolution

Load stack-specific best-practice profiles for the target repository.
Profiles contain rules you MUST follow. This block has two variants —
use the one matching your role.

### Path resolution

The canonical absolute path after installation is
`~/.claude/agents/best-practices/`. When running directly from the skills
repo, use `shared/best-practices/`. Always try the absolute installed path
first; fall back to the repo path only if Read fails. Every reference to
`best-practices/<file>` below means: try `~/.claude/agents/best-practices/<file>`,
then `shared/best-practices/<file>`.

### Step 1: Read the index

Read `best-practices/index.yaml`. This file lists detection signals and maps
them to profile paths.

**Floor behaviour:** if `index.yaml` cannot be read (missing/unparseable),
do NOT abort — fall back to loading `default/{coder|reviewer}.md` only and
report "index unavailable, default profile only". If even `default/` is
missing, proceed with no profile and say so explicitly. The workflow never
stops because a profile file is absent.

### Step 2: Detect stack

Inspect the TARGET repository for detection signals. The index defines
these signal types:

- **`file:`** — the named file exists in the detection root
- **`grep:`** — the pattern matches in the listed manifest files
- **`directory:`** — the named directory exists in the detection root
- **`glob:`** — at least one file matching the glob exists in the detection root (e.g. `*.tf`)

**Detection root.** For a single-project repo, the detection root is the repo
root. For a monorepo (see Step 3), run detection **inside each active
component's directory** — manifests like `package.json`, `go.mod`, `main.tf`
live in the component subdirectory, not the repo root, so root-only detection
under-detects monorepos. Detect per component, then resolve per component.

Check categories in this order:

1. **Frameworks** — for each framework entry, check its signals.
2. **Languages** — for each language entry, check its signals.
3. **Tooling** — for each tooling entry, check its signals.

Any signal match triggers the profile. Record every match.
A repo can match multiple stacks (e.g., python + fastapi + ansible).

When multiple profiles match at the same precedence level, load them in
this fixed order so later-loaded files override earlier ones on conflict:

- **Languages:** `js` → `typescript` (TS extends JS — TS rules supersede
  JS rules on shared topics like type safety).
- **Frameworks/tooling:** alphabetical by name. Frameworks targeting the
  same language are independent — conflicts between them are bugs in
  the profiles, not the resolver's concern.

### Step 3: Check for project overrides

In the TARGET repository, look for project-level profiles:

- `.agents/best-practices/project/` — canonical location
- For monorepos, also check `.agents/best-practices/projects/<component>/`

**Monorepo component identification:** if the repo has multiple
independently-deployable packages (e.g., `packages/`, `apps/`,
`services/`), identify the active component(s) from changed files. Use a
robust diff base — `HEAD~1` does not exist on first commit or shallow
clones:

```bash
git diff --name-only "$(git merge-base HEAD origin/main 2>/dev/null \
  || git merge-base HEAD main 2>/dev/null \
  || echo HEAD~1)"...HEAD 2>/dev/null \
  | cut -d/ -f1-2 | sort -u
```

Each line of output (e.g. `packages/api`, `services/web`) is one
**component path**. The `<component>` token used for the project-override
path is this full relative path. So for changed files under `packages/api`,
the override location is `.agents/best-practices/projects/packages/api/`,
and you re-run Step 2 detection with `packages/api` as the detection root
(so `packages/api/go.mod` → go profile, `services/web/package.json` → js).

If changes span multiple components, detect and resolve each independently,
then load profiles for each and report all matches per component.

Also read platform-native guidance files if present:
`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`

### Step 4: Assemble profile chain

Build the chain by precedence (highest first):

| Precedence | Source | Location |
|------------|--------|----------|
| 1. Project | Target repo | `.agents/best-practices/project/` |
| 2. Tooling | Skills repo | `best-practices/tooling/<name>/` |
| 3. Framework | Skills repo | `best-practices/frameworks/<name>/` |
| 4. Language | Skills repo | `best-practices/languages/<name>/` |
| 5. Default | Skills repo | `best-practices/default/` |

Load the role-appropriate file from each level that exists (see variants below).

Tooling sits above framework because tools like Terraform or Ansible
define infrastructure-level rules that override application-framework
guidance when both are present (rare but possible — e.g., a Vue app
deployed via Terraform-managed infra).

### Load order

Read profiles bottom-up: default first, then language, then framework,
then tooling, then project. When a higher-precedence profile addresses
the same topic, follow the higher-level guidance. Later-loaded content
naturally overrides earlier, so loading in ascending precedence order
ensures correct behavior.

When passing profile content to subagents, concatenate in this order:
1. `default/{coder|reviewer}.md`
2. `languages/<lang>/{coder|reviewer}.md` (multiple profiles use the
   same-level order from Step 2)
3. `frameworks/<fw>/{coder|reviewer}.md`
4. `tooling/<tool>/{coder|reviewer}.md`
5. `.agents/best-practices/project/{coder|reviewer}.md`

### Step 5: Report resolution

State exactly which profiles were loaded. Examples:

- "Loaded: project, fastapi, python, default"
- "Fallback: no project-level profile found, using framework as highest
  precedence"

If NO profiles match at all, report that explicitly and load default only.
Fallback MUST NOT be silent — always state which levels were skipped.

---

### Variants

<coder_variant>
**For developer/implementation agents.**
At each level in Step 4, load `coder.md`.
Apply all loaded coder rules when writing or modifying code.
</coder_variant>

<reviewer_variant>
**For code review agents.**
At each level in Step 4, load `reviewer.md`.
Apply all loaded reviewer rules when evaluating code changes.
</reviewer_variant>

</resolve_best_practice_profiles>
