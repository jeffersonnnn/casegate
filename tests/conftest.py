"""Shared pytest fixtures and the golden-file helper."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent / "golden"


@pytest.fixture(autouse=True)
def _no_step_summary(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # CI sets GITHUB_STEP_SUMMARY; tests must never append to the real job summary.
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    yield


def assert_golden(name: str, text: str) -> None:
    """Compare text exactly with tests/golden/<name>; UPDATE_GOLDEN=1 rewrites it."""
    assert text.endswith("\n") and not text.endswith("\n\n"), (
        f"{name}: text must end with exactly one newline"
    )
    path = GOLDEN_DIR / name
    if os.environ.get("UPDATE_GOLDEN") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return
    expected = path.read_bytes().decode("utf-8")
    assert text == expected, f"{name}: output differs from the golden file"
