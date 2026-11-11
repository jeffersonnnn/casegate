"""Turns token counts into dollars so every run can report what it cost.

The table is a dated snapshot (FACTS §4.4); CASEGATE_PRICES lets a user correct or extend
it without a release. An unknown model gives None, never 0, so a missing price shows up as
"cost unknown" instead of a run that looks free.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

PRICES_AS_OF = "2026-11-03"  # source: claude-api reference; FACTS §4.4
PRICES: dict[str, tuple[float, float]] = {  # USD per 1M tokens: (input, output)
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "gpt-4.1-mini": (0.40, 1.60),  # UNVERIFIED: re-check at M2 against the provider page
    "gpt-4.1": (2.00, 8.00),  # UNVERIFIED
}


def _load_overrides(path: str) -> dict[str, tuple[float, float]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"CASEGATE_PRICES {path}: expected a JSON object of model -> [in, out]")
    table: dict[str, tuple[float, float]] = {}
    for model, pair in raw.items():
        if not (isinstance(pair, list) and len(pair) == 2):
            raise ValueError(f"CASEGATE_PRICES {path}: {model!r} must be [input, output]")
        price_in, price_out = float(pair[0]), float(pair[1])
        # NaN, inf or a negative price would print as "$nan" or make a run look cheaper.
        if not all(math.isfinite(p) and p >= 0 for p in (price_in, price_out)):
            raise ValueError(f"CASEGATE_PRICES {path}: {model!r} prices must be finite and >= 0")
        table[str(model)] = (price_in, price_out)
    return table


def price_table() -> dict[str, tuple[float, float]]:
    """The built-in table with CASEGATE_PRICES merged over it (read on each call)."""
    table = dict(PRICES)
    override = os.environ.get("CASEGATE_PRICES")
    if override:
        table.update(_load_overrides(override))
    return table


def cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    prices = price_table().get(model)
    if prices is None:
        return None
    price_in, price_out = prices
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000
