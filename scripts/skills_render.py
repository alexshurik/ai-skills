"""Render platform-specific install trees without touching live targets."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skills_common import TEXT_SUFFIXES, repo_source_path, safe_relative


MAX_RENDER_SOURCE_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class RenderContext:
    platform: str
    output: Path
    installed_root: Path


def replace_paths(text: str, context: RenderContext) -> str:
    if context.platform in {"codex", "cursor"}:
        replacements = (
            (
                "~/.claude/agents/best-practices",
                str(context.installed_root / "best-practices"),
            ),
            (
                "~/.claude/agents/review-steps",
                str(context.installed_root / "review-steps"),
            ),
            ("~/.claude/agents/shared", str(context.installed_root / "shared")),
            ("~/.claude/agents/", f"{context.installed_root / 'agents'}/"),
        )
    elif context.platform == "kimi":
        references = context.installed_root / "agents" / "references"
        replacements = (
            ("~/.claude/agents/best-practices", str(references / "best-practices")),
            ("~/.claude/agents/review-steps", str(references / "review-steps")),
            ("~/.claude/agents/shared", str(references / "shared")),
            ("~/.claude/agents/", f"{references}/"),
        )
    else:
        return text
    for original, replacement in replacements:
        text = text.replace(original, replacement)
    return text


def ensure_new_leaf(destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"render target collision: {destination}")


def checked_source_stat(source: Path) -> os.stat_result:
    metadata = source.lstat()
    if stat.S_ISLNK(metadata.st_mode):
        raise ValueError(f"render source symlink is not allowed: {source}")
    if not stat.S_ISDIR(metadata.st_mode) and not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"render source is not a regular file/directory: {source}")
    return metadata


def validate_source_tree(source: Path) -> None:
    metadata = checked_source_stat(source)
    if not stat.S_ISDIR(metadata.st_mode):
        return
    for child in sorted(source.iterdir()):
        validate_source_tree(child)


def read_source_file(source: Path) -> tuple[bytes, int]:
    before = checked_source_stat(source)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"render source is not a regular file: {source}")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(source, flags)
    with os.fdopen(descriptor, "rb") as source_file:
        opened = os.fstat(source_file.fileno())
        identity = (before.st_dev, before.st_ino)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError(f"render source changed while opening: {source}")
        if identity != (opened.st_dev, opened.st_ino):
            raise ValueError(f"render source changed while opening: {source}")
        if opened.st_size > MAX_RENDER_SOURCE_BYTES:
            raise ValueError(f"render source exceeds the size limit: {source}")
        content = source_file.read(MAX_RENDER_SOURCE_BYTES + 1)
        if len(content) > MAX_RENDER_SOURCE_BYTES:
            raise ValueError(f"render source exceeds the size limit: {source}")
        return content, opened.st_mode


def read_source_text(source: Path) -> str:
    content, _ = read_source_file(source)
    return content.decode("utf-8")


def copy_validated(
    source: Path,
    destination: Path,
    context: RenderContext,
) -> None:
    if source.name == "__pycache__" or source.suffix.lower() in {".pyc", ".pyo"}:
        return
    metadata = checked_source_stat(source)
    if stat.S_ISDIR(metadata.st_mode):
        if destination.exists() and (
            destination.is_symlink() or not destination.is_dir()
        ):
            raise ValueError(f"render target collision: {destination}")
        destination.mkdir(parents=True, exist_ok=True)
        for child in sorted(source.iterdir()):
            copy_validated(child, destination / child.name, context)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    ensure_new_leaf(destination)
    content, source_mode = read_source_file(source)
    if source.suffix.lower() in TEXT_SUFFIXES or source.name == "SKILL.md":
        destination.write_text(
            replace_paths(content.decode("utf-8"), context),
            encoding="utf-8",
        )
    else:
        destination.write_bytes(content)
    if source_mode & 0o111:
        destination.chmod(destination.stat().st_mode | 0o111)


def copy_rendered(
    source: Path,
    destination: Path,
    context: RenderContext,
) -> None:
    validate_source_tree(source)
    copy_validated(source, destination, context)


def render_review_steps(
    manifest: dict[str, Any],
    destination: Path,
    context: RenderContext,
) -> None:
    for item in manifest["review_steps"]:
        source = repo_source_path(item["source"])
        copy_rendered(source, destination / source.name, context)


def render_catalog_tree(manifest: dict[str, Any], context: RenderContext) -> None:
    for item in manifest["catalog"]:
        copy_rendered(
            repo_source_path(item["source"]),
            context.output / item["name"],
            context,
        )
    for item in manifest["onboarding"]:
        copy_rendered(
            repo_source_path(item["source"]),
            context.output / item["name"] / "SKILL.md",
            context,
        )
    for item in manifest["agents"]:
        copy_rendered(
            repo_source_path(item["source"]),
            context.output / "agents" / f"{item['name']}.md",
            context,
        )
    render_review_steps(manifest, context.output / "review-steps", context)
    target_field = f"{context.platform}_target"
    for item in manifest["resources"]:
        copy_rendered(
            repo_source_path(item["source"]),
            context.output / safe_relative(item[target_field]),
            context,
        )


def link(source: Path, destination: Path) -> None:
    validate_source_tree(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ensure_new_leaf(destination)
    destination.symlink_to(source)


def render_claude(manifest: dict[str, Any], context: RenderContext) -> None:
    for item in manifest["catalog"]:
        link(
            repo_source_path(item["source"]),
            context.output / "skills" / item["name"],
        )
    for item in manifest["onboarding"]:
        link(
            repo_source_path(item["source"]),
            context.output / "commands" / f"{item['name']}.md",
        )
    for item in manifest["agents"]:
        link(
            repo_source_path(item["source"]),
            context.output / "agents" / f"{item['name']}.md",
        )
    for item in manifest["review_steps"]:
        source = repo_source_path(item["source"])
        link(source, context.output / "agents/review-steps" / source.name)
    for item in manifest["resources"]:
        link(
            repo_source_path(item["source"]),
            context.output / safe_relative(item["claude_target"]),
        )


def kimi_agent_yaml(name: str) -> str:
    return (
        "version: 1\nagent:\n  extend: ./sk-team.yaml\n"
        f"  system_prompt_path: ./references/{name}.md\n"
        "  exclude_tools:\n"
        '    - "kimi_cli.tools.agent:Agent"\n'
    )


def kimi_team_yaml(manifest: dict[str, Any]) -> str:
    lines = [
        "version: 1",
        "agent:",
        "  name: sk-team",
        "  extend: default",
        "  system_prompt_path: ./references/sk-team-feature.md",
        "  subagents:",
    ]
    for item in (*manifest["agents"], *manifest["review_steps"]):
        short_name = item["name"].removeprefix("sk-")
        lines += [
            f"    {short_name}:",
            f"      path: ./{item['name']}.yaml",
            f'      description: "Internal role: {item["name"]}"',
        ]
    return "\n".join(lines) + "\n"


def kimi_team_prompt(context: RenderContext) -> str:
    feature_root = repo_source_path("workflow/skills/sk-team-feature")
    validate_source_tree(feature_root)
    prompt = replace_paths(
        read_source_text(feature_root / "SKILL.md"),
        context,
    )
    prompt = prompt.replace(
        "(references/phase-prompts.md)",
        "(#embedded-phase-prompts)",
    )
    phase_prompts = replace_paths(
        read_source_text(feature_root / "references/phase-prompts.md"),
        context,
    )
    kimi_override = """## Kimi execution override

Kimi subagents already run in isolated contexts and return only their final result
to this root. The current stable Agent tool does not permit a child to create its
own child, so the root owns all dispatch. During a full code-review phase, do not
send the whole review to `sk-review-orchestrator` as a child. The root performs the
orchestrator setup/aggregation steps and launches the registered `review-security`,
`review-architecture`, `review-abstraction`, `review-structure`, `review-imports`,
`review-stack-rules`, and (when applicable) `review-instruction-quality` leaf
subagents over one artifact snapshot. First run `review-structure` as the
full-coverage reader, validate its neutral coverage ledger against the deterministic
review map, then launch the other six as targeted independent lenses. This preserves
seven independent clean verdicts without unsupported nesting or seven redundant
full-scope reads.

Apply the installed shared `scope-governance.md` during aggregation. Preserve every
lens finding, but separate severity from `required_fix`, `user_decision`, `backlog`,
and `baseline`; show Review Triage and pass remediation only an approved finding-ID
allowlist. New non-critical final-review ideas go to `DEFERRED.md` rather than a new
automatic remediation cycle.

Within each stage, launch all available lens work in background before awaiting
results. Kimi sends completion notifications automatically; do not repeatedly poll
task status. Keep full reports/logs in shared artifact paths and accept only compact
final receipts in the root context. Ordinary feature roles remain leaf subagents.
"""
    return (
        "${KIMI_AGENTS_MD}\n\n"
        f"{kimi_override.rstrip()}\n\n"
        f"{prompt.rstrip()}\n\n"
        '<a id="embedded-phase-prompts"></a>\n\n'
        "## Embedded phase prompts\n\n"
        f"{phase_prompts.rstrip()}\n"
    )


def write_generated(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_new_leaf(path)
    path.write_text(content, encoding="utf-8")


def render_kimi(manifest: dict[str, Any], context: RenderContext) -> None:
    skills = context.output / "skills"
    agents = context.output / "agents"
    references = agents / "references"
    for item in manifest["catalog"]:
        copy_rendered(
            repo_source_path(item["source"]),
            skills / item["name"],
            context,
        )
    for item in manifest["onboarding"]:
        copy_rendered(
            repo_source_path(item["source"]),
            skills / item["name"] / "SKILL.md",
            context,
        )
    write_generated(
        references / "sk-team-feature.md",
        kimi_team_prompt(context),
    )
    write_generated(agents / "sk-team.yaml", kimi_team_yaml(manifest))
    for item in manifest["agents"]:
        copy_rendered(
            repo_source_path(item["source"]),
            references / f"{item['name']}.md",
            context,
        )
        write_generated(
            agents / f"{item['name']}.yaml",
            kimi_agent_yaml(item["name"]),
        )
    render_review_steps(manifest, references / "review-steps", context)
    for item in manifest["review_steps"]:
        write_generated(
            agents / f"{item['name']}.yaml",
            kimi_agent_yaml(item["name"]),
        )
    for item in manifest["resources"]:
        copy_rendered(
            repo_source_path(item["source"]),
            context.output / safe_relative(item["kimi_target"]),
            context,
        )


def render_tree(manifest: dict[str, Any], context: RenderContext) -> None:
    context.output.mkdir(parents=True, exist_ok=True)
    renderers = {
        "codex": render_catalog_tree,
        "cursor": render_catalog_tree,
        "claude": render_claude,
        "kimi": render_kimi,
    }
    try:
        renderer = renderers[context.platform]
    except KeyError as error:
        raise ValueError(f"unsupported platform: {context.platform}") from error
    renderer(manifest, context)
