#!/bin/bash
# Fail-closed final approval validator for immutable review evidence.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/python-runtime.sh"
sk_resolve_python || exit 127
exec "${SK_PYTHON_CMD[@]}" "$SCRIPT_DIR/review_gate.py" "$@"
