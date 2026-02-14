# Implementation Tasks: Add Flow Skill Support

## Task Breakdown

### Phase 1: Foundation

#### Task 1.1: Create workflow/flows/ directory structure
- **Files**: Create `workflow/flows/` directory
- **Details**: Set up directory for flow skills, mirroring `workflow/skills/` pattern
- **Verify**: `ls workflow/flows/` shows directory exists

#### Task 1.2: Create sk-team-feature-flow skill
- **Files**: `workflow/flows/sk-team-feature-flow/SKILL.md`
- **Details**:
  - Add YAML frontmatter with `type: flow`
  - Create Mermaid diagram for 6-phase workflow
  - Document each phase (SETUP, ANALYST, ARCHITECT, TESTER, DEVELOPER, REVIEWER, ACCEPTANCE)
  - Include usage examples and comparison table
- **Verify**: File exists and has valid frontmatter

#### Task 1.3: Create sk-team-quick-flow skill
- **Files**: `workflow/flows/sk-team-quick-flow/SKILL.md`
- **Details**:
  - Add YAML frontmatter with `type: flow`
  - Create Mermaid diagram for 2-phase workflow (CHECK → DEVELOPER → REVIEWER)
  - Include complexity check and escalation path
  - Document usage examples
- **Verify**: File exists and has valid frontmatter

### Phase 2: Integration

#### Task 2.1: Update install-kimi.sh for flow skills
- **Files**: `scripts/install-kimi.sh`
- **Details**:
  - Add loop to install flow skills from `workflow/flows/`
  - Display "✓ Linked flow skill: name" message
  - Update summary count to include flow skills
- **Verify**: Run script and see flow skills installed

#### Task 2.2: Update adapters/kimi/README.md
- **Files**: `adapters/kimi/README.md`
- **Details**:
  - Add "Option 3: Flow Skills" section
  - Explain `/flow:` vs `/skill:` difference
  - Add flow skills to available skills table
  - Fix option numbering (4 for project-level)
- **Verify**: README renders correctly with all sections

### Phase 3: Testing

#### Task 3.1: Test installation
- **Command**: `./scripts/install-kimi.sh`
- **Verify**: 
  - Flow skills appear in `~/.config/agents/skills/`
  - Count shows 14+ skills

#### Task 3.2: Test flow skill content
- **Command**: `cat workflow/flows/sk-team-feature-flow/SKILL.md`
- **Verify**:
  - Valid YAML frontmatter
  - Mermaid diagram present
  - All phases documented

#### Task 3.3: Test quick flow skill
- **Command**: `cat workflow/flows/sk-team-quick-flow/SKILL.md`
- **Verify**:
  - Valid YAML frontmatter
  - Complexity check described
  - Escalation path documented

## Dependencies

- Task 1.2 depends on Task 1.1 (needs directory)
- Task 1.3 depends on Task 1.1 (needs directory)
- Task 2.1 can run after Task 1.2 and 1.3 complete
- Task 2.2 can run in parallel with Task 2.1
- Task 3.x depend on all implementation tasks

## Testing Tasks

- [ ] Manual verification of flow skill format
- [ ] Installation script executes without errors
- [ ] Flow skills appear in skills listing
- [ ] Documentation is clear and complete
