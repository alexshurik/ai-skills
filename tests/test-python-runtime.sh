#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

make_failure() {
    local target="$1"
    printf '%s\n' '#!/bin/sh' 'exit 1' > "$target"
    chmod +x "$target"
}

make_success() {
    local target="$1"
    local expected_prefix="$2"
    printf '%s\n' \
        '#!/bin/sh' \
        "if [ \"\${1:-}\" = \"$expected_prefix\" ]; then shift; fi" \
        'if [ "${1:-}" = "-c" ]; then exit 0; fi' \
        'printf "%s\n" "$*"' > "$target"
    chmod +x "$target"
}

FALLBACK_DIR="$TEST_ROOT/python-fallback"
mkdir -p "$FALLBACK_DIR"
make_failure "$FALLBACK_DIR/python3"
make_success "$FALLBACK_DIR/python" "unused"
OUTPUT="$(PATH="$FALLBACK_DIR:$PATH" bash -c \
    '. "$1"; sk_require_python; sk_python selected-python' shell "$REPO_DIR/scripts/python-runtime.sh")"
[ "$OUTPUT" = "selected-python" ]

LAUNCHER_DIR="$TEST_ROOT/launcher-fallback"
mkdir -p "$LAUNCHER_DIR"
make_failure "$LAUNCHER_DIR/python3"
make_failure "$LAUNCHER_DIR/python"
make_success "$LAUNCHER_DIR/py" "-3"
OUTPUT="$(PATH="$LAUNCHER_DIR:$PATH" bash -c \
    '. "$1"; sk_require_python; sk_python selected-launcher' shell "$REPO_DIR/scripts/python-runtime.sh")"
[ "$OUTPUT" = "selected-launcher" ]

echo "OK: Python runtime resolver"
