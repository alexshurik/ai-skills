#!/bin/bash
# Generate AGENTS.md from all skills
# Creates a cross-platform agent documentation file

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$REPO_DIR/AGENTS.md"

echo "Generating AGENTS.md..."

# Function to extract description from file
extract_desc() {
    local file="$1"
    grep "^description:" "$file" 2>/dev/null | head -1 | sed 's/^description:[[:space:]]*//'
}

cat > "$OUTPUT" << 'HEADER'
# AGENTS.md

> Auto-generated. Provides context for AI coding agents.
> Compatible with: OpenAI Codex, Cursor, Aider, RooCode, Zed

## Available Commands

HEADER

echo "### Workflow (Multi-Agent Team)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for skill in "$REPO_DIR"/workflow/skills/sk-*/SKILL.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$(dirname "$skill")")
        desc=$(extract_desc "$skill")
        echo "- \`/$name\` - $desc" >> "$OUTPUT"
    fi
done

echo "" >> "$OUTPUT"
echo "### Onboarding" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for cmd in "$REPO_DIR"/onboarding/*.md; do
    if [ -f "$cmd" ]; then
        name=$(basename "$cmd" .md)
        desc=$(extract_desc "$cmd")
        echo "- \`/$name\` - $desc" >> "$OUTPUT"
    fi
done

echo "" >> "$OUTPUT"
echo "### Utilities" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for skill in "$REPO_DIR"/utilities/sk-*/SKILL.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$(dirname "$skill")")
        desc=$(extract_desc "$skill")
        echo "- \`/$name\` - $desc" >> "$OUTPUT"
    fi
done

echo "" >> "$OUTPUT"
echo "### Context Management" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for skill in "$REPO_DIR"/context/sk-*/SKILL.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$(dirname "$skill")")
        desc=$(extract_desc "$skill")
        echo "- \`/$name\` - $desc" >> "$OUTPUT"
    fi
done

echo "" >> "$OUTPUT"
echo "## Agent Definitions" >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo "The following agents are available for task delegation:" >> "$OUTPUT"
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

cat >> "$OUTPUT" << 'FOOTER'

## Usage

### Claude Code
```bash
./scripts/install-claude-code.sh
```

### OpenAI Codex
```bash
./scripts/install-codex.sh
```

### Cursor
```bash
./scripts/generate-cursorrules.sh
cp adapters/cursor/.cursorrules /path/to/project/
```

## Quick Start

1. **Start a feature**: `/sk-team-feature Add user authentication`
2. **Quick fix**: `/sk-team-quick Fix null pointer in login`
3. **Check status**: `/sk-team-status`
4. **Get help**: `/sk-team-help`

## License

MIT
FOOTER

echo "Generated: $OUTPUT"
echo "Lines: $(wc -l < "$OUTPUT" | tr -d ' ')"
