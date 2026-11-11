import json
from pathlib import Path

import pytest

from casegate.prices import PRICES, PRICES_AS_OF, cost


@pytest.fixture(autouse=True)
def _no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CASEGATE_PRICES", raising=False)


def test_table_matches_facts() -> None:
    assert PRICES_AS_OF == "2026-11-03"
    assert PRICES["claude-haiku-5-5"] == (0.10, 0.50)
    assert PRICES["claude-sonnet-5-5"] == (2.00, 10.00)
    assert PRICES["claude-opus-5-5"] == (4.00, 20.00)


def test_cost_known_model() -> None:
    assert cost("claude-sonnet-5-5", 1_000_000, 1_000_000) == pytest.approx(12.0)
    assert cost("claude-haiku-5-5", 1000, 200) == pytest.approx(0.0002)
    assert cost("claude-opus-5-5", 0, 0) == 0.0


def test_unknown_model_is_none_not_zero() -> None:
    assert cost("no-such-model", 10, 10) is None


def test_env_override_merges(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "prices.json"
    path.write_text(json.dumps({"my-model": [1.0, 2.0], "claude-haiku-5-5": [0.0, 0.0]}))
    monkeypatch.setenv("CASEGATE_PRICES", str(path))
    assert cost("my-model", 1_000_000, 500_000) == pytest.approx(2.0)
    assert cost("claude-haiku-5-5", 1000, 1000) == 0.0
    assert cost("claude-sonnet-5-5", 1_000_000, 0) == pytest.approx(2.0)  # untouched rows kept
    assert PRICES["claude-haiku-5-5"] == (0.10, 0.50)  # the built-in table is not mutated


@pytest.mark.parametrize("content", ['["a"]', '{"m": [1]}', '{"m": "cheap"}'])
def test_bad_override_raises(content: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "prices.json"
    path.write_text(content)
    monkeypatch.setenv("CASEGATE_PRICES", str(path))
    with pytest.raises(ValueError, match="CASEGATE_PRICES"):
        cost("m", 1, 1)


@pytest.mark.parametrize("pair", ["[NaN, 1]", "[1, Infinity]", "[-1, 1]"])
def test_override_rejects_non_finite_or_negative(
    pair: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "prices.json"
    path.write_text('{"m": ' + pair + "}")
    monkeypatch.setenv("CASEGATE_PRICES", str(path))
    with pytest.raises(ValueError, match="finite"):
        cost("m", 1, 1)
