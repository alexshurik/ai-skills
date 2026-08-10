from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "workflow/agents/shared/runtime-state/sk_state.py"
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


def json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [json_value(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: json_value(item) for key, item in value.items()}
    raise TypeError("value is not JSON-compatible")


def json_object(value: object) -> JsonObject:
    checked = json_value(value)
    if not isinstance(checked, dict):
        raise TypeError("value is not a JSON object")
    return checked


def object_at(value: JsonValue, *keys: str) -> JsonObject:
    current = value
    for key in keys:
        current = json_object(current)[key]
    return json_object(current)


def array_at(value: JsonValue, *keys: str) -> list[JsonValue]:
    current: JsonValue = object_at(value, *keys[:-1])[keys[-1]]
    if not isinstance(current, list):
        raise TypeError(f"{'/'.join(keys)} is not a JSON array")
    return current


def load_runtime_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sk_state", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("runtime facade could not be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SK_STATE = load_runtime_module()


class RuntimeCase(unittest.TestCase):
    temporary: tempfile.TemporaryDirectory[str]
    base: Path

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(self, *arguments: str) -> tuple[int, str, str]:
        output = io.StringIO()
        errors = io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            args = SK_STATE.build_parser().parse_args(list(arguments))
            try:
                args.handler(args)
            except (OSError, SK_STATE.StateError) as error:
                print(f"ERROR: {error}", file=sys.stderr)
                return 1, output.getvalue(), errors.getvalue()
        return 0, output.getvalue(), errors.getvalue()

    def expect_ok(self, *arguments: str) -> JsonObject | None:
        code, output, errors = self.invoke(*arguments)
        self.assertEqual(code, 0, errors)
        return json_object(json.loads(output)) if output.startswith("{") else None

    def init_runtime(self, name: str) -> tuple[Path, JsonObject]:
        runtime = self.base / name
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            name,
            "--workflow",
            "sk-team-feature",
            "--policy-revision",
            "test-policy",
        )
        assert state is not None
        return runtime, state

    def mutate(self, runtime: Path, revision: int, command: str, *arguments: str) -> JsonObject:
        result = self.expect_ok(
            command,
            "--runtime-dir",
            str(runtime),
            "--expected-revision",
            str(revision),
            "--command-id",
            f"command-{revision + 1}",
            *arguments,
        )
        assert result is not None
        return result

    def invoke_error(
        self, runtime: Path, revision: int, command_id: str, command: str, *arguments: str
    ) -> str:
        code, _, errors = self.invoke(
            command,
            "--runtime-dir",
            str(runtime),
            "--expected-revision",
            str(revision),
            "--command-id",
            command_id,
            *arguments,
        )
        self.assertEqual(code, 1)
        return errors

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL_PATH), *arguments],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
