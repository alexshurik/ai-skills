#!/bin/bash

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <empty-output-dir>" >&2
    exit 2
fi

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$1"

if [ -e "$OUTPUT_DIR" ] && [ -n "$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
    echo "Output directory must be empty: $OUTPUT_DIR" >&2
    exit 2
fi

mkdir -p "$OUTPUT_DIR"
cp "$SOURCE_DIR/legacy_module.py" "$OUTPUT_DIR/legacy_module.py"
git -C "$OUTPUT_DIR" init -q
git -C "$OUTPUT_DIR" config user.email "skill-eval@example.invalid"
git -C "$OUTPUT_DIR" config user.name "Skill Eval"
git -C "$OUTPUT_DIR" add legacy_module.py
git -C "$OUTPUT_DIR" commit -qm "baseline"
cp "$SOURCE_DIR/new_transport.py" "$OUTPUT_DIR/new_transport.py"

echo "Review-scope fixture created at $OUTPUT_DIR"
