#!/usr/bin/env python3
"""Lock the adaptive router, authorization boundaries, and mnemonic UI contract."""

from __future__ import annotations

import json
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
    manifest = json.loads(read("skills-manifest.yaml"))
    catalog = {item["name"]: item["source"] for item in manifest["catalog"]}
    assert catalog["sk-team"] == "workflow/skills/sk-team"

    router = read("workflow/skills/sk-team/SKILL.md")
    policy = read("workflow/agents/shared/workflow-charter-policy.md")
    feature = read("workflow/skills/sk-team-feature/SKILL.md")
    quick = read("workflow/skills/sk-team-quick/SKILL.md")
    help_text = read("workflow/skills/sk-team-help/SKILL.md")
    status = read("workflow/skills/sk-team-status/SKILL.md")
    product = read("workflow/agents/sk-product-analyst.md")
    architect = read("workflow/agents/sk-architect.md")
    tester = read("workflow/agents/sk-tester.md")

    require(
        router,
        "super-short / micro",
        "short / quick",
        "full",
        "do not ask the workflow choices again",
        "never inherit yolo",
        "record the matching terminal receipt",
    )
    for label in (
        "Подбери сам",
        "Суперкороткий",
        "Короткий",
        "Полный",
        "Каждый этап",
        "Только важное",
        "YOLO",
        "Текущая",
        "Отдельная",
        "Выбрать безопасно",
        "Только разобраться",
        "Оставить правки",
        "Коммит",
        "PR",
        "Merge",
        "Deploy",
    ):
        assert label in policy, label

    require(
        policy,
        "manual",
        "checkpoints",
        "yolo",
        "micro → quick → full",
        "required_fix",
        "within_approved_design",
        "one run/objective",
        "the selected destination is authority",
        "visual quality is not an optional assurance mode",
        "narrow successor recovery",
    )
    for reason in (
        "decision.material_product",
        "decision.material_scope",
        "boundary.external_access",
        "boundary.destructive_or_irreversible",
        "boundary.live_cost_or_value",
        "boundary.terminal_not_authorized",
        "evidence.unverifiable",
        "budget.exhausted",
        "control.user_reset",
    ):
        assert reason in policy, reason

    require(
        feature,
        "gate behavior",
        "schema-v3",
        "selected destination counts as explicit authority",
    )
    reject(
        feature,
        "never auto-proceed between phases",
        "every completed phase requires explicit user approval",
        "worktree-isolated multi-agent feature workflow",
    )
    require(quick, "manual or checkpoints", "in yolo", "schema-v3 runtime state")
    reject(quick, "wait for explicit user approval before sending")
    require(product, "valid yolo policy confirmation", "genuine material")
    require(architect, "valid yolo policy", "no `sd-*` addition")
    require(tester, "recorded policy approval", "sensitive/live/destructive boundary")
    require(
        help_text,
        "start charter",
        "super-short",
        "important checkpoints",
        "visual quality is mandatory",
    )
    require(
        status,
        "legacy_v2",
        "delivery receipt",
        "invoke `sk-team`",
        "engineering",
        "visual",
        "acceptance",
    )

    state_schema = json.loads(read("workflow/agents/shared/runtime-state/state.schema.json"))
    event_schema = json.loads(read("workflow/agents/shared/runtime-state/event.schema.json"))
    assert state_schema["properties"]["schema_version"]["const"] == 3
    assert event_schema["properties"]["event_schema_version"]["const"] == 2


if __name__ == "__main__":
    main()
    print("OK: workflow charter contracts")
