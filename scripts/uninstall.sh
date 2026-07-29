#!/bin/bash
# Remove only entries owned by this repository's skills manifest.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
CLAUDE_DIR="${CLAUDE_SKILLS_ROOT:-$HOME/.claude}"
KIMI_DIR="${KIMI_AGENTS_ROOT:-$HOME/.config/agents}"

python3 "$REPO_DIR/scripts/skills_tool.py" uninstall \
    --missing-ok \
    --target codex "$CODEX_DIR" \
    --target claude "$CLAUDE_DIR" \
    --target kimi "$KIMI_DIR"

echo "Current manifest-owned installations removed."
echo "Legacy ~/.codex/skills entries were not deleted."
echo "Use scripts/migrate-legacy-codex.sh for a recoverable legacy migration."
