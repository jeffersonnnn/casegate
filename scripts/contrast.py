"""Check the casegate palettes against WCAG 2.x contrast (docs/DESIGN.md §1 and §7).

A colour change in DESIGN must not quietly break AA, so this prints every required pair
and exits 1 when one fails. Usage: `contrast.py` for all pairs, `contrast.py FG BG` for one.
"""
from __future__ import annotations

import sys

TEXT_MIN = 4.5  # WCAG 1.4.3 AA, normal text
GRAPHIC_MIN = 3.0  # WCAG 1.4.11, graphical objects


def _channel(v: int) -> float:
    c = v / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"expected #RRGGBB, got {hex_colour!r}")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def ratio(fg: str, bg: str) -> float:
    a, b = sorted((luminance(fg), luminance(bg)), reverse=True)
    return round((a + 0.05) / (b + 0.05), 2)


# Each pair carries its own minimum: text needs AA, the logo parts are graphics (1.4.11).
DARK_BG, DARK_SURFACE = "#0B0F0E", "#141A18"
LIGHT_BG = "#F4F7F5"
PAIRS: list[tuple[str, str, str, str, str, float]] = []
for name, fg in [
    ("text", "#E3ECE7"),
    ("muted", "#8FA39A"),
    ("pass", "#3DDC84"),
    ("fail", "#FF5D5D"),
    ("warn", "#E8C547"),
]:
    PAIRS.append(("dark §1", name, fg, "bg", DARK_BG, TEXT_MIN))
    PAIRS.append(("dark §1", name, fg, "surface", DARK_SURFACE, TEXT_MIN))
PAIRS += [
    ("light §7", "text", "#0B0F0E", "bg", LIGHT_BG, TEXT_MIN),
    ("light §7", "muted / grey ticks", "#5E6E67", "bg", LIGHT_BG, TEXT_MIN),
    ("light §7", "fail ticks", "#C8312F", "bg", LIGHT_BG, TEXT_MIN),
    ("light §7", "post/hub material", "#0B0F0E", "bg", LIGHT_BG, GRAPHIC_MIN),
    ("light §7", "arm", "#1A8F4E", "bg", LIGHT_BG, GRAPHIC_MIN),
]


def main(argv: list[str]) -> int:
    if len(argv) == 2:
        print(f"{ratio(argv[0], argv[1]):.2f}:1")
        return 0
    if argv:
        print(__doc__, file=sys.stderr)
        return 2
    bad = 0
    print(f"{'palette':<9} {'pair':<36} {'ratio':>8}  {'min':>4}  ok")
    for pal, fname, fg, bname, bg, need in PAIRS:
        r = ratio(fg, bg)
        ok = r >= need
        bad += not ok
        pair = f"{fname} {fg} on {bname}"
        print(f"{pal:<9} {pair:<36} {r:>6.2f}:1  {need:>4.1f}  {'yes' if ok else 'NO'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
