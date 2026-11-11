"""Every number, money and table-cell format that casegate prints, in one place.

The terminal, the Markdown report, the comparison, the PR comment and calibration all show
the same numbers. One module for the formats keeps them identical everywhere, and keeps the
rules (U+2212 minus, no signed zero, cell escaping) testable in one file.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from casegate.models import RunSummary

REASON_LIMIT = 120
ERROR_LIMIT = 200
_BEFORE_LT = re.compile(r"(\\*)<")
MINUS = "\N{MINUS SIGN}"  # a real minus sign; a hyphen looks wrong next to digits


def _signed(text: str, negative: bool, plus: bool) -> str:
    if negative:
        return MINUS + text
    return ("+" + text) if plus else text


def _money_digits(x: float) -> tuple[float, int]:
    """Round |x| to the shown decimals: 4 below one cent, else 2."""
    r4 = round(abs(x), 4)
    if 0 < r4 < 0.01:
        return r4, 4
    return round(abs(x), 2), 2


def fmt_rate(x: float | None) -> str:
    return "—" if x is None else f"{x:.3f}"


def fmt_money(x: float | None) -> str:
    if x is None:
        return "unknown"
    value, digits = _money_digits(x)
    if value == 0:  # zero rule: a rounded zero is never signed
        return "$0.00"
    return _signed(f"${value:.{digits}f}", x < 0, plus=False)


def fmt_delta(x: float | None) -> str:
    if x is None:
        return ""
    value = round(abs(x), 3)
    if value == 0:
        return "0.000"
    return _signed(f"{value:.3f}", x < 0, plus=True)


def fmt_delta_int(x: int) -> str:
    if x == 0:
        return "0"
    return _signed(str(abs(x)), x < 0, plus=True)


def fmt_delta_money(a: float | None, b: float | None) -> str:
    if a is None or b is None:
        return ""
    d = b - a
    value, digits = _money_digits(d)
    if value == 0:
        return "$0.00"
    return _signed(f"${value:.{digits}f}", d < 0, plus=True)


def fmt_signed3(x: float) -> str:
    value = round(abs(x), 3)
    if value == 0:
        return "0.000"
    return _signed(f"{value:.3f}", x < 0, plus=False)


def fmt_cache(s: RunSummary) -> str:
    # With a cache the runner does one output lookup per task, so 0 lookups means no cache.
    if s.cache_output_total == 0:
        return "cache off"
    text = f"cache {s.cache_output_hits}/{s.cache_output_total} outputs"
    if s.cache_judge_total:
        text += f" · {s.cache_judge_hits}/{s.cache_judge_total} judge"
    return text


def fmt_ts(dt: datetime) -> str:
    if dt.tzinfo is None:  # run files always hold UTC; a naive time is read as UTC
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def md_cell(s: str, limit: int, *, markdown: bool = True) -> str:
    """Make free text safe for one table cell, at most `limit` chars long.

    `markdown=False` is the terminal cell: the same text without the HTML and mention escapes.
    """
    s = s.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    s = s.replace("|", "\\|")
    if markdown:
        # The PR comment is public: raw HTML must not render and an @name must not notify.
        # Backslashes before "<" are doubled first so they cannot cancel the "\<" escape.
        s = _BEFORE_LT.sub(lambda m: m.group(1) * 2 + "\\<", s)
        s = s.replace("@", "@\u200d")  # a zero-width joiner after @ stops the mention
    if len(s) > limit:
        cut = s[: limit - 1]
        # A cut between "\" and "|" or "<" would leave a lone backslash that escapes the "…".
        if cut.endswith("\\") and s[limit - 1] in "|<":
            cut = cut[:-1]
        s = cut + "…"
    return s
