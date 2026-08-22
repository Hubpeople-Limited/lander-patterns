"""The two brand dials, and every way a brand can get them wrong.

Kept apart from brand_fit.py so the rules are testable on their own, and so
the range they enforce sits in one place rather than being restated wherever
it happens to be needed.

The first version of this check was worse than nothing twice over: it printed
its findings and then returned an exit code derived from something else
entirely, so a build gated on the exit status shipped the fault anyway - and
it accepted `0`, which is a more complete way to destroy a page than the unit
it was written to catch.
"""

import re

# The range TOKENS.md documents, and it has to be the same number in both
# places: the contrast guarantees are stated across this range, and CI holds
# every --color-heading floor above 24px at TYPE_MIN. Widen it here and those
# guarantees quietly stop covering the range the contract claims they cover.
# Outside it the clamp() floors also stop being sensible at 320px, headlines
# held to 16ch break in the wrong places, and 44px targets lose their room.
TYPE_MIN, TYPE_MAX = 0.9, 1.2
SPACE_MIN, SPACE_MAX = 0.85, 1.2

# Unanchored, and tolerant of what really appears in a declaration: several
# declarations share a line, and `!important` and trailing comments are both
# valid and both were flagged as faults by the first version of this.
DIAL = re.compile(r"--(type|space)-scale\s*:\s*([^;}]+)")
NUMBER = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)$")


def read_dial(raw):
    """The declared value with !important and comments stripped, or None."""
    v = re.sub(r"/\*.*?\*/", " ", raw, flags=re.S)
    v = re.sub(r"!\s*important", " ", v, flags=re.I)
    return v.strip() or None


def strip_comments(text):
    """A commented-out declaration is not a declaration.

    This cut both ways and neither was right: a commented-out dial was
    reported as a fatal fault although it ships nothing, and a commented-out
    `--space-scale: 1` satisfied the ramp check while resolving to nothing.
    """
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


# Below this, a multiplier is not a smaller page - it is a blank one. The
# first version made only an exact 0 fatal, so 0.0001 was a warning and the
# build passed with every heading computed to three thousandths of a pixel.
COLLAPSE = 0.5


def check_dials(brand, text):
    """Every way --type-scale or --space-scale can be set wrong.

    A dial is a bare multiplier. The failure modes, in descending order of how
    quietly they break a live page:

    - A length (`1.1rem`). Length times length is an area, the whole calc() is
      invalid, the declaration drops, and the heading falls back to inherited
      size. Nothing errors; the page just goes flat on every display size at
      once.
    - Zero. Every display size computes to 0px and the headings are simply
      gone. legibility.py already treats font-size 0 as hidden content inside
      the library; a brand can do the same thing from outside it.
    - Negative. A negative font-size is invalid, so the declaration drops the
      same way a length does.
    - Merely extreme. Valid, renders, and looks broken - which is the one case
      worth a softer word, because a brand may mean it.
    """
    out = []
    for which, raw in DIAL.findall(strip_comments(text)):
        v = read_dial(raw)
        token = "--%s-scale" % which
        lo, hi = (TYPE_MIN, TYPE_MAX) if which == "type" else (SPACE_MIN, SPACE_MAX)

        # A dial reached through the brand's own indirection is a reasonable
        # thing to write and cannot be resolved from one file, so it is left
        # alone rather than called a fault. calc() likewise computes to a
        # number; the unit trap this check exists for is not available there.
        if v and re.match(r"^(var|calc|clamp|min|max)\s*\(", v, re.I):
            continue

        if v is None or not NUMBER.match(v):
            out.append((True, f"{brand}: {token} is {raw.strip()!r}. It must be "
                              f"a bare number - a unit makes every declaration "
                              f"using it invalid, and the type silently "
                              f"collapses to inherited size."))
            continue

        n = float(v)
        if 0 <= n < COLLAPSE:
            out.append((True, f"{brand}: {token} is {v}, which computes the "
                              f"sizes it touches to nothing readable. Below "
                              f"{COLLAPSE} the text is not small, it is gone."))
        elif n < 0:
            out.append((True, f"{brand}: {token} is {v}. A negative multiplier "
                              f"makes the result invalid, so the declaration "
                              f"drops and the size falls back to inherited."))
        elif not lo <= n <= hi:
            out.append((False, f"{brand}: {token} is {v}, outside the "
                               f"{lo}-{hi} range TOKENS.md documents. It will "
                               f"render, but it was not designed to."))
    return out


def check_ramp_resolves(brand, text):
    """A spacing ramp defined in terms of a dial the brand never declared.

    TOKENS.md gives the ramp recipe as `calc(0.25rem * var(--space-scale))`.
    Copy that without the `--space-scale: 1` line above it and every --space-*
    token is defined, valid to the eye, and resolves to nothing - which takes
    every padding, margin and gap in all forty patterns with it.

    Checking that a token is *defined* cannot see this. That is the whole
    reason it is worth a check of its own: the name is there, and the value is
    not.
    """
    text = strip_comments(text)
    # Not `calc\([^)]*` - that cannot cross a nested closing bracket, so a
    # ramp written as calc(var(--base, 0.25rem) * var(--space-scale)) was
    # missed. Any bare use of the dial inside a calc is the same hazard.
    uses_bare = re.search(r"calc\(.*?var\(\s*--space-scale\s*\)", text, re.S)
    declares = re.search(r"--space-scale\s*:", text)
    if uses_bare and not declares:
        return [(True, f"{brand}: the spacing ramp is defined in terms of "
                       f"var(--space-scale) with no fallback, and --space-scale "
                       f"is never declared. Every --space-* token resolves to "
                       f"nothing, which deletes every padding, margin and gap "
                       f"in every pattern. Either declare it or write the "
                       f"fallback: var(--space-scale, 1).")]
    return []
