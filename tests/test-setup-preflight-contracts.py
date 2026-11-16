#!/usr/bin/env python3
"""Lock Full-workflow Setup preflight: analyzer probe and run-start dirty baseline."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
COLLECT = ROOT / "shared/review-evidence/collect-change-evidence.sh"
REVIEW_MAP = ROOT / "shared/review-evidence/review-map.sh"
PRESERVED = ("notes/staged.txt", "notes/unstaged.txt", "notes/untracked.txt")


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.lower().split())


def require(text: str, *phrases: str) -> None:
    flat = normalized(text)
    for phrase in phrases:
        assert phrase.lower() in flat, phrase


def setup_section() -> str:
    skill = read("workflow/skills/sk-team-feature/SKILL.md")
    start = skill.index("## Setup")
    return normalized(skill[start : skill.index("\n## ", start + 1)])


def check_setup_contract() -> None:
    setup = setup_section()
    require(
        setup,
        "run-static-analysis.sh --probe-only",
        "settle the analyzer install decision with the user now",
        "no authorization mode, yolo included, installs tools",
        "record the analyzer probe and its install decision",
        "run-start hashes",
        "register each run-start baseline with `record-artifact` before leaving setup",
    )
    ordered = (
        "--probe-only",
        "run-start hashes",
        "resolve the workspace once",
        "create `openspec/changes/<name>/`",
        "enter setup as the first stage",
    )
    positions = [setup.index(phrase) for phrase in ordered]
    assert positions == sorted(positions), "Setup must probe and capture before it writes"


def check_reference_contracts() -> None:
    require(
        read("workflow/agents/references/review-tooling.md"),
        "## probe at workflow setup",
        "run-static-analysis.sh --probe-only",
        "is never valid review provenance",
        "code review reuses it instead of asking again",
        "unless the workflow's setup probe already recorded the user's decision",
        "lizard warning rows (not its always-printed threshold banner)",
    )
    require(
        read("workflow/agents/shared/workspace-lifecycle.md"),
        "## run-start baseline for dirty repositories",
        "--base head --format json",
        "kind `run-start-baseline`",
        "never from the snapshot under review",
        "cannot be classified `preserved_baseline`",
    )
    require(
        read("workflow/agents/shared/scope-governance.md"),
        "run-start capture in `workspace-lifecycle.md`, never from snapshot time",
    )


def git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments], capture_output=True, check=True, text=True
    )
    return completed.stdout.strip()


def helper(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(script), *arguments],
        capture_output=True,
        check=False,
        text=True,
        env={**os.environ, "PYTHON": sys.executable},
        timeout=60,
    )


def make_dirty_repository(repo: Path) -> str:
    (repo / "notes").mkdir(parents=True)
    (repo / "src").mkdir()
    for name in ("staged", "unstaged"):
        (repo / f"notes/{name}.txt").write_text(f"{name} committed\n")
    (repo / "src/app.py").write_text("VALUE = 1\n")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    identity = ("-c", "user.name=test", "-c", "user.email=test@example.invalid")
    git(repo, *identity, "-c", "commit.gpgsign=false", "commit", "-q", "--no-verify", "-m", "b")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "notes/staged.txt").write_text("staged edit\n")
    git(repo, "add", "notes/staged.txt")
    (repo / "notes/unstaged.txt").write_text("unstaged edit\n")
    (repo / "notes/untracked.txt").write_text("untracked note\n")
    return base


def capture(repo: Path, base: str, output: Path) -> dict[str, Any]:
    completed = helper(
        COLLECT, "--repo", str(repo), "--base", base, "--format", "json", "--output", str(output)
    )
    assert completed.returncode == 0, completed.stderr
    evidence: dict[str, Any] = json.loads(output.read_text())
    return evidence


def build_map(root: Path, evidence: str, policy: Path) -> subprocess.CompletedProcess[str]:
    return helper(
        REVIEW_MAP,
        "build",
        "--evidence",
        str(root / evidence),
        "--policy",
        str(policy),
        "--output",
        str(root / f"map-{evidence}"),
    )


def write_policy(root: Path, run_start: dict[str, Any]) -> Path:
    hashes = {entry["path"]: entry["current_sha256"] for entry in run_start["files"]}
    assert sorted(hashes) == list(PRESERVED), f"run start must list exactly dirty paths: {hashes}"
    policy = {
        "path_classes": dict.fromkeys(PRESERVED, "preserved_baseline"),
        "path_class_reasons": dict.fromkeys(PRESERVED, "dirty before run start"),
        "preserved_baseline_hashes": hashes,
    }
    path = root / "policy.json"
    path.write_text(json.dumps(policy))
    return path


def check_run_start_baseline_proves_preserved_identity() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        repo = root / "repo"
        base = make_dirty_repository(repo)
        run_start = capture(repo, "HEAD", root / "run-start/repo-dirty-baseline.json")
        policy = write_policy(root, run_start)

        (repo / "src/app.py").write_text("VALUE = 2\n")
        capture(repo, base, root / "first.json")
        built = build_map(root, "first.json", policy)
        assert built.returncode == 0, built.stderr
        files = json.loads((root / "map-first.json").read_text())["files"]
        classes = {entry["path"]: entry["review_class"] for entry in files}
        assert classes["src/app.py"] == "reviewable", classes
        assert {classes[path] for path in PRESERVED} == {"preserved_baseline"}, classes

        (repo / "notes/unstaged.txt").write_text("edited after run start\n")
        capture(repo, base, root / "second.json")
        rejected = build_map(root, "second.json", policy)
        assert rejected.returncode != 0, rejected.stdout
        expected = "preserved baseline changed after capture: notes/unstaged.txt"
        assert expected in rejected.stderr, rejected.stderr


def main() -> None:
    check_setup_contract()
    check_reference_contracts()
    check_run_start_baseline_proves_preserved_identity()
    print("OK: setup preflight contracts")


if __name__ == "__main__":
    main()
