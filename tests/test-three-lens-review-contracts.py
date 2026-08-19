#!/usr/bin/env python3
"""Lock the three-lens review lifecycle and bounded remediation contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LENSES = {
    "sk-review-architecture-design": "architecture-design.md",
    "sk-review-correctness-safety": "correctness-safety.md",
    "sk-review-engineering-quality": "engineering-quality.md",
}


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(text: str, *phrases: str) -> None:
    normalized = " ".join(text.lower().split())
    for phrase in phrases:
        assert phrase.lower() in normalized, phrase


def reject(text: str, *phrases: str) -> None:
    normalized = " ".join(text.lower().split())
    for phrase in phrases:
        assert phrase.lower() not in normalized, phrase


def assert_manifest() -> None:
    manifest = json.loads(read("skills-manifest.yaml"))
    review_steps = {item["name"]: Path(item["source"]).name for item in manifest["review_steps"]}
    assert review_steps == LENSES, review_steps
    for filename in LENSES.values():
        assert (ROOT / "workflow/agents/review-steps" / filename).is_file()
    for filename in (
        "security.md",
        "architecture.md",
        "abstraction.md",
        "structure.md",
        "imports.md",
        "stack-rules.md",
        "instruction-quality.md",
    ):
        assert not (ROOT / "workflow/agents/review-steps" / filename).exists(), filename


def assert_full_review_contract() -> None:
    orchestrator = read("workflow/agents/sk-review-orchestrator.md")
    require(
        orchestrator,
        "exactly three independent lenses",
        "architecture-design",
        "correctness-safety",
        "engineering-quality",
        "one codex wave",
        "root runs readiness gates once per snapshot",
        "must not rerun the full suite",
        "complete finding set",
        "freeze the exact remediation allowlist",
        "required outcome",
        "remedy authority",
        "send only `within_approved_design` ids",
        "targeted round 2",
        "immutable pre/post fingerprints",
        "unchanged hashes",
        "exceptional round 3",
        "no automatic round 4",
        "needs user decision",
        "parent full review",
        "zero required unverified dimensions",
        "design/adr amendment always invalidates targeted mode",
    )
    reject(
        orchestrator,
        "structure/coverage",
        "coverage-ledger.json",
        "seven independent",
        "other six",
        "all applicable lenses",
        "fresh full review through",
    )

    verdict = read("workflow/agents/references/review-verdict-policy.md")
    require(
        verdict,
        "round 1",
        "targeted round 2",
        "exceptional round 3",
        "no automatic round 4",
        "mode",
        "parent",
        "complete routing",
        "zero required unverified dimensions",
    )

    scope = read("workflow/agents/shared/scope-governance.md")
    require(
        scope,
        "freeze the exact remediation allowlist",
        "complete finding set",
        "remedy_authority",
        "architecture_decision_required",
    )


def assert_lens_ownership() -> None:
    architecture = read("workflow/agents/review-steps/architecture-design.md")
    correctness = read("workflow/agents/review-steps/correctness-safety.md")
    quality = read("workflow/agents/review-steps/engineering-quality.md")
    require(
        architecture,
        "owns shape and ownership",
        "dependency direction",
        "abstraction/navigation cost",
        "api/schema/model shape",
        "packaging",
        "simplest viable alternative",
        "permanent complexity",
    )
    require(
        correctness,
        "owns semantics and risk",
        "state transitions",
        "recovery",
        "concurrency",
        "idempotency",
        "trust boundaries",
        "executable instruction correctness",
        "invariant alignment row",
        "transaction/coordination scope",
    )
    require(
        quality,
        "owns implementation and tool evidence",
        "root-produced provenance",
        "must not rerun the full suite",
        "test-code quality",
    )
    for lens in (architecture, correctness, quality):
        require(
            lens,
            "complete finding set",
            "scope-governance.md",
            "change_class:",
            "disposition:",
            "scope_basis:",
            "required_outcome:",
            "remedy_authority:",
            "risk_if_deferred:",
            "blocks_release:",
        )


def assert_consumers() -> None:
    code_review = read("utilities/sk-code-review/SKILL.md")
    feature = read("workflow/skills/sk-team-feature/SKILL.md")
    phase = read("workflow/skills/sk-team-feature/references/phase-prompts.md")
    quick = read("workflow/skills/sk-team-quick/SKILL.md")
    require(code_review, "exactly three independent lenses", "one codex wave")
    require(feature, "targeted round 2", "exceptional round 3", "no automatic round 4")
    require(
        phase,
        "complete finding set",
        "architecture replan after review",
        "caller records the route transition",
        "allowlist plus each id's remedy authority/route",
        "developer-routed allowlisted ids",
    )
    require(
        quick,
        "one combined reviewer",
        "architecture-design",
        "correctness-safety",
        "engineering-quality",
        "same three-round cap",
    )

    active = "\n".join((code_review, feature, phase, quick))
    reject(
        active,
        "coverage-ledger.json",
        "structure/coverage reviewer",
        "seven review",
        "seven independent",
        "other six",
        "fresh full review through all",
    )


def main() -> None:
    assert_manifest()
    assert_full_review_contract()
    assert_lens_ownership()
    assert_consumers()


if __name__ == "__main__":
    main()
    print("OK: three-lens review contracts")
