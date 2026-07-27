#!/bin/bash
# Move only manifest-owned legacy sk-* entries out of ~/.codex/skills.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LEGACY_CODEX_DIR="$HOME/.codex/skills"
BACKUP_DIR="${1:-$HOME/.codex/backups/sk-skills-legacy-$(date +%Y%m%d-%H%M%S)}"

python3 "$REPO_DIR/scripts/skills_tool.py" migrate-legacy \
    --legacy-root "$LEGACY_CODEX_DIR" \
    --backup-root "$BACKUP_DIR"
