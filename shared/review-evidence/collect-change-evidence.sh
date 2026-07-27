#!/bin/bash
# Collect complete Git scope, file-size, changed-line, and local-import evidence.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/collect_change_evidence.py" "$@"
