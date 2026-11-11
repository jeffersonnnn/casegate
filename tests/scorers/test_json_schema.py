import json
from pathlib import Path

import pytest

from casegate.errors import SuiteError
from casegate.scorers import build_scorers
from tests.scorers._util import make_case, make_suite, score

SCHEMA = {
    "type": "object",
    "required": ["amount", "items"],
    "properties": {
        "amount": {"type": "number"},
        "items": {"type": "array", "items": {"type": "string"}},
    },
}


def errors_for(scorer: dict, expected: dict | None = None, root: Path | str = ".") -> list[str]:
    with pytest.raises(SuiteError) as exc:
        build_scorers(make_case([scorer], expected), make_suite(root))
    return exc.value.errors


def test_valid_inline_schema_from_expected() -> None:
    s = score({"type": "json_schema"}, '{"amount": 3, "items": ["a"]}', {"schema": SCHEMA})
    assert (s.value, s.passed, s.reason) == (1.0, True, "ok")


def test_fenced_json_is_extracted() -> None:
    text = 'Here:\n```json\n{"amount": 1, "items": []}\n```\nthanks'
    assert score({"type": "json_schema", "schema": SCHEMA}, text).passed


def test_invalid_json_reason() -> None:
    s = score({"type": "json_schema", "schema": SCHEMA}, "not json")
    assert s.value == 0.0
    assert s.reason.startswith("invalid JSON: Expecting value")


def test_root_error_uses_dollar() -> None:
    s = score({"type": "json_schema", "schema": SCHEMA}, '{"amount": 1}')
    assert s.reason == "$: 'items' is a required property"


def test_first_error_is_shallowest_path() -> None:
    s = score({"type": "json_schema", "schema": SCHEMA}, '{"amount": "x", "items": [1]}')
    assert s.reason == "$.amount: 'x' is not of type 'number'"
    s = score({"type": "json_schema", "schema": SCHEMA}, '{"amount": 1, "items": ["a", 2]}')
    assert s.reason == "$.items.1: 2 is not of type 'string'"


def test_schema_path_json_and_yaml(tmp_path: Path) -> None:
    (tmp_path / "s.json").write_text(json.dumps(SCHEMA))
    (tmp_path / "s.yaml").write_text("type: object\nrequired: [a]\n")
    assert score(
        {"type": "json_schema", "schema_path": "s.json"}, '{"amount":1,"items":[]}', root=tmp_path
    ).passed
    assert not score({"type": "json_schema", "schema_path": "s.yaml"}, "{}", root=tmp_path).passed


def test_schema_path_errors(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{nope")
    (tmp_path / "s.txt").write_text("{}")
    (tmp_path / "list.json").write_text("[1]")
    pre = "case c1 scorer json_schema: json_schema: "
    assert errors_for(
        {"type": "json_schema", "schema_path": "schemas/missing.json"}, root=tmp_path
    ) == [pre + "schema_path not found: schemas/missing.json"]
    (err,) = errors_for({"type": "json_schema", "schema_path": "bad.json"}, root=tmp_path)
    assert err.startswith(pre + "cannot parse bad.json: ")
    (err,) = errors_for({"type": "json_schema", "schema_path": "s.txt"}, root=tmp_path)
    assert err.startswith(pre + "schema_path must end in")
    assert errors_for({"type": "json_schema", "schema_path": "list.json"}, root=tmp_path) == [
        pre + "schema must be an object"
    ]


def test_source_errors() -> None:
    pre = "case c1 scorer json_schema: json_schema: "
    assert errors_for({"type": "json_schema"}) == [
        pre + "needs schema, schema_path or expected.schema"
    ]
    both = {"type": "json_schema", "schema": SCHEMA, "schema_path": "x.json"}
    assert errors_for(both) == [pre + "schema and schema_path are mutually exclusive"]
    assert errors_for({"type": "json_schema", "schema": {"type": 5}}) == [
        pre + "invalid schema: 5 is not valid under any of the given schemas"
    ]
    assert errors_for({"type": "json_schema"}, {"schema": [1]}) == [
        "case c1 scorer json_schema: expected.schema: Input should be a valid dictionary"
    ]


def test_check_fills_schema_for_every_source(tmp_path: Path) -> None:
    (tmp_path / "s.json").write_text(json.dumps(SCHEMA))
    case = make_case([{"type": "json_schema", "schema_path": "s.json"}])
    (built,) = build_scorers(case, make_suite(tmp_path))
    assert built.params.schema_ == SCHEMA  # type: ignore[attr-defined]
