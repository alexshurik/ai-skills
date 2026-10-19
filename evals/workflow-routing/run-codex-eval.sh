#!/bin/bash
# Run each routing case in an isolated, ephemeral Codex session.

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <empty-output-dir> <model>" >&2
    exit 2
fi

EVAL_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$EVAL_DIR/../.." && pwd)"
CONFIG="$EVAL_DIR/eval.json"
OUTPUT_DIR="$1"
MODEL="$2"
FIXTURES_DIR="$OUTPUT_DIR/fixtures"
RESPONSES_DIR="$OUTPUT_DIR/responses"

if [ -z "$MODEL" ]; then
    echo "Model must be pinned explicitly" >&2
    exit 2
fi
if [ -e "$OUTPUT_DIR" ] && [ ! -d "$OUTPUT_DIR" ]; then
    echo "Output path is not a directory: $OUTPUT_DIR" >&2
    exit 2
fi
if [ -e "$OUTPUT_DIR" ] && [ -n "$(find "$OUTPUT_DIR" -mindepth 1 -print -quit)" ]; then
    echo "Output directory must be empty: $OUTPUT_DIR" >&2
    exit 2
fi
command -v codex >/dev/null
python3 "$EVAL_DIR/validate.py" "$CONFIG"

mkdir -p "$FIXTURES_DIR" "$RESPONSES_DIR"

copy_public_inputs() {
    local fixture="$1"
    python3 - "$CONFIG" <<'PY' |
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    config = json.load(source)
for relative in config["skill_inputs"]:
    print(relative)
PY
    while IFS= read -r relative; do
        mkdir -p "$fixture/$(dirname "$relative")"
        cp "$SKILLS_DIR/$relative" "$fixture/$relative"
    done

    cp "$EVAL_DIR/response.schema.json" "$fixture/response.schema.json"
    python3 - "$CONFIG" "$fixture/policy-inputs.txt" <<'PY'
import json
import pathlib
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    config = json.load(source)
pathlib.Path(sys.argv[2]).write_text(
    "\n".join(config["skill_inputs"]) + "\n",
    encoding="utf-8",
)
PY
}

run_case() {
    local case_id="$1"
    local phase="$2"
    local encoded_input="$3"
    local fixture="$FIXTURES_DIR/$case_id"
    local response="$RESPONSES_DIR/$case_id.json"
    local scenario

    mkdir -p "$fixture"
    copy_public_inputs "$fixture"
    git -C "$fixture" init -q
    git -C "$fixture" config user.email "workflow-routing-eval@example.invalid"
    git -C "$fixture" config user.name "Workflow Routing Eval"
    git -C "$fixture" add .
    git -C "$fixture" commit -qm "isolated public policy fixture"
    scenario="$(python3 - "$encoded_input" <<'PY'
import base64
import sys

print(base64.b64decode(sys.argv[1]).decode("utf-8"))
PY
)"

    {
        sed -n '1,240p' "$EVAL_DIR/prompt.md"
        printf '\nCase ID: %s\n' "$case_id"
        printf 'Phase: %s\n' "$phase"
        printf 'Scenario: %s\n' "$scenario"
    } | codex exec \
        --ephemeral \
        --ignore-user-config \
        --ignore-rules \
        --model "$MODEL" \
        --sandbox read-only \
        --color never \
        --cd "$fixture" \
        --output-schema "$fixture/response.schema.json" \
        --output-last-message "$response" \
        -
}

python3 - "$EVAL_DIR/cases.json" <<'PY' |
import base64
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    cases = json.load(source)["cases"]
for case in cases:
    encoded = base64.b64encode(case["input"].encode("utf-8")).decode("ascii")
    print(case["id"], case["phase"], encoded, sep="\t")
PY
while IFS=$'\t' read -r case_id phase encoded_input; do
    run_case "$case_id" "$phase" "$encoded_input"
done

SKILLS_COMMIT="$(git -C "$SKILLS_DIR" rev-parse HEAD)"
SKILLS_DIRTY=false
if [ -n "$(git -C "$SKILLS_DIR" status --porcelain)" ]; then
    SKILLS_DIRTY=true
fi
CODEX_VERSION="$(codex --version)"

python3 - \
    "$EVAL_DIR/cases.json" \
    "$RESPONSES_DIR" \
    "$OUTPUT_DIR/run-manifest.json" \
    "$MODEL" \
    "$CODEX_VERSION" \
    "$SKILLS_COMMIT" \
    "$SKILLS_DIRTY" <<'PY'
import datetime
import hashlib
import json
import pathlib
import sys

cases_path = pathlib.Path(sys.argv[1])
responses_dir = pathlib.Path(sys.argv[2])
manifest_path = pathlib.Path(sys.argv[3])
with cases_path.open(encoding="utf-8") as source:
    cases = json.load(source)["cases"]

runs = []
for case in cases:
    output = responses_dir / f"{case['id']}.json"
    runs.append(
        {
            "id": case["id"],
            "phase": case["phase"],
            "output": str(output.relative_to(manifest_path.parent)),
            "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "fresh_context": True,
            "expected_assertions_withheld": True,
        }
    )

manifest = {
    "version": 1,
    "suite": "workflow-routing",
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "model": sys.argv[4],
    "codex_cli": sys.argv[5],
    "skills_source": {
        "commit": sys.argv[6],
        "dirty": sys.argv[7] == "true",
    },
    "semantic_scoring": "not_performed",
    "runs": runs,
}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY

echo "Fresh-context responses: $RESPONSES_DIR"
echo "Run provenance: $OUTPUT_DIR/run-manifest.json"
echo "Score with: python3 $EVAL_DIR/validate.py $CONFIG --responses $RESPONSES_DIR"
