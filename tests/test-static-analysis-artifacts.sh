#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/sk-static-artifacts.XXXXXX)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

mkdir -p "$FIXTURE_DIR/bin" "$FIXTURE_DIR/logs"
for tool in jscpd lizard semgrep complexipy radon vulture bandit; do
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

grep -q 'SUMMARY: 8 OK' "$FIXTURE_DIR/summary.txt"
grep -q 'Full log' "$FIXTURE_DIR/summary.txt"
if grep -q 'FULL RAW OUTPUT' "$FIXTURE_DIR/summary.txt"; then
  echo "summary-only leaked raw analyzer output" >&2
  exit 1
fi

test "$(find "$FIXTURE_DIR/logs" -type f -name '*.log' | wc -l | tr -d ' ')" -eq 8
grep -q 'FULL RAW OUTPUT' "$FIXTURE_DIR/logs"/*.log

cat > "$FIXTURE_DIR/bin/jscpd" <<'EOF'
#!/bin/sh
if [ "$1" = "--version" ]; then echo "fake 1.0"; exit 0; fi
echo "Clone found (2.15% duplication)"
exit 0
EOF
cat > "$FIXTURE_DIR/bin/lizard" <<'EOF'
#!/bin/sh
if [ "$1" = "--version" ]; then echo "fake 1.0"; exit 0; fi
cat <<'OUT'
!!!! Warnings (cyclomatic_complexity > 15 or length > 1000 or nloc > 1000000 or parameter_count > 100) !!!!
================================================
  NLOC    CCN   token  PARAM  length  location
------------------------------------------------
      36     18    127      1      36 hot@1-36@src/hot.py
==========================================================================================
Total nloc   Avg.NLOC  AvgCCN  Avg.token   Fun Cnt  Warning cnt   Fun Rt   nloc Rt
------------------------------------------------------------------------------------------
        38      19.0     9.5       67.0        2            1      0.50    0.95
OUT
exit 0
EOF
cat > "$FIXTURE_DIR/bin/radon" <<'EOF'
#!/bin/sh
if [ "$1" = "--version" ]; then echo "fake 1.0"; exit 0; fi
echo "src/hotspot.py - C (0.00)"
exit 0
EOF
chmod +x "$FIXTURE_DIR/bin/jscpd" "$FIXTURE_DIR/bin/lizard" "$FIXTURE_DIR/bin/radon"

PATH="$FIXTURE_DIR/bin:$PATH" RUN="" \
  "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" \
  --artifact-dir "$FIXTURE_DIR/logs-output-findings" --summary-only . \
  > "$FIXTURE_DIR/findings-summary.txt"

grep -q 'duplication.*FINDINGS (reported with exit 0)' "$FIXTURE_DIR/findings-summary.txt"
grep -q 'cyclomatic+length.*FINDINGS (reported with exit 0)' "$FIXTURE_DIR/findings-summary.txt"
grep -q 'maintainability.*FINDINGS (reported with exit 0)' "$FIXTURE_DIR/findings-summary.txt"
grep -q 'SUMMARY: 4 OK · 4 FINDINGS · 0 UNVERIFIED' "$FIXTURE_DIR/findings-summary.txt"

if "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" --summary-only . \
    > /dev/null 2>&1; then
  echo "summary-only without artifacts unexpectedly succeeded" >&2
  exit 1
fi

# Lizard always prints a threshold banner naming cyclomatic_complexity. A clean run
# (banner only, zero warning rows) must be OK; any real warning row is FINDINGS.
LIZARD_DIR="$FIXTURE_DIR/lizard-cases"
mkdir -p "$LIZARD_DIR"
cat > "$LIZARD_DIR/clean-current.txt" <<'EOF'
================================================
  NLOC    CCN   token  PARAM  length  location
------------------------------------------------
       2      1      7      1       2 ok@1-2@clean.py
1 file analyzed.
==============================================================
NLOC    Avg.NLOC  AvgCCN  Avg.token  function_cnt    file
--------------------------------------------------------------
      2       2.0     1.0        7.0         1     clean.py

===============================================================================================================
No thresholds exceeded (cyclomatic_complexity > 15 or length > 1000 or nloc > 1000000 or parameter_count > 100)
==========================================================================================
Total nloc   Avg.NLOC  AvgCCN  Avg.token   Fun Cnt  Warning cnt   Fun Rt   nloc Rt
------------------------------------------------------------------------------------------
         2       2.0     1.0        7.0        1            0      0.00    0.00
EOF
cat > "$LIZARD_DIR/clean-legacy-banner.txt" <<'EOF'
================================================
  NLOC    CCN   token  PARAM  length  location
------------------------------------------------
       2      1      7      1       2 ok@1-2@clean.py
1 file analyzed.
===========================================================================================================
!!!! Warnings (cyclomatic_complexity > 15 or length > 1000 or parameter_count > 100) !!!!
================================================
  NLOC    CCN   token  PARAM  length  location
------------------------------------------------
==========================================================================================
Total nloc   Avg.NLOC  AvgCCN  Avg.token   Fun Cnt  Warning cnt   Fun Rt   nloc Rt
------------------------------------------------------------------------------------------
         2       2.0     1.0        7.0        1            0      0.00    0.00
EOF
printf '%s\n' \
  'src/hot.py:1: warning: hot has 36 NLOC, 18 CCN, 127 token, 1 PARAM, 36 length, 0 ND' \
  > "$LIZARD_DIR/warning-line.txt"

LIZARD_PROJECT="$FIXTURE_DIR/lizard-project"
mkdir -p "$LIZARD_PROJECT/bin"
assert_lizard_status() {
  local fixture="$1" expected="$2"
  printf '%s\n' \
    '#!/bin/sh' \
    'if [ "$1" = "--version" ]; then echo "fake 1.0"; exit 0; fi' \
    "cat '$LIZARD_DIR/$fixture'" \
    'exit 0' > "$LIZARD_PROJECT/bin/lizard"
  chmod +x "$LIZARD_PROJECT/bin/lizard"
  (
    cd "$LIZARD_PROJECT"
    PATH="$LIZARD_PROJECT/bin:$FIXTURE_DIR/bin:$PATH" RUN="" \
      "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" \
      --artifact-dir "$LIZARD_PROJECT/logs-$fixture" --summary-only . \
      > "$LIZARD_PROJECT/summary-$fixture"
  )
  if ! grep -qE "^cyclomatic\+length \| lizard \|.*\| 0 \| $expected \|" \
      "$LIZARD_PROJECT/summary-$fixture"; then
    echo "lizard fixture $fixture was not classified $expected" >&2
    grep -E '^cyclomatic\+length' "$LIZARD_PROJECT/summary-$fixture" >&2 || true
    exit 1
  fi
}
assert_lizard_status clean-current.txt 'OK'
assert_lizard_status clean-legacy-banner.txt 'OK'
assert_lizard_status warning-line.txt 'FINDINGS \(reported with exit 0\)'

# --probe-only resolves the same battery for the detected stack, runs no analyzer,
# names every missing tool, and cannot be mistaken for review provenance.
PROBE_PROJECT="$FIXTURE_DIR/probe-project"
mkdir -p "$PROBE_PROJECT/probe-bin" "$PROBE_PROJECT/sysbin"
printf '[project]\nname = "probe"\n' > "$PROBE_PROJECT/pyproject.toml"
for cmd in bash sh env grep sed awk tr head cat mkdir dirname touch; do
  ln -s "$(command -v "$cmd")" "$PROBE_PROJECT/sysbin/$cmd"
done
for tool in jscpd lizard radon vulture; do
  printf '%s\n' \
    '#!/bin/sh' \
    'if [ "$1" = "--version" ]; then echo "fake 1.0"; exit 0; fi' \
    "touch '$PROBE_PROJECT/analyzer-ran'" \
    'exit 0' > "$PROBE_PROJECT/probe-bin/$tool"
  chmod +x "$PROBE_PROJECT/probe-bin/$tool"
done
(
  cd "$PROBE_PROJECT"
  PATH="$PROBE_PROJECT/probe-bin:$PROBE_PROJECT/sysbin" \
    "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" --probe-only \
    > "$PROBE_PROJECT/probe.txt"
)
test ! -e "$PROBE_PROJECT/analyzer-ran"
grep -q 'STATIC ANALYSIS PROBE (no analyzer runs)' "$PROBE_PROJECT/probe.txt"
grep -q '^cyclomatic+length | lizard | gate | <global PATH> | AVAILABLE$' "$PROBE_PROJECT/probe.txt"
grep -q '^SAST | semgrep | gate | — | MISSING$' "$PROBE_PROJECT/probe.txt"
grep -q '^py-SAST | bandit | gate | — | MISSING$' "$PROBE_PROJECT/probe.txt"
grep -q '^PROBE: 5 AVAILABLE · 3 MISSING$' "$PROBE_PROJECT/probe.txt"
grep -q '^MISSING TOOLS: semgrep complexipy bandit$' "$PROBE_PROJECT/probe.txt"
if grep -q 'STATIC ANALYSIS PROVENANCE' "$PROBE_PROJECT/probe.txt"; then
  echo "probe output must not look like review provenance" >&2
  exit 1
fi
if "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" --probe-only . \
    > /dev/null 2>&1; then
  echo "probe-only with analysis targets unexpectedly succeeded" >&2
  exit 1
fi
grep -q '^SEMGREP RULES: auto$' "$PROBE_PROJECT/probe.txt"

# Semgrep rules are pinnable: SEMGREP_CONFIG, then a repository-local config;
# the registry's floating `auto` is used only as a flagged last resort.
SEMGREP_PROJECT="$FIXTURE_DIR/semgrep-project"
mkdir -p "$SEMGREP_PROJECT"
run_semgrep_case() {
  local name="$1"; shift
  (
    cd "$SEMGREP_PROJECT"
    env PATH="$FIXTURE_DIR/bin:$PATH" RUN="" "$@" \
      "$REPO_DIR/shared/static-analysis/run-static-analysis.sh" \
      --artifact-dir "$SEMGREP_PROJECT/logs-$name" --summary-only . \
      > "$SEMGREP_PROJECT/$name.txt"
  )
}
assert_semgrep_rules() {
  local name="$1" rules="$2"
  if ! grep -qE "^SAST \| semgrep \|[^|]*\| +semgrep --config $rules --error --quiet \. \|" \
      "$SEMGREP_PROJECT/$name.txt"; then
    echo "semgrep case $name did not run with --config $rules" >&2
    grep '^SAST' "$SEMGREP_PROJECT/$name.txt" >&2 || true
    exit 1
  fi
}
run_semgrep_case unpinned
assert_semgrep_rules unpinned auto
grep -q 'results are not reproducible' "$SEMGREP_PROJECT/unpinned.txt"
touch "$SEMGREP_PROJECT/.semgrep.yml"
run_semgrep_case repository
assert_semgrep_rules repository '\.semgrep\.yml'
if grep -q 'not reproducible' "$SEMGREP_PROJECT/repository.txt"; then
  echo "a repository-pinned semgrep config was reported as unpinned" >&2
  exit 1
fi
run_semgrep_case explicit SEMGREP_CONFIG=rules/pinned.yml
assert_semgrep_rules explicit 'rules/pinned\.yml'

echo "OK: static analysis artifacts"
