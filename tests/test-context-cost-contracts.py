#!/usr/bin/env python3
"""Keep context-cost controls explicit across the workflow suite."""

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
    policy = read("workflow/agents/shared/orchestration-policy.md")
    require(
        policy,
        'fork_turns="none"',
        "depth 2",
        "one bounded deliverable",
        "parent model",
        "final or blocked",
        "longest timeout",
        "list_agents",
        "artifact paths",
    )
    reject(policy, 'fork_turns="all" by default')

    handoff = read("workflow/agents/shared/handoff-protocol.md")
    require(handoff, "durable artifact", "compact return", "50 lines")
    reject(
        handoff,
        "relay handoffs verbatim",
        "do not summarize, truncate",
        "it is a loop, not a one-shot",
    )

    feature = read("workflow/skills/sk-team-feature/SKILL.md")
    require(
        feature,
        "orchestration-policy.md",
        'fork_turns="none"',
        "one short follow-up",
        "initial full review",
        "final full review",
        "all applicable lenses",
        "two review/remediation cycles",
        "one acceptance repair",
        "git rev-parse --git-path sk-workflow",
    )
    reject(feature, "original prompt plus verbatim answers")

    review = read("workflow/agents/sk-review-orchestrator.md")
    require(
        review,
        "seven independent clean",
        "review snapshot",
        "artifact paths",
        "final approval",
        "all applicable lenses",
        "no lens may spawn",
    )
    reject(review, "full changed files/base diffs")

    quick = read("workflow/skills/sk-team-quick/SKILL.md")
    require(quick, "two bounded threads", 'fork_turns="none"')
    reject(quick, "show the full findings list and verdict verbatim")

    discover = read("onboarding/sk-discover-project.md")
    explore = read("onboarding/sk-explore-codebase.md")
    onboard = read("onboarding/sk-onboard.md")
    require(discover, "at most three clean explorers", "common facts")
    require(explore, "at most two clean explorers", "common facts")
    require(onboard, "project fingerprint", "reuse")

    evidence = read("shared/review-evidence/collect_change_evidence.py")
    require(evidence, '"--output"', "fingerprint")

    static_analysis = read("shared/static-analysis/run-static-analysis.sh")
    require(static_analysis, "--artifact-dir", "summary-only")

    plan_mode = read("planning/sk-plan-mode/SKILL.md")
    require(plan_mode, "plans/<slug>.md", "existing plan")
    reject(plan_mode, ".kimi/plan.md (if `.kimi/` directory exists or can be created)")


if __name__ == "__main__":
    main()
    print("OK: context-cost contracts")
