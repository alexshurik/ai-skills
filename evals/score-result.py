#!/usr/bin/env python3
"""Validate a recorded fresh-context behavioral evaluation result."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def validate_run_output(run: dict[str, Any], result_path: Path) -> None:
    output = result_path.parent / run["output"]
    if not output.is_file() or not output.read_text(encoding="utf-8").strip():
        raise ValueError(f"recorded run output missing: {output}")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    if digest != run.get("output_sha256"):
        raise ValueError(f"recorded run output hash mismatch: {output}")


def validate_runs(
    result: dict[str, Any],
    result_path: Path,
) -> dict[str, dict[str, Any]]:
    runs = {run["id"]: run for run in result["runs"]}
    if not runs or not all(run.get("fresh_context") for run in runs.values()):
        raise ValueError("every recorded behavioral run must use fresh context")
    if not all(run.get("expected_diagnoses_withheld") for run in runs.values()):
        raise ValueError("expected diagnoses leaked into at least one run")
    for run in runs.values():
        validate_run_output(run, result_path)
    return runs


def validate_assertions(
    config: dict[str, Any],
    result: dict[str, Any],
    runs: dict[str, dict[str, Any]],
) -> tuple[int, int]:
    required = set(config["required_assertions"])
    assertions = {item["assertion"]: item for item in result["assertions"]}
    if set(assertions) != required:
        raise ValueError("recorded assertions do not match eval.yaml")
    for assertion, item in assertions.items():
        if not item.get("passed"):
            raise ValueError(f"failed assertion: {assertion}")
        if item.get("run") not in runs or not item.get("evidence"):
            raise ValueError(f"assertion lacks run/evidence: {assertion}")
    return sum(bool(item["passed"]) for item in assertions.values()), len(required)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("eval_config", type=Path)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()

    config = load(args.eval_config)
    result = load(args.result)
    runs = validate_runs(result, args.result)
    final_score, required_count = validate_assertions(config, result, runs)
    if final_score != result["scores"]["final"]:
        raise ValueError("recorded final score is inconsistent")
    if final_score != required_count:
        raise ValueError(f"behavioral regression score is {final_score}/{required_count}")
    print(
        f"OK: behavioral eval {result['scores']['baseline']}/{required_count}"
        f" -> {final_score}/{required_count}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
