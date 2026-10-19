#!/usr/bin/env python3
"""Validate the adaptive workflow-routing behavioral golden eval."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "evals/workflow-routing"
CONFIG = EVAL_DIR / "eval.json"
VALIDATOR = EVAL_DIR / "validate.py"
RUNNER = EVAL_DIR / "run-codex-eval.sh"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=check,
        text=True,
        capture_output=True,
    )


def main() -> None:
    result = run(sys.executable, str(VALIDATOR), str(CONFIG))
    assert "workflow-routing eval specification" in result.stdout
    run("bash", "-n", str(RUNNER))

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    cases_doc = json.loads((EVAL_DIR / config["cases"]).read_text(encoding="utf-8"))
    goldens_doc = json.loads((EVAL_DIR / config["goldens"]).read_text(encoding="utf-8"))
    case_names = {case["name"] for case in cases_doc["cases"]}
    assert set(config["required_case_names"]) <= case_names
    case_ids = {case["name"]: case["id"] for case in cases_doc["cases"]}
    deli_decision = goldens_doc["goldens"][case_ids["deli-check-multi-screen-polish"]]
    assert deli_decision["route"] == "quick"
    assert deli_decision["visual_gate"] == "quick_dual_view_independent_plus_root"
    assert deli_decision["agent_shape"] == "developer_then_combined_reviewer"
    assurance = {decision["assurance"] for decision in goldens_doc["goldens"].values()}
    assert assurance == {"standard", "elevated"}

    runner = RUNNER.read_text(encoding="utf-8")
    assert "goldens.json" not in runner
    assert "--ephemeral" in runner
    assert "--ignore-user-config" in runner
    assert "--output-schema" in runner
    assert "FIXTURES_DIR/$case_id" in runner
    assert "expected_assertions_withheld" in runner

    with tempfile.TemporaryDirectory(prefix="sk-workflow-routing-eval-") as temp:
        responses = Path(temp)
        for case_id, golden in goldens_doc["goldens"].items():
            response = {"case_id": case_id, "decision": golden}
            (responses / f"{case_id}.json").write_text(
                json.dumps(response) + "\n",
                encoding="utf-8",
            )

        passing = run(
            sys.executable,
            str(VALIDATOR),
            str(CONFIG),
            "--responses",
            str(responses),
        )
        assert "decisions match goldens" in passing.stdout

        changed_id = "wr-001"
        changed_path = responses / f"{changed_id}.json"
        changed = json.loads(changed_path.read_text(encoding="utf-8"))
        changed["decision"]["route"] = "quick"
        changed_path.write_text(json.dumps(changed) + "\n", encoding="utf-8")
        rejected = run(
            sys.executable,
            str(VALIDATOR),
            str(CONFIG),
            "--responses",
            str(responses),
            check=False,
        )
        assert rejected.returncode != 0
        assert "decision mismatches" in rejected.stderr

    print("OK: adaptive workflow-routing behavioral golden eval")


if __name__ == "__main__":
    main()
