#!/bin/bash
# Install manifest-owned sk-* skills and internal roles for Claude Code.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DIR="${CLAUDE_SKILLS_ROOT:-$HOME/.claude}"

. "$REPO_DIR/scripts/python-runtime.sh"
sk_require_python

echo "Validating source..."
sk_python "$REPO_DIR/scripts/skills_tool.py" validate

echo "Linking Claude Code tree into $CLAUDE_DIR ..."
sk_python "$REPO_DIR/scripts/skills_tool.py" install \
    --platform claude \
    --target "$CLAUDE_DIR"
sk_python "$REPO_DIR/scripts/skills_tool.py" verify \
    --platform claude \
    --target "$CLAUDE_DIR"

echo "Claude Code installation verified. Restart Claude Code to reload skills."
