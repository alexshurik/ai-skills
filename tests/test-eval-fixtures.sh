#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EVAL_DIR="$REPO_DIR/evals/webapp-auth-shell"

python3 - "$EVAL_DIR/eval.yaml" <<'PY'
import json
import pathlib
import sys

config_path = pathlib.Path(sys.argv[1])
with config_path.open(encoding="utf-8") as config_file:
    config = json.load(config_file)

assert config["historical_fixture"]["base"] == "ee6100b"
assert config["historical_fixture"]["head"] == "5aa47ea"
assert len(config["required_assertions"]) == 10
for prompt in config["prompts"].values():
    assert (config_path.parent / prompt).is_file(), prompt
for case in config["targeted_cases"]:
    assert (config_path.parent / case).is_dir(), case
PY

test "$(find "$EVAL_DIR/cases/codestyle-frequency-trap/src" -name 'sample*.py' | wc -l | tr -d ' ')" = "12"
python3 "$REPO_DIR/evals/score-result.py" \
    "$EVAL_DIR/eval.yaml" \
    "$EVAL_DIR/results/2026-07-24.json"

TEST_ROOT="$(mktemp -d /tmp/sk-eval-fixtures.XXXXXX)"
trap 'rm -rf "$TEST_ROOT"' EXIT
"$EVAL_DIR/cases/review-scope-baseline/build-fixture.sh" "$TEST_ROOT/review-scope" >/dev/null
test "$(git -C "$TEST_ROOT/review-scope" status --short)" = "?? new_transport.py"

echo "OK: eval fixture definitions"
