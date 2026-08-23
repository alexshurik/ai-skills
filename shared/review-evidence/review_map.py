#!/usr/bin/env python3
"""Build a lossless review map and validate core plus conditional lens scopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".html",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".scala",
    ".sh",
    ".sql",
    ".svelte",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
    ".css",
}
CONFIG_SUFFIXES = {".json", ".toml", ".yaml", ".yml"}
BINARY_SUFFIXES = {
    ".7z",
    ".avi",
    ".bin",
    ".bmp",
    ".class",
    ".dll",
    ".dylib",
    ".eot",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp3",
    ".mp4",
    ".o",
    ".otf",
    ".pdf",
    ".png",
    ".so",
    ".tar",
    ".tiff",
    ".ttf",
    ".wasm",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}
LOCK_NAMES = {
    "cargo.lock",
    "composer.lock",
    "gemfile.lock",
    "go.sum",
    "package-lock.json",
    "pipfile.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "yarn.lock",
}
DEPENDENCY_MANIFESTS = {
    "cargo.toml",
    "composer.json",
    "gemfile",
    "go.mod",
    "package.json",
    "pipfile",
    "pyproject.toml",
    "requirements.txt",
}
GENERATED_DIRS = {
    ".next",
    ".nuxt",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "vendor",
}
DEPLOY_PARTS = {
    ".github",
    "ansible",
    "charts",
    "ci",
    "deploy",
    "deployment",
    "docker",
    "helm",
    "infra",
    "infrastructure",
    "k8s",
    "kubernetes",
    "terraform",
}
TRUST_TERMS = {
    "access",
    "auth",
    "authorization",
    "billing",
    "credential",
    "jwt",
    "oauth",
    "password",
    "payment",
    "permission",
    "role",
    "secret",
    "session",
    "token",
    "webhook",
}
INSTRUCTION_NAMES = {"agents.md", "claude.md", "skill.md"}
INSTRUCTION_PARTS = {
    ".agents",
    ".claude",
    ".cursor",
    "adrs",
    "docs",
    "openspec",
    "prompts",
    "specs",
    "skills",
}
VALID_DEPTHS = {"full-content", "targeted-content", "metadata-only"}
REQUIRED_LENSES = {
    "architecture-design",
    "correctness-safety",
    "engineering-quality",
}
OPTIONAL_LENSES = {"ui-ux"}
REVIEW_CLASSES = {
    "reviewable",
    "preserved_baseline",
    "workflow_output",
    "derived_acceptance_output",
}
WORKFLOW_OUTPUT_NAMES = {
    "code_review.md",
    "deferred.md",
    "doc_review.md",
    "retrospective.md",
    "review.md",
}
DERIVED_ACCEPTANCE_OUTPUT_NAMES = {
    "api_changelog.md",
    "operational_tasks.md",
    "summary.md",
    "verification.md",
    "visual_report.html",
}
UI_SUFFIXES = {".astro", ".css", ".html", ".jsx", ".scss", ".svelte", ".tsx", ".vue"}


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as temporary:
        temporary.write(content)
        temporary.flush()
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


def safe_parts(raw_path: str) -> tuple[str, ...]:
    path = PurePosixPath(raw_path)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"unsafe review-map path: {raw_path!r}")
    return tuple(part.lower() for part in path.parts)


def is_generated_candidate(path: Path, parts: tuple[str, ...]) -> bool:
    lowered = path.name.lower()
    return bool(
        GENERATED_DIRS.intersection(parts)
        or ".generated." in lowered
        or lowered.endswith((".min.css", ".min.js", ".map", "_pb2.py", ".g.dart"))
    )


def content_class(entry: dict[str, Any]) -> tuple[str, str, str]:
    raw_path = str(entry["path"])
    path = Path(raw_path)
    parts = safe_parts(raw_path)
    suffix = path.suffix.lower()
    name = path.name.lower()
    current_kind = entry.get("current_kind")
    current_status = entry.get("current_read_status")

    if name in LOCK_NAMES:
        result = (
            "dependency-lock",
            "metadata-only",
            "lockfile; inspect dependency deltas, not every serialized line",
        )
    elif is_generated_candidate(path, parts):
        result = (
            "generated-candidate",
            "metadata-only",
            "generated/vendor candidate; verify provenance and escalate if authored",
        )
    elif suffix in BINARY_SUFFIXES:
        result = (
            "binary",
            "metadata-only",
            "binary content; verify path, type, size, and provenance",
        )
    elif current_kind == "symlink":
        result = ("symlink", "metadata-only", "symlink; verify target and repository boundary")
    elif current_kind == "missing":
        if entry.get("base_read_status") == "ok":
            result = (
                "deleted-authored",
                "full-content",
                "deleted readable file; inspect authoritative base content",
            )
        else:
            result = (
                "deleted-unavailable",
                "metadata-only",
                "deleted file base content is unavailable",
            )
    elif current_kind != "regular" or current_status != "ok":
        result = (
            "unavailable",
            "metadata-only",
            "content unavailable or not a regular readable file",
        )
    else:
        result = (
            "authored-text",
            "full-content",
            "human-authored readable text requires full coverage review",
        )
    return result


def has_test_marker(path: Path, parts: tuple[str, ...]) -> bool:
    name = path.name.lower()
    return bool(
        {"test", "tests", "spec", "specs"}.intersection(parts)
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
        or name.endswith("_test.go")
    )


def risk_tags(entry: dict[str, Any], classification: str) -> list[str]:
    raw_path = str(entry["path"])
    path = Path(raw_path)
    parts = safe_parts(raw_path)
    name = path.name.lower()
    suffix = path.suffix.lower()
    lexical_tokens = set(parts)
    for part in parts:
        lexical_tokens.update(token for token in part.replace("-", "_").split("_") if token)

    lowered_path = raw_path.lower()
    is_trust_lead = bool(TRUST_TERMS.intersection(lexical_tokens)) or any(
        term in lowered_path for term in TRUST_TERMS
    )
    instruction_prefixes = ("adr", "architecture", "design", "proposal", "requirement", "spec")
    is_instruction = bool(
        name in INSTRUCTION_NAMES
        or INSTRUCTION_PARTS.intersection(parts)
        or name.startswith(instruction_prefixes)
    )
    metadata_classes = {
        "binary",
        "dependency-lock",
        "generated-candidate",
        "symlink",
        "unavailable",
    }
    conditions = (
        (suffix in SOURCE_SUFFIXES, "source"),
        (suffix in CONFIG_SUFFIXES or name in {"dockerfile", "makefile"}, "configuration"),
        (has_test_marker(path, parts), "test"),
        (
            name in LOCK_NAMES or name in DEPENDENCY_MANIFESTS or name.startswith("requirements"),
            "dependency",
        ),
        (bool(DEPLOY_PARTS.intersection(parts)) or name.startswith("dockerfile"), "deployment"),
        (is_trust_lead, "trust-boundary-lead"),
        (is_instruction, "instruction"),
        (bool(entry.get("local_imports")), "import-candidate"),
        (
            any(entry.get(flag) for flag in ("over_300", "crossed_300", "micro_file_candidate")),
            "structure-lead",
        ),
        (classification in metadata_classes, classification),
    )
    tags = {"changed-path", *(tag for matches, tag in conditions if matches)}
    return sorted(tags)


def canonical_fingerprint(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def verified_review_map_fingerprint(review_map: dict[str, Any]) -> str:
    claimed = review_map.get("fingerprint")
    if not isinstance(claimed, str):
        raise ValueError("review map fingerprint must be a string")

    canonical_map = dict(review_map)
    del canonical_map["fingerprint"]
    if canonical_fingerprint(canonical_map) != claimed:
        raise ValueError("review map fingerprint mismatch")
    return claimed


def default_review_class(path: str) -> str:
    parts = safe_parts(path)
    name = Path(path).name.lower()
    is_change_artifact = bool(
        len(parts) >= 3 and parts[0] == "openspec" and parts[1] in {"changes", "completed"}
    )
    if not is_change_artifact:
        return "reviewable"
    if name in WORKFLOW_OUTPUT_NAMES:
        return "workflow_output"
    if name in DERIVED_ACCEPTANCE_OUTPUT_NAMES:
        return "derived_acceptance_output"
    return "reviewable"


def validated_path_classes(raw: dict[str, Any]) -> dict[str, str]:
    path_classes = raw.get("path_classes", {})
    if not isinstance(path_classes, dict):
        raise ValueError("review_policy.path_classes must be an object")
    for path, review_class in path_classes.items():
        if not isinstance(path, str):
            raise ValueError("review policy paths must be strings")
        safe_parts(path)
        if review_class not in REVIEW_CLASSES:
            raise ValueError(f"invalid review class for {path}: {review_class!r}")
    return path_classes


def validated_preserved_hashes(raw: dict[str, Any], path_classes: dict[str, str]) -> dict[str, str]:
    preserved_hashes = raw.get("preserved_baseline_hashes", {})
    if not isinstance(preserved_hashes, dict) or any(
        not isinstance(path, str) or not isinstance(digest, str)
        for path, digest in preserved_hashes.items()
    ):
        raise ValueError("review_policy.preserved_baseline_hashes must be an object")
    preserved_paths = {
        path for path, review_class in path_classes.items() if review_class == "preserved_baseline"
    }
    if set(preserved_hashes) != preserved_paths:
        raise ValueError("preserved baseline paths require exact initial hashes")
    return preserved_hashes


def validated_classification_reasons(
    raw: dict[str, Any], path_classes: dict[str, str]
) -> dict[str, str]:
    reasons = raw.get("path_class_reasons", {})
    if not isinstance(reasons, dict) or any(
        not isinstance(path, str) or not isinstance(reason, str) or not reason.strip()
        for path, reason in reasons.items()
    ):
        raise ValueError("review_policy.path_class_reasons must be an object")
    if set(reasons) != set(path_classes):
        raise ValueError("every manual path class needs exactly one non-empty reason")
    return reasons


def validated_ui_policy(raw: dict[str, Any]) -> tuple[bool | None, str | None, list[str] | None]:
    ui_required = raw.get("ui_ux_required")
    if ui_required is not None and not isinstance(ui_required, bool):
        raise ValueError("review_policy.ui_ux_required must be boolean")
    ui_reason = raw.get("ui_ux_reason")
    if ui_reason is not None and (not isinstance(ui_reason, str) or not ui_reason.strip()):
        raise ValueError("review_policy.ui_ux_reason must be a non-empty string")
    if ui_required is not None and ui_reason is None:
        raise ValueError("an explicit UI/UX decision needs ui_ux_reason")
    ui_impact_paths = raw.get("ui_impact_paths")
    if ui_impact_paths is not None and (
        not isinstance(ui_impact_paths, list)
        or any(not isinstance(path, str) for path in ui_impact_paths)
    ):
        raise ValueError("review_policy.ui_impact_paths must be a list of paths")
    for path in ui_impact_paths or []:
        safe_parts(path)
    if ui_required is True and not ui_impact_paths:
        raise ValueError("required UI/UX review needs explicit ui_impact_paths")
    if ui_required is False and ui_impact_paths:
        raise ValueError("non-empty UI impact paths require UI/UX review")
    return ui_required, ui_reason, ui_impact_paths


def classification_policy(evidence: dict[str, Any]) -> dict[str, Any]:
    raw = evidence.get("review_policy", {})
    if not isinstance(raw, dict):
        raise ValueError("evidence.review_policy must be an object")
    path_classes = validated_path_classes(raw)
    preserved_hashes = validated_preserved_hashes(raw, path_classes)
    classification_reasons = validated_classification_reasons(raw, path_classes)
    ui_required, ui_reason, ui_impact_paths = validated_ui_policy(raw)
    return {
        "path_classes": path_classes,
        "preserved_baseline_hashes": preserved_hashes,
        "path_class_reasons": classification_reasons,
        "ui_ux_required": ui_required,
        "ui_ux_reason": ui_reason,
        "ui_impact_paths": ui_impact_paths,
    }


def is_ui_candidate(path: str, review_class: str) -> bool:
    lowered = path.lower()
    return bool(
        review_class == "reviewable"
        and Path(path).suffix.lower() in UI_SUFFIXES
        and not has_test_marker(Path(path), safe_parts(path))
        and not any(part in lowered for part in ("/build/", "/dist/", "/generated/"))
    )


def mapped_evidence_entry(raw_entry: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    path = raw_entry["path"]
    classification, requirement, reason = content_class(raw_entry)
    review_class = policy["path_classes"].get(path, default_review_class(path))
    if review_class == "preserved_baseline" and (
        raw_entry.get("current_sha256") != policy["preserved_baseline_hashes"][path]
    ):
        raise ValueError(f"preserved baseline changed after capture: {path}")
    return {
        "path": path,
        "base_path": raw_entry.get("base_path"),
        "base_blob_oid": raw_entry.get("base_blob_oid"),
        "content_class": classification,
        "review_class": review_class,
        "review_class_reason": policy["path_class_reasons"].get(
            path, "deterministic default classification"
        ),
        "coverage_requirement": requirement,
        "coverage_reason": reason,
        "base_lines": raw_entry.get("base_lines"),
        "current_lines": raw_entry.get("current_lines"),
        "current_kind": raw_entry.get("current_kind"),
        "current_sha256": raw_entry.get("current_sha256"),
        "changed_intervals": raw_entry.get("changed_intervals", []),
        "interval_status": raw_entry.get("interval_status"),
        "local_imports": raw_entry.get("local_imports", []),
        "risk_tags": risk_tags(raw_entry, classification),
        "ui_impact_candidate": is_ui_candidate(path, review_class),
    }


def map_evidence_files(
    files: list[Any], policy: dict[str, Any]
) -> tuple[list[dict[str, Any]], set[str]]:
    mapped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_entry in files:
        if not isinstance(raw_entry, dict) or not isinstance(raw_entry.get("path"), str):
            raise ValueError("each evidence file entry needs a string path")
        path = raw_entry["path"]
        safe_parts(path)
        if path in seen:
            raise ValueError(f"duplicate evidence path: {path}")
        seen.add(path)
        mapped.append(mapped_evidence_entry(raw_entry, policy))
    return mapped, seen


def resolved_ui_review(
    policy: dict[str, Any], reviewable_files: list[dict[str, Any]]
) -> tuple[bool, str, list[str], list[str]]:
    ui_candidates = [item["path"] for item in reviewable_files if item["ui_impact_candidate"]]
    ui_impact_paths = policy["ui_impact_paths"] or ui_candidates
    non_reviewable_ui_paths = sorted(
        set(ui_impact_paths) - {item["path"] for item in reviewable_files}
    )
    if non_reviewable_ui_paths:
        raise ValueError(f"UI impact paths must be reviewable: {non_reviewable_ui_paths}")
    ui_required = policy["ui_ux_required"]
    if ui_required is None:
        ui_required = bool(ui_candidates)
        ui_reason = (
            "automatic UI-file candidate detection; root must override false for tests/config/"
            "type-only or proven non-rendered changes"
            if ui_required
            else "no user-visible frontend candidate detected"
        )
    else:
        ui_reason = policy["ui_ux_reason"]
    return ui_required, ui_reason, ui_candidates, ui_impact_paths


def build_review_map(evidence: dict[str, Any]) -> dict[str, Any]:
    files = evidence.get("files")
    if not isinstance(files, list):
        raise ValueError("evidence.files must be a list")
    if not isinstance(evidence.get("fingerprint"), str):
        raise ValueError("evidence fingerprint must be a string")

    policy = classification_policy(evidence)
    mapped, seen = map_evidence_files(files, policy)

    unknown_policy_paths = sorted(
        (set(policy["path_classes"]) | set(policy["ui_impact_paths"] or [])) - seen
    )
    if unknown_policy_paths:
        raise ValueError(f"review policy paths are not in evidence: {unknown_policy_paths}")

    sorted_files = sorted(mapped, key=lambda item: item["path"])
    reviewable_files = [item for item in sorted_files if item["review_class"] == "reviewable"]
    ui_required, ui_reason, ui_candidates, ui_impact_paths = resolved_ui_review(
        policy, reviewable_files
    )

    source_identity = {
        "base": evidence.get("base"),
        "files": reviewable_files,
    }
    source_fingerprint = canonical_fingerprint(source_identity)
    resolved_policy = {
        "ui_ux_required": ui_required,
        "ui_ux_reason": ui_reason,
        "ui_candidates": ui_candidates,
        "ui_impact_paths": sorted(set(ui_impact_paths)),
    }

    review_map: dict[str, Any] = {
        "schema_version": 2,
        "repository": evidence.get("repository"),
        "base": evidence.get("base"),
        "head": evidence.get("head"),
        "evidence_fingerprint": evidence.get("fingerprint"),
        "files": sorted_files,
        "source_fingerprint": source_fingerprint,
        "review_fingerprint": canonical_fingerprint(
            {"source_fingerprint": source_fingerprint, "review_policy": resolved_policy}
        ),
        "review_policy": resolved_policy,
        "note": (
            "Lossless deterministic Git inventory. Lens coverage applies only to reviewable "
            "paths; risk tags and UI candidates are leads, not verdicts."
        ),
    }
    review_map["fingerprint"] = canonical_fingerprint(review_map)
    return review_map


def expected_scope_entries(review_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected_files = review_map.get("files")
    if not isinstance(expected_files, list):
        raise ValueError("review map files must be a list")
    return {
        str(item["path"]): item
        for item in expected_files
        if item.get("review_class", "reviewable") == "reviewable"
    }


def manifest_entries(
    manifest: dict[str, Any],
    fingerprint: str,
    actual_lenses: set[str],
) -> tuple[str, list[dict[str, Any]]]:
    lens = manifest.get("lens")
    entries = manifest.get("entries")
    if lens not in REQUIRED_LENSES | OPTIONAL_LENSES or lens in actual_lenses:
        raise ValueError(f"invalid or duplicate scope lens: {lens!r}")
    if manifest.get("review_map_fingerprint") != fingerprint:
        raise ValueError(f"scope manifest fingerprint mismatch: {lens}")
    if not isinstance(entries, list):
        raise ValueError(f"scope manifest entries must be a list: {lens}")
    actual_lenses.add(lens)
    return lens, entries


def collect_scope_assignments(
    manifests: list[dict[str, Any]], fingerprint: str
) -> tuple[dict[str, list[dict[str, Any]]], set[str]]:
    if len(manifests) not in {len(REQUIRED_LENSES), len(REQUIRED_LENSES) + 1}:
        raise ValueError("three core scope manifests and at most one UI/UX manifest are required")

    assigned: dict[str, list[dict[str, Any]]] = {}
    actual_lenses: set[str] = set()
    for manifest in manifests:
        lens, entries = manifest_entries(manifest, fingerprint, actual_lenses)
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                raise ValueError(f"each scope entry needs a string path: {lens}")
            path = entry["path"]
            if path in seen:
                raise ValueError(f"duplicate scope path in {lens}: {path}")
            seen.add(path)
            assigned.setdefault(path, []).append({**entry, "_lens": lens})
    return assigned, actual_lenses


def require_complete_scope_paths(
    expected: dict[str, dict[str, Any]],
    assigned: dict[str, list[dict[str, Any]]],
) -> None:
    missing = sorted(set(expected) - set(assigned))
    extra = sorted(set(assigned) - set(expected))
    if missing or extra:
        raise ValueError(f"scope path mismatch; missing={missing}, extra={extra}")


def validate_scope_entry(
    path: str,
    entry: dict[str, Any],
    expected_entry: dict[str, Any],
) -> None:
    depth = entry.get("reading_depth")
    if depth not in VALID_DEPTHS:
        raise ValueError(f"invalid reading depth for {path}: {depth!r}")
    if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
        raise ValueError(f"scope entry {path} needs a non-empty reason")
    if not isinstance(entry.get("risk_leads"), list):
        raise ValueError(f"scope entry {path} risk leads must be a list")
    for hash_name in ("base_blob_oid", "current_sha256"):
        expected_hash = expected_entry.get(hash_name)
        if expected_hash is not None and entry.get(hash_name) != expected_hash:
            raise ValueError(f"scope entry {path} has stale {hash_name}")


def validate_path_coverage(
    path: str,
    expected_entry: dict[str, Any],
    entries: list[dict[str, Any]],
) -> None:
    for entry in entries:
        validate_scope_entry(path, entry, expected_entry)
    has_content_read = any(
        entry["reading_depth"] in {"full-content", "targeted-content"} for entry in entries
    )
    if expected_entry.get("coverage_requirement") == "full-content" and not has_content_read:
        raise ValueError(f"authored content is metadata-only across scopes: {path}")


def validate_scopes(
    review_map: dict[str, Any],
    manifests: list[dict[str, Any]],
) -> dict[str, Any]:
    fingerprint = verified_review_map_fingerprint(review_map)
    expected = expected_scope_entries(review_map)
    assigned, actual_lenses = collect_scope_assignments(manifests, fingerprint)

    if not REQUIRED_LENSES.issubset(actual_lenses):
        raise ValueError(f"scope lens mismatch: {sorted(actual_lenses)}")
    ui_required = bool(review_map.get("review_policy", {}).get("ui_ux_required"))
    if ui_required != ("ui-ux" in actual_lenses):
        raise ValueError("UI/UX scope mismatch: ui-ux manifest presence must match review policy")

    core_assigned = {
        path: entries
        for path, entries in assigned.items()
        if any(entry.get("_lens") in REQUIRED_LENSES for entry in entries)
    }
    require_complete_scope_paths(expected, assigned)
    missing_core = sorted(set(expected) - set(core_assigned))
    if missing_core:
        raise ValueError(f"core scope path mismatch; missing={missing_core}")
    if ui_required:
        ui_assigned = {
            path
            for path, entries in assigned.items()
            if any(entry.get("_lens") == "ui-ux" for entry in entries)
        }
        required_ui_paths = set(review_map["review_policy"].get("ui_impact_paths", []))
        missing_ui = sorted(required_ui_paths - ui_assigned)
        if not ui_assigned or missing_ui:
            raise ValueError(f"UI/UX scope path mismatch; missing={missing_ui}")

    for path, expected_entry in expected.items():
        validate_path_coverage(path, expected_entry, assigned[path])

    return {
        "review_map_fingerprint": fingerprint,
        "source_fingerprint": review_map.get("source_fingerprint"),
        "review_fingerprint": review_map.get("review_fingerprint"),
        "lenses": sorted(actual_lenses),
        "accounted_paths": len(review_map.get("files", [])),
        "reviewable_paths": len(expected),
        "status": "valid",
    }


def command_build(args: argparse.Namespace) -> int:
    evidence = read_json(args.evidence)
    if args.policy is not None:
        evidence["review_policy"] = read_json(args.policy)
    review_map = build_review_map(evidence)
    write_atomic(args.output, review_map)
    print(
        json.dumps(
            {
                "artifact": str(args.output.resolve()),
                "fingerprint": review_map["fingerprint"],
            }
        )
    )
    return 0


def command_validate_scopes(args: argparse.Namespace) -> int:
    receipt = validate_scopes(
        read_json(args.review_map),
        [read_json(path) for path in args.manifest],
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="build a lossless deterministic review map")
    build.add_argument("--evidence", type=Path, required=True)
    build.add_argument(
        "--policy",
        type=Path,
        help="optional path-class and conditional UI/UX decision JSON",
    )
    build.add_argument("--output", type=Path, required=True)
    build.set_defaults(handler=command_build)

    validate = commands.add_parser(
        "validate-scopes",
        help="validate core and conditional UI/UX scope manifests",
    )
    validate.add_argument("--review-map", type=Path, required=True)
    validate.add_argument("--manifest", type=Path, action="append", required=True)
    validate.set_defaults(handler=command_validate_scopes)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"review-map error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
