#!/bin/bash
# Install manifest-owned sk-* skills and generated Kimi agent wrappers.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
KIMI_DIR="${KIMI_AGENTS_ROOT:-$HOME/.config/agents}"
KIMI_MIN_AGENT_VERSION="1.25.0"

. "$REPO_DIR/scripts/python-runtime.sh"
sk_require_python

echo "Validating source..."
sk_python "$REPO_DIR/scripts/skills_tool.py" validate

echo "Installing Kimi tree to $KIMI_DIR ..."
sk_python "$REPO_DIR/scripts/skills_tool.py" install \
    --platform kimi \
    --target "$KIMI_DIR"
sk_python "$REPO_DIR/scripts/skills_tool.py" verify \
    --platform kimi \
    --target "$KIMI_DIR"

echo "Kimi files verified."

if command -v kimi >/dev/null 2>&1; then
    KIMI_VERSION_OUTPUT="$(kimi --version 2>/dev/null || true)"
    KIMI_DETECTED_VERSION="$(printf '%s\n' "$KIMI_VERSION_OUTPUT" | sed -nE 's/.*version[[:space:]]+([0-9]+(\.[0-9]+)+).*/\1/p' | head -1)"
    if [ -n "$KIMI_DETECTED_VERSION" ] && ! sk_python - \
        "$KIMI_DETECTED_VERSION" "$KIMI_MIN_AGENT_VERSION" <<'PY'
import sys


def parts(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


detected = parts(sys.argv[1])
required = parts(sys.argv[2])
width = max(len(detected), len(required))
detected += (0,) * (width - len(detected))
required += (0,) * (width - len(required))
raise SystemExit(0 if detected >= required else 1)
PY
    then
        echo "WARNING: detected Kimi CLI $KIMI_DETECTED_VERSION; generated team agents require >= $KIMI_MIN_AGENT_VERSION." >&2
        echo "Upgrade Kimi before running the generated team agent." >&2
    elif [ -z "$KIMI_DETECTED_VERSION" ]; then
        echo "WARNING: could not determine Kimi CLI version; team agents require >= $KIMI_MIN_AGENT_VERSION." >&2
    fi
else
    echo "NOTE: Kimi CLI is not installed; generated team agents require >= $KIMI_MIN_AGENT_VERSION."
fi

echo "Run after compatibility is confirmed: kimi --agent-file $KIMI_DIR/agents/sk-team.yaml"
