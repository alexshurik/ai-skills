#!/usr/bin/env python3
"""Executable and import-compatible facade for the workflow runtime."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

MINIMUM_PYTHON = (3, 10)


def _require_supported_python() -> None:
    """Fail clearly before the runtime package hits a 3.10-only construct."""
    version: tuple[int, ...] = tuple(sys.version_info[:3])
    if version >= MINIMUM_PYTHON:
        return
    found = ".".join(str(part) for part in version)
    message = (
        f"sk_state.py requires Python >= 3.10, but {sys.executable or 'this interpreter'} "
        f"is {found}. Re-run it with a 3.10+ interpreter: set PYTHON=/path/to/python3.10+ "
        'and run "$PYTHON" sk_state.py, or try `python` or `py -3` '
        "(macOS /usr/bin/python3 is 3.9)."
    )
    if __name__ == "__main__":
        print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(2)
    raise ImportError(message)


_require_supported_python()


def _module_origin(module: ModuleType) -> Path | None:
    origin = getattr(getattr(module, "__spec__", None), "origin", None)
    file_name = origin or getattr(module, "__file__", None)
    return Path(file_name).resolve() if file_name else None


def _runtime_package_key(package_init: Path) -> str:
    digest = hashlib.sha256(str(package_init).encode()).hexdigest()
    return f"_sk_runtime_{digest}"


def _cached_runtime_package(package_key: str, package_init: Path) -> ModuleType | None:
    existing = sys.modules.get(package_key)
    if existing is None:
        return None
    if _module_origin(existing) != package_init:
        raise ImportError(f"runtime package key collision for {package_init}")
    return existing


def _remove_failed_runtime_modules(
    package_key: str,
    module: ModuleType,
    loaded_before: set[str],
) -> None:
    for name in tuple(sys.modules):
        is_own_package = name == package_key and sys.modules[name] is module
        is_new_submodule = name not in loaded_before and name.startswith(f"{package_key}.")
        if is_own_package or is_new_submodule:
            sys.modules.pop(name, None)


def _load_runtime_package() -> ModuleType:
    package_init = (Path(__file__).with_name("_sk_runtime") / "__init__.py").resolve()
    package_key = _runtime_package_key(package_init)
    existing = _cached_runtime_package(package_key, package_init)
    if existing is not None:
        return existing

    spec = importlib.util.spec_from_file_location(
        package_key,
        package_init,
        submodule_search_locations=[str(package_init.parent)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load runtime package from {package_init.parent}")
    module = importlib.util.module_from_spec(spec)
    loaded_before = set(sys.modules)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        _remove_failed_runtime_modules(package_key, module, loaded_before)
        raise
    return module


_runtime = _load_runtime_package()

EVENT_SCHEMA_VERSION = _runtime.EVENT_SCHEMA_VERSION
EVENT_SPECS = _runtime.EVENT_SPECS
EVENT_TYPES = _runtime.EVENT_TYPES
STATE_SCHEMA_VERSION = _runtime.STATE_SCHEMA_VERSION
StateError = _runtime.StateError
TERMINAL_ATTEMPTS = _runtime.TERMINAL_ATTEMPTS
TERMINAL_STAGES = _runtime.TERMINAL_STAGES
apply_event = _runtime.apply_event
build_parser = _runtime.build_parser
canonical_json = _runtime.canonical_json
commit_transition = _runtime.commit_transition
load_runtime = _runtime.load_runtime
make_event = _runtime.make_event
normalized_legacy_state = _runtime.normalized_legacy_state
read_events = _runtime.read_events
replay = _runtime.replay
runtime_paths = _runtime.runtime_paths
safe_legacy_name = _runtime.safe_legacy_name
validate_event = _runtime.validate_event
validate_state = _runtime.validate_state


if __name__ == "__main__":
    raise SystemExit(_runtime.main())
