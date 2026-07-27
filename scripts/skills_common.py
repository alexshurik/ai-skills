"""Shared data and filesystem helpers for the skill toolchain."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "skills-manifest.yaml"
RECEIPT_NAME = ".sk-skills-install.json"
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".txt"}


@dataclass(frozen=True)
class Issue:
    level: str
    message: str


def load_manifest() -> dict[str, Any]:
    # JSON is a strict subset of YAML 1.2 and needs no third-party parser.
    with MANIFEST_PATH.open(encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def entry_value(path: Path) -> str | None:
    if path.is_symlink():
        return f"symlink:{path.readlink()}"
    if path.is_file():
        return hash_file(path)
    return None


def tree_entries(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    entries: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        value = entry_value(path)
        if value is not None:
            entries[path.relative_to(root).as_posix()] = value
    return entries


def source_revision() -> tuple[str, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    return commit or "unknown", dirty
