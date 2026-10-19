#!/usr/bin/env python3
"""Validate and score the adaptive workflow-routing golden eval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASES = {
    "setup",
    "workspace_resolution",
    "scope_lock",
    "planning",
    "readiness",
    "execution_gate",
    "execution",
    "macro_visual_preflight",
    "remediation_verification",
    "bounded_recovery",
    "finish",
}
USER_INPUT_APPROVALS = {
    "ask_compact_charter",
    "wait_scope_lock",
    "wait_execution",
    "typed_stop",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def local_file(eval_dir: Path, value: object, field: str) -> Path:
    assert isinstance(value, str) and value, f"{field} must be a non-empty string"
    relative = Path(value)
    assert relative.name == value and not relative.is_absolute(), (
        f"{field} must be a local filename: {value}"
    )
    path = eval_dir / relative
    assert path.is_file(), f"missing {field}: {path}"
    return path


def decision_contract(schema: dict[str, Any]) -> tuple[set[str], dict[str, set[Any]]]:
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"case_id", "decision"}
    decision = schema["properties"]["decision"]
    assert decision["type"] == "object"
    assert decision["additionalProperties"] is False
    required = set(decision["required"])
    assert required == set(decision["properties"])

    values: dict[str, set[Any]] = {}
    for field, contract in decision["properties"].items():
        if contract["type"] == "boolean":
            values[field] = {False, True}
        else:
            assert contract["type"] == "string" and contract.get("enum"), field
            values[field] = set(contract["enum"])
    return required, values


def validate_decision(
    decision: object,
    required: set[str],
    values: dict[str, set[Any]],
    context: str,
) -> dict[str, Any]:
    assert isinstance(decision, dict), f"{context}: decision must be an object"
    assert set(decision) == required, (
        f"{context}: decision fields differ: "
        f"missing={sorted(required - set(decision))}, "
        f"extra={sorted(set(decision) - required)}"
    )
    for field, value in decision.items():
        assert value in values[field], f"{context}: invalid {field}: {value!r}"
    return decision


def validate_invariants(case_id: str, decision: dict[str, Any]) -> None:
    approval = decision["approval"]
    stop_reason = decision["stop_reason"]
    needs_input = decision["requires_user_input"]

    assert needs_input == (approval in USER_INPUT_APPROVALS), (
        f"{case_id}: requires_user_input conflicts with approval"
    )
    assert (approval == "typed_stop") == (stop_reason != "none"), (
        f"{case_id}: typed stop and stop_reason must agree"
    )
    if decision["scope_action"] == "await_scope_delta":
        assert decision["route_change"] == "quick_to_full", case_id
        assert stop_reason == "decision.material_scope", case_id
        assert decision["agent_shape"] == "blocked_before_dispatch", case_id
    if decision["route_change"] == "micro_to_quick":
        assert decision["route"] == "quick", case_id
    if decision["route_change"] == "quick_to_full":
        assert decision["route"] == "full", case_id
    if decision["route"] == "micro":
        assert decision["agent_shape"] == "root_only", case_id
    if decision["visual_gate"] == "micro_root_single_view":
        assert decision["route"] == "micro", case_id
    if decision["visual_gate"] == "quick_dual_view_independent_plus_root":
        assert decision["route"] == "quick", case_id
    if decision["visual_gate"] == "full_dual_view_lens_plus_root":
        assert decision["route"] == "full", case_id
    if decision["broad_suite"] == "defer_until_visual_pass":
        assert decision["visual_gate"] != "not_applicable", case_id
        assert approval == "return_to_implementation", case_id
    if decision["broad_suite"] == "targeted_changed_inputs_reuse_exact_receipt":
        assert decision["agent_shape"] in {
            "impacted_lenses_only",
            "blocked_before_dispatch",
        }, case_id
    if approval == "finish_without_reapproval":
        assert decision["destination"] in {"commit", "pr", "merge", "deploy"}, case_id
        assert decision["broad_suite"] == "reuse_exact_receipt_without_rerun", case_id


def decision_coverage(decision: dict[str, Any]) -> set[str]:
    coverage = {
        f"route.{decision['route']}",
        f"authorization.{decision['authorization']}",
        f"assurance.{decision['assurance']}",
        f"workspace.{decision['workspace']}",
        f"destination.{decision['destination']}",
    }
    approval_tags = {
        "ask_compact_charter": "approval.compact-charter",
        "wait_execution": "approval.execution-gate",
        "continue_by_policy": "approval.policy-continue",
        "finish_without_reapproval": "approval.no-terminal-reapproval",
    }
    visual_tags = {
        "micro_root_single_view": "visual.micro",
        "quick_dual_view_independent_plus_root": "visual.quick",
        "full_dual_view_lens_plus_root": "visual.full",
    }
    agent_tags = {
        "root_only": {"agent.root-only"},
        "developer_then_combined_reviewer": {"agent.quick-pair"},
        "full_roles_three_core": {"agent.full-core"},
        "full_roles_three_core_plus_ui": {
            "agent.full-core",
            "agent.conditional-ui",
        },
        "impacted_lenses_only": {"agent.impacted-only"},
        "blocked_before_dispatch": set(),
    }
    verification_tags = {
        "focused_only": "verification.focused",
        "run_once_before_review": "verification.broad-once",
        "defer_until_visual_pass": "verification.visual-before-broad",
        "targeted_changed_inputs_reuse_exact_receipt": "verification.receipt-reuse",
        "reuse_exact_receipt_without_rerun": "verification.receipt-reuse",
    }
    stop_tags = {
        "decision.material_scope": "stop.material-scope",
        "boundary.external_access": "stop.external-access",
        "boundary.terminal_not_authorized": "stop.terminal-not-authorized",
        "budget.exhausted": "stop.budget-exhausted",
    }

    for mapping, value in (
        (approval_tags, decision["approval"]),
        (visual_tags, decision["visual_gate"]),
        (verification_tags, decision["broad_suite"]),
        (stop_tags, decision["stop_reason"]),
    ):
        if value in mapping:
            coverage.add(mapping[value])
    coverage.update(agent_tags[decision["agent_shape"]])
    if decision["visual_gate"] == "full_dual_view_lens_plus_root":
        coverage.add("agent.conditional-ui")
    if decision["route_change"] != "none":
        coverage.add("scope.upward-escalation")
    if decision["scope_action"] == "await_scope_delta":
        coverage.add("scope.material-delta-stop")
    return coverage


def validate_suite(config_path: Path) -> tuple[
    Path,
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    set[str],
    dict[str, set[Any]],
]:
    config_path = config_path.resolve()
    eval_dir = config_path.parent
    repo_root = eval_dir.parents[1]
    config = load_json(config_path)

    assert config["version"] == 1
    assert config["suite"] == "workflow-routing"
    expected_config_fields = {
        "version",
        "suite",
        "prompt",
        "cases",
        "goldens",
        "response_schema",
        "validator",
        "runner",
        "skill_inputs",
        "required_case_names",
        "required_coverage",
    }
    assert set(config) == expected_config_fields

    prompt_path = local_file(eval_dir, config["prompt"], "prompt")
    cases_path = local_file(eval_dir, config["cases"], "cases")
    goldens_path = local_file(eval_dir, config["goldens"], "goldens")
    schema_path = local_file(eval_dir, config["response_schema"], "response_schema")
    assert local_file(eval_dir, config["validator"], "validator") == Path(__file__).resolve()
    local_file(eval_dir, config["runner"], "runner")

    prompt = prompt_path.read_text(encoding="utf-8")
    assert "Return only the JSON object" in prompt
    assert "Do not search outside the fixture" in prompt

    inputs = config["skill_inputs"]
    assert isinstance(inputs, list) and inputs
    assert len(inputs) == len(set(inputs))
    for relative in inputs:
        assert isinstance(relative, str) and relative
        assert not Path(relative).is_absolute() and ".." not in Path(relative).parts
        assert (repo_root / relative).is_file(), relative

    cases_doc = load_json(cases_path)
    goldens_doc = load_json(goldens_path)
    schema = load_json(schema_path)
    assert cases_doc["version"] == goldens_doc["version"] == 1
    assert cases_doc["suite"] == goldens_doc["suite"] == config["suite"]
    assert set(cases_doc) == {"version", "suite", "cases"}
    assert set(goldens_doc) == {"version", "suite", "goldens"}

    cases = cases_doc["cases"]
    goldens = goldens_doc["goldens"]
    assert isinstance(cases, list) and len(cases) >= 12
    assert isinstance(goldens, dict)
    case_ids = [case["id"] for case in cases]
    case_names = [case["name"] for case in cases]
    assert len(case_ids) == len(set(case_ids))
    assert len(case_names) == len(set(case_names))
    assert set(case_ids) == set(goldens)
    assert set(config["required_case_names"]) <= set(case_names)

    coverage: set[str] = set()
    required, values = decision_contract(schema)
    for case in cases:
        assert set(case) == {"id", "name", "phase", "input", "coverage"}, case.get("id")
        case_id = case["id"]
        assert case_id and case_id == case_id.lower() and "_" not in case_id
        assert case["name"] and case["name"] == case["name"].lower(), case_id
        assert case["phase"] in PHASES, case_id
        assert isinstance(case["input"], str) and case["input"].strip(), case_id
        assert isinstance(case["coverage"], list) and case["coverage"], case_id
        assert len(case["coverage"]) == len(set(case["coverage"])), case_id
        coverage.update(case["coverage"])
        assert case_id not in prompt, case_id
        assert case["name"] not in prompt, case_id
        assert case["input"] not in prompt, case_id
        decision = validate_decision(goldens[case_id], required, values, case_id)
        validate_invariants(case_id, decision)
        assert set(case["coverage"]) == decision_coverage(decision), (
            f"{case_id}: coverage does not match golden decision"
        )

    assert coverage == set(config["required_coverage"]), (
        "declared required coverage differs from case coverage"
    )
    return eval_dir, cases, goldens, required, values


def score_responses(
    responses_dir: Path,
    cases: list[dict[str, Any]],
    goldens: dict[str, dict[str, Any]],
    required: set[str],
    values: dict[str, set[Any]],
) -> None:
    expected_ids = {case["id"] for case in cases}
    assert responses_dir.is_dir(), f"responses directory not found: {responses_dir}"
    response_paths = {path.stem: path for path in responses_dir.glob("*.json")}
    assert set(response_paths) == expected_ids, (
        "response files differ: "
        f"missing={sorted(expected_ids - set(response_paths))}, "
        f"extra={sorted(set(response_paths) - expected_ids)}"
    )

    failures: list[str] = []
    for case_id in sorted(expected_ids):
        response = load_json(response_paths[case_id])
        assert isinstance(response, dict), f"{case_id}: response must be an object"
        assert set(response) == {"case_id", "decision"}, (
            f"{case_id}: response fields must be case_id and decision only"
        )
        assert response["case_id"] == case_id, (
            f"{case_id}: response case_id is {response['case_id']!r}"
        )
        decision = validate_decision(response["decision"], required, values, case_id)
        validate_invariants(case_id, decision)
        for field in sorted(required):
            actual = decision[field]
            expected = goldens[case_id][field]
            if actual != expected:
                failures.append(
                    f"{case_id}.{field}: expected {expected!r}, got {actual!r}"
                )

    assert not failures, "decision mismatches:\n" + "\n".join(failures)
    print(f"OK: {len(expected_ids)} workflow-routing decisions match goldens")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--responses", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _, cases, goldens, required, values = validate_suite(args.config)
    if args.responses is None:
        print(f"OK: workflow-routing eval specification ({len(cases)} cases)")
        return
    score_responses(args.responses.resolve(), cases, goldens, required, values)


if __name__ == "__main__":
    main()
