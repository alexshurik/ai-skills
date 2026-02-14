#!/bin/bash
# Generate .cursorrules from all skills
# Creates a single file with all skill descriptions for Cursor

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$REPO_DIR/adapters/cursor/.cursorrules"

echo "Generating .cursorrules..."

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

echo "Generated: $OUTPUT"
echo "Lines: $(wc -l < "$OUTPUT" | tr -d ' ')"
echo ""
echo "Copy this file to your project root as .cursorrules"
