#!/bin/bash
# Move only manifest-owned legacy sk-* entries out of ~/.codex/skills.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$REPO_DIR/scripts/python-runtime.sh"
LEGACY_CODEX_DIR="$HOME/.codex/skills"
BACKUP_DIR="${1:-$HOME/.codex/backups/sk-skills-legacy-$(date +%Y%m%d-%H%M%S)}"

sk_python "$REPO_DIR/scripts/skills_tool.py" migrate-legacy \
    --legacy-root "$LEGACY_CODEX_DIR" \
    --backup-root "$BACKUP_DIR"
