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

# Only USER-INVOCABLE skills become catalog entries (a dir with SKILL.md). Internal
# pieces — agents, review sub-passes, shared docs, best-practice profiles — are copied
# as plain resource files WITHOUT a SKILL.md so Codex does not surface them in the skill
# catalog (which would pollute routing). The orchestrators reference them by path.
SKILL_COUNT=0

# Function to copy a user-invocable skill into the catalog
copy_skill() {
    local skill_dir="$1"
    local name=$(basename "$skill_dir")

    if [ -f "$skill_dir/SKILL.md" ]; then
        mkdir -p "$CODEX_DIR/$name"
        cp "$skill_dir/SKILL.md" "$CODEX_DIR/$name/SKILL.md"
        echo "  ✓ Copied skill: $name"
        SKILL_COUNT=$((SKILL_COUNT + 1))
    fi
}

# 1. Workflow Skills (user-invocable)
echo "Installing workflow skills..."
for skill_dir in "$REPO_DIR"/workflow/skills/sk-*/; do
    [ -d "$skill_dir" ] && copy_skill "$skill_dir"
done

# 2. Utility Skills (user-invocable)
echo "Installing utility skills..."
for skill_dir in "$REPO_DIR"/utilities/sk-*/; do
    [ -d "$skill_dir" ] && copy_skill "$skill_dir"
done

# 3. Context Skills (user-invocable)
echo "Installing context skills..."
for skill_dir in "$REPO_DIR"/context/sk-*/; do
    [ -d "$skill_dir" ] && copy_skill "$skill_dir"
done

# 4. Planning Skills (user-invocable)
echo "Installing planning skills..."
for skill_dir in "$REPO_DIR"/planning/sk-*/; do
    [ -d "$skill_dir" ] && copy_skill "$skill_dir"
done

# 5. Onboarding commands (user-invocable)
echo "Installing onboarding commands..."
for cmd in "$REPO_DIR"/onboarding/*.md; do
    if [ -f "$cmd" ]; then
        name=$(basename "$cmd" .md)
        mkdir -p "$CODEX_DIR/$name"
        cp "$cmd" "$CODEX_DIR/$name/SKILL.md"
        echo "  ✓ Copied command: $name"
        SKILL_COUNT=$((SKILL_COUNT + 1))
    fi
done

# --- Internal resources (NOT catalog skills: no SKILL.md) ---

# 6. Agents → agents/ (internal sub-roles invoked by the orchestrators, not skills)
echo "Installing agents (internal resources)..."
mkdir -p "$CODEX_DIR/agents"
for agent in "$REPO_DIR"/workflow/agents/*.md; do
    if [ -f "$agent" ]; then
        cp "$agent" "$CODEX_DIR/agents/$(basename "$agent")"
        echo "  ✓ Copied agent: $(basename "$agent")"
    fi
done

# 7. Review sub-passes → review-steps/
echo "Installing review steps..."
if [ -d "$REPO_DIR/workflow/agents/review-steps" ]; then
    mkdir -p "$CODEX_DIR/review-steps"
    for step in "$REPO_DIR"/workflow/agents/review-steps/*.md; do
        [ -f "$step" ] && cp "$step" "$CODEX_DIR/review-steps/$(basename "$step")"
    done
    echo "  ✓ Copied: review-steps/"
fi

# 8. Shared agent docs (handoff/clarification protocol) → shared/
echo "Installing shared agent docs..."
if [ -d "$REPO_DIR/workflow/agents/shared" ]; then
    mkdir -p "$CODEX_DIR/shared"
    for doc in "$REPO_DIR"/workflow/agents/shared/*.md; do
        [ -f "$doc" ] && cp "$doc" "$CODEX_DIR/shared/$(basename "$doc")"
    done
    echo "  ✓ Copied: shared/"
fi

# 9. Best-practice profiles → best-practices/
echo "Installing best-practice profiles..."
if [ -d "$REPO_DIR/shared/best-practices" ]; then
    rm -rf "$CODEX_DIR/best-practices"
    cp -R "$REPO_DIR/shared/best-practices" "$CODEX_DIR/best-practices"
    echo "  ✓ Copied: best-practices/"
fi

# 10. Rewrite Claude-Code paths to the Codex install location so the resolver, handoff
#     protocol, and agent cross-references resolve here. Scope the rewrite to the files
#     WE installed — $CODEX_DIR is a shared standard dir that may hold other tools'
#     skills, so never rewrite the whole tree. Order matters: map specific resource dirs
#     before the general agents/ fallback.
echo "Rewriting ~/.claude paths for Codex..."
OWNED=("$CODEX_DIR/agents" "$CODEX_DIR/review-steps" "$CODEX_DIR/shared" "$CODEX_DIR/best-practices")
for d in "$REPO_DIR"/workflow/skills/sk-*/ "$REPO_DIR"/utilities/sk-*/ \
         "$REPO_DIR"/context/sk-*/ "$REPO_DIR"/planning/sk-*/; do
    [ -d "$d" ] && OWNED+=("$CODEX_DIR/$(basename "$d")")
done
for cmd in "$REPO_DIR"/onboarding/*.md; do
    [ -f "$cmd" ] && OWNED+=("$CODEX_DIR/$(basename "$cmd" .md)")
done
for root in "${OWNED[@]}"; do
    [ -e "$root" ] || continue
    find "$root" -name '*.md' -type f -print0 | while IFS= read -r -d '' f; do
        sed -i.bak \
            -e "s|~/.claude/agents/best-practices|$CODEX_DIR/best-practices|g" \
            -e "s|~/.claude/agents/review-steps|$CODEX_DIR/review-steps|g" \
            -e "s|~/.claude/agents/shared|$CODEX_DIR/shared|g" \
            -e "s|~/.claude/agents/|$CODEX_DIR/agents/|g" \
            "$f"
        rm -f "$f.bak"
    done
done

echo ""
echo "Installation complete!"
echo "Catalog skills installed: $SKILL_COUNT (agents/review-steps/shared/best-practices are internal resources, not catalog skills)"
echo ""
echo "Note: You may need to restart Codex to load new skills."
