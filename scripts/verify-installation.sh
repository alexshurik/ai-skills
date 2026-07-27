#!/bin/bash
# Verify an installed tree against the manifest-rendered expected tree.

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <codex|claude|kimi> <target-root>" >&2
    exit 2
fi

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$REPO_DIR/scripts/skills_tool.py" verify \
    --platform "$1" \
    --target "$2"
