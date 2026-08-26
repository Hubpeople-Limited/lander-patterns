"""The five brand dials, and every way a brand can get them wrong.

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
# What all three share is that a unit is a fault. What the unit COSTS is not
# shared, and is not even shared within a kind - see LOST below.
MULTIPLIER, OFFSET, WEIGHT = "multiplier", "offset", "weight"
DIALS = {
    "type-scale":       (MULTIPLIER, TYPE_MIN, TYPE_MAX),
    "space-scale":      (MULTIPLIER, SPACE_MIN, SPACE_MAX),
    "heading-leading":  (MULTIPLIER, LEAD_MIN, LEAD_MAX),
    "heading-tracking": (OFFSET, TRACK_MIN, TRACK_MAX),
    "weight-display":   (WEIGHT, WEIGHT_MIN, WEIGHT_MAX),
}

# Where each dial ACTUALLY lands when the substitution is invalid, per dial
# and not per kind. Keyed by kind, two of these five named the wrong fallback,
# and a wrong fallback sends the reader looking somewhere the fault is not:
#
#   --weight-display does not fall back to the pattern's own 700, because
#   font-weight is inherited: an invalid substitution is invalid at
#   computed-value time, and the element takes its ANCESTOR's weight. Probed
#   with an ancestor at 300 and the dial at 700px, the heading computes 300 -
#   body weight, so a real brand's headings go bold to regular.
#
#   --heading-leading is not "the type collapses to inherited size" either.
#   Nothing about font-size moves; the leading does, and it lands on the
#   inherited line-height rather than on the 1.02 the pattern designed.
#
# The two length-times-length dials both drop, and they drop to different
# places, because font-size is inherited and padding is not.
LOST = {
    "type-scale":
        "every calc() reading it is invalid and drops, and font-size is "
        "inherited, so every display size collapses to whatever it sits "
        "inside - on every viewport at once",
    "space-scale":
        "every step of the ramp is invalid where it is used, and padding, "
        "margin and gap are not inherited, so they fall to 0 and the page "
        "loses every gap it had",
    "heading-leading":
        "every line-height reading it drops, so display type takes the "
        "inherited leading rather than the tight one the pattern designed",
    "heading-tracking":
        "letter-spacing falls back to `normal` - not to the value the pattern "
        "designed, so the brand loses tracking it never set",
    "weight-display":
        "font-weight is inherited, so the declaration is invalid at "
        "computed-value time and the element takes its ANCESTOR's weight "
        "rather than the pattern's 700. On a brand whose body is 400 that is "
        "every display heading going from bold to regular",
}

# --heading-leading is the one dial a unit does not break by dropping. The
# pattern writes `calc(1.02 * var(--heading-leading, 1))`, and number times
# length is VALID CSS: nothing drops and nothing warns. Chromium computes
# `calc(1.02 * 1.1rem)` to 17.952px, line-height is inherited, so a 40px
# heading and the 20px line under it are both set on a 17.952px body and the
# text overlaps itself. Saying "it drops" here would be the same class of
# mistake this table exists to correct.
LOST_UNIT = dict(LOST, **{
    "heading-leading":
        "a number times a length is valid CSS, so nothing drops and nothing "
        "warns - line-height becomes a fixed length that no longer tracks "
        "font-size and is inherited by everything under the heading. "
        "calc(1.02 * 1.1rem) is 17.952px on a 40px heading and 17.952px on "
        "the 20px line below it, which overlap",
})

# Unanchored, and tolerant of what really appears in a declaration: several
# declarations share a line, and `!important` and trailing comments are both
# valid and both were flagged as faults by the first version of this.
# Longest-first so `type-scale` cannot shadow a longer name sharing a prefix.
#
# `[^;}]*`, not `[^;}]+`: `--heading-tracking:;` is a legal declaration whose
# value is the empty token sequence, and it is not equivalent to not setting
# the dial. var() substitutes nothing into the calc(), the calc() is invalid,
# and letter-spacing computes to `normal`. Requiring one character made that
# declaration invisible to this whole module.
DIAL = re.compile(r"--(%s)\s*:\s*([^;}]*)"
                  % "|".join(sorted(DIALS, key=len, reverse=True)))
# Scientific notation is a bare number in CSS: `1e-2` is 0.01 and computes
# exactly like `0.01`. Rejecting it made a valid value a fatal fault.
NUMBER = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")


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


def var_fallback(v):
    """The fallback inside a leading `var(...)`, or None when there is none.

    Splits on the first comma at depth one, so a nested `var(--a, var(--b, 1))`
    hands back `var(--b, 1)` whole rather than `var(--b` - which would then be
    read for units and found clean.
    """
    m = re.match(r"^var\s*\(", v, re.I)
    if not m:
        return None
    depth, i, comma = 1, m.end(), None
    while i < len(v) and depth:
        if v[i] == "(":
            depth += 1
        elif v[i] == ")":
            depth -= 1
            if not depth:
                break
        elif v[i] == "," and depth == 1 and comma is None:
            comma = i
        i += 1
    if comma is None:
        return None
    return v[comma + 1:i]


def check_dials(brand, text):
    """Every way a brand can set one of the five dials wrong.

    A dial is a bare number. The failure modes, in descending order of how
    quietly they break a live page:

    - A length (`1.1rem`). What it costs differs per dial and is spelled out
      in LOST above: three of the five drop the declaration, --heading-leading
      stays valid and silently stops scaling, and --weight-display hands the
      element its ancestor's weight.
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
        # thing to write and the referenced property cannot be resolved from
        # one file - but the FALLBACK can, because it is right there in the
        # same declaration, and it is the value the brand ships whenever the
        # indirection is not set. Exempting the whole var() reopened the unit
        # trap on the dial TOKENS.md calls the worst in the library:
        # `--heading-tracking: var(--brand-track, 0.02em)` passed clean and
        # computed letter-spacing to `normal`.
        #
        # A var() with NO fallback is genuinely left alone, and correctly so:
        # an unresolvable var() makes the custom property guaranteed-invalid,
        # which means the pattern's own `var(--heading-tracking, 0)` falls
        # back to the designed value. Probed: letter-spacing -0.02em, intact.
        #
        # calc() and its relatives are NOT exempt, however convenient that
        # was. calc(1.1px) computes to a length, not a number, so the unit
        # trap this whole check exists for is fully available inside one -
        # and exempting them reopened it. A math function is read for units
        # like anything else.
        if v and re.match(r"^var\s*\(", v, re.I):
            inner = var_fallback(v)
            if inner is None:
                continue
            if not inner.strip():
                out.append((True, f"{brand}: {token} is {raw.strip()!r}, whose "
                                  f"fallback is empty. An empty fallback "
                                  f"substitutes nothing rather than the "
                                  f"default, so {LOST[which]}."))
            elif UNIT.search(inner):
                out.append((True, f"{brand}: {token} is {raw.strip()!r}. The "
                                  f"fallback carries a unit, and it is the "
                                  f"value that ships whenever the brand's own "
                                  f"property is not set - "
                                  f"{LOST_UNIT[which]}."))
            continue
        if v and re.match(r"^(calc|clamp|min|max)\s*\(", v, re.I):
            if UNIT.search(v):
                out.append((True, f"{brand}: {token} is {raw.strip()!r}, which "
                                  f"computes to a length rather than a number. "
                                  f"A math function is not an escape from the "
                                  f"unit rule - {LOST_UNIT[which]}."))
            continue

        if v is None or not NUMBER.match(v):
            # Every dial has to be a bare number. What that COSTS is per dial,
            # not per kind - naming the wrong fallback sends the reader
            # looking somewhere the fault is not, which is worse than saying
            # nothing. And a unit is not the same fault as an empty or
            # unreadable value: on --heading-leading a unit stays valid.
            if v is None:
                out.append((True, f"{brand}: {token} is empty. An empty value "
                                  f"is a declaration, not the absence of one, "
                                  f"and it substitutes nothing: {LOST[which]}."))
            else:
                out.append((True, f"{brand}: {token} is {raw.strip()!r}. It "
                                  f"must be a bare number: "
                                  f"{LOST_UNIT[which] if UNIT.search(v) else LOST[which]}."))
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
