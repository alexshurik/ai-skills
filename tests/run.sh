#!/bin/bash

set -e

export PYTHONDONTWRITEBYTECODE=1

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

. "$REPO_DIR/scripts/python-runtime.sh"
sk_require_python

"$REPO_DIR/scripts/check-python.sh"

"$REPO_DIR/scripts/validate-skills.sh"
"$REPO_DIR/scripts/generate-agents-md.sh" --check
"$REPO_DIR/scripts/generate-cursorrules.sh" --check
"$REPO_DIR/scripts/generate-cursor-rules.sh" --check
sk_python "$REPO_DIR/tests/test-doc-contracts.py"
sk_python "$REPO_DIR/tests/test-rendered-platform-contracts.py"
sk_python "$REPO_DIR/tests/test-context-cost-contracts.py"
sk_python "$REPO_DIR/tests/test-three-lens-review-contracts.py"
sk_python "$REPO_DIR/tests/test-runtime-state.py"
sk_python "$REPO_DIR/tests/test-scope-governance-contracts.py"
"$REPO_DIR/tests/test-copy-context.sh"
"$REPO_DIR/tests/test-collect-change-evidence.sh"
sk_python "$REPO_DIR/tests/test-review-map.py"
bash "$REPO_DIR/tests/test-static-analysis-artifacts.sh"
sk_python "$REPO_DIR/tests/test-evidence-path-safety.py"
sk_python "$REPO_DIR/tests/test-evidence-git-bounds.py"
"$REPO_DIR/tests/test-workflow-contracts.sh"
"$REPO_DIR/tests/test-eval-fixtures.sh"
sk_python "$REPO_DIR/tests/test-manifest-safety.py"
sk_python "$REPO_DIR/tests/test-render-symlinks.py"
sk_python "$REPO_DIR/tests/test-receipt-boundary.py"
sk_python "$REPO_DIR/tests/test-migration-atomic.py"
sk_python "$REPO_DIR/tests/test-install-atomic.py"
"$REPO_DIR/tests/test-install-rollback.py"
"$REPO_DIR/tests/test-installers.sh"
"$REPO_DIR/tests/test-python-runtime.sh"

echo "OK: all skill tests"
