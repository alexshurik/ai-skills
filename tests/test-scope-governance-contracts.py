#!/usr/bin/env python3
"""Keep scope authority, triage, and artifact ownership aligned."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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


def main() -> None:
    policy = read("workflow/agents/shared/scope-governance.md")
    require(
        policy,
        "scope delta gate",
        "required_fix | user_decision | backlog | baseline",
        "risk_if_deferred",
        "blocks_release",
        "review triage gate",
        "resolve every `user_decision`",
        "do not send “fix all findings”",
        "freeze non-critical scope",
        "openspec/changes/<name>/",
        "git rev-parse --git-path sk-workflow",
        "state.json",
        "deferred.md",
        "openspec/backlog/<slug>.md",
        "candidate | deferred | rejected | promoted",
        "review-summary.md",
    )

    architect = read("workflow/agents/sk-architect.md")
    require(
        architect,
        "scope-governance.md",
        "scope delta gate",
        "sd-*",
        "cost/blast radius",
        "every task cites",
        "deferred.md",
    )

    developer = read("workflow/agents/sk-developer.md")
    require(
        developer,
        "remediation finding allowlist",
        "allowlisted `required_fix`",
        "approved `user_decision`",
        "do not implement backlog/baseline",
    )

    correctness = read("workflow/agents/review-steps/correctness-safety.md")
    require(
        correctness,
        "approved trust model",
        "user_decision`/`backlog",
        "uncertainty is unverified",
        "never reproduce a secret value",
    )
    reject(
        correctness,
        "all security findings are **blocker** by default",
        "when in doubt, keep it blocker",
    )

    instruction = correctness
    require(
        instruction,
        "executable instruction correctness",
        "contradictory owners",
        "unsafe commands",
    )

    stack = read("workflow/agents/review-steps/engineering-quality.md")
    require(
        stack,
        "newly worsened metrics",
        "unchanged debt as baseline",
        "must not rerun the full suite",
    )

    for relative in (
        "workflow/agents/review-steps/architecture-design.md",
        "workflow/agents/review-steps/correctness-safety.md",
        "workflow/agents/review-steps/engineering-quality.md",
    ):
        lens = read(relative)
        require(
            lens,
            "scope-governance.md",
            "change_class:",
            "disposition:",
            "scope_basis:",
            "risk_if_deferred:",
            "blocks_release:",
        )

    verdict = read("workflow/agents/references/review-verdict-policy.md")
    require(
        verdict,
        "finding disposition",
        "only `required_fix` creates automatic remediation authority",
        "triage required",
        "backlog/baseline items never block",
    )

    orchestrator = read("workflow/agents/sk-review-orchestrator.md")
    require(
        orchestrator,
        "scope-governance.md",
        "review triage groups",
        "approved remediation ids",
        "never pass “fix all findings”",
        "after initial triage, freeze non-critical scope",
        "do not create `review-summary.md`",
    )

    feature = read("workflow/skills/sk-team-feature/SKILL.md")
    require(
        feature,
        "scope delta gate",
        "review triage gate",
        "freeze the exact remediation allowlist",
        "deferred.md",
        "openspec/backlog/<slug>.md",
        "do not create a second `review-summary.md`",
    )

    quick = read("workflow/skills/sk-team-quick/SKILL.md")
    require(
        quick,
        "scope delta: none",
        "required_fix | user_decision | backlog | baseline",
        "freeze the exact allowlist",
        "deferred.md",
    )

    deferred = read("shared/templates/deferred.md")
    require(
        deferred,
        "not automatically the project backlog",
        "candidate | deferred | rejected | promoted",
        "risk if deferred",
        "archive check",
    )

    readme = read("README.md")
    require(
        readme,
        "durable openspec artifacts",
        "git-local runtime and review evidence",
        "scope governance",
        "stages own gates/checks/tasks",
        "tasks preserve all attempts",
        "deferred.md",
        "openspec/backlog/<slug>.md",
        "review remains strict across all three dimensions",
    )

    help_text = read("workflow/skills/sk-team-help/SKILL.md")
    require(
        help_text,
        "scope control",
        "git rev-parse --git-path sk-workflow",
        "material proposed addition",
        "all three review dimensions remain strict",
    )


if __name__ == "__main__":
    main()
    print("OK: scope governance contracts")
