#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

"$REPO_DIR/scripts/validate-skills.sh"
"$REPO_DIR/scripts/generate-agents-md.sh" --check
"$REPO_DIR/scripts/generate-cursorrules.sh" --check
"$REPO_DIR/tests/test-collect-change-evidence.sh"
"$REPO_DIR/tests/test-workflow-contracts.sh"
"$REPO_DIR/tests/test-eval-fixtures.sh"
"$REPO_DIR/tests/test-install-rollback.py"
"$REPO_DIR/tests/test-installers.sh"

echo "OK: all skill tests"
