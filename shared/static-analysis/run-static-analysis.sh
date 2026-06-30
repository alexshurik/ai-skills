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
#   run-static-analysis.sh [PATH ...]
#     PATH ...  files or dirs to analyze. If omitted, falls back to the changed
#               files vs the merge-base, then to the current dir.
#
# Honors an exported $RUN (project tool runner, e.g. "uv run") if the caller set
# one; otherwise it resolves the runner itself from lockfiles. Every tool is probed
# via $RUN first, then as a global binary.
#
# Output: a human+machine-readable PROVENANCE table and a SUMMARY line. The caller
# pastes these into the verdict's "Deep Analysis" section verbatim. Exit code is
# always 0 — findings/unverified are reported in the table, not via exit status
# (the reviewer decides severity).

# No `set -u`: this runs in unknown project environments on macOS bash 3.2, where
# empty-array expansion under `set -u` errors. pipefail only.
set -o pipefail

# ---------------------------------------------------------------------------
# 0. Resolve targets
# ---------------------------------------------------------------------------
TARGETS=("$@")
if [ "${#TARGETS[@]}" -eq 0 ]; then
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

# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------
ROWS=()           # provenance rows
N_OK=0; N_FIND=0; N_UNVERIFIED=0

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

# run_tool <dimension> <tool> <gate|info> -- <cmd...>
# <cmd...> is the analysis command WITHOUT the runner prefix (added here).
run_tool() {
  local dim="$1" tool="$2" kind="$3"; shift 3
  [ "$1" = "--" ] && shift
  local prefix ver out rc status
  if ! prefix="$(_probe "$tool")"; then
    ROWS+=("$dim | $tool | (not installed) | — | — | UNVERIFIED (not installed)")
    N_UNVERIFIED=$((N_UNVERIFIED+1))
    printf '  [UNVERIFIED] %-22s %s — not installed\n' "$dim" "$tool"
    return
  fi
  ver="$( ($prefix "$tool" --version) 2>/dev/null | head -1 | tr -d '\n' )"
  echo "::: $dim :: $prefix $tool $* :::"
  out="$(_timeout 150 $prefix "$tool" "$@" 2>&1)"; rc=$?
  echo "$out"
  if [ "$rc" -eq 124 ]; then
    status="UNVERIFIED (timed out >150s)"; N_UNVERIFIED=$((N_UNVERIFIED+1))
  elif echo "$out" | grep -qiE 'traceback \(most recent call last\)|command not found|no such file|unrecognized arguments|error: unknown'; then
    status="UNVERIFIED (failed to execute)"; N_UNVERIFIED=$((N_UNVERIFIED+1))
  elif [ "$rc" -eq 0 ]; then
    status="OK"; N_OK=$((N_OK+1))
  else
    status="FINDINGS (exit $rc)"; N_FIND=$((N_FIND+1))
  fi
  ROWS+=("$dim | $tool | ${ver:-?} | $prefix $tool $* | $rc | $status")
}

# ---------------------------------------------------------------------------
# 3. Run the battery by detected stack
# ---------------------------------------------------------------------------
echo "=============================================="
echo " STATIC ANALYSIS BATTERY"
echo " runner: ${RUN:-<global PATH>}"
echo " targets: ${TARGETS[*]}"
echo "=============================================="

# Multi-language dimensions (always attempt)
run_tool "duplication"        jscpd   gate -- --min-lines 5 --threshold 0 --reporters consoleFull "${TARGETS[@]}"
run_tool "cyclomatic+length"  lizard  gate -- "${TARGETS[@]}"
run_tool "SAST"               semgrep gate -- --config auto --error --quiet "${TARGETS[@]}"

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
echo ""
echo "===== STATIC ANALYSIS PROVENANCE ====="
echo "Dimension | Tool | Version | Command | Exit | Status"
echo "----------|------|---------|---------|------|-------"
for r in "${ROWS[@]}"; do echo "$r"; done
echo "===== END PROVENANCE ====="
echo ""
echo "SUMMARY: ${N_OK} OK · ${N_FIND} FINDINGS · ${N_UNVERIFIED} UNVERIFIED"
if [ "$N_UNVERIFIED" -gt 0 ]; then
  echo "NOTE: ${N_UNVERIFIED} dimension(s) UNVERIFIED — these must appear in the verdict as"
  echo "      UNVERIFIED (not as a silent pass). A gate dimension UNVERIFIED blocks APPROVED."
fi
exit 0
