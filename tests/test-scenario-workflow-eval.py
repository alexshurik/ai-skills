#!/usr/bin/env python3
"""Validate raw case integrity; this is not an independent behavioral evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "evals" / "scenario-workflow"


def confined_file(base: Path, relative: str) -> Path:
    path = base / relative
    assert not Path(relative).is_absolute(), relative
    assert path.resolve().is_relative_to(base.resolve()), relative
    assert path.is_file() and not path.is_symlink(), relative
    return path


def check_case(case: dict[str, Any]) -> None:
    assert case["request"].strip() and case["criteria"] and case["sources"], case["id"]
    for source in case["sources"]:
        confined_file(ROOT, source)
        assert "goldens" not in source, source
    fixture = EVAL_DIR / case["fixture_root"]
    assert fixture.resolve().is_relative_to((EVAL_DIR / "cases").resolve()), fixture
    listed = [item["path"] for item in case["files"]]
    assert len(listed) == len(set(listed)), case["id"]
    # The raw project config makes repository Ruff checks write an ignored cache here.
    actual = {
        str(path.relative_to(fixture))
        for path in fixture.rglob("*")
        if path.is_file() and ".ruff_cache" not in path.relative_to(fixture).parts
    }
    assert actual == set(listed), (case["id"], actual.symmetric_difference(listed))
    for item in case["files"]:
        path = confined_file(fixture, item["path"])
        assert "goldens" not in item["path"], item
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], path


def main() -> None:
    corpus = json.loads((EVAL_DIR / "cases.json").read_text(encoding="utf-8"))
    rubrics = json.loads((EVAL_DIR / "goldens.json").read_text(encoding="utf-8"))
    assert corpus["version"] == rubrics["version"] == 1
    assert corpus["suite"] == rubrics["suite"] == "scenario-workflow"
    cases = corpus["cases"]
    identifiers = [case["id"] for case in cases]
    assert len(identifiers) == len(set(identifiers)) == 6
    assert set(identifiers) == set(rubrics["goldens"])
    for case in cases:
        check_case(case)
        rubric = rubrics["goldens"][case["id"]]
        for key in ("required", "forbidden", "artifact_checks"):
            assert rubric[key] and all(item.strip() for item in rubric[key]), (case["id"], key)
        for name, digest in rubric.get("preserved_sha256", {}).items():
            path = confined_file(EVAL_DIR / case["fixture_root"], name)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
    print("OK: scenario-workflow corpus integrity; behavioral evaluation remains separate")


if __name__ == "__main__":
    main()
