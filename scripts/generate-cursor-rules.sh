#!/bin/bash
# Generate the current Cursor Project Rule from the manifest-owned catalog.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$REPO_DIR/adapters/cursor/.cursor/rules/sk-skills.mdc"
CHECK_ONLY=false
CANDIDATE=""
trap 'rm -f "$CANDIDATE"' EXIT

if [ "${1:-}" = "--check" ]; then
    CHECK_ONLY=true
    CANDIDATE="$(mktemp /tmp/sk-cursor-rules.XXXXXX)"
elif [ "${1:-}" = "--output" ]; then
    if [ -z "${2:-}" ]; then
        echo "Usage: $0 [--check | --output <path>]" >&2
        exit 2
    fi
    OUTPUT="$2"
elif [ "$#" -ne 0 ]; then
    echo "Usage: $0 [--check | --output <path>]" >&2
    exit 2
fi

TARGET="$OUTPUT"
if [ "$CHECK_ONLY" = true ]; then
    TARGET="$CANDIDATE"
fi

mkdir -p "$(dirname "$TARGET")"
{
    echo "---"
    echo "description: SK-* workflow and agent catalog"
    echo "globs:"
    echo "alwaysApply: true"
    echo "---"
    echo ""
    echo "# SK-* Skills for Cursor"
    echo ""
    echo "Native skills are installed under .cursor/skills; this rule keeps the"
    echo "manifest-owned catalog and internal role map visible as project context."
    echo ""
    python3 "$REPO_DIR/scripts/manifest_inventory.py" all \
        --format cursor-document
} > "$TARGET"

if [ "$CHECK_ONLY" = true ]; then
    if cmp -s "$TARGET" "$OUTPUT"; then
        echo "Cursor Project Rule is current."
    else
        echo "Cursor Project Rule is stale. Run scripts/generate-cursor-rules.sh." >&2
        diff -u "$OUTPUT" "$TARGET" || true
        exit 1
    fi
else
    echo "Generated: $OUTPUT"
    echo "Copy adapters/cursor/.cursor into the target project."
fi
