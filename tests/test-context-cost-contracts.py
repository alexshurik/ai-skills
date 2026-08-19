#!/usr/bin/env python3
"""Keep foreground-join and context-cost controls explicit across workflows."""

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
        "event-driven mailbox wait",
        "foreground join",
        "transport timeout is not a workflow retry",
        "do not end the parent turn",
        "unbounded polling",
        "background work active",
        "events.jsonl",
        "authoritative append-only history",
        "derived compact projection",
        "runtime-state/sk_state.py",
        "waiting_agents",
        "detach_reason",
        "migrate-v1",
        "notifications are observability only",
        "list_agents",
        "artifact paths",
        "scope-governance.md",
        "stages own their gates, checks, and tasks",
        "constraints: <c-* statement",
        "preferences: <non-binding",
        "cannot eliminate a solution class",
    )
    reject(
        policy,
        'fork_turns="all" by default',
        "15 empty wake-ups",
        "30 total idle wake-ups",
        "automatic background-completion notification",
    )

    handoff = read("workflow/agents/shared/handoff-protocol.md")
    require(
        handoff,
        "durable artifact",
        "compact return",
        "50 lines",
        "blocked — replan_required",
        "authority source for every material delegated constraint",
    )
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
        "round 1",
        "targeted round 2",
        "exceptional round 3",
        "no automatic round 4",
        "one acceptance repair",
        "git rev-parse --git-path sk-workflow",
        "foreground-join policy",
        "transport-only timeouts",
        "detach_reason",
        "deterministic lossless review map",
    )
    reject(feature, "original prompt plus verbatim answers", "coverage-ledger.json")

    review = read("workflow/agents/sk-review-orchestrator.md")
    require(
        review,
        "exactly three independent lenses",
        "review snapshot",
        "artifact paths",
        "targeted approved",
        "one codex wave",
        "no lens may spawn",
        "scope manifest",
        "review-map.json",
        "validate-scopes",
        "complete finding set",
        "foreground join",
        "transport-only timeouts",
        "detach_reason",
    )
    reject(review, "full changed files/base diffs", "coverage-ledger.json")

    quick = read("workflow/skills/sk-team-quick/SKILL.md")
    require(
        quick,
        "two bounded threads",
        'fork_turns="none"',
        "foreground-join policy",
        "transport-only timeouts",
        "detach_reason",
    )
    reject(quick, "show the full findings list and verdict verbatim")

    discover = read("onboarding/sk-discover-project.md")
    explore = read("onboarding/sk-explore-codebase.md")
    onboard = read("onboarding/sk-onboard.md")
    require(
        discover,
        "at most three clean explorers",
        "common facts",
        "foreground-join policy",
        "transport-only timeouts",
        "detach_reason",
    )
    require(
        explore,
        "at most two clean explorers",
        "common facts",
        "foreground-join policy",
        "transport-only timeouts",
        "detach_reason",
    )
    require(onboard, "project fingerprint", "reuse")

    code_review = read("utilities/sk-code-review/SKILL.md")
    require(
        code_review,
        "scope manifest",
        "review-map.json",
        "exactly three independent lenses",
        "one codex wave",
        "foreground wait",
        "transport-only timeouts",
    )
    reject(code_review, "coverage-ledger.json", "structure/coverage")

    for relative in (
        "workflow/agents/review-steps/architecture-design.md",
        "workflow/agents/review-steps/correctness-safety.md",
        "workflow/agents/review-steps/engineering-quality.md",
    ):
        require(
            read(relative),
            "scope manifest",
            "complete finding set",
            "current/base",
            "unverified",
        )

    agents_md = read("AGENTS.md")
    require(
        agents_md,
        "foreground join",
        "transport-only timeouts",
        "notifications are observability",
    )

    status = read("workflow/skills/sk-team-status/SKILL.md")
    require(
        status,
        "runtime-state-policy.md",
        "events.jsonl",
        "derived projection",
        "snapshot_status",
        "waiting_agents",
        "attempt ids",
        "migrate-v1",
        "read-only status request",
    )

    for text in (policy, feature, review, quick, discover, explore, code_review, agents_md):
        reject(
            text,
            "15 minutes/15 empty wake-ups",
            "15-minute/15-empty-wakeup",
            "30 idle wake-ups",
            "empty-wait counters",
        )

    evidence = read("shared/review-evidence/collect_change_evidence.py")
    require(evidence, '"--output"', "fingerprint")

    review_map = read("shared/review-evidence/review_map.py")
    require(
        review_map,
        "lossless review map",
        "coverage_requirement",
        "risk_tags",
        "validate_scopes",
        "review_map_fingerprint",
    )

    static_analysis = read("shared/static-analysis/run-static-analysis.sh")
    require(static_analysis, "--artifact-dir", "summary-only")


if __name__ == "__main__":
    main()
    print("OK: context-cost contracts")
