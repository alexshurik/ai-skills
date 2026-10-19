#!/usr/bin/env python3
"""Validate the review-enforcement corpus and its held-out goldens."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = ROOT / "cases.json"
GOLDENS = ROOT / "goldens.json"
VERDICTS = {"approved", "changes_requested", "unverified"}


def main() -> None:
    cases_doc = json.loads(CASES.read_text(encoding="utf-8"))
    goldens_doc = json.loads(GOLDENS.read_text(encoding="utf-8"))
    assert cases_doc["suite"] == goldens_doc["suite"] == "review-enforcement"
    cases = cases_doc["cases"]
    ids = [case["id"] for case in cases]
    names = [case["name"] for case in cases]
    assert len(ids) == len(set(ids)) and len(names) == len(set(names))
    assert set(ids) == set(goldens_doc["goldens"])
    assert any("negative_control" in case["coverage"] for case in cases)
    coverage = {signal for case in cases for signal in case["coverage"]}
    for required in (
        "route_owner.mixed",
        "route_owner.observation_not_verdict",
        "snapshot.stale",
        "lens.missing",
        "static.semantic_output",
        "structure.second_responsibility",
        "tasks.incomplete",
        "scale.large",
    ):
        assert required in coverage, required
    for case in cases:
        assert case["input"].strip() and case["coverage"]
        golden = goldens_doc["goldens"][case["id"]]
        assert golden["verdict"] in VERDICTS
        assert golden["gate_reason"] and golden["required_action"]
    print("OK: review-enforcement golden corpus")


if __name__ == "__main__":
    main()
