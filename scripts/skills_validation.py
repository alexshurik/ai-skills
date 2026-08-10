"""Source and rendered-tree validation for the manifest-owned skill suite."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skills_common import REPO_ROOT, Issue, repo_source_path, safe_relative
from skills_render import RenderContext, render_tree

FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*]\((?P<target>[^)]+)\)")
NAME_RE = re.compile(r"^[a-z0-9-]{1,63}$")
URI_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
PROMPT_GROUPS = ("catalog", "onboarding", "agents", "review_steps")
MANIFEST_GROUPS = (*PROMPT_GROUPS, "resources")
PLATFORM_TARGETS = {
    "codex": "codex_target",
    "cursor": "cursor_target",
    "claude": "claude_target",
    "kimi": "kimi_target",
}


@dataclass
class ValidationState:
    limits: dict[str, int]
    issues: list[Issue] = field(default_factory=list)
    seen_names: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptSpec:
    path: Path
    name: str
    line_limit: int


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


def positive_integer_issue(value: Any, label: str) -> list[Issue]:
    is_positive_integer = isinstance(value, int) and not isinstance(value, bool) and value > 0
    if is_positive_integer:
        return []
    return [Issue("ERROR", f"{label} must be a positive integer")]


def validate_limits_shape(value: Any) -> list[Issue]:
    if not isinstance(value, dict):
        return [Issue("ERROR", "manifest limits must be an object")]
    return [
        issue
        for field_name in ("catalog_skill_lines", "agent_prompt_lines")
        for issue in positive_integer_issue(
            value.get(field_name),
            f"manifest limit {field_name}",
        )
    ]


def validate_group_shape(manifest: dict[str, Any], group: str) -> list[Issue]:
    items = manifest.get(group)
    if not isinstance(items, list):
        return [Issue("ERROR", f"manifest {group} must be a list")]
    return [
        Issue("ERROR", f"manifest {group} item {index} must be an object")
        for index, item in enumerate(items)
        if not isinstance(item, dict)
    ]


def validate_manifest_shape(manifest: Any) -> list[Issue]:
    if not isinstance(manifest, dict):
        return [Issue("ERROR", "manifest root must be an object")]
    return [
        *positive_integer_issue(manifest.get("version"), "manifest version"),
        *validate_limits_shape(manifest.get("limits")),
        *[issue for group in MANIFEST_GROUPS for issue in validate_group_shape(manifest, group)],
    ]


def manifest_limits(manifest: dict[str, Any]) -> dict[str, int]:
    limits = manifest["limits"]
    return {
        "catalog": int(limits["catalog_skill_lines"]),
        "onboarding": int(limits["catalog_skill_lines"]),
        "agents": int(limits["agent_prompt_lines"]),
        "review_steps": int(limits["agent_prompt_lines"]),
    }


def item_source(item: dict[str, Any], state: ValidationState) -> Path | None:
    value = item.get("source")
    if not isinstance(value, str):
        state.issues.append(Issue("ERROR", f"invalid source path: {value!r}"))
        return None
    try:
        return repo_source_path(value)
    except ValueError as error:
        state.issues.append(Issue("ERROR", str(error)))
        return None


def validate_item_identity(
    item: dict[str, Any],
    group: str,
    state: ValidationState,
) -> str | None:
    name = item.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        state.issues.append(Issue("ERROR", f"invalid name: {name!r}"))
        return None
    if previous := state.seen_names.get(name):
        state.issues.append(Issue("ERROR", f"duplicate name {name}: {previous}, {group}"))
    state.seen_names[name] = group
    return name


def validate_prompt(
    spec: PromptSpec,
    state: ValidationState,
) -> None:
    try:
        frontmatter = parse_frontmatter(spec.path)
    except (OSError, ValueError) as error:
        state.issues.append(Issue("ERROR", f"{spec.path}: {error}"))
        return
    if frontmatter.get("name") != spec.name:
        state.issues.append(
            Issue(
                "ERROR",
                f"{spec.path}: name {frontmatter.get('name')!r} != {spec.name!r}",
            )
        )
    if not frontmatter.get("description"):
        state.issues.append(Issue("ERROR", f"{spec.path}: missing description"))
    line_total = len(spec.path.read_text(encoding="utf-8").splitlines())
    if line_total > spec.line_limit:
        relative = spec.path.relative_to(REPO_ROOT)
        state.issues.append(Issue("ERROR", f"{relative}: {line_total} lines > {spec.line_limit}"))


def validate_prompt_item(
    item: dict[str, Any],
    group: str,
    state: ValidationState,
) -> None:
    source = item_source(item, state)
    name = validate_item_identity(item, group, state)
    if source is None or name is None:
        return
    if not source.exists():
        state.issues.append(Issue("ERROR", f"missing source: {item['source']}"))
        return
    prompt = source / "SKILL.md" if source.is_dir() else source
    validate_prompt(PromptSpec(prompt, name, state.limits[group]), state)
    if source.is_dir() and group == "catalog":
        state.issues.extend(validate_openai_yaml(source))


def validate_resource_item(item: dict[str, Any], state: ValidationState) -> None:
    source = item_source(item, state)
    validate_item_identity(item, "resources", state)
    if source is not None and not source.exists():
        state.issues.append(Issue("ERROR", f"missing resource tree: {item['source']}"))
    for platform, field_name in PLATFORM_TARGETS.items():
        value = item.get(field_name)
        if not isinstance(value, str):
            state.issues.append(Issue("ERROR", f"{item.get('name')}: missing {platform} target"))
            continue
        try:
            safe_relative(value)
        except ValueError as error:
            state.issues.append(Issue("ERROR", str(error)))


def discovered_manifest_sources() -> set[str]:
    directory_patterns = (
        "workflow/skills/sk-*/SKILL.md",
        "utilities/sk-*/SKILL.md",
        "planning/sk-*/SKILL.md",
        "context/sk-*/SKILL.md",
    )
    discovered = {
        prompt.parent.relative_to(REPO_ROOT).as_posix()
        for pattern in directory_patterns
        for prompt in REPO_ROOT.glob(pattern)
    }
    file_patterns = (
        "onboarding/sk-*.md",
        "workflow/agents/sk-*.md",
        "workflow/agents/review-steps/*.md",
    )
    discovered.update(
        path.relative_to(REPO_ROOT).as_posix()
        for pattern in file_patterns
        for path in REPO_ROOT.glob(pattern)
    )
    return discovered


def validate_declared_inventory(manifest: dict[str, Any]) -> list[Issue]:
    declared = {
        item["source"]
        for group in PROMPT_GROUPS
        for item in manifest[group]
        if isinstance(item.get("source"), str)
    }
    discovered = discovered_manifest_sources()
    issues = [
        Issue("ERROR", f"installable source is not declared in manifest: {source}")
        for source in sorted(discovered - declared)
    ]
    issues.extend(
        Issue("ERROR", f"manifest prompt source is outside installable roots: {source}")
        for source in sorted(declared - discovered)
    )
    return issues


def validate_manifest_items(manifest: dict[str, Any]) -> list[Issue]:
    state = ValidationState(manifest_limits(manifest))
    for group in PROMPT_GROUPS:
        for item in manifest[group]:
            validate_prompt_item(item, group, state)
    for item in manifest["resources"]:
        validate_resource_item(item, state)
    state.issues.extend(validate_declared_inventory(manifest))
    return state.issues


def local_markdown_target(target: str) -> str | None:
    candidate = target.strip().split(maxsplit=1)[0].strip("<>")
    candidate = candidate.split("#", 1)[0]
    if not candidate or candidate.startswith(("#", "/", "~")):
        return None
    if URI_SCHEME_RE.match(candidate):
        return None
    if Path(candidate).suffix.lower() != ".md":
        return None
    return candidate


def validate_markdown_references(root: Path, platform: str) -> list[Issue]:
    issues: list[Issue] = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = local_markdown_target(match.group("target"))
            if target is None or (path.parent / target).exists():
                continue
            relative = path.relative_to(root)
            issues.append(
                Issue(
                    "ERROR",
                    f"{platform} rendered reference missing: {relative} -> {target}",
                )
            )
    return issues


def validate_rendered_trees(manifest: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    with tempfile.TemporaryDirectory(prefix="sk-skills-validation-") as temporary:
        temporary_root = Path(temporary)
        for platform in PLATFORM_TARGETS:
            output = temporary_root / platform
            installed_root = Path("/manifest-validation") / platform
            try:
                render_tree(
                    manifest,
                    RenderContext(platform, output, installed_root),
                )
            except (OSError, ValueError) as error:
                issues.append(Issue("ERROR", f"{platform} render failed: {error}"))
                continue
            issues.extend(validate_markdown_references(output, platform))
    return issues


def shell_scripts() -> list[Path]:
    return [path for path in sorted(REPO_ROOT.rglob("*.sh")) if ".git" not in path.parts]


def validate_shell_script(script: Path) -> list[Issue]:
    result = subprocess.run(
        ["bash", "-n", str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    if not result.returncode:
        return []
    relative = script.relative_to(REPO_ROOT)
    return [Issue("ERROR", f"{relative}: bash -n failed: {result.stderr.strip()}")]


def validate_shellcheck(scripts: list[Path]) -> list[Issue]:
    shellcheck = shutil.which("shellcheck")
    if shellcheck is None:
        return []
    result = subprocess.run(
        [shellcheck, *map(str, scripts)],
        check=False,
        capture_output=True,
        text=True,
    )
    if not result.returncode:
        return []
    message = f"shellcheck failed:\n{result.stdout}{result.stderr}".rstrip()
    return [Issue("ERROR", message)]


def validate_python_source(source: Path) -> list[Issue]:
    if ".git" in source.parts:
        return []
    try:
        compile(source.read_text(encoding="utf-8"), str(source), "exec")
    except (SyntaxError, UnicodeDecodeError) as error:
        relative = source.relative_to(REPO_ROOT)
        return [Issue("ERROR", f"{relative}: Python syntax failed: {error}")]
    return []


def validate_scripts() -> list[Issue]:
    scripts = shell_scripts()
    issues = [issue for script in scripts for issue in validate_shell_script(script)]
    issues.extend(validate_shellcheck(scripts))
    issues.extend(
        issue
        for source in sorted(REPO_ROOT.rglob("*.py"))
        for issue in validate_python_source(source)
    )
    return issues


def validate(manifest: Any) -> list[Issue]:
    shape_issues = validate_manifest_shape(manifest)
    if shape_issues:
        return [*shape_issues, *validate_scripts()]
    manifest_issues = validate_manifest_items(manifest)
    rendered_issues = [] if manifest_issues else validate_rendered_trees(manifest)
    return [*manifest_issues, *rendered_issues, *validate_scripts()]
