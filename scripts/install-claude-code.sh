#!/bin/bash
# Install sk-* skills/agents/commands for Claude Code
# Creates symlinks in ~/.claude/

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Installing sk-* for Claude Code..."
echo "Repository: $REPO_DIR"
echo "Target: $CLAUDE_DIR"
echo ""

# Ensure directories exist
mkdir -p "$CLAUDE_DIR/skills"
mkdir -p "$CLAUDE_DIR/agents"
mkdir -p "$CLAUDE_DIR/commands"

# 1. Workflow Skills → ~/.claude/skills/
echo "Installing workflow skills..."
for skill_dir in "$REPO_DIR"/workflow/skills/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$CLAUDE_DIR/skills/$name"
        echo "  ✓ Linked skill: $name"
    fi
done

# 2. Utility Skills → ~/.claude/skills/
echo "Installing utility skills..."
for skill_dir in "$REPO_DIR"/utilities/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$CLAUDE_DIR/skills/$name"
        echo "  ✓ Linked skill: $name"
    fi
done

# 3. Context Skills → ~/.claude/skills/
echo "Installing context skills..."
for skill_dir in "$REPO_DIR"/context/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$CLAUDE_DIR/skills/$name"
        echo "  ✓ Linked skill: $name"
    fi
done

# 4. Planning Skills → ~/.claude/skills/
echo "Installing planning skills..."
for skill_dir in "$REPO_DIR"/planning/sk-*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        ln -sfn "$skill_dir" "$CLAUDE_DIR/skills/$name"
        echo "  ✓ Linked skill: $name"
    fi
done

# 5. Agents → ~/.claude/agents/
echo "Installing agents..."
for agent in "$REPO_DIR"/workflow/agents/*.md; do
    if [ -f "$agent" ]; then
        name=$(basename "$agent")
        ln -sfn "$agent" "$CLAUDE_DIR/agents/$name"
        echo "  ✓ Linked agent: $name"
    fi
done

# 6. Review Steps → ~/.claude/agents/review-steps/
echo "Installing review steps..."
if [ -d "$REPO_DIR/workflow/agents/review-steps" ]; then
    ln -sfn "$REPO_DIR/workflow/agents/review-steps" "$CLAUDE_DIR/agents/review-steps"
    echo "  ✓ Linked: agents/review-steps/"
fi

# 6b. Shared agent docs (handoff/clarification protocol) → ~/.claude/agents/shared/
echo "Installing shared agent docs..."
if [ -d "$REPO_DIR/workflow/agents/shared" ]; then
    ln -sfn "$REPO_DIR/workflow/agents/shared" "$CLAUDE_DIR/agents/shared"
    echo "  ✓ Linked: agents/shared/"
fi

# 7. Best-practice profiles → ~/.claude/agents/best-practices/
echo "Installing best-practice profiles..."
ln -sfn "$REPO_DIR/shared/best-practices" "$CLAUDE_DIR/agents/best-practices"
echo "  ✓ Linked: agents/best-practices/"

# 8. Commands → ~/.claude/commands/
echo "Installing commands..."
for cmd in "$REPO_DIR"/onboarding/*.md; do
    if [ -f "$cmd" ]; then
        name=$(basename "$cmd")
        ln -sfn "$cmd" "$CLAUDE_DIR/commands/$name"
        echo "  ✓ Linked command: $name"
    fi
done

echo ""
echo "Installation complete!"
echo ""
echo "Installed:"
echo "  - Skills: $(ls -1 "$CLAUDE_DIR/skills/" | grep "^sk-" | wc -l | tr -d ' ') items"
echo "  - Agents: $(ls -1 "$CLAUDE_DIR/agents/" | grep "^sk-" | wc -l | tr -d ' ') items"
echo "  - Commands: $(ls -1 "$CLAUDE_DIR/commands/" | grep "^sk-" | wc -l | tr -d ' ') items"
echo ""
echo "Restart Claude Code to use new skills."
echo ""
echo "Quick start:"
echo "  /sk-team-help     - Show team workflow documentation"
echo "  /sk-onboard       - Onboard to a new project"
echo "  /sk-code-review   - Review uncommitted changes"
