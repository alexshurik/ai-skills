# Cursor Adapter

Current Cursor releases support Agent Skills and Project Rules. Use native skills
for the workflows; the generated rule is an optional always-on catalog.

## Native Skill Installation

Install into a target project's `.cursor/skills` directory:

```bash
CURSOR_SKILLS_DIR=/path/to/project/.cursor/skills \
  ./scripts/install-cursor.sh
```

Cursor discovers each manifest-owned `SKILL.md` and exposes it through its slash
menu. Skills may also activate automatically from their descriptions.

Verify or uninstall that explicit project target:

```bash
./scripts/verify-installation.sh \
  cursor /path/to/project/.cursor/skills
python3 scripts/skills_tool.py uninstall \
  --target cursor /path/to/project/.cursor/skills
```

## Optional Project Rule

Generate an always-on catalog under `.cursor/rules/`:

```bash
./scripts/generate-cursor-rules.sh
cp -R adapters/cursor/.cursor /path/to/project/
```

The rule lists every manifest-owned public skill and internal role. Edit the copy
in the target project if it needs project-specific context.

## Legacy Compatibility

`.cursorrules` is still generated for older Cursor versions, but Cursor classifies
that root-level format as legacy:

```bash
./scripts/generate-cursorrules.sh
cp adapters/cursor/.cursorrules /path/to/project/
```

Prefer native skills plus `.cursor/rules` or `AGENTS.md` for new installations.

## Invocation

Open Cursor's slash menu and select a skill such as:

```text
/sk-team-help
/sk-team-feature
/sk-team-quick
/sk-onboard
```

## See Also

- [Cursor 2.4: Subagents, Skills, and Image Generation](https://cursor.com/changelog/2-4)
- [Cursor Project Rules](https://docs.cursor.com/context/rules)
