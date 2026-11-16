#!/bin/bash
# Collect complete Git scope, file-size, changed-line, and local-import evidence.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/python-runtime.sh"
sk_resolve_python || exit 127
exec "${SK_PYTHON_CMD[@]}" "$SCRIPT_DIR/collect_change_evidence.py" "$@"
