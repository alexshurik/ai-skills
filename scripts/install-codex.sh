#!/bin/bash
# Install sk-* skills for OpenAI Codex
# Copies SKILL.md files to Codex skills folder

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"

echo "Installing sk-* for OpenAI Codex..."
echo "Repository: $REPO_DIR"
echo "Target: $CODEX_DIR"
echo ""

# Ensure directory exists
mkdir -p "$CODEX_DIR"

# Function to copy skill
copy_skill() {
    local skill_dir="$1"
    local name=$(basename "$skill_dir")

    if [ -f "$skill_dir/SKILL.md" ]; then
        mkdir -p "$CODEX_DIR/$name"
        cp "$skill_dir/SKILL.md" "$CODEX_DIR/$name/SKILL.md"
        echo "  ✓ Copied: $name"
    fi
}

# 1. Workflow Skills
echo "Installing workflow skills..."
for skill_dir in "$REPO_DIR"/workflow/skills/sk-*/; do
    [ -d "$skill_dir" ] && copy_skill "$skill_dir"
done

# 2. Utility Skills
echo "Installing utility skills..."
for skill_dir in "$REPO_DIR"/utilities/sk-*/; do
    [ -d "$skill_dir" ] && copy_skill "$skill_dir"
done

# 3. Context Skills
echo "Installing context skills..."
for skill_dir in "$REPO_DIR"/context/sk-*/; do
    [ -d "$skill_dir" ] && copy_skill "$skill_dir"
done

# 4. Planning Skills
echo "Installing planning skills..."
for skill_dir in "$REPO_DIR"/planning/sk-*/; do
    [ -d "$skill_dir" ] && copy_skill "$skill_dir"
done

# 4. Copy agents as skills (Codex format)
echo "Installing agents as skills..."
for agent in "$REPO_DIR"/workflow/agents/*.md; do
    if [ -f "$agent" ]; then
        name=$(basename "$agent" .md)
        mkdir -p "$CODEX_DIR/$name"
        cp "$agent" "$CODEX_DIR/$name/SKILL.md"
        echo "  ✓ Copied agent: $name"
    fi
done

# 5. Copy commands as skills
echo "Installing commands as skills..."
for cmd in "$REPO_DIR"/onboarding/*.md; do
    if [ -f "$cmd" ]; then
        name=$(basename "$cmd" .md)
        mkdir -p "$CODEX_DIR/$name"
        cp "$cmd" "$CODEX_DIR/$name/SKILL.md"
        echo "  ✓ Copied command: $name"
    fi
done

echo ""
echo "Installation complete!"
echo "Total skills: $(ls -1 "$CODEX_DIR" | wc -l | tr -d ' ')"
echo ""
echo "Note: You may need to restart Codex to load new skills."
