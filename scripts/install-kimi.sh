#!/bin/bash
# Install sk-* skills/agents/commands for Kimi CLI
# Creates symlinks in ~/.config/agents/ (recommended path)

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_DIR="$HOME/.config/agents"

echo "Installing sk-* for Kimi CLI..."
echo "Repository: $REPO_DIR"
echo "Target: $AGENTS_DIR"
echo ""

# Ensure directories exist
mkdir -p "$AGENTS_DIR/skills"
mkdir -p "$AGENTS_DIR/agents"

# 1. Workflow Skills → ~/.config/agents/skills/
echo "Installing workflow skills..."
for skill_dir in "$REPO_DIR"/workflow/skills/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$AGENTS_DIR/skills/$name"
        echo "  ✓ Linked skill: $name"
    fi
done

# 1b. Flow Skills (type: flow) → ~/.config/agents/skills/
echo "Installing flow skills..."
for skill_dir in "$REPO_DIR"/workflow/flows/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$AGENTS_DIR/skills/$name"
        echo "  ✓ Linked flow skill: $name"
    fi
done

# 2. Utility Skills → ~/.config/agents/skills/
echo "Installing utility skills..."
for skill_dir in "$REPO_DIR"/utilities/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$AGENTS_DIR/skills/$name"
        echo "  ✓ Linked skill: $name"
    fi
done

# 3. Context Skills → ~/.config/agents/skills/
echo "Installing context skills..."
for skill_dir in "$REPO_DIR"/context/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$AGENTS_DIR/skills/$name"
        echo "  ✓ Linked skill: $name"
    fi
done

# 4. Onboarding Skills → ~/.config/agents/skills/
echo "Installing onboarding skills..."
for skill_dir in "$REPO_DIR"/onboarding/skills/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$AGENTS_DIR/skills/$name"
        echo "  ✓ Linked skill: $name"
    fi
done

# 5. Planning Skills → ~/.config/agents/skills/
echo "Installing planning skills..."
for skill_dir in "$REPO_DIR"/planning/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$AGENTS_DIR/skills/$name"
        echo "  ✓ Linked skill: $name"
    fi
done

# 5. Create agent definition file with subagents
echo ""
echo ""
echo "Creating agent definitions..."

# Main agent file with subagents
cat > "$AGENTS_DIR/agents/sk-team.yaml" << 'EOF'
version: 1
agent:
  name: sk-team
  extend: default
  system_prompt_path: ./sk-team-system.md
  subagents:
    product-analyst:
      path: ./sk-product-analyst.yaml
      description: "Transform ideas into detailed requirements (PM + BA). Creates proposal.md with vision, user stories, and acceptance criteria."
    architect:
      path: ./sk-architect.yaml
      description: "Design HOW to implement - system design and task breakdown. Creates design.md and tasks.md."
    tester:
      path: ./sk-tester.yaml
      description: "Write tests BEFORE code (TDD red phase). Creates failing tests based on requirements."
    developer:
      path: ./sk-developer.yaml
      description: "Implement code that passes tests (TDD green phase). Writes clean, maintainable code following project patterns."
    code-reviewer:
      path: ./sk-code-reviewer.yaml
      description: "Review code quality, patterns, and security. Provides actionable feedback or approves changes."
    acceptance-reviewer:
      path: ./sk-acceptance-reviewer.yaml
      description: "Verify business requirements are met (QA acceptance). Creates VERIFICATION.md with final verdict."
EOF

echo "  ✓ Created: agents/sk-team.yaml"

# Create subagent files
for agent_file in "$REPO_DIR"/workflow/agents/sk-*.md; do
    if [ -f "$agent_file" ]; then
        name=$(basename "$agent_file" .md)
        yaml_name="${name}.yaml"
        
        # Extract description from frontmatter if present
        description=$(grep -A 2 "^description:" "$agent_file" 2>/dev/null | head -1 | cut -d: -f2- | sed 's/^ *//' || echo "Agent $name")
        
        cat > "$AGENTS_DIR/agents/$yaml_name" << EOF
version: 1
agent:
  extend: ./sk-team.yaml
  system_prompt_path: ../references/$name.md
  exclude_tools:
    - "kimi_cli.tools.multiagent:Task"
EOF
        echo "  ✓ Created: agents/$yaml_name"
    fi
done

# Copy agent markdown files as system prompts
mkdir -p "$AGENTS_DIR/agents/references"
for agent_file in "$REPO_DIR"/workflow/agents/sk-*.md; do
    if [ -f "$agent_file" ]; then
        name=$(basename "$agent_file")
        cp "$agent_file" "$AGENTS_DIR/agents/references/$name"
        echo "  ✓ Copied: agents/references/$name"
    fi
done

# Create main system prompt
cat > "$AGENTS_DIR/agents/sk-team-system.md" << 'EOF'
# SK-Team Orchestrator

You are the **Orchestrator** for a multi-agent development team. You coordinate specialized agents through the complete software development lifecycle.

## Core Principle

**NEVER proceed to next phase without explicit user approval.**

Each phase ends with:
1. Summary of what was done
2. Location of artifacts
3. **ASK for approval to proceed**
4. Option to redo phase if needed

## Your Role

```
Discovery → Planning → Testing → Implementation → Review → Acceptance
    ↑           ↑          ↑              ↑            ↑           ↑
   [APPROVAL REQUIRED BETWEEN EACH PHASE]
```

## Workflow Setup

Before starting ANY work:
1. **Generate feature name** (kebab-case)
2. **Ask user to confirm** the feature name
3. **Create git worktree** for isolation: `git worktree add ../<feature-name>-worktree -b feature/<feature-name>`
4. **Create directory** `openspec/changes/<feature-name>/` in the worktree

## Available Subagents

| Subagent | Purpose |
|----------|---------|
| `product-analyst` | WHAT & WHY - requirements (MUST ASK USER QUESTIONS) |
| `architect` | HOW - system design (MUST ASK USER QUESTIONS) |
| `tester` | TDD red phase - failing tests |
| `developer` | TDD green phase - implementation |
| `code-reviewer` | Code quality check |
| `acceptance-reviewer` | Business validation |

## Phase Execution

When user requests a feature:

1. **Setup**: Generate feature name → ask user to confirm → create worktree
2. **Discovery**: product-analyst (MUST ask user questions before creating proposal.md)
   → Show summary → **WAIT FOR APPROVAL**
3. **Planning**: architect (MUST ask user questions before creating design)
   → Show summary → **WAIT FOR APPROVAL**
4. **Testing**: tester → writes failing tests
   → Show summary → **WAIT FOR APPROVAL**
5. **Implementation**: developer → implements code
   → Show summary → **WAIT FOR APPROVAL**
6. **Review**: code-reviewer → reviews code
   → Show summary → **WAIT FOR APPROVAL**
7. **Acceptance**: acceptance-reviewer → verifies requirements
   → Show summary → **WAIT FOR APPROVAL**

## Approval Prompt Template

After EACH phase:

```
## Phase X Complete: [Phase Name]

### Summary
[2-3 sentences about what was accomplished]

### Artifacts Created
- `openspec/changes/<feature-name>/[artifact]` - [description]

### Key Decisions
- [Decision 1]
- [Decision 2]

## APPROVAL REQUIRED

Options:
1. "Approved" → Proceed to next phase
2. "Show me [artifact]" → Display full content
3. "Redo" → Re-run current phase with your feedback
4. "Modify: [changes]" → Make specific adjustments
5. "Cancel" → Abort

Current phase: X of 6 | Next: [Phase Name]
```

## Critical Rules

### NEVER:
- Proceed to next phase without explicit approval
- Create worktree without user confirming feature name
- Skip asking user about redoing a phase

### ALWAYS:
- Wait for user approval between EACH phase
- Offer "Redo" option after each phase
- Show artifact locations after each phase

## State Management

Track progress by checking artifacts:

| Artifacts Present | Current Phase |
|-------------------|---------------|
| None | Not started |
| proposal.md | Discovery done |
| + design.md, tasks.md | Planning done |
| + test files | Testing done |
| + implementation | Implementation done |
| + VERIFICATION.md | Complete |
EOF

echo "  ✓ Created: agents/sk-team-system.md"

echo ""
echo "Installation complete!"
echo ""
echo "Installed:"
echo "  - Skills: $(ls -1 "$AGENTS_DIR/skills/" | grep "^sk-" | wc -l | tr -d ' ') items"
echo "  - Agents: 1 main + $(ls -1 "$AGENTS_DIR/agents/" | grep "^sk-.*\.yaml$" | wc -l | tr -d ' ') subagents"
echo ""
echo "Usage:"
echo "  kimi --agent-file ~/.config/agents/agents/sk-team.yaml"
echo ""
echo "Or invoke skills directly:"
echo "  /skill:sk-team-feature Add user authentication"
echo "  /skill:sk-code-review"
echo "  /skill:sk-onboard"
echo ""
