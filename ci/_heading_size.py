"""--color-heading may only be used at a size it is guaranteed at, dial included.

TOKENS.md promises --color-heading at 3:1 against --color-bg and no more, so
it is valid only on text WCAG counts as large: 24px, or 18.66px when bold.
Every pattern using it carries a comment saying its clamp floor clears that
bar - and six of them cleared it by landing exactly on 24px, which stopped
being true the moment --type-scale shipped. At the 0.92 the contract itself
recommends for a quieter register, those six render 22.08px in a 3:1 ink.

The token is usually reached through a ground modifier rather than named
directly:

    .link-cluster--plain { --link-cluster-title-ink: var(--color-heading); }
    .link-cluster-title  { color: var(--link-cluster-title-ink); }

so a check that greps for the token in the same rule as the font-size is
blind to most of the library. Pattern-local properties are resolved
transitively here for that reason.
"""

import re

RULE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
LOCAL = re.compile(r"(--[\w-]+)\s*:\s*([^;}]+)")
VAR = re.compile(r"var\(\s*(--[\w-]+)")

# The bar the token is promised at, and the bottom of the documented dial
# range. Both halves have to hold at once: a floor that clears 24px at scale 1
# and not at 0.9 is a floor that clears it on the brands that never touched
# the dial, which is not the same as clearing it.
LARGE_PX = 24.0
LARGE_BOLD_PX = 18.66
TYPE_MIN = 0.9


def _locals(css):
    """Every --pattern-local: value pair in the file, resolved transitively."""
    raw = {}
    for m in RULE.finditer(css):
        for name, value in LOCAL.findall(m.group(2)):
            raw.setdefault(name, value.strip())

    def resolve(name, seen=()):
        if name in seen:
            return set()
        value = raw.get(name)
        if value is None:
            return {name}
        refs = VAR.findall(value)
        if not refs:
            return set()
        out = set()
        for r in refs:
            out |= resolve(r, seen + (name,)) or {r}
        return out

    return {n: resolve(n) for n in raw}


SIZE = re.compile(r"(?<![-\w])font-size\s*:\s*([^;}]+)")
COLOUR = re.compile(r"(?<![-\w])color\s*:\s*([^;}]+)")
WEIGHT = re.compile(r"(?<![-\w])font-weight\s*:\s*(\d+)")
LENGTH = re.compile(r"(?<![-\w.])(\d+(?:\.\d+)?)\s*(rem|px|em)(?![\w-])")


def _floor_px(value):
    """The smallest size a font-size can render at, in px.

    A clamp() floor if there is one; otherwise the smallest length anywhere in
    the value. Reading only a leading clamp( or a leading number could not
    read `calc(1.25rem * var(--type-scale, 1))` - which is the exact form the
    display-type check tells authors to write, so following one gate's advice
    switched this one off.
    """
    m = re.search(r"clamp\(\s*([^,]+),", value)
    if m:
        candidates = LENGTH.findall(m.group(1))
    else:
        candidates = LENGTH.findall(value)
    if not candidates:
        return None
    return min(float(n) * (16 if unit in ("rem", "em") else 1)
               for n, unit in candidates)


def heading_size_faults(css):
    """(selector, floor_px, bar, at_min) for every --color-heading rule whose
    size stops being large enough at the bottom of the documented dial range.

    Colour and size are resolved across the file, not within one rule. They
    are routinely declared apart - a shared rule for the ink, a per-element
    rule for the size - and three patterns were changed to inherit the ink
    entirely, which is the same shape seen from further away.
    """
    text = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    locals_ = _locals(text)
    rules = [(m.group(1).strip(), m.group(2)) for m in RULE.finditer(text)]

    def takes_heading(body):
        colour = COLOUR.search(body)
        if not colour:
            return False
        reached = set()
        for ref in VAR.findall(colour.group(1)):
            reached |= locals_.get(ref, {ref})
        return "--color-heading" in reached

    # Pass one: every selector the file gives the heading ink to.
    inked = set()
    for selector, body in rules:
        if takes_heading(body):
            inked.update(s.strip() for s in selector.split(",") if s.strip())

    out = []
    for selector, body in rules:
        parts = [s.strip() for s in selector.split(",") if s.strip()]
        if not any(p in inked for p in parts):
            continue
        for size in SIZE.finditer(body):
            floor = _floor_px(size.group(1))
            if floor is None:
                continue
            weight = WEIGHT.search(body)
            # Unstated weight is treated as not bold. A brand's own stylesheet
            # may set heading weights, so the UA default is not relyable.
            bar = (LARGE_BOLD_PX if (weight and int(weight.group(1)) >= 700)
                   else LARGE_PX)
            at_min = floor * TYPE_MIN
            if at_min < bar:
                out.append((parts[0], floor, bar, at_min))
    return out
