"""Source validation for the manifest-owned skill suite."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from skills_common import Issue, REPO_ROOT


FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
NAME_RE = re.compile(r"^[a-z0-9-]{1,63}$")


def parse_frontmatter(path: Path) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        raise ValueError("missing YAML frontmatter")
    values: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if line.startswith((" ", "\t", "#")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def validate_openai_yaml(skill_dir: Path) -> list[Issue]:
    path = skill_dir / "agents" / "openai.yaml"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    issues: list[Issue] = []
    required = ("display_name:", "short_description:", "default_prompt:")
    if not all(field in text for field in required):
        issues.append(Issue("ERROR", f"{path}: incomplete interface metadata"))
    expected = f"${skill_dir.name}"
    if expected not in text:
        issues.append(Issue("ERROR", f"{path}: default_prompt must mention {expected}"))
    return issues


def validate_manifest_items(manifest: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    seen_names: dict[str, str] = {}
    limits = {
        "catalog": int(manifest["limits"]["catalog_skill_lines"]),
        "onboarding": int(manifest["limits"]["catalog_skill_lines"]),
        "agents": int(manifest["limits"]["agent_prompt_lines"]),
        "review_steps": int(manifest["limits"]["agent_prompt_lines"]),
    }
    for group in limits:
        for item in manifest[group]:
            source = REPO_ROOT / item["source"]
            name = item["name"]
            if not source.exists():
                issues.append(Issue("ERROR", f"missing source: {item['source']}"))
                continue
            if not NAME_RE.fullmatch(name):
                issues.append(Issue("ERROR", f"invalid name: {name}"))
            if previous := seen_names.get(name):
                issues.append(Issue("ERROR", f"duplicate name {name}: {previous}, {group}"))
            seen_names[name] = group
            prompt = source / "SKILL.md" if source.is_dir() else source
            try:
                frontmatter = parse_frontmatter(prompt)
            except ValueError as error:
                issues.append(Issue("ERROR", f"{prompt}: {error}"))
                continue
            if frontmatter.get("name") != name:
                issues.append(
                    Issue("ERROR", f"{prompt}: name {frontmatter.get('name')!r} != {name!r}")
                )
            if not frontmatter.get("description"):
                issues.append(Issue("ERROR", f"{prompt}: missing description"))
            line_total = len(prompt.read_text(encoding="utf-8").splitlines())
            if line_total > limits[group]:
                relative = prompt.relative_to(REPO_ROOT)
                issues.append(
                    Issue("ERROR", f"{relative}: {line_total} lines > {limits[group]}")
                )
            if source.is_dir() and group == "catalog":
                issues.extend(validate_openai_yaml(source))
    for item in manifest["resources"]:
        if not (REPO_ROOT / item["source"]).exists():
            issues.append(Issue("ERROR", f"missing resource tree: {item['source']}"))
    return issues


def validate_scripts() -> list[Issue]:
    issues: list[Issue] = []
    shell_scripts = [
        path for path in sorted(REPO_ROOT.rglob("*.sh")) if ".git" not in path.parts
    ]
    for script in shell_scripts:
        result = subprocess.run(
            ["bash", "-n", str(script)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            relative = script.relative_to(REPO_ROOT)
            issues.append(
                Issue("ERROR", f"{relative}: bash -n failed: {result.stderr.strip()}")
            )
    if shellcheck := shutil.which("shellcheck"):
        result = subprocess.run(
            [shellcheck, *map(str, shell_scripts)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            issues.append(
                Issue("ERROR", f"shellcheck failed:\n{result.stdout}{result.stderr}".rstrip())
            )
    for source in sorted(REPO_ROOT.rglob("*.py")):
        if ".git" in source.parts:
            continue
        try:
            compile(source.read_text(encoding="utf-8"), str(source), "exec")
        except (SyntaxError, UnicodeDecodeError) as error:
            issues.append(
                Issue(
                    "ERROR",
                    f"{source.relative_to(REPO_ROOT)}: Python syntax failed: {error}",
                )
            )
    return issues


def validate(manifest: dict[str, Any]) -> list[Issue]:
    return [*validate_manifest_items(manifest), *validate_scripts()]
