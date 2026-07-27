#!/bin/bash
# Install manifest-owned sk-* skills and internal roles for Claude Code.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DIR="${CLAUDE_SKILLS_ROOT:-$HOME/.claude}"

echo "Validating source..."
python3 "$REPO_DIR/scripts/skills_tool.py" validate

echo "Linking Claude Code tree into $CLAUDE_DIR ..."
python3 "$REPO_DIR/scripts/skills_tool.py" install \
    --platform claude \
    --target "$CLAUDE_DIR"
python3 "$REPO_DIR/scripts/skills_tool.py" verify \
    --platform claude \
    --target "$CLAUDE_DIR"

echo "Claude Code installation verified. Restart Claude Code to reload skills."
