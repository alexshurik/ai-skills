#!/bin/bash
# Uninstall sk-* skills/agents/commands installed by this repo.
# Cleans both Claude Code (~/.claude symlinks) and OpenAI Codex (copied files).
# Only removes items THIS repo installs — never wipes a shared skills directory.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Uninstalling sk-* ..."
echo ""

# ---------------------------------------------------------------------------
# Claude Code  (~/.claude — symlinks created by install-claude-code.sh)
# ---------------------------------------------------------------------------
echo "== Claude Code =="

echo "Removing skills..."
for link in "$CLAUDE_DIR/skills/"sk-*; do
    if [ -L "$link" ] || [ -d "$link" ]; then
        rm -rf "$link"
        echo "  ✓ Removed skill: $(basename "$link")"
    fi
done

echo "Removing agents..."
for link in "$CLAUDE_DIR/agents/"sk-*.md; do
    if [ -L "$link" ] || [ -f "$link" ]; then
        rm -f "$link"
        echo "  ✓ Removed agent: $(basename "$link")"
    fi
done

echo "Removing agent resource links..."
for res in review-steps shared best-practices; do
    link="$CLAUDE_DIR/agents/$res"
    if [ -L "$link" ]; then
        rm -f "$link"
        echo "  ✓ Removed: agents/$res"
    fi
done

echo "Removing commands..."
for cmd in "$REPO_DIR"/onboarding/*.md; do
    [ -f "$cmd" ] || continue
    link="$CLAUDE_DIR/commands/$(basename "$cmd")"
    if [ -L "$link" ] || [ -f "$link" ]; then
        rm -f "$link"
        echo "  ✓ Removed command: $(basename "$link")"
    fi
done

# ---------------------------------------------------------------------------
# OpenAI Codex  (copied files — current $HOME/.agents/skills + legacy ~/.codex/skills)
# ---------------------------------------------------------------------------
echo ""
echo "== OpenAI Codex =="

# Remove a resource dir only if a known marker file proves it is ours (these dirs live
# in a shared skills directory that may also hold other tools' skills).
remove_owned_dir() {
    local dir="$1" marker="$2"
    if [ -d "$dir" ] && [ -e "$dir/$marker" ]; then
        rm -rf "$dir"
        echo "  ✓ Removed: $(basename "$dir")/"
    fi
}

clean_codex_dir() {
    local base="$1"
    [ -d "$base" ] || return 0
    echo "Cleaning $base ..."

    # Catalog skills we install (user-invocable), by source-derived name.
    for d in "$REPO_DIR"/workflow/skills/sk-*/ "$REPO_DIR"/utilities/sk-*/ \
             "$REPO_DIR"/context/sk-*/ "$REPO_DIR"/planning/sk-*/; do
        [ -d "$d" ] || continue
        target="$base/$(basename "$d")"
        [ -d "$target" ] && rm -rf "$target" && echo "  ✓ Removed skill: $(basename "$d")"
    done
    for cmd in "$REPO_DIR"/onboarding/*.md; do
        [ -f "$cmd" ] || continue
        target="$base/$(basename "$cmd" .md)"
        [ -d "$target" ] && rm -rf "$target" && echo "  ✓ Removed command: $(basename "$cmd" .md)"
    done

    # Legacy: old installs placed each agent as its own catalog skill dir.
    for agent in "$REPO_DIR"/workflow/agents/*.md; do
        [ -f "$agent" ] || continue
        target="$base/$(basename "$agent" .md)"
        if [ -d "$target" ] && [ -f "$target/SKILL.md" ]; then
            rm -rf "$target"
            echo "  ✓ Removed legacy agent skill: $(basename "$agent" .md)"
        fi
    done

    # Internal resource dirs (guarded by marker files).
    remove_owned_dir "$base/agents"         "sk-developer.md"
    remove_owned_dir "$base/review-steps"   "security.md"
    remove_owned_dir "$base/shared"         "handoff-protocol.md"
    remove_owned_dir "$base/best-practices" "resolver.md"
}

clean_codex_dir "${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
# Legacy location used by older versions of the installer.
[ "${CODEX_SKILLS_DIR:-$HOME/.agents/skills}" != "$HOME/.codex/skills" ] && \
    clean_codex_dir "$HOME/.codex/skills"

echo ""
echo "Uninstallation complete!"
echo "Restart Claude Code / Codex to apply changes."
