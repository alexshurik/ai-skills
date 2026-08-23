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
    )
    reject(tester, "one test per acceptance criterion minimum")

    developer = read("workflow/agents/sk-developer.md")
    require(
        developer,
        "when the workflow selected a separate tester",
        "otherwise implement the approved test strategy yourself",
        "early rendered visual loop",
        "exact-source screenshots",
    )

    acceptance = read("workflow/agents/sk-acceptance-reviewer.md")
    require(
        acceptance,
        "trusted green full-suite receipt matches exactly",
        "high-risk",
        "the only universal acceptance artifact",
        "never mutate task checkboxes after code review",
        "no placeholder",
    )
    reject(
        acceptance,
        "create three artifacts",
        'write "no api changes"',
        'write "no operational tasks"',
    )

    tooling = read("workflow/agents/references/review-tooling.md")
    require(
        tooling,
        "gate receipts and reuse",
        "entire input closure is identical",
        "acceptance consumes the green receipt",
    )

    architecture = read("workflow/agents/references/architecture-gates.md")
    require(
        architecture,
        "number is a review trigger",
        "forecast miss alone is not a blocker",
        "exact hard loc caps remain blockers",
    )

    ui_coder = read("shared/best-practices/ui/coder.md")
    ui_reviewer = read("shared/best-practices/ui/reviewer.md")
    require(ui_coder, "rendered composition gate", "one primary user task", "one primary cta")
    require(
        ui_reviewer,
        "rendered inspection is mandatory",
        "source/grep alone yields `unverified`",
        "useful screenshots",
    )


if __name__ == "__main__":
    main()
    print("OK: workflow efficiency contracts")
