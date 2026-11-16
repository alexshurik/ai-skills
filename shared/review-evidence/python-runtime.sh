#!/bin/bash
# Resolve a Python >= 3.10 interpreter for the SK helper scripts.
#
# Source this file, then call `sk_resolve_python`. On success it sets the array
# SK_PYTHON_CMD to the interpreter argv prefix. Resolution order:
#   1. $PYTHON when set (an interpreter path or command name). It is used
#      exclusively: an explicit override that is too old is an error, not a hint.
#   2. python3, then python, then the Windows launcher `py -3`.
# macOS ships /usr/bin/python3 3.9, so the first python3 on PATH is not assumed to
# qualify. On failure it reports what each candidate is and returns 1, so a helper
# stops before a 3.10-only construct fails halfway through a run.

SK_PYTHON_PROBE='import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'

_sk_python_version() {
    "$@" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null ||
        echo "not runnable"
}

sk_resolve_python() {
    SK_PYTHON_CMD=()
    if [ -n "${PYTHON:-}" ]; then
        if "$PYTHON" -c "$SK_PYTHON_PROBE" >/dev/null 2>&1; then
            SK_PYTHON_CMD=("$PYTHON")
            return 0
        fi
        echo "ERROR: SK helpers require Python >= 3.10, but PYTHON=$PYTHON is $(_sk_python_version "$PYTHON")." >&2
        echo "       Point PYTHON at a Python 3.10+ interpreter, or unset it to search python3, python, and py -3." >&2
        return 1
    fi
    local candidate found=""
    for candidate in python3 python "py -3"; do
        command -v "${candidate%% *}" >/dev/null 2>&1 || continue
        # Unquoted on purpose: "py -3" is the launcher plus its version flag.
        # shellcheck disable=SC2086
        if $candidate -c "$SK_PYTHON_PROBE" >/dev/null 2>&1; then
            # shellcheck disable=SC2206
            SK_PYTHON_CMD=($candidate)
            return 0
        fi
        # shellcheck disable=SC2086
        found="$found $candidate is $(_sk_python_version $candidate);"
    done
    echo "ERROR: SK helpers require Python >= 3.10; found:${found:- no python3, python, or py launcher}" >&2
    echo "       Install Python 3.10+ or set PYTHON=/path/to/python3.10+ (macOS /usr/bin/python3 is 3.9)." >&2
    return 1
}
