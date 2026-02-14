#!/bin/bash
# Uninstall sk-* skills/agents/commands from Claude Code
# Removes symlinks from ~/.claude/

set -e

CLAUDE_DIR="$HOME/.claude"

echo "Uninstalling sk-* from Claude Code..."
echo ""

# Remove skills
echo "Removing skills..."
for link in "$CLAUDE_DIR/skills/"sk-*; do
    if [ -L "$link" ] || [ -d "$link" ]; then
        rm -rf "$link"
        echo "  ✓ Removed: $(basename "$link")"
    fi
done

# Remove agents
echo "Removing agents..."
for link in "$CLAUDE_DIR/agents/"sk-*.md; do
    if [ -L "$link" ] || [ -f "$link" ]; then
        rm -f "$link"
        echo "  ✓ Removed: $(basename "$link")"
    fi
done

# Remove commands
echo "Removing commands..."
for link in "$CLAUDE_DIR/commands/"sk-*.md; do
    if [ -L "$link" ] || [ -f "$link" ]; then
        rm -f "$link"
        echo "  ✓ Removed: $(basename "$link")"
    fi
done

echo ""
echo "Uninstallation complete!"
echo "Restart Claude Code to apply changes."
