#!/usr/bin/env python3
"""Fail closed before approval when review evidence is stale or incomplete."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from review_map import REQUIRED_LENSES, read_json, validate_scopes, verified_review_map_fingerprint

PASS_STATUS_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?status(?:\*\*)?\s*:\s*PASS\s*$")
UNCHECKED_TASK_RE = re.compile(r"^\s*[-*]\s+\[\s\]\s+(?P<text>.+?)\s*$", re.IGNORECASE)


def nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def validate_current_source(approved: dict[str, Any], current: dict[str, Any]) -> None:
    verified_review_map_fingerprint(approved)
    verified_review_map_fingerprint(current)
    for field in ("source_fingerprint", "review_fingerprint"):
        if approved.get(field) != current.get(field):
            raise ValueError(f"current {field} differs from the reviewed snapshot")


def parse_lens_assignment(raw: str) -> tuple[str, Path]:
    lens, separator, path = raw.partition("=")
    if not separator or not lens.strip() or not path.strip():
        raise ValueError("lens reports use LENS=PATH")
    return lens.strip(), Path(path).expanduser().resolve()


def required_lenses(review_map: dict[str, Any]) -> set[str]:
    lenses = set(REQUIRED_LENSES)
    if review_map.get("review_policy", {}).get("ui_ux_required"):
        lenses.add("ui-ux")
    return lenses


def validate_lens_reports(
    review_map: dict[str, Any], raw_reports: list[str], expected: set[str] | None = None
) -> None:
    reports: dict[str, Path] = {}
    for raw in raw_reports:
        lens, path = parse_lens_assignment(raw)
        if lens in reports:
            raise ValueError(f"duplicate lens report: {lens}")
        reports[lens] = path

    expected = expected or required_lenses(review_map)
    missing = sorted(expected - set(reports))
    extra = sorted(set(reports) - expected)
    if missing or extra:
        raise ValueError(f"lens report mismatch; missing={missing}, extra={extra}")

    map_fingerprint = nonempty(review_map.get("fingerprint"), "review map fingerprint")
    source_fingerprint = nonempty(review_map.get("source_fingerprint"), "source fingerprint")
    for lens, path in reports.items():
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise ValueError(f"missing/unreadable lens report for {lens}: {path}") from error
        if not content.strip():
            raise ValueError(f"empty lens report: {lens}")
        if map_fingerprint not in content or source_fingerprint not in content:
            raise ValueError(f"stale/unbound lens report: {lens}")
        if PASS_STATUS_RE.search(content) is None:
            raise ValueError(f"lens report is not PASS: {lens}")


def structural_lead_keys(review_map: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (str(item["path"]), str(lead["kind"]))
        for item in review_map.get("files", [])
        if item.get("review_class") == "reviewable"
        for lead in item.get("structure_leads", [])
        if isinstance(lead, dict) and isinstance(lead.get("kind"), str)
    }


def disposition_items(dispositions: dict[str, Any], key: str) -> list[dict[str, Any]]:
    items = dispositions.get(key, [])
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ValueError(f"dispositions.{key} must be a list of objects")
    return items


def require_rationale_and_authority(item: dict[str, Any], label: str) -> None:
    nonempty(item.get("rationale"), f"{label}.rationale")
    nonempty(item.get("authority"), f"{label}.authority")


def validate_structural_dispositions(
    review_map: dict[str, Any], dispositions: dict[str, Any]
) -> int:
    expected = structural_lead_keys(review_map)
    actual: dict[tuple[str, str], dict[str, Any]] = {}
    for item in disposition_items(dispositions, "structural"):
        key = (
            nonempty(item.get("path"), "structural.path"),
            nonempty(item.get("lead"), "structural.lead"),
        )
        if key in actual:
            raise ValueError(f"duplicate structural disposition: {key}")
        actual[key] = item

    missing = sorted(expected - set(actual))
    extra = sorted(set(actual) - expected)
    if missing:
        raise ValueError(f"undispositioned structural leads: {missing}")
    if extra:
        raise ValueError(f"structural dispositions are not fingerprinted leads: {extra}")
    for key in expected:
        item = actual[key]
        decision = item.get("decision")
        if decision not in {"keep_approved", "not_applicable"}:
            raise ValueError(f"structural lead is not approval-ready: {key}")
        require_rationale_and_authority(item, f"structural {key}")
    return len(expected)


def parse_static_summary(path: Path) -> list[dict[str, str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"missing/unreadable static-analysis summary: {path}") from error
    rows: list[dict[str, str]] = []
    inside = False
    for line in lines:
        if line.strip() == "===== STATIC ANALYSIS PROVENANCE =====":
            inside = True
            continue
        if line.strip() == "===== END PROVENANCE =====":
            break
        if not inside or "|" not in line:
            continue
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) != 7 or cells[0] in {"Dimension", "----------"}:
            continue
        rows.append({"dimension": cells[0], "tool": cells[1], "status": cells[5]})
    if not rows:
        raise ValueError("static-analysis summary contains no provenance rows")
    return rows


def validate_static_row(
    row: dict[str, str], dispositions: dict[tuple[str, str], dict[str, Any]]
) -> bool:
    status = row["status"].upper()
    key = (row["dimension"], row["tool"])
    if status.startswith("UNVERIFIED"):
        raise ValueError(f"static-analysis dimension is UNVERIFIED: {key}")
    if not status.startswith("FINDINGS"):
        if status != "OK":
            raise ValueError(f"unknown static-analysis status for {key}: {row['status']}")
        return False
    item = dispositions.get(key)
    if item is None:
        raise ValueError(f"undispositioned static-analysis findings: {key}")
    if item.get("decision") not in {"baseline", "approved_exception"}:
        raise ValueError(f"static-analysis finding is not approval-ready: {key}")
    require_rationale_and_authority(item, f"static analysis {key}")
    return True


def validate_static_analysis(summary_path: Path | None, dispositions: dict[str, Any]) -> int:
    if summary_path is None:
        return 0
    rows = parse_static_summary(summary_path)
    actual: dict[tuple[str, str], dict[str, Any]] = {}
    for item in disposition_items(dispositions, "static_analysis"):
        key = (
            nonempty(item.get("dimension"), "static_analysis.dimension"),
            nonempty(item.get("tool"), "static_analysis.tool"),
        )
        if key in actual:
            raise ValueError(f"duplicate static-analysis disposition: {key}")
        actual[key] = item

    return sum(validate_static_row(row, actual) for row in rows)


def incomplete_tasks(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"missing/unreadable tasks artifact: {path}") from error
    return [match.group("text") for line in lines if (match := UNCHECKED_TASK_RE.match(line))]


def validate_tasks(path: Path | None, dispositions: dict[str, Any]) -> int:
    if path is None:
        return 0
    pending = incomplete_tasks(path)
    exceptions: dict[str, dict[str, Any]] = {}
    for item in disposition_items(dispositions, "incomplete_tasks"):
        task = nonempty(item.get("task"), "incomplete_tasks.task")
        if task in exceptions:
            raise ValueError(f"duplicate incomplete-task disposition: {task}")
        exceptions[task] = item
    missing = sorted(set(pending) - set(exceptions))
    if missing:
        raise ValueError(f"unchecked tasks without approved disposition: {missing}")
    for task in pending:
        item = exceptions[task]
        if item.get("decision") not in {"deferred", "not_applicable"}:
            raise ValueError(f"unchecked task is not approval-ready: {task}")
        require_rationale_and_authority(item, f"incomplete task {task}")
    return len(pending)


def validate_change_scale(review_map: dict[str, Any], dispositions: dict[str, Any]) -> bool:
    scale = review_map.get("change_scale", {})
    if not scale.get("large_change"):
        return False
    item = dispositions.get("scale")
    if not isinstance(item, dict) or item.get("decision") != "approved_exception":
        raise ValueError("large change requires an explicit approved scale exception")
    require_rationale_and_authority(item, "scale")
    return True


def validate(args: argparse.Namespace) -> dict[str, Any]:
    approved = read_json(args.approved_map)
    current = read_json(args.current_map)
    validate_current_source(approved, current)
    mode = getattr(args, "mode", "full")
    manifests = [read_json(path) for path in args.manifest]
    if mode == "full":
        if not manifests:
            raise ValueError("full approval requires validated lens scope manifests")
        scope_receipt = validate_scopes(approved, manifests)
        validate_lens_reports(approved, args.lens_report)
    else:
        if manifests:
            raise ValueError("quick approval does not accept full-review scope manifests")
        validate_lens_reports(approved, args.lens_report, {"combined"})
        scope_receipt = {
            "review_map_fingerprint": approved.get("fingerprint"),
            "source_fingerprint": approved.get("source_fingerprint"),
            "review_fingerprint": approved.get("review_fingerprint"),
            "lenses": ["combined"],
            "accounted_paths": len(approved.get("files", [])),
            "reviewable_paths": sum(
                item.get("review_class") == "reviewable" for item in approved.get("files", [])
            ),
            "status": "valid",
        }

    dispositions = read_json(args.dispositions)
    if dispositions.get("review_map_fingerprint") != approved.get("fingerprint"):
        raise ValueError("dispositions are stale or belong to another review map")
    structural_count = validate_structural_dispositions(approved, dispositions)
    static_findings = validate_static_analysis(args.static_summary, dispositions)
    pending_tasks = validate_tasks(args.tasks, dispositions)
    scale_exception = validate_change_scale(approved, dispositions)
    return {
        **scope_receipt,
        "approval_gate": "PASS",
        "structural_leads": structural_count,
        "static_findings_dispositioned": static_findings,
        "incomplete_tasks_dispositioned": pending_tasks,
        "scale_exception": scale_exception,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("full", "quick"), default="full")
    parser.add_argument("--approved-map", type=Path, required=True)
    parser.add_argument("--current-map", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, action="append", default=[])
    parser.add_argument("--lens-report", action="append", default=[])
    parser.add_argument("--dispositions", type=Path, required=True)
    parser.add_argument("--static-summary", type=Path)
    parser.add_argument("--tasks", type=Path)
    return parser


def main() -> int:
    try:
        receipt = validate(build_parser().parse_args())
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"review approval gate: FAIL: {error}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
