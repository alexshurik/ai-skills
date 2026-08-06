#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

python3 - "$REPO_DIR" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
with (root / "skills-manifest.yaml").open(encoding="utf-8") as manifest_file:
    manifest = json.load(manifest_file)

expected_lenses = {
    "sk-review-security",
    "sk-review-architecture",
    "sk-review-abstraction",
    "sk-review-structure",
    "sk-review-imports",
    "sk-review-stack-rules",
    "sk-review-instruction-quality",
}
actual_lenses = {item["name"] for item in manifest["review_steps"]}
assert actual_lenses == expected_lenses, (actual_lenses, expected_lenses)

architect = (root / "workflow/agents/sk-architect.md").read_text()
developer = (root / "workflow/agents/sk-developer.md").read_text()
review = (root / "workflow/agents/sk-review-orchestrator.md").read_text()
feature = (root / "workflow/skills/sk-team-feature/SKILL.md").read_text()
scope = (root / "workflow/agents/shared/scope-governance.md").read_text()
runtime_policy = (root / "workflow/agents/shared/runtime-state-policy.md").read_text()
runtime_tool = root / "workflow/agents/shared/runtime-state/sk_state.py"
state_schema = root / "workflow/agents/shared/runtime-state/state.schema.json"
event_schema = root / "workflow/agents/shared/runtime-state/event.schema.json"
authority = (root / "shared/best-practices/convention-evidence-model.md").read_text()
architecture_lens = (root / "workflow/agents/review-steps/architecture.md").read_text()
abstraction_lens = (root / "workflow/agents/review-steps/abstraction.md").read_text()
architecture_lens_normalized = " ".join(architecture_lens.lower().split())
abstraction_lens_normalized = " ".join(abstraction_lens.lower().split())

for phrase in ("boundary matrix", "business-vocabulary", "module-growth", "non-goals"):
    assert phrase.lower() in architect.lower(), phrase
for phrase in ("pre-write gate", "observed neighboring code", "local/dynamic import"):
    assert phrase.lower() in developer.lower(), phrase
for phrase in ("untracked", "baseline/out-of-scope", "sk-review-abstraction", "sk-review-imports"):
    assert phrase.lower() in review.lower(), phrase
for phrase in (
    "concern ownership",
    "application vocabulary",
    "cross-cutting reuse",
    "boundary shapes and non-goals",
    "capability_phrase",
    "transport_calls_or_policy_branches",
):
    assert phrase.lower() in architecture_lens_normalized, phrase
for phrase in ("one row per candidate", "grouped rows", "disposition"):
    assert phrase.lower() in abstraction_lens_normalized, phrase
for phrase in ("RETROSPECTIVE.md", "named existing skill", "no promotion"):
    assert phrase.lower() in feature.lower(), phrase
for phrase in ("Scope Delta Gate", "Review Triage Gate", "required_fix", "DEFERRED.md"):
    assert phrase.lower() in scope.lower(), phrase
for phrase in (
    "events.jsonl",
    "authoritative append-only semantic history",
    "state.json",
    "expected-revision",
    "command-id",
    "migrate-v1",
):
    assert phrase.lower() in runtime_policy.lower(), phrase
assert runtime_tool.is_file() and runtime_tool.stat().st_mode & 0o111
assert state_schema.is_file() and event_schema.is_file()
for phrase in ("Enforced", "Approved", "Observed", "Legacy/uncertain"):
    assert phrase in authority, phrase

# Project regression vocabulary may live in eval fixtures, never normative prompts.
normative_roots = [
    root / "workflow",
    root / "utilities",
    root / "shared/best-practices",
]
for base in normative_roots:
    for path in base.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        forbidden = re.search(
            r"deli-check|TelegramAuthService|LoginNonceService",
            text,
            re.IGNORECASE,
        )
        assert forbidden is None, f"project-specific leakage in {path}: {forbidden.group(0)}"
PY

echo "OK: workflow contracts"
