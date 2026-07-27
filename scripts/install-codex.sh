#!/bin/bash
# Install the manifest-owned sk-* catalog and internal resources for Codex.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"

echo "Validating source..."
python3 "$REPO_DIR/scripts/skills_tool.py" validate

echo "Installing Codex tree to $CODEX_DIR ..."
python3 "$REPO_DIR/scripts/skills_tool.py" install \
    --platform codex \
    --target "$CODEX_DIR"
python3 "$REPO_DIR/scripts/skills_tool.py" verify \
    --platform codex \
    --target "$CODEX_DIR"

echo "Checking for duplicate legacy skills..."
if ! python3 "$REPO_DIR/scripts/skills_tool.py" doctor \
    --root "$CODEX_DIR" \
    --root "$HOME/.codex/skills"; then
    echo ""
    echo "Installation is current, but duplicate legacy skills remain."
    echo "Review them, then run: $REPO_DIR/scripts/migrate-legacy-codex.sh"
    exit 1
fi

echo "Codex installation verified. Restart Codex to reload skills."
