# Feature Summary: Add Flow Skill Support

## Overview

Implemented automated workflow execution through "flow skills" — a new skill type that executes multi-phase agent workflows without manual orchestration. This enables hands-off feature development where the system automatically coordinates Product Analyst → Architect → Tester → Developer → Code Reviewer → Acceptance Reviewer.

## Key Decisions

- **Separate directory for flows**: Created `workflow/flows/` instead of mixing with standard skills in `workflow/skills/`. This provides clear separation of concerns.
- **Same skill format**: Flow skills use identical `SKILL.md` structure with just `type: flow` added to frontmatter, ensuring compatibility across tools.
- **Extended deliverables**: Added SUMMARY.md, API_CHANGELOG.md, and OPERATIONAL_TASKS.md generation to acceptance-reviewer for comprehensive handoff.
- **No new agent needed**: Reused existing agent team, just automated the orchestration via Mermaid diagrams.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `workflow/flows/sk-team-feature-flow/SKILL.md` | New | Full 6-phase automated workflow |
| `workflow/flows/sk-team-quick-flow/SKILL.md` | New | Streamlined 2-phase quick fix workflow |
| `workflow/agents/sk-acceptance-reviewer.md` | Modified | Added deliverables generation section |
| `scripts/install-kimi.sh` | Modified | Added flow skills installation loop |
| `adapters/kimi/README.md` | Modified | Added flow skills documentation |

## Testing

- Unit tests: N/A (documentation/skill framework)
- Integration tests: 
  - ✅ Installation script executes without errors
  - ✅ Flow skills properly linked to `~/.config/agents/skills/`
  - ✅ Skills accessible via `/flow:` command

## Deployment Notes

No special deployment requirements. Changes are immediately available after:
```bash
./scripts/install-kimi.sh
```

## Impact

- **Developers**: Can now run `/flow:sk-team-feature-flow "Add auth"` for hands-off development
- **Frontend Teams**: Will receive API_CHANGELOG.md with every backend feature
- **DevOps/Managers**: Will receive OPERATIONAL_TASKS.md with setup instructions
- **Tech Leads**: Can review SUMMARY.md for quick feature understanding
