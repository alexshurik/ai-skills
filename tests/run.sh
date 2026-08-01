#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

"$REPO_DIR/scripts/validate-skills.sh"
"$REPO_DIR/scripts/generate-agents-md.sh" --check
"$REPO_DIR/scripts/generate-cursorrules.sh" --check
"$REPO_DIR/scripts/generate-cursor-rules.sh" --check
python3 "$REPO_DIR/tests/test-doc-contracts.py"
python3 "$REPO_DIR/tests/test-rendered-platform-contracts.py"
python3 "$REPO_DIR/tests/test-context-cost-contracts.py"
"$REPO_DIR/tests/test-copy-context.sh"
"$REPO_DIR/tests/test-collect-change-evidence.sh"
bash "$REPO_DIR/tests/test-static-analysis-artifacts.sh"
python3 "$REPO_DIR/tests/test-evidence-path-safety.py"
python3 "$REPO_DIR/tests/test-evidence-git-bounds.py"
"$REPO_DIR/tests/test-workflow-contracts.sh"
"$REPO_DIR/tests/test-eval-fixtures.sh"
python3 "$REPO_DIR/tests/test-manifest-safety.py"
python3 "$REPO_DIR/tests/test-render-symlinks.py"
python3 "$REPO_DIR/tests/test-receipt-boundary.py"
python3 "$REPO_DIR/tests/test-migration-atomic.py"
python3 "$REPO_DIR/tests/test-install-atomic.py"
"$REPO_DIR/tests/test-install-rollback.py"
"$REPO_DIR/tests/test-installers.sh"

echo "OK: all skill tests"
