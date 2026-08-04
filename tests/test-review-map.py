#!/usr/bin/env python3
"""Exercise deterministic review-map generation and coverage validation."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "shared" / "review-evidence"))

from review_map import build_review_map, validate_coverage  # noqa: E402


def evidence_entry(path: str, **overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "path": path,
        "base_path": path,
        "base_lines": 10,
        "base_read_status": "ok",
        "current_kind": "regular",
        "current_read_status": "ok",
        "current_lines": 12,
        "current_sha256": "a" * 64,
        "changed_intervals": [[2, 4]],
        "interval_status": "complete",
        "local_imports": [],
        "over_300": False,
        "crossed_300": False,
        "micro_file_candidate": False,
    }
    entry.update(overrides)
    return entry


def main() -> None:
    evidence = {
        "repository": "/tmp/example",
        "base": "base",
        "head": "head",
        "fingerprint": "b" * 64,
        "files": [
            evidence_entry("src/auth/session.py", local_imports=[{"line": 3}]),
            evidence_entry("tests/test_session.py"),
            evidence_entry("docs/ADR.md"),
            evidence_entry("package-lock.json"),
            evidence_entry("dist/app.js"),
            evidence_entry(
                "public/logo.png",
                current_read_status="unavailable",
                current_lines=None,
            ),
        ],
    }
    review_map = build_review_map(evidence)
    files = {entry["path"]: entry for entry in review_map["files"]}

    assert set(files) == {entry["path"] for entry in evidence["files"]}
    assert len(review_map["fingerprint"]) == 64
    assert files["src/auth/session.py"]["coverage_requirement"] == "full-content"
    assert "trust-boundary-lead" in files["src/auth/session.py"]["risk_tags"]
    assert "import-candidate" in files["src/auth/session.py"]["risk_tags"]
    assert "test" in files["tests/test_session.py"]["risk_tags"]
    assert "instruction" in files["docs/ADR.md"]["risk_tags"]
    assert files["package-lock.json"]["content_class"] == "dependency-lock"
    assert files["dist/app.js"]["content_class"] == "generated-candidate"
    assert files["public/logo.png"]["content_class"] == "binary"

    ledger = {
        "review_map_fingerprint": review_map["fingerprint"],
        "entries": [
            {
                "path": path,
                "reading_depth": entry["coverage_requirement"],
                "status": "reviewed",
                "purpose": "explicitly recorded",
                "changed_responsibilities": [],
                "placement_owner": "recorded",
                "risk_leads": [],
            }
            for path, entry in sorted(files.items())
        ],
    }
    receipt = validate_coverage(review_map, ledger)
    assert receipt == {
        "review_map_fingerprint": review_map["fingerprint"],
        "paths": len(files),
        "status": "valid",
    }

    broken = json.loads(json.dumps(ledger))
    broken["entries"] = broken["entries"][:-1]
    try:
        validate_coverage(review_map, broken)
    except ValueError as error:
        assert "coverage path mismatch" in str(error)
    else:
        raise AssertionError("missing coverage path was accepted")

    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        evidence_path = directory / "evidence.json"
        map_path = directory / "review-map.json"
        ledger_path = directory / "coverage-ledger.json"
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
        build = subprocess.run(
            [
                str(ROOT / "shared" / "review-evidence" / "review-map.sh"),
                "build",
                "--evidence",
                str(evidence_path),
                "--output",
                str(map_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        built = json.loads(map_path.read_text(encoding="utf-8"))
        assert json.loads(build.stdout)["fingerprint"] == built["fingerprint"]

        cli_ledger = json.loads(json.dumps(ledger))
        cli_ledger["review_map_fingerprint"] = built["fingerprint"]
        ledger_path.write_text(json.dumps(cli_ledger), encoding="utf-8")
        validate = subprocess.run(
            [
                str(ROOT / "shared" / "review-evidence" / "review-map.sh"),
                "validate",
                "--review-map",
                str(map_path),
                "--ledger",
                str(ledger_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(validate.stdout)["status"] == "valid"


if __name__ == "__main__":
    main()
    print("OK: review map")
