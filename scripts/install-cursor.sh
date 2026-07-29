#!/bin/bash
# Install manifest-owned skills and internal resources for current Cursor.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CURSOR_DIR="${CURSOR_SKILLS_DIR:-${1:-}}"

if [ -z "$CURSOR_DIR" ]; then
    echo "Usage: CURSOR_SKILLS_DIR=<skills-dir> $0" >&2
    echo "Example: CURSOR_SKILLS_DIR=/path/to/project/.cursor/skills $0" >&2
    exit 2
fi

echo "Validating source..."
python3 "$REPO_DIR/scripts/skills_tool.py" validate

echo "Installing Cursor skills into $CURSOR_DIR ..."
python3 "$REPO_DIR/scripts/skills_tool.py" install \
    --platform cursor \
    --target "$CURSOR_DIR"
python3 "$REPO_DIR/scripts/skills_tool.py" verify \
    --platform cursor \
    --target "$CURSOR_DIR"

echo "Cursor skill installation verified. Restart Cursor to reload skills."
