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
> Compatible with: OpenAI Codex, Cursor, Aider, RooCode, Zed, Kimi/MiniMax

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
echo "### Planning" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for skill in "$REPO_DIR"/planning/sk-*/SKILL.md; do
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

# Best-practice profiles (review-steps live under workflow/agents/review-steps/ and are
# internal sub-passes of sk-review-orchestrator, intentionally not listed as top-level agents)
cat >> "$OUTPUT" << 'BPHEADER'
## Best Practices Profiles

Stack-specific coding and review rules live in `shared/best-practices/`, organized by
language, framework, and tooling. The review orchestrator and developer resolve the
project stack via `shared/best-practices/index.yaml` and load matching profiles
automatically (precedence: project > tooling > framework > language > default).
Downstream projects override or extend profiles via `.agents/best-practices/project/`.

Available profiles:

BPHEADER

for category in languages frameworks tooling; do
    dir="$REPO_DIR/shared/best-practices/$category"
    [ -d "$dir" ] || continue
    names=$(find "$dir" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort | paste -sd ',' - | sed 's/,/, /g')
    [ -n "$names" ] && echo "- **$category**: $names" >> "$OUTPUT"
done
echo "" >> "$OUTPUT"

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
