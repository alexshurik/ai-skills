#!/usr/bin/env python3
"""Full evidence collection must gate large blobs before show/diff capture."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "shared" / "review-evidence"))

import collect_change_evidence as evidence  # noqa: E402

LARGE_BYTES = 5 * 1024 * 1024 + 1
LARGE_PATHS = {"large-base.txt", "large-current.txt"}
LARGE_BASE_PATH = "large-base.txt"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def write_large(path: Path, marker: bytes) -> None:
    with path.open("wb") as output:
        output.write(marker)
        output.truncate(LARGE_BYTES)


def prepare_repository(root: Path) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.email", "skills-test@example.invalid")
    git(root, "config", "user.name", "Skills Test")
    write_large(root / "large-base.txt", b"BASE_SECRET")
    (root / "large-current.txt").write_text("small base\n", encoding="utf-8")
    (root / "normal.txt").write_text("before\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "baseline")
    (root / "large-base.txt").write_text("small current\n", encoding="utf-8")
    write_large(root / "large-current.txt", b"CURRENT_SECRET")
    (root / "normal.txt").write_text("after\n", encoding="utf-8")


def guarded_run(
    original: Callable[..., subprocess.CompletedProcess[bytes]],
) -> Callable[..., subprocess.CompletedProcess[bytes]]:
    def run(
        command: list[str], *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        if command[:2] == ["git", "show"]:
            assert LARGE_BASE_PATH not in command[-1]
        return original(command, *args, **kwargs)

    return run


def guarded_popen(
    original: Callable[..., subprocess.Popen[bytes]],
) -> Callable[..., subprocess.Popen[bytes]]:
    def popen(command: list[str], *args: object, **kwargs: object) -> subprocess.Popen[bytes]:
        is_interval_diff = "--unified=0" in command
        if is_interval_diff:
            assert not any(path in command for path in LARGE_PATHS)
        return original(command, *args, **kwargs)

    return popen


def evidence_files(data: dict[str, object]) -> dict[str, dict[str, object]]:
    values = data.get("files")
    if not isinstance(values, list):
        raise TypeError("evidence files must be a list")
    entries = [item for item in values if isinstance(item, dict)]
    if len(entries) != len(values):
        raise TypeError("evidence file entries must be objects")
    return {str(item["path"]): item for item in entries}


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sk-evidence-git-bounds-") as temporary:
        root = Path(temporary).resolve()
        prepare_repository(root)
        real_run = subprocess.run
        real_popen = subprocess.Popen
        with (
            mock.patch.object(
                evidence.subprocess,
                "run",
                side_effect=guarded_run(real_run),
            ),
            mock.patch.object(
                evidence.subprocess,
                "Popen",
                side_effect=guarded_popen(real_popen),
            ),
        ):
            data = evidence.collect(root, "HEAD")
            with mock.patch.object(evidence, "MAX_GIT_DIFF_BYTES", 1):
                output_limited_data = evidence.collect(root, "HEAD")

    files = evidence_files(data)
    assert files["large-base.txt"]["base_read_status"] == "size-limit"
    assert files["large-base.txt"]["interval_status"] == "size-limit"
    assert files["large-current.txt"]["current_read_status"] == "size-limit"
    assert files["large-current.txt"]["interval_status"] == "size-limit"
    assert files["normal.txt"]["interval_status"] == "ok"
    assert files["normal.txt"]["changed_intervals"]
    assert "BASE_SECRET" not in repr(data)
    assert "CURRENT_SECRET" not in repr(data)

    bounded_markdown = evidence.markdown(data)
    assert "| `large-base.txt` | size-limit → 1 |" in bounded_markdown
    assert "| `large-current.txt` | 1 → size-limit |" in bounded_markdown
    assert "- `large-base.txt`: interval status `size-limit`" in bounded_markdown
    assert "- `large-current.txt`: interval status `size-limit`" in bounded_markdown

    output_limited_files = evidence_files(output_limited_data)
    assert output_limited_files["normal.txt"]["interval_status"] == "output-limit"
    output_limited_markdown = evidence.markdown(output_limited_data)
    assert "- `normal.txt`: interval status `output-limit`" in output_limited_markdown


if __name__ == "__main__":
    main()
    print("OK: evidence Git bounds")
