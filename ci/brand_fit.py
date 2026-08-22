#!/usr/bin/env python3
"""Report which pattern declarations would drop on a real brand's stylesheet.

A `var()` with no fallback and no definition INVALIDATES THE WHOLE DECLARATION
at compute time. The property is not set at all: it does not fall back to a
sensible default and it does not keep the author's intent. So a token this
library assumes and a brand does not define is a missing rule rather than a
different shade - `background: var(--color-scrim)` paints nothing, and the text
meant to sit on that scrim sits on the photograph instead.

Every other check here tests the library against its own declared contract.
This one tests the contract against the brands, which is the only way to find
out whether the contract is true.

    python ci/brand_fit.py <dir-of-brand-checkouts> [more dirs...]

Each directory is searched for global.css files, one per brand. Nothing about
any brand is stored in this repository: the paths are supplied by whoever runs
it and the report goes to stdout, which is why this is not wired into CI.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAR_USE = re.compile(r"var\(\s*(--[\w-]+)\s*(,)?")
# Unanchored on purpose: brands put several declarations on one line, and an
# anchored match sees only the first, which understates what they define.
# A use is var(--x) with no colon, so this cannot mistake one for a definition.
VAR_DEF = re.compile(r"(--[\w-]+)\s*:")


def defined_in(text):
    return set(VAR_DEF.findall(text))


def pattern_needs():
    """{pattern: {token: uses}} counting only tokens with no fallback that the
    pattern does not define for itself."""
    out = {}
    for folder in sorted(p for p in (ROOT / "patterns").iterdir() if p.is_dir()):
        css = re.sub(r"/\*.*?\*/", "",
                     (folder / "pattern.css").read_text(encoding="utf-8"),
                     flags=re.S)
        own = defined_in(css)
        need = defaultdict(int)
        for tok, fallback in VAR_USE.findall(css):
            if tok not in own and not fallback:
                need[tok] += 1
        out[folder.name] = dict(need)
    return out


DIAL = re.compile(r"--(type|space)-scale\s*:\s*([^;}]+)")


def check_dials(brand, text):
    """The two dials are unitless multipliers, and a unit silently deletes type.

    calc(clamp(2rem, 4vw, 3.5rem) * var(--type-scale, 1)) multiplies a length
    by a number. Give it a length instead and the product is an area, the
    whole calc is invalid, and font-size falls back to whatever is inherited -
    which on a heading is body size. The page does not error; it just goes
    flat, on every display size at once.

    A brand is outside this library's CI, so this is the only place the
    mistake can be caught before it ships.
    """
    out = []
    for which, value in DIAL.findall(text):
        v = value.strip()
        if not re.fullmatch(r"\d*\.?\d+", v):
            out.append(f"  {brand}: --{which}-scale is {v!r} - it must be a "
                       f"bare number. A unit makes every declaration using it "
                       f"invalid, and the type silently collapses to inherited size.")
    return out


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    brands = {}
    dial_faults = []
    for root in argv:
        base = Path(root)
        # One stylesheet per brand. A checkout often holds the same tokens
        # twice - assets/global.css and for-toolkit/site/global.css - and
        # counting both inflates the denominator, which makes a token look
        # better covered than it is. Group by the top folder under the root
        # and keep the deepest path, which is the checkout rather than a copy.
        best = {}
        for css in sorted(base.rglob("global.css")):
            rel = css.relative_to(base)
            brand = rel.parts[0]
            if brand not in best or len(rel.parts) > len(best[brand].relative_to(base).parts):
                best[brand] = css
        for brand, css in best.items():
            raw = css.read_text(encoding="utf-8", errors="replace")
            brands[brand] = defined_in(raw)
            dial_faults.extend(check_dials(brand, raw))
    if not brands:
        print("no global.css found under: " + ", ".join(argv))
        return 2

    if dial_faults:
        print("dial faults - these break type outright:")
        print(chr(10).join(dial_faults) + chr(10))

    needs = pattern_needs()
    every = sorted({t for n in needs.values() for t in n})
    print(f"{len(needs)} patterns against {len(brands)} brand stylesheets\n")

    unmet = []
    for tok in every:
        have = sum(1 for d in brands.values() if tok in d)
        note = "" if have == len(brands) else (
            "   <-- NONE" if not have else "   <-- partial")
        print(f"  {tok:<24} {have}/{len(brands)}{note}")
        if not have:
            unmet.append(tok)

    print("\nper brand, declarations that would not apply:")
    for label, defined in sorted(brands.items()):
        lost = sum(n for u in needs.values()
                   for t, n in u.items() if t not in defined)
        pats = sum(1 for u in needs.values()
                   if any(t not in defined for t in u))
        print(f"  {label:<24} {lost:>4} across {pats}/{len(needs)} patterns")

    if unmet:
        print(f"\ndefined by no brand at all ({len(unmet)}):")
        for t in unmet:
            print(f"  {t}")
    return 1 if unmet else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
