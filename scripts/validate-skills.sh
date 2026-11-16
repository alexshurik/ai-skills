#!/bin/bash
# Validate source metadata, prompt budgets, resources, and shell syntax.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$REPO_DIR/scripts/python-runtime.sh"
sk_python "$REPO_DIR/scripts/skills_tool.py" validate
