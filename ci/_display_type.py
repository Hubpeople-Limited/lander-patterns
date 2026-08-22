"""Which font-sizes in a stylesheet are display type, and must carry the dial.

The first version of this asked one question per rule: does this rule set both
the heading face and a font-size? That misses every stylesheet written the way
stylesheets are actually written - the face declared once for a group of
selectors, the sizes declared separately underneath. Three sizes in the
shipped library evaded it, and a fourth was a media-query override of a size
that did carry the dial, which produced a worse fault than a static size: a
12.8px discontinuity across a single pixel of viewport width.

So the face is resolved across the whole file first, and only then are the
sizes checked.
"""

import re

RULE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
FACE = "var(--font-heading)"

# A font-size may be the last declaration in a rule with no trailing
# semicolon, and a rule may carry more than one - a base size and an override.
# Matching only `...;` and only the first occurrence missed both.
SIZE = re.compile(r"font-size\s*:\s*([^;}]+)")
SHORTHAND = re.compile(r"(?<![-\w])font\s*:\s*([^;}]+)")

# A keyword size takes its value from somewhere that already carries the dial,
# so it moves correctly by doing nothing. `font: inherit` is also the standard
# reset on a button, where flagging it would teach people to ignore this check.
KEYWORDS = ("inherit", "initial", "unset", "revert", "revert-layer")

# Names that are display type wherever they appear. The face is usually set on
# them too, but not always, and a heading that keeps its size while every
# other heading moves reads as a bug rather than a choice.
NAMED = re.compile(r"-(title|heading|claim|figure|price|numeral|value)$")
ELEMENT = re.compile(r"(^|\s|>)h[1-4]$")


def _selectors(prelude):
    return [s.strip() for s in prelude.split(",") if s.strip()]


def _is_named_display(sel):
    base = re.sub(r"::?[\w-]+(\([^)]*\))?$", "", sel).strip()
    return bool(NAMED.search(base) or ELEMENT.search(base))


def display_faults(css):
    """(selector, value, why) for every display size not carrying the dial."""
    text = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    rules = [(_selectors(m.group(1)), m.group(2)) for m in RULE.finditer(text)]

    # Pass one: every selector the file gives the heading face to, including
    # each member of a selector list that shares one declaration.
    faced = set()
    for sels, body in rules:
        if FACE in body:
            faced.update(sels)

    # Pass two: the sizes.
    out = []
    for sels, body in rules:
        display = [s for s in sels if s in faced or _is_named_display(s)]
        if not display:
            continue
        where = ", ".join(display)
        for m in SHORTHAND.finditer(body):
            value = m.group(1).strip()
            # `font: inherit` is the standard reset on a button or input and
            # sets no size of its own - it takes the one it inherits, which
            # already carries the dial.
            if value in KEYWORDS:
                continue
            out.append((where, value,
                        "the font shorthand sets a size the dial cannot reach; "
                        "use font-family and font-size separately"))
        for m in SIZE.finditer(body):
            value = m.group(1).strip()
            # A keyword takes its size from somewhere that already carries the
            # dial, so it moves correctly by doing nothing.
            if value in KEYWORDS:
                continue
            if "var(--type-scale" not in value:
                out.append((where, value,
                            "wrap it: calc(%s * var(--type-scale, 1))" % value))
    return out
