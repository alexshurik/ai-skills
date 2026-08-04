#!/usr/bin/env python3
"""Validate integrity and pass status of a recorded behavioral eval result."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
GIT_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def require_unique_strings(values: Any, label: str) -> list[str]:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{label} must be a non-empty list")
    if not all(isinstance(value, str) and value for value in values):
        raise ValueError(f"{label} must contain non-empty strings")
    if len(set(values)) != len(values):
        raise ValueError(f"{label} contains duplicates")
    return values


def resolve_output(result_path: Path, output_value: Any) -> Path:
    if not isinstance(output_value, str) or not output_value:
        raise ValueError("recorded run output must be a non-empty relative path")
    relative = Path(output_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(
            f"recorded run output escapes result directory: {output_value}"
        )
    result_root = result_path.parent.resolve()
    candidate = result_root / relative
    current = result_root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"recorded run output traverses a symlink: {output_value}")
    output = candidate.resolve()
    if output == result_root or result_root not in output.parents:
        raise ValueError(
            f"recorded run output escapes result directory: {output_value}"
        )
    return output


def validate_run_output(run: dict[str, Any], result_path: Path) -> None:
    output = resolve_output(result_path, run.get("output"))
    if not output.is_file():
        raise ValueError(f"recorded run output missing or unsafe: {output}")
    if not output.read_text(encoding="utf-8").strip():
        raise ValueError(f"recorded run output is empty: {output}")
    expected_digest = run.get("output_sha256")
    if not isinstance(expected_digest, str) or not SHA256_PATTERN.fullmatch(
        expected_digest
    ):
        raise ValueError(f"recorded run output has invalid SHA-256: {output}")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    if digest != expected_digest:
        raise ValueError(f"recorded run output hash mismatch: {output}")


def validate_runs(
    result: dict[str, Any], result_path: Path
) -> dict[str, dict[str, Any]]:
    run_values = result.get("runs")
    if not isinstance(run_values, list) or not run_values:
        raise ValueError("runs must be a non-empty list")
    if not all(isinstance(run, dict) for run in run_values):
        raise ValueError("every run must be an object")
    run_ids = [run.get("id") for run in run_values]
    require_unique_strings(run_ids, "run IDs")
    runs = dict(zip(run_ids, run_values))
    for run in runs.values():
        if run.get("fresh_context") is not True:
            raise ValueError("every recorded behavioral run must use fresh context")
        if run.get("expected_diagnoses_withheld") is not True:
            raise ValueError("expected diagnoses leaked into at least one run")
        validate_run_output(run, result_path)
    return runs


def validate_provenance(result: dict[str, Any]) -> None:
    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("result provenance must be an object")
    if provenance.get("semantic_evaluator") != "manual":
        raise ValueError("semantic_evaluator must explicitly be manual")
    reproducible = provenance.get("reproducible")
    if not isinstance(reproducible, bool):
        raise ValueError("provenance.reproducible must be a boolean")
    skills_source = provenance.get("skills_source")
    if not isinstance(skills_source, dict):
        raise ValueError("provenance.skills_source must be an object")
    if not isinstance(skills_source.get("dirty"), bool):
        raise ValueError("provenance.skills_source.dirty must be a boolean")
    if reproducible:
        commit = skills_source.get("commit")
        if not isinstance(commit, str) or not GIT_COMMIT_PATTERN.fullmatch(commit):
            raise ValueError("reproducible result requires a full skills commit SHA")
        if skills_source.get("dirty") is not False:
            raise ValueError("reproducible result requires a clean skills source")
        for field in ("model", "codex_cli"):
            if not isinstance(provenance.get(field), str) or not provenance[field]:
                raise ValueError(f"reproducible result requires provenance.{field}")
    else:
        limitations = provenance.get("limitations")
        require_unique_strings(limitations, "provenance limitations")


def validate_assertions(
    config: dict[str, Any],
    result: dict[str, Any],
    runs: dict[str, dict[str, Any]],
) -> tuple[int, int]:
    required = require_unique_strings(
        config.get("required_assertions"), "required assertions"
    )
    assertion_values = result.get("assertions")
    if not isinstance(assertion_values, list):
        raise ValueError("assertions must be a list")
    if not all(isinstance(item, dict) for item in assertion_values):
        raise ValueError("every assertion must be an object")
    assertion_ids = [item.get("assertion") for item in assertion_values]
    require_unique_strings(assertion_ids, "recorded assertions")
    assertions = dict(zip(assertion_ids, assertion_values))
    if set(assertions) != set(required):
        raise ValueError("recorded assertions do not match eval config")
    for assertion, item in assertions.items():
        if not isinstance(item.get("passed"), bool):
            raise ValueError(f"assertion pass status is not a boolean: {assertion}")
        if item.get("run") not in runs:
            raise ValueError(f"assertion references an unknown run: {assertion}")
        if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            raise ValueError(f"assertion lacks evidence: {assertion}")
    return sum(bool(item["passed"]) for item in assertions.values()), len(required)


def validate_scores(result: dict[str, Any], final_score: int, total: int) -> None:
    scores = result.get("scores")
    if not isinstance(scores, dict):
        raise ValueError("scores must be an object")
    score_names = ("baseline", "first_full_upgraded_review", "final")
    values = [scores.get(name) for name in score_names]
    if not all(isinstance(value, int) and 0 <= value <= total for value in values):
        raise ValueError("recorded scores must be integers within the assertion range")
    if values != sorted(values):
        raise ValueError("recorded score progression is inconsistent")
    if scores["final"] != final_score:
        raise ValueError("recorded final score is inconsistent")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("eval_config", type=Path)
    parser.add_argument("result", type=Path)
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="return an error unless every required assertion passed",
    )
    args = parser.parse_args()

    config = load(args.eval_config)
    result = load(args.result)
    if config.get("version") != 2 or result.get("version") != 2:
        raise ValueError("unsupported eval config or result version")
    if result.get("suite") != config.get("suite"):
        raise ValueError("result suite does not match eval config")
    validate_provenance(result)
    runs = validate_runs(result, args.result)
    final_score, required_count = validate_assertions(config, result, runs)
    validate_scores(result, final_score, required_count)
    if args.require_pass and final_score != required_count:
        raise ValueError(
            f"recorded behavioral regression score is {final_score}/{required_count}"
        )
    print(
        "OK: recorded eval result integrity "
        f"(manual score {result['scores']['baseline']}/{required_count}"
        f" -> {final_score}/{required_count})"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
