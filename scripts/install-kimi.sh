#!/bin/bash
# Install manifest-owned sk-* skills and generated Kimi agent wrappers.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
KIMI_DIR="${KIMI_AGENTS_ROOT:-$HOME/.config/agents}"

echo "Validating source..."
python3 "$REPO_DIR/scripts/skills_tool.py" validate

echo "Installing Kimi tree to $KIMI_DIR ..."
python3 "$REPO_DIR/scripts/skills_tool.py" install \
    --platform kimi \
    --target "$KIMI_DIR"
python3 "$REPO_DIR/scripts/skills_tool.py" verify \
    --platform kimi \
    --target "$KIMI_DIR"

echo "Kimi installation verified."
echo "Run: kimi --agent-file $KIMI_DIR/agents/sk-team.yaml"
