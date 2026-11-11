#!/usr/bin/env python3
"""Check that docs/explain/ stays true to the code.

- Every `path:line` (or `path:line-line`) reference in docs/explain/**/*.md must point at an
  existing file and line. If written as `path:line` `symbol`, the symbol must appear within
  5 lines of that line.
- Every row in 03-numbers.md must name an existing source file in its "Source" column.
- README.md must hold the readability check table.
- [PLANNED: ...] and [TBD: ...] markers are counted, not failed.

Usage: python scripts/check_explain.py [repo_root]   (exit 1 on any broken reference)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REF = re.compile(r"`([A-Za-z0-9_./-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`(?:\s*`([^`]+)`)?")
PLANNED = re.compile(r"\[PLANNED:[^\]]*\]")
TBD = re.compile(r"\[TBD:[^\]]*\]")
WINDOW = 5


def check(root: Path) -> int:
    explain = root / "docs" / "explain"
    if not explain.is_dir():
        print(f"no {explain}")
        return 1
    errors: list[str] = []
    refs = planned = tbd = 0
    for md in sorted(explain.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        planned += len(PLANNED.findall(text))
        tbd += len(TBD.findall(text))
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in REF.finditer(line):
                refs += 1
                path, start, end, symbol = m.group(1), int(m.group(2)), m.group(3), m.group(4)
                target = root / path
                where = f"{md.relative_to(explain)}:{lineno}"
                if not target.is_file():
                    errors.append(f"{where}: missing file {path}")
                    continue
                src = target.read_text(encoding="utf-8", errors="replace").splitlines()
                last = int(end) if end else start
                if start < 1 or last > len(src) or last < start:
                    errors.append(f"{where}: {path}:{start}{'-' + end if end else ''} out of range (file has {len(src)} lines)")
                    continue
                if symbol:
                    lo, hi = max(0, start - 1 - WINDOW), min(len(src), last + WINDOW)
                    name = symbol.strip("()").split(".")[-1]
                    if not any(name in s for s in src[lo:hi]):
                        errors.append(f"{where}: symbol `{symbol}` not within {WINDOW} lines of {path}:{start}")
    numbers = explain / "03-numbers.md"
    rows = 0
    if numbers.is_file():
        lines = numbers.read_text(encoding="utf-8").splitlines()
        header = None
        for lineno, line in enumerate(lines, 1):
            if not line.startswith("|"):
                header = None
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if header is None:
                header = [c.lower() for c in cells]
                continue
            if set(line) <= set("|-: "):
                continue
            if "source" not in header:
                continue
            rows += 1
            value = cells[header.index("value")] if "value" in header else ""
            source = cells[header.index("source")].strip("` ")
            if TBD.search(value) or TBD.search(source):
                continue
            src_path = source.split(":")[0].split(" ")[0].strip("`")
            if not src_path or not (root / src_path).exists():
                errors.append(f"03-numbers.md:{lineno}: source `{source}` does not exist")
    readme = explain / "README.md"
    if not readme.is_file() or "readability check" not in readme.read_text(encoding="utf-8").lower():
        errors.append("README.md: missing the readability check table (see walkthrough FORMAT.md)")
    for e in errors:
        print("FAIL", e)
    print(f"refs={refs} number_rows={rows} planned={planned} tbd={tbd} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(check(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()))
