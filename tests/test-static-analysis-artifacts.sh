#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/sk-static-artifacts.XXXXXX)"
REPORT_DIR="$REPO_DIR/tests/fixtures/static-analysis"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

mkdir -p "$FIXTURE_DIR/bin" "$FIXTURE_DIR/logs"
for tool in jscpd semgrep complexipy radon vulture bandit; do
  printf '%s\n' \
    '#!/bin/sh' \
    'if [ "$1" = "--version" ]; then echo "fake 1.0"; exit 0; fi' \
    'echo "FULL RAW OUTPUT: analyzer details"' \
    'exit 0' > "$FIXTURE_DIR/bin/$tool"
  chmod +x "$FIXTURE_DIR/bin/$tool"
done
cat > "$FIXTURE_DIR/bin/lizard" <<'TOOL'
#!/bin/sh
if [ "$1" = "--version" ]; then echo "1.21.2"; exit 0; fi
cat "$LIZARD_REPORT"
exit "$LIZARD_EXIT"
TOOL
chmod +x "$FIXTURE_DIR/bin/lizard"
export LIZARD_REPORT="$REPORT_DIR/lizard-clean.txt" LIZARD_EXIT=0

PATH="$FIXTURE_DIR/bin:$PATH" RUN="env" \
  "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" \
  --artifact-dir "$FIXTURE_DIR/logs" --summary-only . \
  > "$FIXTURE_DIR/summary.txt"

# The real clean report contains the threshold expression that formerly caused FINDINGS.
grep -q 'SUMMARY: 8 OK' "$FIXTURE_DIR/summary.txt" || {
  cat "$FIXTURE_DIR/summary.txt" >&2
  exit 1
}
grep -q 'Full log' "$FIXTURE_DIR/summary.txt"
if grep -q 'FULL RAW OUTPUT' "$FIXTURE_DIR/summary.txt"; then
  echo "summary-only leaked raw analyzer output" >&2
  exit 1
fi

test "$(find "$FIXTURE_DIR/logs" -type f -name '*.log' | wc -l | tr -d ' ')" -eq 8
grep -q 'FULL RAW OUTPUT' "$FIXTURE_DIR/logs"/*.log
sed -n '6,$p' "$FIXTURE_DIR/logs/02-cyclomatic-length-lizard.log" > "$FIXTURE_DIR/captured.txt"
cmp "$LIZARD_REPORT" "$FIXTURE_DIR/captured.txt"

cat > "$FIXTURE_DIR/bin/jscpd" <<'TOOL'
#!/bin/sh
if [ "$1" = "--version" ]; then echo "fake 1.0"; exit 0; fi
echo "Clone found (2.15% duplication)"
exit 0
TOOL
cat > "$FIXTURE_DIR/bin/radon" <<'TOOL'
#!/bin/sh
if [ "$1" = "--version" ]; then echo "fake 1.0"; exit 0; fi
echo "src/hotspot.py - C (0.00)"
exit 0
TOOL

LIZARD_REPORT="$REPORT_DIR/lizard-findings.txt" PATH="$FIXTURE_DIR/bin:$PATH" RUN="env" \
  "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" \
  --artifact-dir "$FIXTURE_DIR/logs-output-findings" --summary-only . \
  > "$FIXTURE_DIR/findings-summary.txt"

grep -q 'duplication.*FINDINGS (reported with exit 0)' "$FIXTURE_DIR/findings-summary.txt"
grep -q 'cyclomatic+length.*FINDINGS (reported with exit 0)' "$FIXTURE_DIR/findings-summary.txt"
grep -q 'maintainability.*FINDINGS (reported with exit 0)' "$FIXTURE_DIR/findings-summary.txt"
grep -q 'SUMMARY: 4 OK · 4 FINDINGS · 0 UNVERIFIED' "$FIXTURE_DIR/findings-summary.txt"

# Exercise the CLI boundary in both captured-log and in-memory modes.
check_lizard() {
  local name="$1" expected="$2" mode summary status
  for mode in logged memory; do
    summary="$FIXTURE_DIR/$name-$mode.txt"
    if [ "$mode" = logged ]; then
      PATH="$FIXTURE_DIR/bin:$PATH" RUN="env" \
        "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" \
        --artifact-dir "$FIXTURE_DIR/$name-logs" --summary-only . > "$summary"
      if [ "$expected" = 'UNVERIFIED (not installed)' ]; then
        test ! -f "$FIXTURE_DIR/$name-logs/02-cyclomatic-length-lizard.log"
      else
        sed -n '6,$p' "$FIXTURE_DIR/$name-logs/02-cyclomatic-length-lizard.log" > "$FIXTURE_DIR/captured.txt"
        cmp "$LIZARD_REPORT" "$FIXTURE_DIR/captured.txt"
      fi
    else
      PATH="$FIXTURE_DIR/bin:$PATH" RUN="env" \
        "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" . > "$summary"
    fi
    status="$(awk -F ' [|] ' '$1 == "cyclomatic+length" { print $6 }' "$summary")"
    test "$status" = "$expected" || {
      echo "$name ($mode): expected '$expected', got '$status'" >&2
      exit 1
    }
  done
  echo "OK: Lizard $name ($expected), logged and memory"
}

LIZARD_REPORT="$REPORT_DIR/lizard-clean.txt" LIZARD_EXIT=0 check_lizard clean OK
LIZARD_REPORT="$REPORT_DIR/lizard-findings.txt" LIZARD_EXIT=1 check_lizard findings 'FINDINGS (exit 1)'
LIZARD_REPORT="$REPORT_DIR/lizard-findings.txt" LIZARD_EXIT=0 check_lizard findings-zero 'FINDINGS (reported with exit 0)'
LIZARD_REPORT="$REPORT_DIR/lizard-failure.txt" LIZARD_EXIT=2 check_lizard failure 'UNVERIFIED (failed to execute)'
LIZARD_REPORT="$REPORT_DIR/lizard-failure.txt" LIZARD_EXIT=0 check_lizard failure-zero 'UNVERIFIED (failed to execute)'
LIZARD_REPORT="$REPORT_DIR/lizard-clean.txt" LIZARD_EXIT=124 check_lizard timeout 'UNVERIFIED (timed out >150s)'
LIZARD_REPORT="$REPORT_DIR/lizard-clean.txt" LIZARD_EXIT=2 check_lizard unsupported-exit 'UNVERIFIED (unsupported Lizard exit 2)'
LIZARD_REPORT="$REPORT_DIR/lizard-clean.txt" LIZARD_EXIT=1 check_lizard missing-warning 'UNVERIFIED (inconsistent Lizard report)'
cat "$REPORT_DIR/lizard-clean.txt" "$REPORT_DIR/lizard-findings.txt" > "$FIXTURE_DIR/inconsistent.txt"
LIZARD_REPORT="$FIXTURE_DIR/inconsistent.txt" LIZARD_EXIT=0 check_lizard inconsistent 'UNVERIFIED (inconsistent Lizard report)'
cat "$REPORT_DIR/lizard-clean.txt" "$REPORT_DIR/lizard-failure.txt" > "$FIXTURE_DIR/late-error.txt"
LIZARD_REPORT="$FIXTURE_DIR/late-error.txt" LIZARD_EXIT=0 check_lizard late-error 'UNVERIFIED (failed to execute)'
printf '%s\n' 'usage: lizard [options]' > "$FIXTURE_DIR/usage.txt"
LIZARD_REPORT="$FIXTURE_DIR/usage.txt" LIZARD_EXIT=0 check_lizard usage 'UNVERIFIED (failed to execute)'
sed '$d' "$REPORT_DIR/lizard-clean.txt" > "$FIXTURE_DIR/truncated.txt"
LIZARD_REPORT="$FIXTURE_DIR/truncated.txt" LIZARD_EXIT=0 check_lizard truncated 'UNVERIFIED (unrecognized Lizard report)'
printf '%s\n' 'unknown report shape' > "$FIXTURE_DIR/unknown.txt"
LIZARD_REPORT="$FIXTURE_DIR/unknown.txt" LIZARD_EXIT=0 check_lizard unknown 'UNVERIFIED (unrecognized Lizard report)'
LIZARD_REPORT="$FIXTURE_DIR/unknown.txt" LIZARD_EXIT=1 check_lizard unknown-exit-one 'UNVERIFIED (unrecognized Lizard report)'

sed '/^!!!!/d' "$REPORT_DIR/lizard-findings.txt" > "$FIXTURE_DIR/count-only.txt"
LIZARD_REPORT="$FIXTURE_DIR/count-only.txt" LIZARD_EXIT=0 check_lizard positive-count 'FINDINGS (reported with exit 0)'
awk '/Total nloc/ { summary = 1 } { if (summary && NF == 8 && $1 ~ /^[0-9]+$/) $6 = 0; print }' \
  "$REPORT_DIR/lizard-findings.txt" > "$FIXTURE_DIR/warning-zero.txt"
LIZARD_REPORT="$FIXTURE_DIR/warning-zero.txt" LIZARD_EXIT=0 check_lizard warning-zero 'UNVERIFIED (inconsistent Lizard report)'
awk '/Total nloc/ { summary = 1 } { if (summary && NF == 8 && $1 ~ /^[0-9]+$/) $6 = 1; print }' \
  "$REPORT_DIR/lizard-clean.txt" > "$FIXTURE_DIR/clean-positive.txt"
LIZARD_REPORT="$FIXTURE_DIR/clean-positive.txt" LIZARD_EXIT=0 check_lizard clean-positive 'UNVERIFIED (inconsistent Lizard report)'
LIZARD_REPORT="$REPORT_DIR/lizard-findings.txt" LIZARD_EXIT=2 check_lizard findings-failed 'UNVERIFIED (unsupported Lizard exit 2)'
printf '%s\n' 'error: parse failed' >> "$FIXTURE_DIR/late-error.txt"
LIZARD_REPORT="$FIXTURE_DIR/late-error.txt" LIZARD_EXIT=1 check_lizard error-after-report 'UNVERIFIED (failed to execute)'
: > "$FIXTURE_DIR/empty.txt"
LIZARD_REPORT="$FIXTURE_DIR/empty.txt" LIZARD_EXIT=0 check_lizard empty 'UNVERIFIED (unrecognized Lizard report)'
mv "$FIXTURE_DIR/bin/lizard" "$FIXTURE_DIR/lizard-disabled"
PATH=/usr/bin:/bin check_lizard missing 'UNVERIFIED (not installed)'

if "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" --summary-only . \
    > /dev/null 2>&1; then
  echo "summary-only without artifacts unexpectedly succeeded" >&2
  exit 1
fi

echo "OK: static analysis artifacts"
