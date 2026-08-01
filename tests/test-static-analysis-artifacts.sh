#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/sk-static-artifacts.XXXXXX)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

mkdir -p "$FIXTURE_DIR/bin" "$FIXTURE_DIR/logs"
for tool in jscpd lizard semgrep; do
  printf '%s\n' \
    '#!/bin/sh' \
    'if [ "$1" = "--version" ]; then echo "fake 1.0"; exit 0; fi' \
    'echo "FULL RAW OUTPUT: analyzer details"' \
    'exit 0' > "$FIXTURE_DIR/bin/$tool"
  chmod +x "$FIXTURE_DIR/bin/$tool"
done

PATH="$FIXTURE_DIR/bin:$PATH" RUN="" \
  "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" \
  --artifact-dir "$FIXTURE_DIR/logs" --summary-only . \
  > "$FIXTURE_DIR/summary.txt"

grep -q 'SUMMARY: 3 OK' "$FIXTURE_DIR/summary.txt"
grep -q 'Full log' "$FIXTURE_DIR/summary.txt"
if grep -q 'FULL RAW OUTPUT' "$FIXTURE_DIR/summary.txt"; then
  echo "summary-only leaked raw analyzer output" >&2
  exit 1
fi

test "$(find "$FIXTURE_DIR/logs" -type f -name '*.log' | wc -l | tr -d ' ')" -eq 3
grep -q 'FULL RAW OUTPUT' "$FIXTURE_DIR/logs"/*.log

if "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" --summary-only . \
    > /dev/null 2>&1; then
  echo "summary-only without artifacts unexpectedly succeeded" >&2
  exit 1
fi

echo "OK: static analysis artifacts"
