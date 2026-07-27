#!/usr/bin/env python3
"""Collect deterministic review-scope evidence from a Git working tree."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")
PY_LOCAL_IMPORT_RE = re.compile(r"^(?P<indent>[ \t]+)(?:from\s+\S+\s+import|import\s+\S+)")
JS_DYNAMIC_IMPORT_RE = re.compile(r"\b(?:import|require)\s*\(")


def git(repo: Path, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def git_text(repo: Path, *args: str, check: bool = True) -> str:
    return git(repo, *args, check=check).decode(errors="replace").strip()


def resolve_base(repo: Path, explicit: str | None) -> str:
    if explicit:
        git(repo, "rev-parse", "--verify", explicit)
        return git_text(repo, "rev-parse", explicit)

    candidates: list[str] = []
    upstream = git_text(
        repo,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        check=False,
    )
    if upstream:
        candidates.append(upstream)
    candidates.extend(["origin/main", "main"])
    head = git_text(repo, "rev-parse", "HEAD")

    for candidate in candidates:
        if not git(repo, "rev-parse", "--verify", candidate, check=False):
            continue
        if git_text(repo, "rev-parse", candidate, check=False) == head:
            continue
        merge_base = git_text(repo, "merge-base", "HEAD", candidate, check=False)
        if merge_base:
            return merge_base

    parent = git_text(repo, "rev-parse", "--verify", "HEAD^", check=False)
    if parent:
        return parent
    return git_text(repo, "hash-object", "-t", "tree", "/dev/null")


def parse_name_status(raw: bytes) -> list[dict[str, str]]:
    tokens = [token.decode(errors="surrogateescape") for token in raw.split(b"\0") if token]
    entries: list[dict[str, str]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if status.startswith(("R", "C")):
            if index + 1 >= len(tokens):
                break
            old_path, path = tokens[index], tokens[index + 1]
            index += 2
            entries.append({"status": status, "path": path, "old_path": old_path})
        else:
            if index >= len(tokens):
                break
            entries.append({"status": status, "path": tokens[index]})
            index += 1
    return entries


def status_group(repo: Path, *args: str) -> list[dict[str, str]]:
    return parse_name_status(git(repo, "diff", "--name-status", "-z", "--find-renames", *args))


def count_lines_bytes(content: bytes) -> int:
    if not content:
        return 0
    return content.count(b"\n") + (0 if content.endswith(b"\n") else 1)


def current_line_count(repo: Path, relative_path: str) -> int | None:
    path = repo / relative_path
    if not path.is_file():
        return None
    try:
        return count_lines_bytes(path.read_bytes())
    except OSError:
        return None


def base_line_count(repo: Path, base: str, relative_path: str) -> int | None:
    result = subprocess.run(
        ["git", "show", f"{base}:{relative_path}"],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        return None
    return count_lines_bytes(result.stdout)


def changed_intervals(repo: Path, base: str, relative_path: str, is_untracked: bool) -> list[list[int]]:
    if is_untracked:
        count = current_line_count(repo, relative_path) or 0
        return [[1, max(1, count)]] if count else []

    patch = git_text(
        repo,
        "diff",
        "--find-renames",
        "--unified=0",
        "--no-ext-diff",
        base,
        "--",
        relative_path,
        check=False,
    )
    intervals: list[list[int]] = []
    for line in patch.splitlines():
        match = HUNK_RE.match(line)
        if not match:
            continue
        start = int(match.group("start"))
        count = int(match.group("count") or "1")
        if count:
            intervals.append([start, start + count - 1])
    return intervals


def rename_map(groups: Iterable[list[dict[str, str]]]) -> dict[str, str]:
    return {
        entry["path"]: entry["old_path"]
        for group in groups
        for entry in group
        if "old_path" in entry
    }


def local_imports(repo: Path, relative_path: str) -> list[dict[str, object]]:
    path = repo / relative_path
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    findings: list[dict[str, object]] = []
    suffix = path.suffix.lower()
    for number, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if suffix == ".py" and PY_LOCAL_IMPORT_RE.match(line):
            findings.append({"line": number, "kind": "python-local-import", "text": stripped})
        elif suffix in {".js", ".jsx", ".ts", ".tsx", ".vue"} and JS_DYNAMIC_IMPORT_RE.search(line):
            findings.append({"line": number, "kind": "dynamic-import", "text": stripped})
    return findings


def unique_paths(groups: Iterable[list[dict[str, str]]], untracked: list[str]) -> list[str]:
    paths = {entry["path"] for group in groups for entry in group}
    paths.update(untracked)
    return sorted(paths)


def collect(repo: Path, explicit_base: str | None) -> dict[str, object]:
    root = Path(git_text(repo, "rev-parse", "--show-toplevel"))
    base = resolve_base(root, explicit_base)
    committed = status_group(root, base, "HEAD")
    staged = status_group(root, "--cached")
    unstaged = status_group(root)
    untracked = [
        token.decode(errors="surrogateescape")
        for token in git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
        if token
    ]
    paths = unique_paths((committed, staged, unstaged), untracked)
    untracked_set = set(untracked)
    renamed_from = rename_map((committed, staged, unstaged))

    files: list[dict[str, object]] = []
    for relative_path in paths:
        current_lines = current_line_count(root, relative_path)
        base_path = renamed_from.get(relative_path, relative_path)
        base_lines = base_line_count(root, base, base_path)
        is_new = base_lines is None and current_lines is not None
        evidence = {
            "path": relative_path,
            "base_path": base_path,
            "base_lines": base_lines,
            "current_lines": current_lines,
            "over_300": bool(current_lines is not None and current_lines > 300),
            "crossed_300": bool(
                current_lines is not None
                and current_lines > 300
                and (base_lines is None or base_lines <= 300)
            ),
            "micro_file_candidate": bool(is_new and current_lines is not None and current_lines <= 40),
            "changed_intervals": changed_intervals(
                root,
                base,
                relative_path,
                relative_path in untracked_set,
            ),
            "local_imports": local_imports(root, relative_path),
        }
        files.append(evidence)

    return {
        "repository": str(root),
        "base": base,
        "head": git_text(root, "rev-parse", "HEAD"),
        "scope": {
            "committed": committed,
            "staged": staged,
            "unstaged": unstaged,
            "untracked": sorted(untracked),
        },
        "files": files,
        "note": "Evidence only: structural and import candidates require human review.",
    }


def markdown(data: dict[str, object]) -> str:
    scope = data["scope"]
    assert isinstance(scope, dict)
    files = data["files"]
    assert isinstance(files, list)
    lines = [
        "# CHANGE EVIDENCE",
        "",
        f"- Repository: `{data['repository']}`",
        f"- Base: `{data['base']}`",
        f"- Head: `{data['head']}`",
        "",
        "## Scope",
        "",
    ]
    for label in ("committed", "staged", "unstaged", "untracked"):
        entries = scope[label]
        lines.append(f"- {label}: {len(entries)}")
    lines.extend(
        [
            "",
            "## File evidence",
            "",
            "| File | Base → current | >300 | Crossed | Micro-file lead | Local imports |",
            "|---|---:|:---:|:---:|:---:|---:|",
        ]
    )
    for entry in files:
        assert isinstance(entry, dict)
        base_lines = entry["base_lines"] if entry["base_lines"] is not None else "new"
        current_lines = entry["current_lines"] if entry["current_lines"] is not None else "deleted"
        lines.append(
            f"| `{entry['path']}` | {base_lines} → {current_lines} | "
            f"{'yes' if entry['over_300'] else 'no'} | "
            f"{'yes' if entry['crossed_300'] else 'no'} | "
            f"{'yes' if entry['micro_file_candidate'] else 'no'} | "
            f"{len(entry['local_imports'])} |"
        )
    lines.extend(["", f"> {data['note']}", ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        data = collect(args.repo.resolve(), args.base)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
