#!/bin/bash
# Resolve the supported Python runtime without assuming one platform-specific command.

sk_python() {
    if command -v python3 >/dev/null 2>&1 &&
        command python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        command python3 "$@"
    elif command -v python >/dev/null 2>&1 &&
        command python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        command python "$@"
    elif command -v py >/dev/null 2>&1 &&
        command py -3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        command py -3 "$@"
    else
        echo "ERROR: SK skills require Python >= 3.10 (tried python3, python, and py -3)." >&2
        return 127
    fi
}

sk_require_python() {
    if ! sk_python -c 'pass' >/dev/null; then
        echo "ERROR: SK skills require Python >= 3.10." >&2
        return 1
    fi
}
