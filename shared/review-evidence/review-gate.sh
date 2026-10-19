#!/bin/bash
# Fail-closed final approval validator for immutable review evidence.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/review_gate.py" "$@"
