"""Read a suite directory into a validated Suite and its Cases, or fail with every problem at once.

A suite author fixes their YAML faster when one run lists all the errors, so the loader collects
each problem as one line and raises them together as a SuiteError (exit code 2). It also builds
the scorers and the target once, only to validate them, so a bad suite fails before any spend.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from casegate.errors import SuiteError
from casegate.models import Case, Suite
from casegate.scorers import REGISTRY, build_scorers
from casegate.targets import build_target

SUITE_FILE = "suite.yaml"


def load_suite(path: str | Path, tags: list[str] | None = None) -> tuple[Suite, list[Case]]:
    """Load `<path>/suite.yaml` and its case files; keep cases with at least one of `tags`."""
    root = Path(path).resolve()
    errors: list[str] = []
    data = _read_suite_yaml(Path(path) / SUITE_FILE)
    data["root"] = str(root)  # set by the loader, never by the author

    suite: Suite | None = None
    try:
        suite = Suite.model_validate(data)
    except ValidationError as exc:
        errors += [f"{SUITE_FILE}: {line}" for line in _pydantic_lines(exc)]

    # An invalid suite still has its cases checked, so the author sees every error in one pass.
    pattern = suite.cases if suite else _raw_cases_glob(data)
    cases = _load_cases(root, pattern, suite, errors)

    if suite is not None:
        _check_target(suite, errors)

    if tags and cases:
        cases = [c for c in cases if any(t in c.tags for t in tags)]
        if not cases:
            errors.append(f"no cases match tags: {', '.join(tags)}")

    if errors or suite is None:
        raise SuiteError(errors)
    return suite, cases


def _read_suite_yaml(file: Path) -> dict[str, Any]:
    # Without a readable suite.yaml there is no root config to check anything else against.
    if not file.is_file():
        raise SuiteError(f"{SUITE_FILE}: not found: {file}")
    try:
        raw = yaml.safe_load(file.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        raise SuiteError(f"{SUITE_FILE}: cannot parse: {_one_line(exc)}") from None
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise SuiteError(f"{SUITE_FILE}: cannot parse: top level must be a mapping")
    return raw


def _raw_cases_glob(data: dict[str, Any]) -> str:
    value = data.get("cases")
    return value if isinstance(value, str) else "cases/*.yaml"


def _load_cases(root: Path, pattern: str, suite: Suite | None, errors: list[str]) -> list[Case]:
    files = _case_files(root, pattern)
    if not files:
        errors.append(f"no case files match {pattern}")
        return []

    cases: list[Case] = []
    first_file: dict[str, str] = {}
    for file in files:
        rel = file.relative_to(root).as_posix()
        for index, doc in _documents(file, rel, errors):
            case = _validate_case(doc, rel, index, errors)
            if case is None:
                continue
            if case.id in first_file:
                errors.append(f"duplicate case id {case.id}: {first_file[case.id]}, {rel}")
            else:
                first_file[case.id] = rel
            unknown = [cfg.type for cfg in case.scorers if cfg.type not in REGISTRY]
            for scorer_type in unknown:
                errors.append(
                    f"{rel} case {index}: unknown scorer type {scorer_type} "
                    f"(known: {', '.join(sorted(REGISTRY))})"
                )
            # build_scorers needs the suite (root, threshold); skip it when either is unusable.
            if not unknown and suite is not None:
                try:
                    build_scorers(case, suite)
                except SuiteError as exc:
                    errors += exc.errors
            cases.append(case)
    return cases


def _case_files(root: Path, pattern: str) -> list[Path]:
    try:
        found = [p for p in root.glob(pattern) if p.is_file()]
    except (ValueError, NotImplementedError):  # e.g. an absolute or empty pattern
        return []
    # Suite order is the file path relative to the root, so runs are stable across machines.
    return sorted(found, key=lambda p: p.relative_to(root).as_posix())


def _documents(file: Path, rel: str, errors: list[str]) -> list[tuple[int, Any]]:
    try:
        docs = list(yaml.safe_load_all(file.read_text(encoding="utf-8")))
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        errors.append(f"{rel}: cannot parse: {_one_line(exc)}")
        return []
    # An empty document (a trailing `---`) is not a case, but it keeps its place in the index.
    return [(i, doc) for i, doc in enumerate(docs) if doc is not None]


def _validate_case(doc: Any, rel: str, index: int, errors: list[str]) -> Case | None:
    if isinstance(doc, dict):
        doc = {**doc, "source_file": rel}
    try:
        return Case.model_validate(doc)
    except ValidationError as exc:
        errors += [f"{rel} case {index}: {line}" for line in _pydantic_lines(exc)]
        return None


def _check_target(suite: Suite, errors: list[str]) -> None:
    if suite.target.type == "python":
        # Targets are named relative to where casegate runs (the repo root), like `python -m`.
        cwd = os.getcwd()
        if not sys.path or sys.path[0] != cwd:
            sys.path.insert(0, cwd)
    try:
        build_target(suite.target)  # no I/O and no open client, so nothing to close
    except SuiteError as exc:
        errors += exc.errors


def _pydantic_lines(exc: ValidationError) -> list[str]:
    lines = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"])
        lines.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return lines


def _one_line(exc: BaseException) -> str:
    # YAML errors span several lines; the CLI prints one error per line.
    return " ".join(str(exc).split())
