#!/bin/bash
# Install manifest-owned sk-* skills and generated Kimi agent profiles.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
KIMI_DIR="${KIMI_AGENTS_ROOT:-$HOME/.kimi-code}"
LEGACY_KIMI_DIR="$HOME/.config/agents"

. "$REPO_DIR/scripts/python-runtime.sh"
sk_require_python

echo "Validating source..."
sk_python "$REPO_DIR/scripts/skills_tool.py" validate

if [ "$KIMI_DIR" = "$HOME/.kimi-code" ] && \
    [ -f "$LEGACY_KIMI_DIR/.sk-skills-install.json" ]; then
    echo "Removing the receipt-owned legacy Kimi adapter from $LEGACY_KIMI_DIR ..."
    sk_python "$REPO_DIR/scripts/skills_tool.py" uninstall \
        --target kimi "$LEGACY_KIMI_DIR"
fi

echo "Installing Kimi tree to $KIMI_DIR ..."
sk_python "$REPO_DIR/scripts/skills_tool.py" install \
    --platform kimi \
    --target "$KIMI_DIR"
sk_python "$REPO_DIR/scripts/skills_tool.py" verify \
    --platform kimi \
    --target "$KIMI_DIR"

echo "Kimi files verified."

KIMI_BIN="$(command -v kimi 2>/dev/null || true)"
if [ -z "$KIMI_BIN" ] && [ -x "$HOME/.kimi-code/bin/kimi" ]; then
    KIMI_BIN="$HOME/.kimi-code/bin/kimi"
fi

if [ -n "$KIMI_BIN" ]; then
    KIMI_HELP="$("$KIMI_BIN" --help 2>/dev/null || true)"
    if ! printf '%s\n' "$KIMI_HELP" | grep -q -- '--agent-file <path>' || \
        ! printf '%s\n' "$KIMI_HELP" | grep -q 'Markdown file'; then
        echo "WARNING: detected the legacy Python kimi-cli." >&2
        echo "Install the current standalone Kimi Code CLI before using generated Markdown agents." >&2
    fi
else
    echo "NOTE: Kimi Code CLI is not installed; skills were rendered but agent compatibility was not checked."
fi

echo "Run after compatibility is confirmed: kimi --agent-file $KIMI_DIR/agents/sk-team.md"
