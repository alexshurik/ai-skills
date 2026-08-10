#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = (
    ROOT / "evals/validate-result.py",
    ROOT / "scripts",
    ROOT / "shared/review-evidence",
    ROOT / "workflow/agents/shared/runtime-state/sk_state.py",
    ROOT / "workflow/agents/shared/runtime-state/_sk_runtime",
    ROOT / "tests/test-runtime-state.py",
    ROOT / "tests/runtime_state",
)
MAX_FUNCTION_LINES = 70


def python_files() -> list[Path]:
    files: list[Path] = []
    for target in TARGETS:
        files.extend(target.rglob("*.py") if target.is_dir() else [target])
    return sorted(files)


def long_functions(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end_line = node.end_lineno or node.lineno
        length = end_line - node.lineno + 1
        if length > MAX_FUNCTION_LINES:
            relative = path.relative_to(ROOT)
            violations.append(f"{relative}:{node.lineno}: {node.name} is {length} lines")
    return violations


def main() -> int:
    violations = [item for path in python_files() for item in long_functions(path)]
    if violations:
        print("ERROR: functions exceed the 70-line hard limit:", file=sys.stderr)
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("OK: Python functions are at most 70 lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
