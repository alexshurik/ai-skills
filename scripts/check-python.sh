#!/bin/bash
# Reproducible Python format, lint, and type-check gate for repository development.

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: repository development requires uv; install it from https://docs.astral.sh/uv/." >&2
    exit 1
fi

cd "$REPO_DIR"
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy
uv run --frozen python scripts/check-python-structure.py
uv run --frozen coverage run tests/test-runtime-state.py
uv run --frozen coverage report
