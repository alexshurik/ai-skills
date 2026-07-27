#!/bin/bash
# Generate .cursorrules from all skills
# Creates a single file with all skill descriptions for Cursor

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$REPO_DIR/adapters/cursor/.cursorrules"
CHECK_ONLY=false

if [ "${1:-}" = "--check" ]; then
    CHECK_ONLY=true
    OUTPUT="$(mktemp /tmp/sk-cursorrules.XXXXXX)"
    trap 'rm -f "$OUTPUT"' EXIT
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

echo "Generating .cursorrules candidate..."

cat > "$OUTPUT" << 'HEADER'
# SK-* Skills for Cursor
# Auto-generated from sk-* skills repository
#
# These are custom commands available in this project.
# Use them by typing the command name in the chat.

HEADER

# Function to extract description from SKILL.md or .md file
extract_desc() {
    local file="$1"
    grep "^description:" "$file" 2>/dev/null | head -1 | sed 's/^description:[[:space:]]*//'
}

echo "" >> "$OUTPUT"
echo "## Workflow Commands" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for skill in "$REPO_DIR"/workflow/skills/sk-*/SKILL.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$(dirname "$skill")")
        desc=$(extract_desc "$skill")
        echo "### /$name" >> "$OUTPUT"
        echo "$desc" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done

echo "## Onboarding Commands" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for cmd in "$REPO_DIR"/onboarding/*.md; do
    if [ -f "$cmd" ]; then
        name=$(basename "$cmd" .md)
        desc=$(extract_desc "$cmd")
        echo "### /$name" >> "$OUTPUT"
        echo "$desc" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done

echo "## Planning Commands" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for skill in "$REPO_DIR"/planning/sk-*/SKILL.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$(dirname "$skill")")
        desc=$(extract_desc "$skill")
        echo "/$name" >> "$OUTPUT"
        echo "$desc" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done

echo "## Utility Commands" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for skill in "$REPO_DIR"/utilities/sk-*/SKILL.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$(dirname "$skill")")
        desc=$(extract_desc "$skill")
        echo "### /$name" >> "$OUTPUT"
        echo "$desc" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done

echo "## Context Commands" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for skill in "$REPO_DIR"/context/sk-*/SKILL.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$(dirname "$skill")")
        desc=$(extract_desc "$skill")
        echo "### /$name" >> "$OUTPUT"
        echo "$desc" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done

echo "## Available Agents" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for agent in "$REPO_DIR"/workflow/agents/*.md; do
    if [ -f "$agent" ]; then
        name=$(basename "$agent" .md)
        desc=$(extract_desc "$agent")
        echo "### $name" >> "$OUTPUT"
        echo "$desc" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done

if [ "$CHECK_ONLY" = true ]; then
    if cmp -s "$OUTPUT" "$REPO_DIR/adapters/cursor/.cursorrules"; then
        echo ".cursorrules is current."
    else
        echo ".cursorrules is stale. Run scripts/generate-cursorrules.sh." >&2
        diff -u "$REPO_DIR/adapters/cursor/.cursorrules" "$OUTPUT" || true
        exit 1
    fi
else
    echo "Generated: $OUTPUT"
    echo "Lines: $(wc -l < "$OUTPUT" | tr -d ' ')"
    echo ""
    echo "Copy this file to your project root as .cursorrules"
fi
