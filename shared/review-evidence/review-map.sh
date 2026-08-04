#!/bin/bash
# Build or validate deterministic review coverage artifacts.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/review_map.py" "$@"
