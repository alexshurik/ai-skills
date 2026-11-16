#!/bin/bash
# Resolve the supported Python runtime without assuming one platform-specific command.
# Resolution (PYTHON override, then python3, python, py -3; all must be 3.10+) is
# shared with the installed review-evidence helpers so both behave identically.

. "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/shared/review-evidence/python-runtime.sh"

sk_python() {
    sk_resolve_python || return 127
    "${SK_PYTHON_CMD[@]}" "$@"
}

sk_require_python() {
    sk_resolve_python
}
