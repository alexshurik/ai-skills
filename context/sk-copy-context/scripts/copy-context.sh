#!/bin/bash

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <context-file>" >&2
    exit 2
fi

CONTEXT_FILE="$1"
if [ ! -f "$CONTEXT_FILE" ] || [ -L "$CONTEXT_FILE" ]; then
    echo "Context input must be a regular, non-symlink file." >&2
    exit 2
fi

if command -v pbcopy >/dev/null 2>&1; then
    exec pbcopy < "$CONTEXT_FILE"
fi
if command -v wl-copy >/dev/null 2>&1; then
    exec wl-copy < "$CONTEXT_FILE"
fi
if command -v xclip >/dev/null 2>&1; then
    exec xclip -selection clipboard < "$CONTEXT_FILE"
fi
if command -v powershell.exe >/dev/null 2>&1; then
    exec powershell.exe \
        -NoProfile -NonInteractive -Command '$input | Set-Clipboard' \
        < "$CONTEXT_FILE"
fi
if command -v powershell >/dev/null 2>&1; then
    exec powershell \
        -NoProfile -NonInteractive -Command '$input | Set-Clipboard' \
        < "$CONTEXT_FILE"
fi

echo "No supported clipboard command found (pbcopy, wl-copy, xclip, or PowerShell)." >&2
exit 1
