#!/bin/bash
# Validate source metadata, prompt budgets, resources, and shell syntax.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$REPO_DIR/scripts/skills_tool.py" validate
