#!/bin/bash

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EVAL_DIR="$REPO_DIR/evals/webapp-auth-shell"
CONFIG="$EVAL_DIR/eval.json"

python3 - "$CONFIG" <<'PY'
import json
import pathlib
import sys

config_path = pathlib.Path(sys.argv[1])
with config_path.open(encoding="utf-8") as config_file:
    config = json.load(config_file)

assert config["version"] == 2
assert config["suite"] == "webapp-auth-shell"
assert config["historical_fixture"]["base"] == "ee6100b"
assert config["historical_fixture"]["head"] == "5aa47ea"
assert len(config["required_assertions"]) == 10
assert len(set(config["required_assertions"])) == 10
assert len(config["harness_runs"]) == 8
assert len({run["id"] for run in config["harness_runs"]}) == 8
for prompt in config["prompts"].values():
    assert (config_path.parent / prompt).is_file(), prompt
for run in config["harness_runs"]:
    assert run["prompt"] in config["prompts"], run
for case in config["targeted_cases"]:
    assert (config_path.parent / case).is_dir(), case
PY

test "$(find "$EVAL_DIR/cases/codestyle-frequency-trap/src" -name 'sample*.py' | wc -l | tr -d ' ')" = "12"
bash -n \
    "$EVAL_DIR/run-codex-eval.sh" \
    "$EVAL_DIR/build-historical-fixture.sh" \
    "$EVAL_DIR/cases/review-scope-baseline/build-fixture.sh"
python3 "$REPO_DIR/evals/validate-result.py" \
    "$CONFIG" \
    "$EVAL_DIR/results/2026-07-24.json" \
    --require-pass

TEST_ROOT="$(mktemp -d /tmp/sk-eval-fixtures.XXXXXX)"
trap 'rm -rf "$TEST_ROOT"' EXIT
cp -R "$EVAL_DIR/results" "$TEST_ROOT/results"
python3 - "$TEST_ROOT/results/2026-07-24.json" "$TEST_ROOT/outside.md" <<'PY'
import hashlib
import json
import pathlib
import sys

result_path = pathlib.Path(sys.argv[1])
outside_path = pathlib.Path(sys.argv[2])
outside_path.write_text("forged output\n", encoding="utf-8")
result = json.loads(result_path.read_text(encoding="utf-8"))
result["runs"][0]["output"] = "../outside.md"
result["runs"][0]["output_sha256"] = hashlib.sha256(outside_path.read_bytes()).hexdigest()
result_path.write_text(json.dumps(result), encoding="utf-8")
PY
if python3 "$REPO_DIR/evals/validate-result.py" \
    "$CONFIG" \
    "$TEST_ROOT/results/2026-07-24.json" >/dev/null 2>&1; then
    echo "ERROR: eval validator accepted an output path escape" >&2
    exit 1
fi

"$EVAL_DIR/cases/review-scope-baseline/build-fixture.sh" "$TEST_ROOT/review-scope" >/dev/null
test "$(git -C "$TEST_ROOT/review-scope" status --short)" = "?? new_transport.py"

echo "OK: eval fixture definitions and recorded-result integrity"
