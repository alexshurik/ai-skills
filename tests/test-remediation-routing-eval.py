#!/usr/bin/env python3
"""Validate the remediation-routing behavioral eval specification."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "evals/remediation-routing/eval.json"

EXPECTED_AUTHORITIES = {
    "within_approved_design",
    "architecture_decision_required",
    "scope_decision_required",
    "investigation_required",
}
EXPECTED_ROUTES = {"Developer", "Architecture", "Scope Triage", "Investigation"}


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert config["version"] == 1
    assert config["suite"] == "remediation-routing"
    assert (CONFIG.parent / config["prompt"]).is_file()

    for relative in config["skill_inputs"]:
        assert (ROOT / relative).is_file(), relative

    cases = config["cases"]
    assert len(cases) >= 6
    assert len({case["id"] for case in cases}) == len(cases)
    assert {case["expected"]["remedy_authority"] for case in cases} == EXPECTED_AUTHORITIES
    assert {case["expected"]["route"] for case in cases} == EXPECTED_ROUTES

    for case in cases:
        assert case["input"].strip()
        expected = case["expected"]
        assert expected["must_preserve"]
        assert expected["must_not"]
        assert expected["remedy_authority"] not in case["input"]
        assert expected["route"] not in case["input"]

    prompt = " ".join((CONFIG.parent / config["prompt"]).read_text(encoding="utf-8").split())
    assert "Do not read or infer the case's expected result" in prompt
    assert "Do not design or implement the fix" in prompt


if __name__ == "__main__":
    main()
    print("OK: remediation-routing behavioral eval specification")
