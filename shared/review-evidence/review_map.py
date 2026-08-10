#!/usr/bin/env python3
"""Build a lossless review map and validate three-lens scope manifests."""

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


def build_review_map(evidence: dict[str, Any]) -> dict[str, Any]:
    files = evidence.get("files")
    if not isinstance(files, list):
        raise ValueError("evidence.files must be a list")
    if not isinstance(evidence.get("fingerprint"), str):
        raise ValueError("evidence fingerprint must be a string")

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
        classification, requirement, reason = content_class(raw_entry)
        mapped.append(
            {
                "path": path,
                "base_path": raw_entry.get("base_path"),
                "base_blob_oid": raw_entry.get("base_blob_oid"),
                "content_class": classification,
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
            }
        )

    review_map: dict[str, Any] = {
        "schema_version": 1,
        "repository": evidence.get("repository"),
        "base": evidence.get("base"),
        "head": evidence.get("head"),
        "evidence_fingerprint": evidence.get("fingerprint"),
        "files": sorted(mapped, key=lambda item: item["path"]),
        "note": "Lossless deterministic inventory. Risk tags are leads, not review verdicts.",
    }
    review_map["fingerprint"] = canonical_fingerprint(review_map)
    return review_map


def expected_scope_entries(review_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected_files = review_map.get("files")
    if not isinstance(expected_files, list):
        raise ValueError("review map files must be a list")
    return {str(item["path"]): item for item in expected_files}


def manifest_entries(
    manifest: dict[str, Any],
    fingerprint: str,
    actual_lenses: set[str],
) -> tuple[str, list[dict[str, Any]]]:
    lens = manifest.get("lens")
    entries = manifest.get("entries")
    if lens not in REQUIRED_LENSES or lens in actual_lenses:
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
    if len(manifests) != len(REQUIRED_LENSES):
        raise ValueError("exactly three scope manifests are required")

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
            assigned.setdefault(path, []).append(entry)
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

    if actual_lenses != REQUIRED_LENSES:
        raise ValueError(f"scope lens mismatch: {sorted(actual_lenses)}")
    require_complete_scope_paths(expected, assigned)

    for path, expected_entry in expected.items():
        validate_path_coverage(path, expected_entry, assigned[path])

    return {
        "review_map_fingerprint": fingerprint,
        "lenses": sorted(actual_lenses),
        "paths": len(expected),
        "status": "valid",
    }


def command_build(args: argparse.Namespace) -> int:
    evidence = read_json(args.evidence)
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
    build.add_argument("--output", type=Path, required=True)
    build.set_defaults(handler=command_build)

    validate = commands.add_parser(
        "validate-scopes",
        help="validate the three-lens scope-manifest union",
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
