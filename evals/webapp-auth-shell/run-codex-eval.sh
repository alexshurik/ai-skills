#!/bin/bash
# Run the configured behavioral prompts in isolated, ephemeral Codex sessions.

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <historical-backend-repo> <empty-output-dir> <model>" >&2
    exit 2
fi

EVAL_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$EVAL_DIR/../.." && pwd)"
CONFIG="$EVAL_DIR/eval.json"
SOURCE_REPO="$1"
OUTPUT_DIR="$2"
MODEL="$3"
FIXTURES_DIR="$OUTPUT_DIR/fixtures"
RESPONSES_DIR="$OUTPUT_DIR/responses"

config_value() {
    python3 - "$CONFIG" "$1" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    value = json.load(source)
for key in sys.argv[2].split("."):
    value = value[key]
if not isinstance(value, str) or not value:
    raise SystemExit(f"configuration value is not a non-empty string: {sys.argv[2]}")
print(value)
PY
}

BASE_COMMIT="$(config_value historical_fixture.base)"
HEAD_COMMIT="$(config_value historical_fixture.head)"
FIXTURE_BUILDER="$(config_value historical_fixture.builder)"

if [ -z "$MODEL" ]; then
    echo "Model must be pinned explicitly" >&2
    exit 2
fi
case "$FIXTURE_BUILDER" in
    */* | .* | *..*)
        echo "Historical fixture builder must be a local filename: $FIXTURE_BUILDER" >&2
        exit 2
        ;;
esac
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
if [ -e "$OUTPUT_DIR" ] && [ -n "$(find "$OUTPUT_DIR" -mindepth 1 -print -quit)" ]; then
    echo "Output directory must be empty: $OUTPUT_DIR" >&2
    exit 2
fi
command -v codex >/dev/null

mkdir -p "$FIXTURES_DIR" "$RESPONSES_DIR"
"$EVAL_DIR/$FIXTURE_BUILDER" \
    "$SOURCE_REPO" \
    "$FIXTURES_DIR/review" \
    "$BASE_COMMIT" \
    "$HEAD_COMMIT"

mkdir -p "$FIXTURES_DIR/architect"
git -C "$SOURCE_REPO" archive "$BASE_COMMIT" | tar -x -C "$FIXTURES_DIR/architect"
mkdir -p "$FIXTURES_DIR/architect/cases"
cp "$EVAL_DIR/cases/architect-proposal.md" \
    "$FIXTURES_DIR/architect/cases/architect-proposal.md"
cp -R "$EVAL_DIR/cases/developer-weak-design" "$FIXTURES_DIR/developer"
cp -R "$EVAL_DIR/cases/codestyle-frequency-trap" "$FIXTURES_DIR/codestyle"
cp -R "$EVAL_DIR/cases/retrospective-routing" "$FIXTURES_DIR/retrospective"
cp -R "$EVAL_DIR/cases/local-import-claim" "$FIXTURES_DIR/local-import"
cp -R "$EVAL_DIR/cases/deployment-scope-creep" "$FIXTURES_DIR/deployment"
"$EVAL_DIR/cases/review-scope-baseline/build-fixture.sh" \
    "$FIXTURES_DIR/review-scope"

initialize_fixture() {
    local fixture="$1"
    git -C "$fixture" init -q
    git -C "$fixture" config user.email "skill-eval@example.invalid"
    git -C "$fixture" config user.name "Skill Eval"
    git -C "$fixture" add .
    git -C "$fixture" commit -qm "eval fixture"
}

initialize_fixture "$FIXTURES_DIR/architect"
initialize_fixture "$FIXTURES_DIR/developer"
initialize_fixture "$FIXTURES_DIR/codestyle"
initialize_fixture "$FIXTURES_DIR/retrospective"

git -C "$FIXTURES_DIR/local-import" init -q
git -C "$FIXTURES_DIR/local-import" config user.email "skill-eval@example.invalid"
git -C "$FIXTURES_DIR/local-import" config user.name "Skill Eval"
git -C "$FIXTURES_DIR/local-import" add src/storage.py
git -C "$FIXTURES_DIR/local-import" commit -qm "local-import baseline"

git -C "$FIXTURES_DIR/deployment" init -q
git -C "$FIXTURES_DIR/deployment" config user.email "skill-eval@example.invalid"
git -C "$FIXTURES_DIR/deployment" config user.name "Skill Eval"
git -C "$FIXTURES_DIR/deployment" add AGENTS.md
git -C "$FIXTURES_DIR/deployment" commit -qm "deployment baseline"

run_agent() {
    local name="$1"
    local fixture="$2"
    local prompt_name="$3"
    local prompt="$EVAL_DIR/prompts/$prompt_name.md"
    local response="$RESPONSES_DIR/$name.md"
    {
        sed -n '1,240p' "$prompt"
        printf '\nSkills source: %s\n' "$SKILLS_DIR"
        printf '%s\n' \
            "Do not inspect the eval configuration, expected assertions, or other fixtures."
    } | codex --ask-for-approval never exec \
        --ephemeral \
        --ignore-user-config \
        --model "$MODEL" \
        --sandbox workspace-write \
        --color never \
        --cd "$fixture" \
        --output-last-message "$response" \
        -
}

python3 - "$CONFIG" <<'PY' |
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    config = json.load(source)
for run in config["harness_runs"]:
    print(run["id"], run["fixture"], run["prompt"], sep="\t")
PY
while IFS=$'\t' read -r run_id fixture_name prompt_name; do
    run_agent "$run_id" "$FIXTURES_DIR/$fixture_name" "$prompt_name"
done

SKILLS_COMMIT="$(git -C "$SKILLS_DIR" rev-parse HEAD)"
SKILLS_DIRTY=false
if [ -n "$(git -C "$SKILLS_DIR" status --porcelain)" ]; then
    SKILLS_DIRTY=true
fi
CODEX_VERSION="$(codex --version)"

python3 - \
    "$CONFIG" \
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

config_path = pathlib.Path(sys.argv[1])
responses_dir = pathlib.Path(sys.argv[2])
manifest_path = pathlib.Path(sys.argv[3])
with config_path.open(encoding="utf-8") as source:
    config = json.load(source)

runs = []
for configured_run in config["harness_runs"]:
    output = responses_dir / f"{configured_run['id']}.md"
    runs.append(
        {
            "id": configured_run["id"],
            "prompt": configured_run["prompt"],
            "fixture": configured_run["fixture"],
            "output": str(output.relative_to(manifest_path.parent)),
            "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "fresh_context": True,
            "expected_diagnoses_withheld": True,
        }
    )

manifest = {
    "version": config["version"],
    "suite": config["suite"],
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "model": sys.argv[4],
    "codex_cli": sys.argv[5],
    "skills_source": {
        "commit": sys.argv[6],
        "dirty": sys.argv[7] == "true",
    },
    "historical_fixture": {
        "base": config["historical_fixture"]["base"],
        "head": config["historical_fixture"]["head"],
    },
    "semantic_scoring": "not_performed",
    "runs": runs,
}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY

echo "Fresh-context responses: $RESPONSES_DIR"
echo "Run provenance: $OUTPUT_DIR/run-manifest.json"
echo "Semantic scoring has not been performed; review outputs against eval.json."
