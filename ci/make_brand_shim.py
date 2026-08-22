#!/usr/bin/env python3
"""Write the block that makes this library's contract true on a real brand.

Brands ship a design-system scale - --radius-lg, --shadow-md, --color-accent -
where this library names roles: --card-radius, --card-shadow, --color-on-primary.
Most of that is a rename and can be mapped mechanically. Five tokens cannot,
because no brand carries them, and one of those five needs a decision that only
a measurement can make: whether text on the brand's primary colour should be
light or dark. Guessing white is wrong on any brand with a pale primary, and
wrong silently, because an unreadable button still looks like a button.

    python ci/make_brand_shim.py <brand>/site/global.css

Prints a :root block to paste into that brand's stylesheet, directly after its
own :root, plus the measurements behind every choice it made. Reads only; it
never edits the brand.
"""
import math
import re
import sys
from pathlib import Path

VAR_DEF = re.compile(r"^\s*(--[\w-]+)\s*:\s*([^;]+);", re.M)

# A dark neutral, deliberately not derived from the brand. TOKENS.md requires
# the scrim to be a neutral rather than a brand tint: a tinted scrim over a
# photograph shifts every colour under it, and the contrast promise is made
# against this value rather than against whatever the brand's darkest ink is.
SCRIM = "#11161d"
ON_SCRIM = "#ffffff"


def srgb(hex_or_rgb):
    s = hex_or_rgb.strip()
    m = re.match(r"#([0-9a-fA-F]{3})$", s)
    if m:
        s = "#" + "".join(c * 2 for c in m.group(1))
    m = re.match(r"#([0-9a-fA-F]{6})", s)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    m = re.match(r"rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)", s)
    if m:
        return tuple(int(m.group(i)) / 255 for i in (1, 2, 3))
    return None


def luminance(rgb):
    def ch(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    l1, l2 = luminance(a), luminance(b)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def calibrated():
    """Refuse to report a figure from an implementation that cannot reproduce
    two answers known independently."""
    checks = [(("#ffffff", "#000000"), 21.00), (("#ffffff", "#767676"), 4.54)]
    return all(abs(ratio(srgb(a), srgb(b)) - want) < 0.05 for (a, b), want in checks)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if not calibrated():
        print("contrast implementation failed calibration; reporting nothing")
        return 3

    path = Path(argv[0])
    tokens = dict(VAR_DEF.findall(path.read_text(encoding="utf-8", errors="replace")))

    def has(name):
        return name in tokens

    print(f"/* read: {path.name} */")
    notes, unresolved = [], []

    primary = srgb(tokens.get("--color-primary", ""))
    text = srgb(tokens.get("--color-text", ""))
    on_primary = None
    if primary:
        white, dark = srgb("#ffffff"), text or srgb("#000000")
        rw, rd = ratio(white, primary), ratio(dark, primary)
        # Prefer whichever clears 4.5:1; where both do, take the higher.
        if max(rw, rd) < 4.5:
            unresolved.append(
                f"--color-on-primary: neither white ({rw:.2f}) nor the brand's "
                f"own text colour ({rd:.2f}) clears 4.5:1 against "
                f"--color-primary. This brand needs a different button ink or a "
                f"darker primary; it cannot be decided here.")
        else:
            on_primary = "#ffffff" if rw >= rd else tokens["--color-text"].strip()
            notes.append(f"--color-on-primary: white {rw:.2f}, brand text "
                         f"{rd:.2f} against --color-primary; took "
                         f"{'white' if rw >= rd else 'the brand text colour'}")
    else:
        unresolved.append("--color-primary is not defined or not a plain colour, "
                          "so --color-on-primary cannot be measured")

    if primary is None:
        pass
    notes.append(f"--color-on-scrim on --color-scrim: "
                 f"{ratio(srgb(ON_SCRIM), srgb(SCRIM)):.2f}")

    print(":root {")
    print("  /* Shape: the brand's scale, under the names the patterns use. */")
    for role, source, default in (
            ("--card-radius", "--radius-lg", "0.75rem"),
            ("--btn-radius", "--radius-md", "0.5rem"),
            ("--chip-radius", "--radius-pill", "999px"),
            ("--card-shadow", "--shadow-md", "none"),
    ):
        src = f"var({source}, {default})" if has(source) else default
        print(f"  {role}: {src};")
    print("  --card-border: 1px solid color-mix(in srgb, var(--color-text) 12%, transparent);")
    slow = "--transition-base" if has("--transition-base") else None
    print(f"  --transition-slow: {'var(%s, 400ms ease)' % slow if slow else '400ms ease'};")

    print("\n  /* Inks the contract needs and no brand carries. */")
    print("  --color-heading: var(--color-text);")
    print("  --color-rule: color-mix(in srgb, var(--color-text) 18%, transparent);")
    print(f"  --color-scrim: {SCRIM};")
    print(f"  --color-on-scrim: {ON_SCRIM};")
    if on_primary:
        print(f"  --color-on-primary: {on_primary};")
    else:
        print("  /* --color-on-primary: UNRESOLVED, see below */")
    print("}")

    print("\n/* measured */")
    for n in notes:
        print(f"   {n}")
    if unresolved:
        print("\n/* NEEDS A DECISION */")
        for u in unresolved:
            print(f"   {u}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
