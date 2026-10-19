#!/usr/bin/env python3
"""Keep the real-failure review corpus wired into skill verification."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "evals" / "review-enforcement"


def main() -> None:
    result = subprocess.run(
        [sys.executable, str(EVAL_DIR / "validate.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "review-enforcement golden corpus" in result.stdout
    cases = json.loads((EVAL_DIR / "cases.json").read_text(encoding="utf-8"))["cases"]
    goldens = json.loads((EVAL_DIR / "goldens.json").read_text(encoding="utf-8"))["goldens"]
    by_name = {case["name"]: goldens[case["id"]] for case in cases}
    assert by_name["deli-mixed-cbv-route-owner"]["verdict"] == "changes_requested"
    assert by_name["spotty-stale-final-snapshot"]["verdict"] == "unverified"
    assert by_name["cohesive-large-file-approved-keep"]["verdict"] == "approved"
    assert by_name["module-helper-beside-cbv"]["gate_reason"] == "no_route_owner_conflict"
    assert by_name["project-approved-multiple-route-owners"]["verdict"] == "approved"
    print("OK: review-enforcement eval contract")


if __name__ == "__main__":
    main()
