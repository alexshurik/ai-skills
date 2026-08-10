#!/usr/bin/env python3
"""Exercise deterministic review-map generation and lens-scope validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "shared" / "review-evidence"))

from review_map import build_review_map, validate_scopes  # noqa: E402


def evidence_entry(path: str, **overrides: object) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": path,
        "base_path": path,
        "base_lines": 10,
        "base_read_status": "ok",
        "base_blob_oid": "b" * 40,
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


def assert_rejects_tampered_map(
    review_map: dict[str, Any],
    manifests: list[dict[str, Any]],
) -> None:
    tampered_maps = [json.loads(json.dumps(review_map)) for _ in range(2)]
    tampered_maps[0]["files"].pop()
    tampered_maps[1]["files"][0]["current_sha256"] = "tampered"
    for tampered in tampered_maps:
        assert_validation_error(
            tampered,
            manifests,
            "review map fingerprint mismatch",
        )


def assert_validation_error(
    review_map: dict[str, Any],
    manifests: list[dict[str, Any]],
    expected_error: str,
) -> None:
    try:
        validate_scopes(review_map, manifests)
    except ValueError as error:
        assert expected_error in str(error)
    else:
        raise AssertionError(f"invalid scope was accepted: {expected_error}")


def fixture() -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
    tuple[str, ...],
    dict[str, Any],
]:
    evidence: dict[str, Any] = {
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
    lenses = ("architecture-design", "correctness-safety", "engineering-quality")
    manifests = build_manifests(review_map, files, lenses)
    return review_map, files, manifests, lenses, evidence


def build_manifests(
    review_map: dict[str, Any],
    files: dict[str, dict[str, Any]],
    lenses: tuple[str, ...],
) -> list[dict[str, Any]]:
    return [
        {
            "lens": lens,
            "review_map_fingerprint": review_map["fingerprint"],
            "entries": [
                {
                    "path": path,
                    "reading_depth": entry["coverage_requirement"],
                    "reason": f"assigned to {lens}",
                    "base_blob_oid": entry["base_blob_oid"],
                    "current_sha256": entry["current_sha256"],
                    "risk_leads": entry["risk_tags"],
                }
                for index, (path, entry) in enumerate(sorted(files.items()))
                if index % len(lenses) == lens_index
            ],
        }
        for lens_index, lens in enumerate(lenses)
    ]


def assert_map_classification(
    review_map: dict[str, Any], files: dict[str, dict[str, Any]], evidence: dict[str, Any]
) -> None:
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


def assert_invalid_scope_variants(
    review_map: dict[str, Any], manifests: list[dict[str, Any]]
) -> None:
    variants = (
        ("scope path mismatch", missing_scope(manifests)),
        ("stale current_sha256", stale_scope(manifests)),
        ("invalid or duplicate scope lens", duplicate_lens_scope(manifests)),
        ("authored content is metadata-only", metadata_only_scope(manifests)),
    )
    for expected_error, invalid in variants:
        assert_validation_error(review_map, invalid, expected_error)


def clone_manifests(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], json.loads(json.dumps(manifests)))


def missing_scope(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    broken = clone_manifests(manifests)
    broken[-1]["entries"] = broken[-1]["entries"][:-1]
    return broken


def stale_scope(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stale = clone_manifests(manifests)
    stale[0]["entries"][0]["current_sha256"] = "stale"
    return stale


def duplicate_lens_scope(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    duplicate = clone_manifests(manifests)
    duplicate[-1]["lens"] = duplicate[0]["lens"]
    return duplicate


def metadata_only_scope(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metadata_only = clone_manifests(manifests)
    for manifest in metadata_only:
        for entry in manifest["entries"]:
            if entry["path"] == "src/auth/session.py":
                entry["reading_depth"] = "metadata-only"
    return metadata_only


def main() -> None:
    review_map, files, manifests, lenses, evidence = fixture()
    assert_map_classification(review_map, files, evidence)
    receipt = validate_scopes(review_map, manifests)
    assert receipt == {
        "review_map_fingerprint": review_map["fingerprint"],
        "lenses": sorted(lenses),
        "paths": len(files),
        "status": "valid",
    }
    assert_rejects_tampered_map(review_map, manifests)
    assert_invalid_scope_variants(review_map, manifests)

    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        evidence_path = directory / "evidence.json"
        map_path = directory / "review-map.json"
        manifest_paths = [directory / f"{lens}.json" for lens in lenses]
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
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

        cli_manifests = json.loads(json.dumps(manifests))
        for manifest, manifest_path in zip(cli_manifests, manifest_paths, strict=True):
            manifest["review_map_fingerprint"] = built["fingerprint"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        validate = subprocess.run(
            [
                str(ROOT / "shared" / "review-evidence" / "review-map.sh"),
                "validate-scopes",
                "--review-map",
                str(map_path),
                *[
                    argument
                    for manifest_path in manifest_paths
                    for argument in ("--manifest", str(manifest_path))
                ],
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(validate.stdout)["status"] == "valid"


if __name__ == "__main__":
    main()
    print("OK: review map")
