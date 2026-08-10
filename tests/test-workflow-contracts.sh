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
    "sk-review-architecture-design",
    "sk-review-correctness-safety",
    "sk-review-engineering-quality",
}
actual_lenses = {item["name"] for item in manifest["review_steps"]}
assert actual_lenses == expected_lenses, (actual_lenses, expected_lenses)

architect = (root / "workflow/agents/sk-architect.md").read_text()
developer = (root / "workflow/agents/sk-developer.md").read_text()
review = (root / "workflow/agents/sk-review-orchestrator.md").read_text()
feature = (root / "workflow/skills/sk-team-feature/SKILL.md").read_text()
scope = (root / "workflow/agents/shared/scope-governance.md").read_text()
runtime_policy = (root / "workflow/agents/shared/runtime-state-policy.md").read_text()
orchestration_policy = (root / "workflow/agents/shared/orchestration-policy.md").read_text()
status_skill = (root / "workflow/skills/sk-team-status/SKILL.md").read_text()
copy_context = (root / "context/sk-copy-context/SKILL.md").read_text()
runtime_tool = root / "workflow/agents/shared/runtime-state/sk_state.py"
state_schema = root / "workflow/agents/shared/runtime-state/state.schema.json"
event_schema = root / "workflow/agents/shared/runtime-state/event.schema.json"
authority = (root / "shared/best-practices/convention-evidence-model.md").read_text()
architecture_lens = (root / "workflow/agents/review-steps/architecture-design.md").read_text()
correctness_lens = (root / "workflow/agents/review-steps/correctness-safety.md").read_text()
quality_lens = (root / "workflow/agents/review-steps/engineering-quality.md").read_text()
architecture_lens_normalized = " ".join(architecture_lens.lower().split())
correctness_lens_normalized = " ".join(correctness_lens.lower().split())
quality_lens_normalized = " ".join(quality_lens.lower().split())

for phrase in ("boundary matrix", "business-vocabulary", "module-growth", "non-goals"):
    assert phrase.lower() in architect.lower(), phrase
for phrase in ("pre-write gate", "observed neighboring code", "local/dynamic import"):
    assert phrase.lower() in developer.lower(), phrase
for phrase in ("untracked", "baseline", "architecture-design", "correctness-safety"):
    assert phrase.lower() in review.lower(), phrase
for phrase in ("concern owner", "api/schema/model", "abstraction", "packaging"):
    assert phrase.lower() in architecture_lens_normalized, phrase
for phrase in ("state transitions", "trust boundaries", "test adequacy"):
    assert phrase.lower() in correctness_lens_normalized, phrase
for phrase in ("root-produced provenance", "test-code quality", "must not rerun"):
    assert phrase.lower() in quality_lens_normalized, phrase
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
for phrase in (
    "parked orchestrator",
    "dispatch",
    "start-attempt",
    "wait-agents --join foreground",
    "grant-review-lease",
    "lease envelope",
):
    assert phrase.lower() in runtime_policy.lower(), phrase
    assert phrase.lower() in feature.lower(), phrase
for phrase in (
    "valid non-empty journal",
    "valid | stale | diverged | missing | orphaned | legacy_v1 | unsupported_schema",
    "recover-journal-or-reinitialize",
    "require-compatible-helper",
):
    assert phrase.lower() in runtime_policy.lower(), phrase
    assert phrase.lower() in status_skill.lower(), phrase
    assert phrase.lower() in copy_context.lower(), phrase
feature_normalized = " ".join(feature.lower().split())
for forbidden in (
    "if the projection is missing/stale, rebuild it with `repair`",
    "if schema version 1 is found, run `migrate-v1`",
):
    assert forbidden not in feature_normalized, forbidden
for phrase in ("recommended_action", "journal-conditioned status matrix"):
    assert phrase in feature_normalized, phrase
assert "bounded nested-review writer lease" in orchestration_policy.lower()
assert "children never edit" not in orchestration_policy.lower()
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
