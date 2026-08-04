#!/bin/bash
# Rebuild the historical auth change as an uncommitted diff in an isolated repo.

set -euo pipefail

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <source-backend-repo> <empty-output-dir> <base-commit> <head-commit>" >&2
    exit 2
fi

SOURCE_REPO="$1"
OUTPUT_DIR="$2"
BASE_COMMIT="$3"
HEAD_COMMIT="$4"

if ! git -C "$SOURCE_REPO" rev-parse --git-dir >/dev/null 2>&1; then
    echo "Historical fixture source is not a Git repository: $SOURCE_REPO" >&2
    exit 2
fi
git -C "$SOURCE_REPO" cat-file -e "$BASE_COMMIT^{commit}"
git -C "$SOURCE_REPO" cat-file -e "$HEAD_COMMIT^{commit}"

if [ -e "$OUTPUT_DIR" ] && [ ! -d "$OUTPUT_DIR" ]; then
    echo "Output path is not a directory: $OUTPUT_DIR" >&2
    exit 2
fi
if [ -e "$OUTPUT_DIR" ] && [ -n "$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
    echo "Output directory must be empty: $OUTPUT_DIR" >&2
    exit 2
fi

mkdir -p "$OUTPUT_DIR"
git -C "$SOURCE_REPO" archive "$BASE_COMMIT" | tar -x -C "$OUTPUT_DIR"
git -C "$OUTPUT_DIR" init -q
git -C "$OUTPUT_DIR" config user.email "skill-eval@example.invalid"
git -C "$OUTPUT_DIR" config user.name "Skill Eval"
git -C "$OUTPUT_DIR" add .
git -C "$OUTPUT_DIR" commit -qm "historical base fixture"
git -C "$SOURCE_REPO" diff --binary "$BASE_COMMIT..$HEAD_COMMIT" \
    | git -C "$OUTPUT_DIR" apply

echo "Historical fixture created at $OUTPUT_DIR"
git -C "$OUTPUT_DIR" status --short
