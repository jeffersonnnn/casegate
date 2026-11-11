"""Every fmt.py rule (SPEC §9): rates, money, signed deltas, the zero rule, cache, cells."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from casegate.fmt import (
    ERROR_LIMIT,
    REASON_LIMIT,
    fmt_cache,
    fmt_delta,
    fmt_delta_int,
    fmt_delta_money,
    fmt_money,
    fmt_rate,
    fmt_signed3,
    fmt_ts,
    md_cell,
)
from casegate.models import RunSummary

M = "\N{MINUS SIGN}"


def test_limits() -> None:
    assert (REASON_LIMIT, ERROR_LIMIT) == (120, 200)


@pytest.mark.parametrize(
    ("x", "text"), [(None, "—"), (0.0, "0.000"), (0.75, "0.750"), (0.8926, "0.893"), (1, "1.000")]
)
def test_fmt_rate(x: float | None, text: str) -> None:
    assert fmt_rate(x) == text


@pytest.mark.parametrize(
    ("x", "text"),
    [
        (None, "unknown"),
        (0, "$0.00"),
        (0.0, "$0.00"),
        (0.27, "$0.27"),
        (1.234, "$1.23"),
        (0.005, "$0.0050"),
        (0.00123, "$0.0012"),
        (0.0099, "$0.0099"),
        (0.00999, "$0.01"),  # rounds to 0.0100, which is not below a cent
        (-0.02, f"{M}$0.02"),
        (-0.003, f"{M}$0.0030"),
        (0.00001, "$0.00"),  # rounds to zero at 4 decimals
        (-0.00001, "$0.00"),  # a rounded zero is never signed
    ],
)
def test_fmt_money(x: float | None, text: str) -> None:
    assert fmt_money(x) == text


@pytest.mark.parametrize(
    ("x", "text"),
    [
        (None, ""),
        (0.009, "+0.009"),
        (-0.106, f"{M}0.106"),
        (0.0, "0.000"),
        (-0.0002, "0.000"),
        (0.0004, "0.000"),
        (0.0005001, "+0.001"),
    ],
)
def test_fmt_delta(x: float | None, text: str) -> None:
    assert fmt_delta(x) == text


@pytest.mark.parametrize(("x", "text"), [(1, "+1"), (-1, f"{M}1"), (0, "0"), (12, "+12")])
def test_fmt_delta_int(x: int, text: str) -> None:
    assert fmt_delta_int(x) == text


@pytest.mark.parametrize(
    ("a", "b", "text"),
    [
        (0.25, 0.27, "+$0.02"),
        (0.27, 0.25, f"{M}$0.02"),
        (0.25, 0.25, "$0.00"),
        (0.01, 0.015, "+$0.0050"),
        (0.015, 0.01, f"{M}$0.0050"),
        (0.1, 0.10001, "$0.00"),
        (None, 0.1, ""),
        (0.1, None, ""),
    ],
)
def test_fmt_delta_money(a: float | None, b: float | None, text: str) -> None:
    assert fmt_delta_money(a, b) == text


@pytest.mark.parametrize(
    ("x", "text"),
    [(0.106, "0.106"), (-0.02, f"{M}0.020"), (0.0, "0.000"), (-0.0001, "0.000")],
)
def test_fmt_signed3(x: float, text: str) -> None:
    assert fmt_signed3(x) == text


def _summary(**counts: int) -> RunSummary:
    return RunSummary(
        pass_rate=None,
        pass_rate_std=0.0,
        per_repeat_pass_rate=[],
        n_cases=0,
        n_scored_cases=0,
        n_repeats_total=0,
        n_error_repeats=0,
        by_tag={},
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        cost_usd_full=0.0,
        duration_s=0.0,
        **counts,
    )


def test_fmt_cache() -> None:
    assert fmt_cache(_summary()) == "cache off"
    both = _summary(
        cache_output_hits=60, cache_output_total=75, cache_judge_hits=90, cache_judge_total=110
    )
    assert fmt_cache(both) == "cache 60/75 outputs · 90/110 judge"
    no_judge = _summary(cache_output_hits=0, cache_output_total=12)
    assert fmt_cache(no_judge) == "cache 0/12 outputs"


def test_fmt_ts_converts_to_utc() -> None:
    assert fmt_ts(datetime(2026, 11, 11, 9, 5, 3, 999, tzinfo=UTC)) == "2026-11-11T09:05:03Z"
    plus_one = timezone(timedelta(hours=1))
    assert fmt_ts(datetime(2026, 11, 11, 10, 0, 0, tzinfo=plus_one)) == "2026-11-11T09:00:00Z"
    assert fmt_ts(datetime(2026, 11, 11, 10, 0, 0)) == "2026-11-11T10:00:00Z"


def test_md_cell_newlines_and_pipes() -> None:
    assert md_cell("a\r\nb\nc\rd", 50) == "a b c d"
    assert md_cell("a|b", 50) == "a\\|b"
    assert md_cell("short", 5) == "short"


def test_md_cell_cut_adds_ellipsis() -> None:
    out = md_cell("abcdefghij", 5)
    assert out == "abcd…"
    assert len(out) == 5


def test_md_cell_cut_never_splits_an_escaped_pipe() -> None:
    # "abc|" escapes to "abc\|"; a cut at 4 keeps "abc\" and must drop that lone backslash.
    assert md_cell("abc|defgh", 5) == "abc…"
    # A cut that keeps the whole "\|" pair stays as is.
    assert md_cell("ab|defgh", 5) == "ab\\|…"


def test_md_cell_limit_after_escaping() -> None:
    text = "x" * 300
    assert len(md_cell(text, REASON_LIMIT)) == REASON_LIMIT
    assert md_cell(text, ERROR_LIMIT).endswith("…")


def test_md_cell_escapes_html_and_mentions_for_markdown() -> None:
    zwj = "‍"
    assert md_cell("<img src=x> hi @octocat", 80) == f"\\<img src=x> hi @{zwj}octocat"
    # A backslash before "<" is doubled, so it cannot cancel the escape.
    assert md_cell("a\\<b", 50) == "a\\\\\\<b"
    assert md_cell("plain text", 50) == "plain text"


def test_md_cell_terminal_keeps_html_and_mentions() -> None:
    assert md_cell("<b> @x|y", 50, markdown=False) == "<b> @x\\|y"
    assert md_cell("x" * 130, 120, markdown=False) == md_cell("x" * 130, 120)


def test_md_cell_cut_never_splits_an_escaped_lt() -> None:
    # "abc<" escapes to "abc\<"; a cut at 4 keeps "abc\" and must drop that lone backslash.
    assert md_cell("abc<defgh", 5) == "abc…"
    assert md_cell("ab<defgh", 5) == "ab\\<…"
