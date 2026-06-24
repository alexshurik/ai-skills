#!/bin/bash
# Install sk-* skills for OpenAI Codex
# Copies SKILL.md files to Codex skills folder

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Codex discovers user-level skills in $HOME/.agents/skills (the agent-agnostic open
# standard, shared with other agents). The old ~/.codex/skills location is not scanned
# per current Codex docs. Override with CODEX_SKILLS_DIR if needed.
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"

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

# 5. Copy review steps
echo "Installing review steps..."
if [ -d "$REPO_DIR/workflow/agents/review-steps" ]; then
    mkdir -p "$CODEX_DIR/review-steps"
    for step in "$REPO_DIR"/workflow/agents/review-steps/*.md; do
        if [ -f "$step" ]; then
            name=$(basename "$step")
            cp "$step" "$CODEX_DIR/review-steps/$name"
            echo "  ✓ Copied review step: $name"
        fi
    done
fi

# 5b. Copy shared agent docs (handoff/clarification protocol)
echo "Installing shared agent docs..."
if [ -d "$REPO_DIR/workflow/agents/shared" ]; then
    mkdir -p "$CODEX_DIR/shared"
    for doc in "$REPO_DIR"/workflow/agents/shared/*.md; do
        if [ -f "$doc" ]; then
            name=$(basename "$doc")
            cp "$doc" "$CODEX_DIR/shared/$name"
            echo "  ✓ Copied shared doc: $name"
        fi
    done
fi

# 6. Copy best-practice profiles
echo "Installing best-practice profiles..."
if [ -d "$REPO_DIR/shared/best-practices" ]; then
    cp -R "$REPO_DIR/shared/best-practices" "$CODEX_DIR/best-practices"
    echo "  ✓ Copied: best-practices/"

    # Agents reference the Claude-Code path ~/.claude/agents/best-practices.
    # Rewrite it to the Codex install location so the resolver resolves here.
    echo "Rewriting best-practices paths for Codex..."
    for skill in "$CODEX_DIR"/*/SKILL.md; do
        [ -f "$skill" ] || continue
        sed -i.bak "s|~/.claude/agents/best-practices|$CODEX_DIR/best-practices|g" "$skill"
        rm -f "$skill.bak"
    done
fi

# 7. Copy commands as skills
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
