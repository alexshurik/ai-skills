#!/bin/bash
# Generate the legacy .cursorrules compatibility file from the manifest.

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
# SK-* Skills for Cursor (Legacy .cursorrules Compatibility)
# Auto-generated from skills-manifest.yaml
#
# Prefer native Agent Skills plus .cursor/rules/sk-skills.mdc for new projects.

HEADER

python3 "$REPO_DIR/scripts/manifest_inventory.py" all \
    --format cursor-document >> "$OUTPUT"

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
    echo "Legacy output only; prefer scripts/generate-cursor-rules.sh"
fi
