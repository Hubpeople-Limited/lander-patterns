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
# held to a measure break in the wrong places, and 44px targets lose their
# room. (That measure used to be 16ch and is now 10.75em - see TOKENS.md on
# why display measures are em: ch is the digit advance of whichever face the
# brand chose, so it moved 26% between this library's own sample brands.)
TYPE_MIN, TYPE_MAX = 0.9, 1.2
SPACE_MIN, SPACE_MAX = 0.85, 1.2

# The tightest leading shipped is 1.02, and 1.02 * 0.9 is 0.918, where
# ascenders and descenders overlap outright - so this floor is 0.95, not the
# 0.9 the other multipliers use. Past 1.15 the 1.3 card headings reach 1.5 and
# the dial has started changing card heights rather than type.
LEAD_MIN, LEAD_MAX = 0.95, 1.15
# An offset in em, so its ends are not arranged about 1 like a multiplier's.
# At -0.02 the -0.035em quotes reach -0.055em, where a tight face touches; at
# +0.04 a headline held to 10.75em gains enough advance to lose a word a line.
TRACK_MIN, TRACK_MAX = -0.02, 0.04
WEIGHT_MIN, WEIGHT_MAX = 400, 800

# Three kinds, and conflating them is exactly what this table exists to stop.
#
#   multiplier  1 is the identity. 0 blanks the page, negative is invalid.
#   offset      0 is the identity, and NEGATIVE IS THE ORDINARY CASE - 40 of
#               the 41 tracking values in this library are negative, because
#               display type is drawn tight. Applying the multiplier rules to
#               tracking would fail the build on the two commonest settings a
#               brand could reasonably choose.
#   weight      neither: a CSS weight, nowhere near 0 or 1 at rest.
#
# What all three DO share is the unit trap, which is why they are all here. A
# unit makes the calc() invalid and the declaration drops. For tracking that
# is worse than it sounds: the fallback is not the pattern's designed
# -0.02em, it is `normal`, so the brand loses tracking it never set.
MULTIPLIER, OFFSET, WEIGHT = "multiplier", "offset", "weight"
DIALS = {
    "type-scale":       (MULTIPLIER, TYPE_MIN, TYPE_MAX),
    "space-scale":      (MULTIPLIER, SPACE_MIN, SPACE_MAX),
    "heading-leading":  (MULTIPLIER, LEAD_MIN, LEAD_MAX),
    "heading-tracking": (OFFSET, TRACK_MIN, TRACK_MAX),
    "weight-display":   (WEIGHT, WEIGHT_MIN, WEIGHT_MAX),
}

# Unanchored, and tolerant of what really appears in a declaration: several
# declarations share a line, and `!important` and trailing comments are both
# valid and both were flagged as faults by the first version of this.
# Longest-first so `type-scale` cannot shadow a longer name sharing a prefix.
DIAL = re.compile(r"--(%s)\s*:\s*([^;}]+)"
                  % "|".join(sorted(DIALS, key=len, reverse=True)))
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

# The same unit set _containment uses. A shorter list here meant calc(1.1vmin)
# and seven other spellings walked through the check that exists to stop
# exactly this.
UNIT = re.compile(
    r"\d\s*(px|rem|em|ch|ex|vw|vh|vmin|vmax|svw|svh|lvw|lvh|dvw|dvh"
    r"|cm|mm|in|pt|pc|q|%)", re.I)


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
        token = "--%s" % which
        kind, lo, hi = DIALS[which]

        # A dial reached through the brand's own indirection is a reasonable
        # thing to write, cannot be resolved from one file, and is therefore
        # left alone rather than called a fault.
        #
        # calc() and its relatives are NOT exempt, however convenient that
        # was. calc(1.1px) computes to a length, not a number, so the unit
        # trap this whole check exists for is fully available inside one -
        # and exempting them reopened it. A math function is read for units
        # like anything else.
        if v and re.match(r"^var\s*\(", v, re.I):
            continue
        if v and re.match(r"^(calc|clamp|min|max)\s*\(", v, re.I):
            if UNIT.search(v):
                out.append((True, f"{brand}: {token} is {raw.strip()!r}, which "
                                  f"computes to a length rather than a number. "
                                  f"A math function is not an escape from the "
                                  f"unit rule - every declaration using the "
                                  f"dial would still be invalid."))
            continue

        if v is None or not NUMBER.match(v):
            # The unit trap, and it is the one rule every kind shares. What
            # the value falls back TO differs, though, and saying the wrong
            # one sends the reader looking in the wrong place.
            lost = {
                MULTIPLIER: "the type silently collapses to inherited size",
                OFFSET: "letter-spacing falls back to `normal` - not to the "
                        "value the pattern designed, so the brand loses "
                        "tracking it never set",
                WEIGHT: "the weight falls back to the pattern's own default",
            }[kind]
            out.append((True, f"{brand}: {token} is {raw.strip()!r}. It must be "
                              f"a bare number - a unit makes every declaration "
                              f"using it invalid, and {lost}."))
            continue

        n = float(v)

        # An offset's identity is 0 and its ordinary case is negative, so the
        # collapse and negative rules below are about multipliers only. Run
        # them on tracking and the build fails on `0` - the documented
        # default - which is the most obviously correct value a brand can set.
        if kind == MULTIPLIER:
            if 0 <= n < COLLAPSE:
                out.append((True, f"{brand}: {token} is {v}, which computes the "
                                  f"sizes it touches to nothing readable. Below "
                                  f"{COLLAPSE} the text is not small, it is gone."))
                continue
            if n < 0:
                out.append((True, f"{brand}: {token} is {v}. A negative "
                                  f"multiplier makes the result invalid, so the "
                                  f"declaration drops and the size falls back "
                                  f"to inherited."))
                continue
        elif kind == WEIGHT:
            if not 1 <= n <= 1000:
                out.append((True, f"{brand}: {token} is {v}, which is not a CSS "
                                  f"weight. Outside 1-1000 the declaration is "
                                  f"invalid and drops."))
                continue

        if not lo <= n <= hi:
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
