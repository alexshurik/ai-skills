#!/usr/bin/env python3
"""Exercise fail-closed approval checks with realistic stale/missing evidence."""

from __future__ import annotations

import json
import sys
import tempfile
from argparse import Namespace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "shared" / "review-evidence"))

from review_gate import validate, validate_change_scale, validate_static_analysis  # noqa: E402
from review_map import build_review_map, canonical_fingerprint  # noqa: E402


def expect_error(expected: str, callback: Any) -> None:
    try:
        callback()
    except ValueError as error:
        assert expected in str(error), error
    else:
        raise AssertionError(f"expected approval failure: {expected}")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def evidence() -> dict[str, Any]:
    return {
        "repository": "/tmp/example",
        "base": "base",
        "head": "head",
        "fingerprint": "e" * 64,
        "files": [
            {
                "path": "src/api.py",
                "base_path": "src/api.py",
                "base_lines": 280,
                "base_read_status": "ok",
                "base_blob_oid": "b" * 40,
                "current_kind": "regular",
                "current_read_status": "ok",
                "current_lines": 330,
                "current_sha256": "a" * 64,
                "changed_intervals": [[281, 330]],
                "interval_status": "ok",
                "local_imports": [],
                "over_300": True,
                "crossed_300": True,
                "micro_file_candidate": False,
                "route_ownership_observations": [
                    {
                        "kind": "competing_route_owners",
                        "framework": "fastapi",
                        "router": "router",
                        "owners": [
                            {
                                "kind": "module_functions",
                                "handlers": [{"name": "create", "line": 12}],
                            },
                            {
                                "kind": "decorated_classes",
                                "decorator": "cbv",
                                "classes": [{"class": "ViewSet", "line": 20, "methods": []}],
                            },
                        ],
                    }
                ],
            }
        ],
        "review_policy": {
            "path_classes": {},
            "path_class_reasons": {},
            "preserved_baseline_hashes": {},
            "ui_ux_required": False,
            "ui_ux_reason": "backend-only fixture",
            "ui_impact_paths": [],
            "additional_structure_leads": [
                {
                    "path": "src/api.py",
                    "kind": "second_responsibility",
                    "reason": "The change adds provider coordination to transport.",
                    "authority": "developer pre-write handoff",
                }
            ],
        },
    }


def manifests(review_map: dict[str, Any]) -> list[dict[str, Any]]:
    item = review_map["files"][0]
    return [
        {
            "lens": lens,
            "review_map_fingerprint": review_map["fingerprint"],
            "entries": [
                {
                    "path": item["path"],
                    "reading_depth": "full-content",
                    "reason": f"fixture assignment to {lens}",
                    "base_blob_oid": item["base_blob_oid"],
                    "current_sha256": item["current_sha256"],
                    "risk_leads": item["risk_tags"],
                }
            ],
        }
        for lens in ("architecture-design", "correctness-safety", "engineering-quality")
    ]


def dispositions(review_map: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_map_fingerprint": review_map["fingerprint"],
        "structural": [
            {
                "path": "src/api.py",
                "lead": lead,
                "decision": "keep_approved",
                "rationale": (
                    "Approved design deliberately separates collection and item route owners."
                    if lead == "competing_route_owners"
                    else "The approved design keeps this structure cohesive."
                ),
                "authority": "approved design D-1",
            }
            for lead in (
                "over_300",
                "crossed_300",
                "competing_route_owners",
                "second_responsibility",
            )
        ],
        "static_analysis": [
            {
                "dimension": "duplication",
                "tool": "jscpd",
                "decision": "baseline",
                "rationale": "The clone is unchanged test-fixture baseline.",
                "authority": "review finding QUAL-BASE-1",
            }
        ],
        "incomplete_tasks": [
            {
                "task": "2. Deferred rollout observation",
                "decision": "deferred",
                "rationale": "Requires production observation after merge.",
                "authority": "approved operational deferment OP-2",
            }
        ],
    }


def refresh_map_fingerprint(review_map: dict[str, Any]) -> None:
    review_map.pop("fingerprint", None)
    review_map["fingerprint"] = canonical_fingerprint(review_map)


def refresh_source_identity(review_map: dict[str, Any]) -> None:
    reviewable = [item for item in review_map["files"] if item.get("review_class") == "reviewable"]
    review_map["source_fingerprint"] = canonical_fingerprint(
        {"base": review_map.get("base"), "files": reviewable}
    )
    review_map["review_fingerprint"] = canonical_fingerprint(
        {
            "source_fingerprint": review_map["source_fingerprint"],
            "review_policy": review_map["review_policy"],
        }
    )
    refresh_map_fingerprint(review_map)


def check_ui_verdicts(directory: Path) -> None:
    source = evidence()
    source["review_policy"].update(
        ui_ux_required=True,
        ui_ux_reason="server-rendered UI fixture",
        ui_impact_paths=["src/api.py"],
    )
    review_map = build_review_map(source)
    map_path = directory / "ui-map.json"
    dispositions_path = directory / "ui-dispositions.json"
    write_json(map_path, review_map)
    write_json(dispositions_path, dispositions(review_map))
    header = (
        f"Review map: {review_map['fingerprint']}\n"
        f"Source fingerprint: {review_map['source_fingerprint']}\n"
    )
    core_reports = []
    scope_paths = []
    scopes = manifests(review_map)
    scopes.append({**scopes[0], "lens": "ui-ux"})
    for scope in scopes:
        path = directory / f"ui-{scope['lens']}.json"
        write_json(path, scope)
        scope_paths.append(path)
        if scope["lens"] != "ui-ux":
            report = directory / f"ui-{scope['lens']}.md"
            report.write_text(header + "Status: PASS\n", encoding="utf-8")
            core_reports.append(f"{scope['lens']}={report}")
    report = directory / "ui-verdict.md"
    for mode in ("quick", "full"):
        args = Namespace(
            mode=mode,
            approved_map=map_path,
            current_map=map_path,
            manifest=scope_paths if mode == "full" else [],
            lens_report=[*core_reports, f"ui-ux={report}"]
            if mode == "full"
            else [f"combined={report}"],
            dispositions=dispositions_path,
            static_summary=None,
            tasks=None,
        )
        check_verdict_cases(args, report, header)


def check_verdict_cases(args: Namespace, report: Path, header: str) -> None:
    passing = "Status: PASS\nCONTRACT: PASS\nVISUAL: PASS\n"
    report.write_text(header + passing, encoding="utf-8")
    assert validate(args)["approval_gate"] == "PASS"
    for field in ("VISUAL", "CONTRACT", "Status"):
        for verdict in ("FAIL", "UNVERIFIED", "FINDINGS", "", "UNKNOWN", "PASS | FAIL"):
            body = passing.replace(f"{field}: PASS", f"{field}: {verdict}")
            report.write_text(header + body, encoding="utf-8")
            expect_error(field, lambda: validate(args))
        report.write_text(header + passing.replace(f"{field}: PASS\n", ""), encoding="utf-8")
        expect_error(field, lambda: validate(args))
        for extra in (f"{field}: FAIL\n", f"{field}: PASS\n", f"- **{field}**: UNVERIFIED\n"):
            report.write_text(header + passing + extra, encoding="utf-8")
            expect_error(field, lambda: validate(args))
    report.write_text(passing, encoding="utf-8")
    expect_error("stale/unbound", lambda: validate(args))
    for body in (
        "- **Status**: PASS\n- **CONTRACT**: PASS\n- **VISUAL**: PASS\n",
        "**Status:** PASS\n**CONTRACT:** PASS\n**VISUAL:** PASS\n",
        "Status: **PASS**\nCONTRACT: **PASS**\nVISUAL: **PASS**\n",
        "**Status: PASS**\n**CONTRACT: PASS**\n**VISUAL: PASS**\n",
    ):
        report.write_text(header + body, encoding="utf-8")
        assert validate(args)["approval_gate"] == "PASS"


def test_lizard_provenance() -> None:
    dispositions = {
        "static_analysis": [
            {
                "dimension": "cyclomatic+length",
                "tool": "lizard",
                "decision": "baseline",
                "rationale": "The sole reported function is unchanged baseline.",
                "authority": "review finding QUAL-BASE-LIZARD",
            }
        ]
    }
    with tempfile.TemporaryDirectory() as temporary:
        summary = Path(temporary) / "static.txt"
        for status, exit_code in (
            ("OK", 0),
            ("FINDINGS (exit 1)", 1),
            ("FINDINGS (reported with exit 0)", 0),
            ("UNVERIFIED (failed to execute)", 2),
            ("UNVERIFIED (inconsistent Lizard report)", 0),
        ):
            summary.write_text(
                "===== STATIC ANALYSIS PROVENANCE =====\n"
                "Dimension | Tool | Version | Command | Exit | Status | Full log\n"
                f"cyclomatic+length | lizard | 1.21.2 | lizard . | {exit_code} | {status} | log\n"
                "===== END PROVENANCE =====\n",
                encoding="utf-8",
            )
            if status == "OK":
                assert validate_static_analysis(summary, {}) == 0
            elif status.startswith("FINDINGS"):
                expect_error(
                    "undispositioned static-analysis findings",
                    lambda: validate_static_analysis(summary, {}),
                )
                assert validate_static_analysis(summary, dispositions) == 1
            else:
                expect_error("UNVERIFIED", lambda: validate_static_analysis(summary, dispositions))


def main() -> None:
    review_map = build_review_map(evidence())
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        approved_path = directory / "approved.json"
        current_path = directory / "current.json"
        dispositions_path = directory / "dispositions.json"
        tasks_path = directory / "tasks.md"
        static_path = directory / "static.txt"
        write_json(approved_path, review_map)
        write_json(current_path, review_map)
        write_json(dispositions_path, dispositions(review_map))
        tasks_path.write_text(
            "- [x] 1. Implement\n- [ ] 2. Deferred rollout observation\n", encoding="utf-8"
        )
        static_path.write_text(
            "===== STATIC ANALYSIS PROVENANCE =====\n"
            "Dimension | Tool | Version | Command | Exit | Status | Full log\n"
            "----------|------|---------|---------|------|--------|---------\n"
            "duplication | jscpd | 1.0 | jscpd . | 1 | FINDINGS (exit 1) | log\n"
            "cyclomatic | radon | 1.0 | radon cc | 0 | OK | log\n"
            "===== END PROVENANCE =====\n",
            encoding="utf-8",
        )

        manifest_paths: list[Path] = []
        for manifest in manifests(review_map):
            path = directory / f"{manifest['lens']}.json"
            write_json(path, manifest)
            manifest_paths.append(path)

        lens_reports: list[str] = []
        for lens in ("architecture-design", "correctness-safety", "engineering-quality"):
            path = directory / f"{lens}.md"
            path.write_text(
                f"Review map: {review_map['fingerprint']}\n"
                f"Source fingerprint: {review_map['source_fingerprint']}\n"
                "Status: PASS\n",
                encoding="utf-8",
            )
            lens_reports.append(f"{lens}={path}")

        args = Namespace(
            approved_map=approved_path,
            current_map=current_path,
            manifest=manifest_paths,
            lens_report=lens_reports,
            dispositions=dispositions_path,
            static_summary=static_path,
            tasks=tasks_path,
        )
        receipt = validate(args)
        assert receipt["approval_gate"] == "PASS"
        assert receipt["structural_leads"] == 4
        assert receipt["static_findings_dispositioned"] == 1
        assert receipt["incomplete_tasks_dispositioned"] == 1

        # Backend-only Quick reviews remain valid without UI verdicts.
        quick = Namespace(
            **{
                **vars(args),
                "mode": "quick",
                "manifest": [],
                "lens_report": [lens_reports[0].replace("architecture-design=", "combined=", 1)],
            }
        )
        assert validate(quick)["approval_gate"] == "PASS"
        check_ui_verdicts(directory)

        stale = json.loads(json.dumps(review_map))
        stale["files"][0]["current_sha256"] = "f" * 64
        refresh_source_identity(stale)
        write_json(current_path, stale)
        expect_error("differs from the reviewed snapshot", lambda: validate(args))
        write_json(current_path, review_map)

        missing_lens = Namespace(**{**vars(args), "lens_report": lens_reports[:-1]})
        expect_error("lens report mismatch", lambda: validate(missing_lens))

        missing_lead = dispositions(review_map)
        missing_lead["structural"].pop()
        write_json(dispositions_path, missing_lead)
        expect_error("undispositioned structural leads", lambda: validate(args))
        write_json(dispositions_path, dispositions(review_map))

        static_path.write_text(
            "===== STATIC ANALYSIS PROVENANCE =====\n"
            "Dimension | Tool | Version | Command | Exit | Status | Full log\n"
            "SAST | semgrep | 1.0 | semgrep | - | UNVERIFIED (not installed) | -\n"
            "===== END PROVENANCE =====\n",
            encoding="utf-8",
        )
        expect_error("UNVERIFIED", lambda: validate(args))

        large = json.loads(json.dumps(review_map))
        large["change_scale"]["large_change"] = True
        expect_error(
            "approved scale exception",
            lambda: validate_change_scale(large, dispositions(review_map)),
        )


if __name__ == "__main__":
    main()
    test_lizard_provenance()
    print("OK: review approval gate")
