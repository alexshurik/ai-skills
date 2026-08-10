#!/usr/bin/env python3
"""Collect deterministic review-scope evidence from a Git working tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")
PY_LOCAL_IMPORT_RE = re.compile(r"^(?P<indent>[ \t]+)(?:from\s+\S+\s+import|import\s+\S+)")
JS_DYNAMIC_IMPORT_RE = re.compile(r"\b(?:import|require)\s*\(")
MAX_EVIDENCE_FILE_BYTES = 4 * 1024 * 1024
# Even when both file sides are individually bounded, diff syntax adds bytes.
# Stream at most this many bytes and discard intervals if Git exceeds the cap.
MAX_GIT_DIFF_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True)
class ChangeScope:
    committed: list[dict[str, str]]
    staged: list[dict[str, str]]
    unstaged: list[dict[str, str]]
    untracked: list[str]

    def tracked_groups(self) -> tuple[list[dict[str, str]], ...]:
        return self.committed, self.staged, self.unstaged

    def as_dict(self) -> dict[str, object]:
        return {
            "committed": self.committed,
            "staged": self.staged,
            "unstaged": self.unstaged,
            "untracked": sorted(self.untracked),
        }


@dataclass(frozen=True)
class EvidenceContext:
    root: Path
    base: str
    untracked: frozenset[str]
    renamed_from: dict[str, str]


@dataclass(frozen=True)
class CurrentEntry:
    kind: str
    content: bytes | None = None
    symlink_target: str | None = None
    read_status: str = "not-applicable"
    size: int | None = None


@dataclass(frozen=True)
class BaseEntry:
    exists: bool
    size: int | None
    line_count: int | None
    read_status: str
    blob_oid: str | None


@dataclass(frozen=True)
class FileSides:
    current: CurrentEntry
    base: BaseEntry


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


def directory_flags() -> int | None:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if not isinstance(no_follow, int) or not isinstance(directory, int):
        return None
    return os.O_RDONLY | no_follow | directory


def relative_parts(relative_path: str) -> tuple[str, ...]:
    relative = PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"unsafe evidence path: {relative_path!r}")
    if any(not part or "\0" in part for part in relative.parts):
        raise ValueError(f"unsafe evidence path: {relative_path!r}")
    return relative.parts


def ancestor_failure_kind(parent_fd: int, name: str) -> str:
    try:
        metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return "ancestor-unavailable"
    if stat.S_ISLNK(metadata.st_mode):
        return "ancestor-symlink"
    return "ancestor-nondirectory"


def open_parent_directory(
    root_fd: int,
    parts: tuple[str, ...],
) -> tuple[int | None, str | None]:
    flags = directory_flags()
    if flags is None:
        return None, "no-follow-unavailable"
    current = os.dup(root_fd)
    for part in parts[:-1]:
        try:
            child = os.open(part, flags, dir_fd=current)
        except OSError:
            kind = ancestor_failure_kind(current, part)
            os.close(current)
            return None, kind
        os.close(current)
        current = child
    return current, None


def bounded_regular_content(
    parent_fd: int,
    name: str,
    before: os.stat_result,
) -> tuple[bytes | None, str]:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:
        return None, "no-follow-unavailable"
    flags = os.O_RDONLY | no_follow | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except OSError:
        return None, "unavailable"
    with os.fdopen(descriptor, "rb") as current_file:
        opened = os.fstat(current_file.fileno())
        if not same_entry(before, opened) or not stat.S_ISREG(opened.st_mode):
            return None, "changed"
        if opened.st_size > MAX_EVIDENCE_FILE_BYTES:
            return None, "size-limit"
        content = current_file.read(MAX_EVIDENCE_FILE_BYTES + 1)
        if len(content) > MAX_EVIDENCE_FILE_BYTES:
            return None, "size-limit"
        return content, "ok"


def same_entry(first: os.stat_result, second: os.stat_result) -> bool:
    return (first.st_dev, first.st_ino) == (second.st_dev, second.st_ino)


def descriptor_symlink_target(
    parent_fd: int,
    name: str,
    before: os.stat_result,
) -> str | None:
    try:
        target = os.readlink(name, dir_fd=parent_fd)
        after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return None
    return target if same_entry(before, after) else None


def entry_from_parent(parent_fd: int, name: str) -> CurrentEntry:
    try:
        metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return CurrentEntry("missing")
    except OSError:
        return CurrentEntry("unavailable", read_status="unavailable")
    if stat.S_ISLNK(metadata.st_mode):
        target = descriptor_symlink_target(parent_fd, name, metadata)
        return CurrentEntry(
            "symlink",
            symlink_target=target,
            size=metadata.st_size,
        )
    if stat.S_ISREG(metadata.st_mode):
        content, status = bounded_regular_content(parent_fd, name, metadata)
        return CurrentEntry(
            "regular",
            content=content,
            read_status=status,
            size=metadata.st_size,
        )
    if stat.S_ISDIR(metadata.st_mode):
        return CurrentEntry("directory")
    return CurrentEntry("other")


def inspect_current_entry(repo: Path, relative_path: str) -> CurrentEntry:
    flags = directory_flags()
    if flags is None:
        return CurrentEntry("unavailable", read_status="no-follow-unavailable")
    try:
        parts = relative_parts(relative_path)
        root_fd = os.open(repo, flags)
    except (OSError, ValueError):
        return CurrentEntry("unavailable", read_status="unavailable")
    try:
        parent_fd, failure = open_parent_directory(root_fd, parts)
        if parent_fd is None:
            return CurrentEntry(failure or "unavailable", read_status="blocked")
        try:
            return entry_from_parent(parent_fd, parts[-1])
        finally:
            os.close(parent_fd)
    finally:
        os.close(root_fd)


def current_line_count(repo: Path, relative_path: str) -> int | None:
    content = inspect_current_entry(repo, relative_path).content
    return count_lines_bytes(content) if content is not None else None


def base_entry(repo: Path, base: str, relative_path: str) -> BaseEntry:
    object_name = f"{base}:{relative_path}"
    blob_oid = git_text(repo, "rev-parse", object_name, check=False) or None
    size_result = subprocess.run(
        ["git", "cat-file", "-s", object_name],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    if size_result.returncode:
        return BaseEntry(False, None, None, "missing", None)
    try:
        size = int(size_result.stdout.strip())
    except ValueError:
        return BaseEntry(True, None, None, "unavailable", blob_oid)
    if size > MAX_EVIDENCE_FILE_BYTES:
        return BaseEntry(True, size, None, "size-limit", blob_oid)
    result = subprocess.run(
        ["git", "show", object_name],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    if result.returncode or len(result.stdout) > MAX_EVIDENCE_FILE_BYTES:
        return BaseEntry(True, size, None, "unavailable", blob_oid)
    return BaseEntry(True, size, count_lines_bytes(result.stdout), "ok", blob_oid)


def base_line_count(repo: Path, base: str, relative_path: str) -> int | None:
    return base_entry(repo, base, relative_path).line_count


def git_limited(
    repo: Path,
    arguments: list[str],
    limit: int,
) -> tuple[bytes | None, str]:
    process = subprocess.Popen(
        ["git", *arguments],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert process.stdout is not None
    content = process.stdout.read(limit + 1)
    if len(content) > limit:
        process.kill()
        process.wait()
        return None, "output-limit"
    return_code = process.wait()
    return (content, "ok") if return_code == 0 else (None, "unavailable")


def interval_gate(sides: FileSides) -> str | None:
    if "size-limit" in {
        sides.current.read_status,
        sides.base.read_status,
    }:
        return "size-limit"
    current_ok = sides.current.kind in {"missing", "symlink"} or (
        sides.current.kind == "regular" and sides.current.read_status == "ok"
    )
    base_ok = sides.base.read_status in {"missing", "ok"}
    return None if current_ok and base_ok else "unavailable"


def untracked_intervals(current: CurrentEntry) -> list[list[int]]:
    count = count_lines_bytes(current.content) if current.content is not None else 0
    return [[1, max(1, count)]] if count else []


def parse_hunk_intervals(patch: bytes) -> list[list[int]]:
    intervals: list[list[int]] = []
    for line in patch.decode(errors="replace").splitlines():
        match = HUNK_RE.match(line)
        if not match:
            continue
        start = int(match.group("start"))
        count = int(match.group("count") or "1")
        if count:
            intervals.append([start, start + count - 1])
    return intervals


def changed_intervals(
    context: EvidenceContext,
    relative_path: str,
    sides: FileSides,
) -> tuple[list[list[int]], str]:
    if gate := interval_gate(sides):
        return [], gate
    if relative_path in context.untracked:
        return untracked_intervals(sides.current), "ok"

    patch, status = git_limited(
        context.root,
        [
            "diff",
            "--find-renames",
            "--unified=0",
            "--no-ext-diff",
            "--no-textconv",
            context.base,
            "--",
            relative_path,
        ],
        MAX_GIT_DIFF_BYTES,
    )
    if patch is None:
        return [], status
    return parse_hunk_intervals(patch), "ok"


def rename_map(groups: Iterable[list[dict[str, str]]]) -> dict[str, str]:
    return {
        entry["path"]: entry["old_path"]
        for group in groups
        for entry in group
        if "old_path" in entry
    }


def import_finding(
    suffix: str,
    number: int,
    line: str,
) -> dict[str, object] | None:
    stripped = line.lstrip()
    if not stripped or stripped.startswith("#"):
        return None
    if suffix == ".py" and PY_LOCAL_IMPORT_RE.match(line):
        return {"line": number, "kind": "python-local-import", "text": stripped}
    script_suffixes = {".js", ".jsx", ".ts", ".tsx", ".vue"}
    if suffix in script_suffixes and JS_DYNAMIC_IMPORT_RE.search(line):
        return {"line": number, "kind": "dynamic-import", "text": stripped}
    return None


def local_imports(
    relative_path: str,
    content: bytes | None,
) -> list[dict[str, object]]:
    if content is None:
        return []
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return []

    findings: list[dict[str, object]] = []
    suffix = Path(relative_path).suffix.lower()
    for number, line in enumerate(lines, start=1):
        finding = import_finding(suffix, number, line)
        if finding is not None:
            findings.append(finding)
    return findings


def unique_paths(groups: Iterable[list[dict[str, str]]], untracked: list[str]) -> list[str]:
    paths = {entry["path"] for group in groups for entry in group}
    paths.update(untracked)
    return sorted(paths)


def collect_scope(root: Path, base: str) -> ChangeScope:
    committed = status_group(root, base, "HEAD")
    staged = status_group(root, "--cached")
    unstaged = status_group(root)
    untracked = [
        token.decode(errors="surrogateescape")
        for token in git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
        if token
    ]
    return ChangeScope(committed, staged, unstaged, untracked)


def structural_flags(
    current: CurrentEntry,
    current_lines: int | None,
    base: BaseEntry,
) -> dict[str, bool]:
    is_new = not base.exists and current.kind == "regular"
    over_300 = current_lines is not None and current_lines > 300
    crossed_300 = over_300 and (
        not base.exists or (base.line_count is not None and base.line_count <= 300)
    )
    micro_file = is_new and current_lines is not None and current_lines <= 40
    return {
        "over_300": over_300,
        "crossed_300": crossed_300,
        "micro_file_candidate": micro_file,
    }


def current_digest(current: CurrentEntry) -> str | None:
    if current.kind == "regular" and current.content is not None:
        return hashlib.sha256(current.content).hexdigest()
    if current.kind == "symlink" and current.symlink_target is not None:
        return hashlib.sha256(current.symlink_target.encode(errors="surrogateescape")).hexdigest()
    return None


def file_evidence(
    context: EvidenceContext,
    relative_path: str,
) -> dict[str, object]:
    current = inspect_current_entry(context.root, relative_path)
    current_lines = count_lines_bytes(current.content) if current.content is not None else None
    base_path = context.renamed_from.get(relative_path, relative_path)
    base = base_entry(context.root, context.base, base_path)
    sides = FileSides(current, base)
    intervals, interval_status = changed_intervals(
        context,
        relative_path,
        sides,
    )
    return {
        "path": relative_path,
        "base_path": base_path,
        "base_lines": base.line_count,
        "base_size": base.size,
        "base_read_status": base.read_status,
        "base_blob_oid": base.blob_oid,
        "current_kind": current.kind,
        "current_symlink_target": current.symlink_target,
        "current_read_status": current.read_status,
        "current_size": current.size,
        "current_lines": current_lines,
        "current_sha256": current_digest(current),
        **structural_flags(current, current_lines, base),
        "changed_intervals": intervals,
        "interval_status": interval_status,
        "local_imports": local_imports(relative_path, current.content),
    }


def collect(repo: Path, explicit_base: str | None) -> dict[str, object]:
    root = Path(git_text(repo, "rev-parse", "--show-toplevel"))
    base = resolve_base(root, explicit_base)
    scope = collect_scope(root, base)
    groups = scope.tracked_groups()
    paths = unique_paths(groups, scope.untracked)
    context = EvidenceContext(
        root,
        base,
        frozenset(scope.untracked),
        rename_map(groups),
    )
    files = [file_evidence(context, relative_path) for relative_path in paths]

    evidence: dict[str, object] = {
        "repository": str(root),
        "base": base,
        "head": git_text(root, "rev-parse", "HEAD"),
        "scope": scope.as_dict(),
        "files": files,
        "note": "Evidence only: structural and import candidates require human review.",
    }
    canonical = json.dumps(
        evidence,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    evidence["fingerprint"] = hashlib.sha256(canonical).hexdigest()
    return evidence


def markdown_base_value(entry: dict[str, object]) -> object:
    if entry["base_lines"] is not None:
        return entry["base_lines"]
    if entry["base_read_status"] == "missing":
        return "new"
    return entry["base_read_status"]


def markdown_current_value(entry: dict[str, object]) -> object:
    if entry["current_lines"] is not None:
        return entry["current_lines"]
    if entry["current_kind"] == "missing":
        return "deleted"
    read_status = entry["current_read_status"]
    if read_status not in {"ok", "not-applicable"}:
        return read_status
    return entry["current_kind"]


def incomplete_interval_lines(files: list[object]) -> list[str]:
    incomplete = [
        entry
        for entry in files
        if isinstance(entry, dict) and entry["interval_status"] not in {"complete", "ok"}
    ]
    if not incomplete:
        return []
    lines = ["", "### Incomplete changed-line evidence", ""]
    lines.extend(
        f"- `{entry['path']}`: interval status `{entry['interval_status']}`" for entry in incomplete
    )
    return lines


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
        f"- Fingerprint: `{data['fingerprint']}`",
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
        base_lines = markdown_base_value(entry)
        current_lines = markdown_current_value(entry)
        lines.append(
            f"| `{entry['path']}` | {base_lines} → {current_lines} | "
            f"{'yes' if entry['over_300'] else 'no'} | "
            f"{'yes' if entry['crossed_300'] else 'no'} | "
            f"{'yes' if entry['micro_file_candidate'] else 'no'} | "
            f"{len(entry['local_imports'])} |"
        )
    lines.extend(incomplete_interval_lines(files))
    lines.extend(["", f"> {data['note']}", ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument(
        "--output",
        type=Path,
        help="Atomically write full evidence to this artifact and print only a receipt",
    )
    return parser


def render(data: dict[str, object], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(data, indent=2, sort_keys=True) + "\n"
    return markdown(data)


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary_name = temporary.name
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            with suppress(FileNotFoundError):
                os.unlink(temporary_name)


def main() -> int:
    args = build_parser().parse_args()
    try:
        data = collect(args.repo.resolve(), args.base)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    rendered = render(data, args.format)
    if args.output:
        artifact = args.output.expanduser().resolve()
        write_atomic(artifact, rendered)
        print(
            json.dumps(
                {"artifact": str(artifact), "fingerprint": data["fingerprint"]},
                sort_keys=True,
            )
        )
    else:
        print(rendered, end="" if rendered.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
