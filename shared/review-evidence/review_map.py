#!/usr/bin/env python3
"""Build and validate lossless review coverage artifacts."""

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
        or lowered.endswith((".min.css", ".min.js", ".map"))
        or lowered.endswith(("_pb2.py", ".g.dart"))
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
        return (
            "dependency-lock",
            "metadata-only",
            "lockfile; inspect dependency deltas, not every serialized line",
        )
    if is_generated_candidate(path, parts):
        return (
            "generated-candidate",
            "metadata-only",
            "generated/vendor candidate; verify provenance and escalate if authored",
        )
    if suffix in BINARY_SUFFIXES:
        return "binary", "metadata-only", "binary content; verify path, type, size, and provenance"
    if current_kind == "symlink":
        return "symlink", "metadata-only", "symlink; verify target and repository boundary"
    if current_kind == "missing":
        if entry.get("base_read_status") == "ok":
            return (
                "deleted-authored",
                "full-content",
                "deleted readable file; inspect authoritative base content",
            )
        return "deleted-unavailable", "metadata-only", "deleted file base content is unavailable"
    if current_kind != "regular" or current_status != "ok":
        return "unavailable", "metadata-only", "content unavailable or not a regular readable file"
    return (
        "authored-text",
        "full-content",
        "human-authored readable text requires full coverage review",
    )


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

    tags = {"changed-path"}
    if suffix in SOURCE_SUFFIXES:
        tags.add("source")
    if suffix in CONFIG_SUFFIXES or name in {"dockerfile", "makefile"}:
        tags.add("configuration")
    if has_test_marker(path, parts):
        tags.add("test")
    if name in LOCK_NAMES or name in DEPENDENCY_MANIFESTS or name.startswith("requirements"):
        tags.add("dependency")
    if DEPLOY_PARTS.intersection(parts) or name.startswith("dockerfile"):
        tags.add("deployment")
    lowered_path = raw_path.lower()
    if TRUST_TERMS.intersection(lexical_tokens) or any(
        term in lowered_path for term in TRUST_TERMS
    ):
        tags.add("trust-boundary-lead")
    instruction_prefixes = ("adr", "architecture", "design", "proposal", "requirement", "spec")
    if (
        name in INSTRUCTION_NAMES
        or INSTRUCTION_PARTS.intersection(parts)
        or name.startswith(instruction_prefixes)
    ):
        tags.add("instruction")
    if entry.get("local_imports"):
        tags.add("import-candidate")
    if any(entry.get(flag) for flag in ("over_300", "crossed_300", "micro_file_candidate")):
        tags.add("structure-lead")
    metadata_classes = {
        "binary",
        "dependency-lock",
        "generated-candidate",
        "symlink",
        "unavailable",
    }
    if classification in metadata_classes:
        tags.add(classification)
    return sorted(tags)


def canonical_fingerprint(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


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


def validate_coverage(review_map: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    expected_files = review_map.get("files")
    entries = ledger.get("entries")
    if not isinstance(expected_files, list) or not isinstance(entries, list):
        raise ValueError("review map files and coverage ledger entries must be lists")
    if ledger.get("review_map_fingerprint") != review_map.get("fingerprint"):
        raise ValueError("coverage ledger review-map fingerprint mismatch")

    expected = {str(item["path"]): item for item in expected_files}
    actual: dict[str, dict[str, Any]] = {}
    for raw_entry in entries:
        if not isinstance(raw_entry, dict) or not isinstance(raw_entry.get("path"), str):
            raise ValueError("each coverage entry needs a string path")
        path = raw_entry["path"]
        if path in actual:
            raise ValueError(f"duplicate coverage path: {path}")
        actual[path] = raw_entry

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing or extra:
        raise ValueError(f"coverage path mismatch; missing={missing}, extra={extra}")

    for path, expected_entry in expected.items():
        entry = actual[path]
        depth = entry.get("reading_depth")
        if depth not in VALID_DEPTHS:
            raise ValueError(f"invalid reading depth for {path}: {depth!r}")
        if entry.get("status") != "reviewed":
            raise ValueError(f"coverage entry is not reviewed: {path}")
        if expected_entry.get("coverage_requirement") == "full-content" and depth != "full-content":
            raise ValueError(f"full-content coverage required for {path}")
        for field in ("purpose", "changed_responsibilities", "placement_owner", "risk_leads"):
            if field not in entry:
                raise ValueError(f"coverage entry {path} is missing {field}")
        if not isinstance(entry["purpose"], str) or not entry["purpose"].strip():
            raise ValueError(f"coverage entry {path} needs a non-empty purpose")
        if not isinstance(entry["placement_owner"], str) or not entry["placement_owner"].strip():
            raise ValueError(f"coverage entry {path} needs a non-empty placement owner")
        if not isinstance(entry["changed_responsibilities"], list):
            raise ValueError(f"coverage entry {path} changed responsibilities must be a list")
        if not isinstance(entry["risk_leads"], list):
            raise ValueError(f"coverage entry {path} risk leads must be a list")

    return {
        "review_map_fingerprint": review_map.get("fingerprint"),
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


def command_validate(args: argparse.Namespace) -> int:
    receipt = validate_coverage(read_json(args.review_map), read_json(args.ledger))
    print(json.dumps(receipt, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="build a lossless deterministic review map")
    build.add_argument("--evidence", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.set_defaults(handler=command_build)

    validate = commands.add_parser("validate", help="validate a full-coverage ledger")
    validate.add_argument("--review-map", type=Path, required=True)
    validate.add_argument("--ledger", type=Path, required=True)
    validate.set_defaults(handler=command_validate)
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
