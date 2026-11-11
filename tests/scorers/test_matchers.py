import pytest

from casegate.scorers.matchers import MatcherError, equal, parse


@pytest.mark.parametrize(
    ("spec", "value", "ok"),
    [
        ("1042", "1042", True),
        ("1042", 1042, False),
        (1, 1.0000000001, True),
        (1, True, False),
        (True, True, True),
        (True, 1, False),
        ({"a": [1, 2]}, {"a": [1, 2]}, True),
        ({"a": [1, 2]}, {"a": [2, 1]}, False),
        ({"a": 1}, {"a": 1, "b": 2}, False),
        ({}, {}, True),
        ([1], [1, 2], False),
        (None, None, True),
        ({"regex": r"^10\d+$"}, 1042, True),
        ({"regex": "^x"}, "yx", False),
        ({"contains": "fund"}, "refund", True),
        ({"contains": "Fund"}, "refund", False),
        ({"gte": 1, "lte": 2}, 1.5, True),
        ({"lte": 39.0}, 39.00000000001, True),
        ({"lte": 39}, 40, False),
        ({"gte": 5}, 4.9, False),
        ({"gte": 5}, 5, True),
        ({"lte": 5}, True, False),
        ({"lte": 5}, "3", False),
        ({"any": True}, None, True),
        ({"one_of": ["a", 1]}, 1.0, True),
        ({"one_of": ["a", 1]}, "b", False),
    ],
)
def test_match(spec: object, value: object, ok: bool) -> None:
    assert parse(spec).match(value, True) is ok


@pytest.mark.parametrize("spec", ["x", {"any": True}, {"lte": 1}, {"regex": "."}])
def test_absent_value_never_matches(spec: object) -> None:
    assert parse(spec).match(None, False) is False


@pytest.mark.parametrize(
    ("value", "ok"),
    [
        ([], True),
        ([{"amount": 10}, {"amount": 39.0}], True),
        ([{"amount": 40}], False),
        ([{"amount": True}], False),
        ([{"x": 1}], False),
        (["a"], False),
        ({"amount": 1}, False),
    ],
)
def test_all_amounts_lte(value: object, ok: bool) -> None:
    assert parse({"all_amounts_lte": 39}, allow_list=True).match(value, True) is ok


def test_dicts_with_other_keys_are_plain_values() -> None:
    m = parse({"regex": "x", "other": 1})
    assert m.is_plain and m.match({"regex": "x", "other": 1}, True)
    assert parse({}).is_plain


def test_render() -> None:
    assert parse({"lte": 39}).render() == '{"lte":39}'
    assert parse("é").render() == '"é"'


@pytest.mark.parametrize(
    ("spec", "message"),
    [
        ({"regex": "x", "gte": 1}, "invalid matcher keys: gte, regex"),
        ({"any": True, "one_of": [1]}, "invalid matcher keys: any, one_of"),
        ({"any": False}, "any must be true"),
        ({"any": 1}, "any must be true"),
        ({"regex": 1}, "regex must be a string"),
        ({"regex": "("}, "invalid regex: missing ), unterminated subpattern at position 0"),
        ({"contains": 1}, "contains must be a string"),
        ({"gte": "1"}, "gte must be a number"),
        ({"lte": True}, "lte must be a number"),
        ({"one_of": []}, "one_of must be a non-empty list"),
        ({"one_of": "ab"}, "one_of must be a non-empty list"),
        ({"all_amounts_lte": 5}, "all_amounts_lte is valid only in state_match"),
    ],
)
def test_parse_errors(spec: object, message: str) -> None:
    with pytest.raises(MatcherError) as exc:
        parse(spec)
    assert str(exc.value) == message


def test_all_amounts_lte_number_check() -> None:
    with pytest.raises(MatcherError, match=r"^all_amounts_lte must be a number$"):
        parse({"all_amounts_lte": "5"}, allow_list=True)


def test_matcher_error_is_value_error() -> None:
    assert issubclass(MatcherError, ValueError)
    assert equal([1, {"a": "b"}], [1.0, {"a": "b"}])
