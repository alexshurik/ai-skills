# OpenAI Codex Adapter

## Installation

Run the installation script:

```bash
./scripts/install-codex.sh
```

By default, this installs skills to the current user-level Codex location,
`~/.agents/skills/`. Previous versions of this repository may have left copies
under `~/.codex/skills/`; the installation doctor reports those before an explicit
recoverable migration.

The installer validates and verifies the current target, then runs the installation
doctor. If legacy duplicates remain, inspect the report and migrate only this
repository's entries:

```bash
./scripts/migrate-legacy-codex.sh
```

The migration preserves `~/.codex/skills/.system` and unrelated skills. Its
backup path must not already exist and must be on the same filesystem as the
legacy tree; failures roll completed moves back without a copy fallback.

All platforms use the same artifact/scope contract: durable decisions live in
`openspec/changes/<name>/`, runtime counters and full review evidence live under
`$(git rev-parse --git-path sk-workflow)/<name>/`, and optional scope is triaged in
`DEFERRED.md`. See the root README's **Artifacts** and **Scope Governance** sections.

To use a different location:
```bash
CODEX_SKILLS_DIR=/custom/path ./scripts/install-codex.sh
```

## Usage

After installation, use the skills in Codex:

```
$sk-team-help       # Show documentation
$sk-team-feature    # Start full feature workflow
$sk-team-quick      # Quick fix workflow
$sk-onboard         # Project onboarding
```

## Skill Format

Codex skills require `name` and `description` in `SKILL.md`:

```yaml
---
name: sk-team-feature
description: Run the full workflow for new features
---

# Instructions...
```

Optional UI metadata, invocation policy, and tool dependencies belong in
`agents/openai.yaml`. Claude-specific `allowed-tools` frontmatter is not a Codex
permission boundary.

## Catalog vs. internal resources

Only **user-invocable** skills (the `sk-team-*`, `sk-onboard`, `sk-code-review`, … )
are installed as catalog entries that Codex surfaces for routing. The workflow
**agents** (`sk-product-analyst`, `sk-developer`, …), review sub-passes, shared docs,
and best-practice profiles are copied as internal **resource files** (under
`agents/`, `review-steps/`, `shared/`, `best-practices/` — no `SKILL.md`), so they do
**not** clutter the skill catalog. The orchestrator skills reference them by path.

## Agent Usage

Agents are internal sub-roles the workflow skills drive; you normally start a workflow
skill rather than invoking an agent directly:

```
Use the sk-product-analyst agent to gather requirements.
```

## Updating

Codex uses manifest-rendered copied directories, including skill references,
scripts, and UI metadata. To update:

```bash
cd /path/to/skills
git pull
./scripts/install-codex.sh
```

Verify or diagnose:

```bash
./scripts/validate-skills.sh
./scripts/doctor-installation.sh
./scripts/verify-installation.sh codex ~/.agents/skills
```

## Compatibility Notes

- Invoke a skill explicitly with `$skill-name` or choose it through `/skills`
- Codex may also select a skill implicitly from its `description`
- `sk-copy-context` detects `pbcopy`, `wl-copy`, `xclip`, or PowerShell and
  reports an error when none is available

## See Also

- [OpenAI Codex skill documentation](https://developers.openai.com/codex/skills/)
