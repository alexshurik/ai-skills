#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

# A real interpreter for the end-to-end wrapper checks, honouring the caller's
# PYTHON (tests/run.sh exports the locked environment's). The resolver cases
# below then need PYTHON unset so that only their stubs are on offer.
REAL_PYTHON="$(bash -c '. "$1"; sk_python -c "import sys; print(sys.executable)"' \
    shell "$REPO_DIR/scripts/python-runtime.sh")"
unset PYTHON

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

# An interpreter stub that reports a fixed version and passes the 3.10 probe only
# when that version qualifies.
make_versioned() {
    local target="$1" version="$2" qualifies="$3"
    printf '%s\n' \
        '#!/bin/sh' \
        'case "$*" in' \
        "  *'version_info[:3]'*) echo $version; exit 0 ;;" \
        "  *'version_info >= (3, 10)'*) exit $qualifies ;;" \
        'esac' \
        "printf '$version:%s\n' \"\$*\"" > "$target"
    chmod +x "$target"
}

# PYTHON wins over python3 when it qualifies, and is exclusive when it does not.
OVERRIDE_DIR="$TEST_ROOT/override"
mkdir -p "$OVERRIDE_DIR/bin"
make_versioned "$OVERRIDE_DIR/bin/python3" 3.12.1 0
make_versioned "$OVERRIDE_DIR/custom-python" 3.11.4 0
make_versioned "$OVERRIDE_DIR/old-python" 3.9.6 1
OUTPUT="$(PATH="$OVERRIDE_DIR/bin:$PATH" PYTHON="$OVERRIDE_DIR/custom-python" bash -c \
    '. "$1"; sk_python chosen' shell "$REPO_DIR/scripts/python-runtime.sh")"
[ "$OUTPUT" = "3.11.4:chosen" ]
if PATH="$OVERRIDE_DIR/bin:$PATH" PYTHON="$OVERRIDE_DIR/old-python" bash -c \
    '. "$1"; sk_python chosen' shell "$REPO_DIR/scripts/python-runtime.sh" \
    > "$TEST_ROOT/old-override.out" 2> "$TEST_ROOT/old-override.err"; then
    echo "an explicit PYTHON older than 3.10 must not fall back to python3" >&2
    exit 1
fi
grep -qF "PYTHON=$OVERRIDE_DIR/old-python is 3.9.6" "$TEST_ROOT/old-override.err"
[ ! -s "$TEST_ROOT/old-override.out" ]

# With only macOS's 3.9 python3, the installed helper wrappers stop with a clear
# message before Python runs, and PYTHON points them at a supported interpreter.
OLD_ONLY="$TEST_ROOT/old-only"
mkdir -p "$OLD_ONLY/bin"
make_versioned "$OLD_ONLY/bin/python3" 3.9.6 1
ln -s "$(command -v dirname)" "$OLD_ONLY/bin/dirname"
for wrapper in collect-change-evidence.sh review-map.sh review-gate.sh; do
    set +e
    PATH="$OLD_ONLY/bin" "$REPO_DIR/shared/review-evidence/$wrapper" --help \
        > "$TEST_ROOT/$wrapper.out" 2> "$TEST_ROOT/$wrapper.err"
    STATUS=$?
    set -e
    [ "$STATUS" -eq 127 ]
    grep -qF 'SK helpers require Python >= 3.10; found: python3 is 3.9.6;' "$TEST_ROOT/$wrapper.err"
    grep -qF 'set PYTHON=/path/to/python3.10+' "$TEST_ROOT/$wrapper.err"
    if grep -q 'Traceback' "$TEST_ROOT/$wrapper.err"; then
        echo "$wrapper reached Python under an unsupported interpreter" >&2
        exit 1
    fi
    PATH="$OLD_ONLY/bin" PYTHON="$REAL_PYTHON" \
        "$REPO_DIR/shared/review-evidence/$wrapper" --help > "$TEST_ROOT/$wrapper.ok"
    grep -q 'usage:' "$TEST_ROOT/$wrapper.ok"
done

# Repository shell scripts reach Python only through the resolver. A bare python3
# call, or running a .py file through its shebang, picks macOS's 3.9 python3.
BYPASS="$(cd "$REPO_DIR" && {
    grep -rnE '(^[[:space:]]*|\$\(|[;&|][[:space:]]*|(if|then|do|exec)[[:space:]]+)python3?[[:space:]]' \
        --include='*.sh' . || true
    grep -rnE '^[[:space:]]*(exec[[:space:]]+)?"?\$[A-Za-z_]+[^[:space:]"]*\.py"?([[:space:]]|$)' \
        --include='*.sh' . || true
} | grep -v '^\./\.venv/' \
  | grep -vE '^[^:]+:[0-9]+:[[:space:]]*#' \
  | grep -v '^\./shared/review-evidence/python-runtime\.sh:' \
  | grep -v '^\./tests/test-python-runtime\.sh:' || true)"
if [ -n "$BYPASS" ]; then
    echo "shell scripts bypass the Python resolver:" >&2
    echo "$BYPASS" >&2
    exit 1
fi

echo "OK: Python runtime resolver"
