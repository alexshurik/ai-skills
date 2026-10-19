#!/usr/bin/env python3
"""Lock risk-routed testing, rendered UI review, receipt reuse, and lean artifacts."""

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
    feature = read("workflow/skills/sk-team-feature/SKILL.md")
    require(
        feature,
        "testing strategy and risk route",
        "auth/authz",
        "new reusable test harness",
        "ordinary ui, local behavior, and standard application changes",
        "this route is risk-based, not ui-only",
        "lowest-faithful-layer regression test",
        "few critical e2e journeys",
    )

    tester = read("workflow/agents/sk-tester.md")
    require(
        tester,
        "lowest faithful layer",
        "unit tests only for non-trivial",
        "component/browser tests",
        "small set of critical e2e journeys",
        "do not repeat the same assertion",
        "recorded policy approval",
        "sensitive/live/destructive boundary",
    )
    reject(tester, "one test per acceptance criterion minimum")

    developer = read("workflow/agents/sk-developer.md")
    require(
        developer,
        "when the workflow selected a separate tester",
        "otherwise implement the approved test strategy yourself",
        "early rendered visual loop",
        "exact-source screenshots",
        "macro visual gate",
        "before the broad safe/applicable suite",
        "specification-conformant but visibly weak",
    )

    acceptance = read("workflow/agents/sk-acceptance-reviewer.md")
    require(
        acceptance,
        "trusted green full-suite receipt matches exactly",
        "high-risk",
        "does not by itself justify repeating",
        "the only universal acceptance artifact",
        "never mutate task checkboxes after code review",
        "no placeholder",
        "visual: pass",
    )
    reject(
        acceptance,
        "create three artifacts",
        'write "no api changes"',
        'write "no operational tasks"',
        "or the change is high-risk",
    )

    tooling = read("workflow/agents/references/review-tooling.md")
    require(
        tooling,
        "gate receipts and reuse",
        "entire input closure is identical",
        "acceptance consumes the green receipt",
        "risk label alone never invalidates",
    )
    reject(tooling, "or the change is high-risk")

    architecture = read("workflow/agents/references/architecture-gates.md")
    require(
        architecture,
        "number is a review trigger",
        "forecast miss alone is not a blocker",
        "exact hard loc caps remain blockers",
    )

    ui_coder = read("shared/best-practices/ui/coder.md")
    ui_reviewer = read("shared/best-practices/ui/reviewer.md")
    composition = read("shared/best-practices/ui/composition-contract.md")
    rendered_evidence = read("shared/best-practices/ui/rendered-evidence.md")
    ui_lens = read("workflow/agents/review-steps/ui-ux.md")
    architect = read("workflow/agents/sk-architect.md")
    codestyle = read("utilities/sk-explore-codestyle/SKILL.md")
    require(
        ui_coder,
        "rendered composition gate",
        "one primary user task",
        "at most one visible primary action",
        "zero is correct",
        "composition-contract.md",
        "rendered-evidence.md",
    )
    require(
        ui_reviewer,
        "rendered inspection is mandatory",
        "source/grep alone yields `unverified`",
        "useful screenshots",
        "complete effective scroll extent",
        "screenshot-first comprehension pass",
        "objective composition quality",
        "contract alignment cannot override",
    )
    require(
        composition,
        "application chrome and effective scroll",
        "nearest domain canon",
        "at most one visible primary action",
        "zero is correct",
        "stable id",
        "long labels",
        "large or negative values",
        "literal user constraints",
        "forbidden alternatives",
    )
    require(
        rendered_evidence,
        "screenshot-first pass",
        "effective scroll extent",
        "semantic and geometry assertions",
        "rejecting fixture",
        "deliberate dom/style mutation",
        "changed screenshot baseline is not evidence",
        "record the first-pass conclusion before reading",
        "webkit",
    )
    require(
        ui_lens,
        "composition-contract.md",
        "rendered-evidence.md",
        "original/native resolution",
        "effective scroll owner/extent",
        "contract: pass | fail | unverified",
        "visual: pass | fail | unverified",
        "a correct implementation of a weak composition can still fail",
    )
    require(
        architect,
        "composition ownership matrix",
        "at most one visible primary action",
        "nearest domain canon",
        "first-viewport composition blueprint",
        "forbidden alternatives",
    )
    require(
        codestyle,
        "application shell/effective scroll owner",
        "merely available",
        "forbidden competing locations",
    )

    router = read("workflow/skills/sk-team/SKILL.md")
    quick = read("workflow/skills/sk-team-quick/SKILL.md")
    feature = read("workflow/skills/sk-team-feature/SKILL.md")
    status = read("workflow/skills/sk-team-status/SKILL.md")
    policy = read("workflow/agents/shared/workflow-charter-policy.md")
    require(
        router,
        "visual quality gate is mandatory",
        "root personally opens",
    )
    require(
        quick,
        "one full review round",
        "one targeted remediation verification",
        "root personally opens",
        "before any broad readiness battery",
        "do not rerun the broad suite",
    )
    require(
        feature,
        "visual macro gate",
        "before broad readiness gates",
        "one full review round",
        "one targeted remediation verification",
        "root personally opens",
    )
    reject(feature, "exceptional round 3", "automatic round 4")
    require(
        status,
        "engineering",
        "visual",
        "acceptance",
    )
    require(
        policy,
        "narrow successor recovery",
        "does not restart a full review",
    )


if __name__ == "__main__":
    main()
    print("OK: workflow efficiency contracts")
