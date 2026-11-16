#!/usr/bin/env bash
# Deterministic static-analysis battery for the code-review flow (step 5).
#
# WHY THIS EXISTS: the review's quantitative battery (complexity, maintainability,
# duplication, dead code, SAST) was repeatedly hand-run tool-by-tool and silently
# skipped under load, with pre-commit/CI relied on as a substitute. This script
# makes "run the battery" a SINGLE command and makes every dimension's outcome
# explicit: OK / FINDINGS / UNVERIFIED. A dimension that did not run is UNVERIFIED,
# never a silent pass. pre-commit passing is NOT a substitute — this is the review's
# own evidence.
#
# Usage:
#   run-static-analysis.sh [--artifact-dir DIR] [--summary-only] [PATH ...]
#   run-static-analysis.sh --probe-only
#     PATH ...  files or dirs to analyze. If omitted, falls back to the changed
#               files vs the merge-base, then to the current dir.
#     --artifact-dir DIR  persist one complete log per tool under DIR.
#     --summary-only      suppress raw tool output on stdout (requires artifact
#                         logs for later inspection).
#     --probe-only        run nothing; report which battery tools for the detected
#                         stack resolve (same runner and probe as a real run), so a
#                         workflow can settle install decisions at Setup instead of
#                         discovering UNVERIFIED rows at the review approval gate.
#
# Honors an exported $RUN (project tool runner, e.g. "uv run") if the caller set
# one; otherwise it resolves the runner itself from lockfiles. Every tool is probed
# via $RUN first, then as a global binary.
#
# Semgrep rules: $SEMGREP_CONFIG if set, else a repository-local .semgrep.yml,
# .semgrep.yaml, or .semgrep/ (pinned with the code), else the registry's `auto`,
# which resolves rules at run time; the output then says SAST is not reproducible.
#
# Output: a human+machine-readable PROVENANCE table and a SUMMARY line. Exit code is
# always 0 — findings/unverified are reported in the table, not via exit status
# (the reviewer decides severity).

# No `set -u`: this runs in unknown project environments on macOS bash 3.2, where
# empty-array expansion under `set -u` errors. pipefail only.
set -o pipefail

# ---------------------------------------------------------------------------
# 0. Resolve output mode and targets
# ---------------------------------------------------------------------------
ARTIFACT_DIR=""
SUMMARY_ONLY=0
PROBE_ONLY=0
TARGETS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --probe-only)
      PROBE_ONLY=1
      shift
      ;;
    --artifact-dir)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --artifact-dir requires a directory" >&2
        exit 2
      fi
      ARTIFACT_DIR="$2"
      shift 2
      ;;
    --summary-only)
      SUMMARY_ONLY=1
      shift
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do TARGETS+=("$1"); shift; done
      ;;
    *)
      TARGETS+=("$1")
      shift
      ;;
  esac
done

if [ "$PROBE_ONLY" -eq 1 ] && { [ -n "$ARTIFACT_DIR" ] || [ "$SUMMARY_ONLY" -eq 1 ] || [ "${#TARGETS[@]}" -gt 0 ]; }; then
  echo "ERROR: --probe-only runs no analyzer and takes no paths or artifact options" >&2
  exit 2
fi
if [ "$SUMMARY_ONLY" -eq 1 ] && [ -z "$ARTIFACT_DIR" ]; then
  echo "ERROR: --summary-only requires --artifact-dir so evidence is not discarded" >&2
  exit 2
fi
if [ -n "$ARTIFACT_DIR" ]; then
  mkdir -p "$ARTIFACT_DIR"
  ARTIFACT_DIR="$(cd "$ARTIFACT_DIR" && pwd)"
fi

if [ "$PROBE_ONLY" -eq 0 ] && [ "${#TARGETS[@]}" -eq 0 ]; then
  base="$(git merge-base HEAD origin/main 2>/dev/null \
        || git merge-base HEAD main 2>/dev/null || echo HEAD~1)"
  # bash 3.2 has no mapfile — read line by line, keep only existing paths
  while IFS= read -r t; do
    [ -n "$t" ] && [ -e "$t" ] && TARGETS+=("$t")
  done < <(git diff --name-only "$base"...HEAD 2>/dev/null \
        || git diff --name-only HEAD~1 2>/dev/null || true)
fi
[ "${#TARGETS[@]}" -eq 0 ] && TARGETS=(".")

# Python-only subset of the targets (most py tools choke on non-py args)
PY_TARGETS=()
for t in "${TARGETS[@]}"; do
  case "$t" in
    *.py) PY_TARGETS+=("$t") ;;
    *) [ -d "$t" ] && PY_TARGETS+=("$t") ;;
  esac
done
[ "${#PY_TARGETS[@]}" -eq 0 ] && PY_TARGETS=(".")

# ---------------------------------------------------------------------------
# 1. Resolve the project tool runner ($RUN) if the caller didn't
# ---------------------------------------------------------------------------
if [ -z "${RUN:-}" ]; then
  if   [ -f uv.lock ] || grep -q "\[tool.uv\]" pyproject.toml 2>/dev/null; then RUN="uv run"
  elif [ -f poetry.lock ]; then RUN="poetry run"
  elif [ -f pdm.lock ]; then RUN="pdm run"
  elif [ -f Pipfile.lock ]; then RUN="pipenv run"
  elif [ -f pnpm-lock.yaml ]; then RUN="pnpm exec"
  elif [ -f yarn.lock ]; then RUN="yarn"
  elif [ -f package-lock.json ]; then RUN="npx"
  else RUN=""
  fi
fi

# Semgrep rule set (see header): explicit, then repository-pinned, then registry.
if   [ -n "${SEMGREP_CONFIG:-}" ]; then SEMGREP_RULES="$SEMGREP_CONFIG"
elif [ -f .semgrep.yml ]; then SEMGREP_RULES=".semgrep.yml"
elif [ -f .semgrep.yaml ]; then SEMGREP_RULES=".semgrep.yaml"
elif [ -d .semgrep ]; then SEMGREP_RULES=".semgrep"
else SEMGREP_RULES="auto"
fi
SEMGREP_NOTE="NOTE: semgrep --config auto resolves registry rules at run time, so SAST
      results are not reproducible; set SEMGREP_CONFIG or commit .semgrep.yml to pin them."

# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------
ROWS=()           # provenance rows (probe rows in --probe-only mode)
N_OK=0; N_FIND=0; N_UNVERIFIED=0
N_AVAILABLE=0; N_MISSING=0; MISSING_TOOLS=""
LOG_INDEX=0

# portable timeout wrapper
_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then timeout "$secs" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then gtimeout "$secs" "$@"
  else "$@"
  fi
}

# probe a tool: succeed if "$RUN tool --version" or global "tool --version" works.
# echoes the resolved invocation prefix ("$RUN" or "") on success.
_probe() {
  local tool="$1"
  if [ -n "$RUN" ] && ( $RUN "$tool" --version ) >/dev/null 2>&1; then echo "$RUN"; return 0; fi
  if command -v "$tool" >/dev/null 2>&1; then echo ""; return 0; fi
  return 1
}

# --probe-only: record whether a battery tool resolves, without running analysis.
_record_probe() {
  local dim="$1" tool="$2" kind="$3" prefix
  if prefix="$(_probe "$tool")"; then
    ROWS+=("$dim | $tool | $kind | ${prefix:-<global PATH>} | AVAILABLE")
    N_AVAILABLE=$((N_AVAILABLE+1))
    return
  fi
  ROWS+=("$dim | $tool | $kind | — | MISSING")
  N_MISSING=$((N_MISSING+1))
  case " $MISSING_TOOLS " in
    *" $tool "*) ;;
    *) MISSING_TOOLS="${MISSING_TOOLS:+$MISSING_TOOLS }$tool" ;;
  esac
}

_result_text() {
  if [ -n "$ARTIFACT_DIR" ]; then
    sed -n '6,$p' "$log"
  else
    printf '%s\n' "$out"
  fi
}

_result_matches() {
  _result_text | grep -qE "$1"
}

# lizard always prints a threshold banner that names cyclomatic_complexity: older
# releases print "!!!! Warnings (...) !!!!" over an empty table, newer ones print
# "No thresholds exceeded (...)". Neither is a finding. Only a function row
# (NLOC CCN token PARAM length name@start-end@file) inside the warnings section, or
# a `-w` style "file:line: warning:" line, counts.
_lizard_reports_warnings() {
  _result_text | awk '
    /^!!!![[:space:]]+Warnings/ { in_warnings = 1; next }
    /^[[:space:]]*Total nloc/ { in_warnings = 0 }
    in_warnings && /^[[:space:]]*[0-9]+[[:space:]]+[0-9]+[[:space:]]+[0-9]+[[:space:]]+[0-9]+[[:space:]]+[0-9]+[[:space:]]+.*@[0-9]+-[0-9]+@/ { found = 1 }
    /:[0-9]+:[[:space:]]+warning:[[:space:]]/ { found = 1 }
    END { exit found ? 0 : 1 }'
}

_tool_reports_findings() {
  case "$tool:$dim" in
    jscpd:duplication)
      _result_matches 'Clone found|Exact clone|duplication[^0-9]*[1-9][0-9]*(\.[0-9]+)?%'
      ;;
    lizard:cyclomatic+length)
      _lizard_reports_warnings
      ;;
    radon:cyclomatic)
      _result_matches '[[:space:]]-[[:space:]][B-F][[:space:]]*\('
      ;;
    radon:maintainability)
      _result_matches '[[:space:]]-[[:space:]][C-F][[:space:]]*\('
      ;;
    vulture:dead-code)
      _result_matches ':[0-9]+:[[:space:]]+unused[[:space:]]'
      ;;
    *)
      return 1
      ;;
  esac
}

# run_tool <dimension> <tool> <gate|info> -- <cmd...>
# <cmd...> is the analysis command WITHOUT the runner prefix (added here).
run_tool() {
  local dim="$1" tool="$2" kind="$3"; shift 3
  [ "$1" = "--" ] && shift
  local prefix ver out rc status log slug
  if [ "$PROBE_ONLY" -eq 1 ]; then
    _record_probe "$dim" "$tool" "$kind"
    return
  fi
  if ! prefix="$(_probe "$tool")"; then
    ROWS+=("$dim | $tool | (not installed) | — | — | UNVERIFIED (not installed) | —")
    N_UNVERIFIED=$((N_UNVERIFIED+1))
    printf '  [UNVERIFIED] %-22s %s — not installed\n' "$dim" "$tool"
    return
  fi
  ver="$( ($prefix "$tool" --version) 2>/dev/null | head -1 | tr -d '\n' )"
  log="—"
  if [ -n "$ARTIFACT_DIR" ]; then
    LOG_INDEX=$((LOG_INDEX+1))
    slug="$(printf '%s-%s' "$dim" "$tool" | tr -cs '[:alnum:]._- ' '-' | tr ' ' '-')"
    log="$ARTIFACT_DIR/$(printf '%02d' "$LOG_INDEX")-$slug.log"
    {
      echo "dimension: $dim"
      echo "tool: $tool"
      echo "version: ${ver:-?}"
      echo "command: $prefix $tool $*"
      echo ""
      _timeout 150 $prefix "$tool" "$@"
    } >"$log" 2>&1
    rc=$?
    if [ "$SUMMARY_ONLY" -eq 0 ]; then
      echo "::: $dim :: $prefix $tool $* :::"
      sed -n '6,$p' "$log"
    fi
    out=""
  else
    echo "::: $dim :: $prefix $tool $* :::"
    out="$(_timeout 150 $prefix "$tool" "$@" 2>&1)"; rc=$?
    echo "$out"
  fi
  if [ "$rc" -eq 124 ]; then
    status="UNVERIFIED (timed out >150s)"; N_UNVERIFIED=$((N_UNVERIFIED+1))
  elif { [ -n "$ARTIFACT_DIR" ] && grep -qiE 'traceback \(most recent call last\)|command not found|no such file|unrecognized arguments|error: unknown' "$log"; } \
    || { [ -z "$ARTIFACT_DIR" ] && echo "$out" | grep -qiE 'traceback \(most recent call last\)|command not found|no such file|unrecognized arguments|error: unknown'; }; then
    status="UNVERIFIED (failed to execute)"; N_UNVERIFIED=$((N_UNVERIFIED+1))
  elif [ "$rc" -eq 0 ] && _tool_reports_findings; then
    status="FINDINGS (reported with exit 0)"; N_FIND=$((N_FIND+1))
  elif [ "$rc" -eq 0 ]; then
    status="OK"; N_OK=$((N_OK+1))
  else
    status="FINDINGS (exit $rc)"; N_FIND=$((N_FIND+1))
  fi
  ROWS+=("$dim | $tool | ${ver:-?} | $prefix $tool $* | $rc | $status | $log")
  if [ "$SUMMARY_ONLY" -eq 1 ]; then
    printf '  [%s] %-22s %s — log: %s\n' "${status%% *}" "$dim" "$tool" "$log"
  fi
}

# ---------------------------------------------------------------------------
# 3. Run the battery by detected stack
# ---------------------------------------------------------------------------
echo "=============================================="
if [ "$PROBE_ONLY" -eq 1 ]; then
  echo " STATIC ANALYSIS PROBE (no analyzer runs)"
else
  echo " STATIC ANALYSIS BATTERY"
fi
echo " runner: ${RUN:-<global PATH>}"
echo " semgrep rules: $SEMGREP_RULES"
[ "$PROBE_ONLY" -eq 0 ] && echo " targets: ${TARGETS[*]}"
[ -n "$ARTIFACT_DIR" ] && echo " artifacts: $ARTIFACT_DIR"
echo "=============================================="

# Multi-language dimensions (always attempt)
run_tool "duplication"        jscpd   gate -- --min-lines 5 --threshold 0 --reporters consoleFull "${TARGETS[@]}"
run_tool "cyclomatic+length"  lizard  gate -- "${TARGETS[@]}"
run_tool "SAST"               semgrep gate -- --config "$SEMGREP_RULES" --error --quiet "${TARGETS[@]}"

# Python
if [ -f pyproject.toml ] || [ -f setup.py ] || [ -f requirements.txt ]; then
  run_tool "cognitive"        complexipy gate -- -d low "${PY_TARGETS[@]}"
  run_tool "cyclomatic"       radon      info -- cc -s -n B "${PY_TARGETS[@]}"
  run_tool "maintainability"  radon      gate -- mi -s "${PY_TARGETS[@]}"
  run_tool "dead-code"        vulture    info -- "${PY_TARGETS[@]}"
  run_tool "py-SAST"          bandit     gate -- -r -q "${PY_TARGETS[@]}"
fi

# JS/TS
if [ -f package.json ]; then
  run_tool "ts-dead-code"     knip          info -- --no-progress
  run_tool "ts-type-coverage" type-coverage info -- --detail
fi

# Go
if [ -f go.mod ]; then
  run_tool "go-SAST"          gosec    gate -- ./...
  run_tool "go-cognitive"     gocognit info -- -over 10 .
fi

# Rust
if [ -f Cargo.toml ]; then
  run_tool "rust-lint"        cargo-clippy gate -- --all-targets -- -D warnings
  run_tool "rust-unused-deps" cargo-machete info -- .
fi

# ---------------------------------------------------------------------------
# 4. Provenance + summary (caller pastes this into the verdict)
# ---------------------------------------------------------------------------
if [ "$PROBE_ONLY" -eq 1 ]; then
  # Deliberately not a PROVENANCE table: review-gate.sh must never accept a probe.
  echo ""
  echo "===== STATIC ANALYSIS PROBE ====="
  echo "Dimension | Tool | Kind | Resolved via | Status"
  echo "----------|------|------|--------------|-------"
  for r in "${ROWS[@]}"; do echo "$r"; done
  echo "===== END PROBE ====="
  echo ""
  echo "PROBE: ${N_AVAILABLE} AVAILABLE · ${N_MISSING} MISSING"
  if [ "$N_MISSING" -gt 0 ]; then
    echo "MISSING TOOLS: ${MISSING_TOOLS}"
    echo "NOTE: each missing tool becomes an UNVERIFIED row in review, and review-gate.sh"
    echo "      rejects APPROVED on any UNVERIFIED row. Settle install or proceed now."
  fi
  echo "SEMGREP RULES: ${SEMGREP_RULES}"
  [ "$SEMGREP_RULES" = "auto" ] && echo "$SEMGREP_NOTE"
  exit 0
fi
echo ""
echo "===== STATIC ANALYSIS PROVENANCE ====="
echo "Dimension | Tool | Version | Command | Exit | Status | Full log"
echo "----------|------|---------|---------|------|--------|---------"
for r in "${ROWS[@]}"; do echo "$r"; done
echo "===== END PROVENANCE ====="
echo ""
echo "SUMMARY: ${N_OK} OK · ${N_FIND} FINDINGS · ${N_UNVERIFIED} UNVERIFIED"
if [ "$N_UNVERIFIED" -gt 0 ]; then
  echo "NOTE: ${N_UNVERIFIED} dimension(s) UNVERIFIED — these must appear in the verdict as"
  echo "      UNVERIFIED (not as a silent pass). review-gate.sh rejects APPROVED on any UNVERIFIED row."
fi
[ "$SEMGREP_RULES" = "auto" ] && echo "$SEMGREP_NOTE"
exit 0
