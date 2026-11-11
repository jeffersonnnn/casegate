"""The one seam between casegate and the system under test.

The runner only knows `Target.run` and `Target.aclose`, so a Python function and an HTTP
service look the same to it. `build_target` checks the config up front and reports every
problem as a `SuiteError`, so a bad target is a load error (exit 2), not a crash mid-run.
"""

from __future__ import annotations

import importlib
import inspect
import os
import re
from typing import Any, Protocol

from casegate.errors import SuiteError
from casegate.models import Output, TargetConfig
from casegate.targets.http import HttpTarget
from casegate.targets.python import PythonTarget

__all__ = ["HttpTarget", "PythonTarget", "Target", "build_target"]

_ENV_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class Target(Protocol):
    async def run(self, case_input: dict[str, Any], *, case_id: str = "") -> Output: ...

    async def aclose(self) -> None: ...


def build_target(cfg: TargetConfig) -> Target:
    """Make the target named by the suite config; does no network I/O."""
    if cfg.type == "python":
        return PythonTarget(_resolve_function(cfg.path or ""), cfg.timeout_s)
    return HttpTarget(cfg.url or "", _expand_headers(cfg.headers), cfg.timeout_s)


def _resolve_function(path: str) -> Any:
    module_name, _, func_name = path.partition(":")
    try:
        module = importlib.import_module(module_name)
    except (Exception, SystemExit) as exc:
        # A user module can fail in any way at import; the loader must still list it as one line.
        raise SuiteError(
            f"target.path: cannot import {module_name}: {type(exc).__name__}: {exc}"
        ) from exc
    if not hasattr(module, func_name):
        raise SuiteError(f"target.path: {module_name} has no attribute {func_name}")
    func = getattr(module, func_name)
    if not inspect.iscoroutinefunction(func):
        raise SuiteError(f"target.path: {module_name}:{func_name} must be an async function")
    return func


def _expand_headers(headers: dict[str, str]) -> dict[str, str]:
    # Secrets stay out of suite.yaml: `${NAME}` is read from the environment once, here.
    errors: list[str] = []
    expanded: dict[str, str] = {}
    for header, value in headers.items():

        def lookup(match: re.Match[str], header: str = header) -> str:
            name = match.group(1)
            if name not in os.environ:
                errors.append(f"target.headers.{header}: environment variable {name} is not set")
                return ""
            return os.environ[name]

        expanded[header] = _ENV_REF.sub(lookup, value)
    if errors:
        raise SuiteError(errors)
    return expanded
