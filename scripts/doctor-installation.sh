#!/bin/bash
# Diagnose duplicate or conflicting sk-* skills without changing installations.

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CURRENT_CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
LEGACY_CODEX_DIR="$HOME/.codex/skills"

STATUS=0
python3 "$REPO_DIR/scripts/skills_tool.py" verify \
    --platform codex \
    --target "$CURRENT_CODEX_DIR" || STATUS=1
python3 "$REPO_DIR/scripts/skills_tool.py" doctor \
    --root "$CURRENT_CODEX_DIR" \
    --root "$LEGACY_CODEX_DIR" || STATUS=1
exit "$STATUS"
