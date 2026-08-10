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


def safe_relative(value: str) -> Path:
    """Return a relative path that cannot escape its intended root."""
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"unsafe manifest/receipt path: {value!r}")
    return relative


def repo_source_path(value: str) -> Path:
    """Return a lexical manifest source after proving its target is in-repo."""
    source = REPO_ROOT / safe_relative(value)
    resolved = source.resolve()
    if resolved != REPO_ROOT and REPO_ROOT not in resolved.parents:
        raise ValueError(f"manifest source escapes repository: {value!r}")
    return source


def load_manifest() -> dict[str, Any]:
    # JSON is a strict subset of YAML 1.2 and needs no third-party parser.
    with MANIFEST_PATH.open(encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)
    if not isinstance(manifest, dict):
        raise ValueError("skills manifest root must be an object")
    return manifest


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
