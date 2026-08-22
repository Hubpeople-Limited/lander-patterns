"""Two things a pattern must not do that nothing was checking.

**Reach off the host.** The banned-tag list stops `<iframe>`, `<object>`,
`<embed>` and `<link>` because "a pattern renders from the token contract and
pulls nothing in from elsewhere". Nothing checked URLs, so the same thing was
available through `@import`, `@font-face`, `background-image: url(...)`, an
`<img src>` on a third-party host, a `srcset` entry, or `<use href>` into a
remote sprite. `@import` is the sharpest of them: it does exactly what `<link>`
is banned for, from the file that gets concatenated into the brand's own
stylesheet.

**Opt out of the spacing ramp.** `--space-scale` is applied by the brand at
the ramp, so a hardcoded `padding-block: 96px` silently removes that band from
the brand's spacing system, density dial included. `--type-scale` has a
dedicated check and `--space-scale` had none, which made half the dial work
unenforceable the day it shipped.
"""

import re

# A scheme, a protocol-relative //, or a bare host. Relative paths and
# slot: attribute placeholders are what a pattern is supposed to use.
EXTERNAL = re.compile(r"""(?:url\(\s*|["']|\s)(?:https?:)?//""", re.I)
AT_IMPORT = re.compile(r"@import\b", re.I)
URL_FN = re.compile(r"url\(\s*['\"]?([^'\")]+)", re.I)

# Properties that lay out the page and therefore belong to the brand's ramp.
SPACING = re.compile(
    r"(?<![-\w])((?:row-|column-)?gap|margin|padding)"
    r"(-(top|right|bottom|left|block|inline)(-(start|end))?)?\s*:\s*([^;}]+)",
    re.I)
# Absolute lengths that are not a spacing decision: hairlines, and the
# absolute floors that make a target a target rather than a proportion.
ALLOWED_LENGTH = re.compile(r"^(0|auto|inherit|initial|unset|revert)$", re.I)
LENGTH = re.compile(r"(?<![-\w.])(\d+(?:\.\d+)?)(px|rem|em)(?![\w-])")

# --space-1 is 0.25rem. Nothing smaller can have come from the ramp.
RAMP_FLOOR_PX = 4.0


def external_faults(text, kind):
    """(what, why) for every reference that leaves the host."""
    out = []
    if kind == "css":
        for m in AT_IMPORT.finditer(text):
            line = text[:m.start()].count("\n") + 1
            out.append((f"line {line}: @import",
                        "@import does exactly what <link> is banned for, from "
                        "the file that is concatenated into the brand's "
                        "stylesheet"))
        for m in URL_FN.finditer(text):
            target = m.group(1).strip()
            if target.startswith(("data:", "#")) or not re.match(
                    r"(https?:)?//", target, re.I):
                continue
            line = text[:m.start()].count("\n") + 1
            out.append((f"line {line}: url({target})",
                        "a pattern renders from the token contract and pulls "
                        "nothing in from elsewhere"))
    else:
        for attr in ("src", "srcset", "href", "poster", "data", "imagesrcset"):
            for m in re.finditer(
                    r"(?<![-\w])%s\s*=\s*[\"']([^\"']*)[\"']" % attr, text, re.I):
                value = m.group(1)
                if not re.search(r"(?:^|[\s,])(?:https?:)?//", value, re.I):
                    continue
                line = text[:m.start()].count("\n") + 1
                out.append((f"line {line}: {attr}=\"{value[:60]}\"",
                            "a third-party host in a pattern is a request the "
                            "brand did not make and cannot see"))
    return out


def spacing_faults(css):
    """(line, declaration) for spacing set in a length instead of the ramp."""
    text = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    out = []
    for m in SPACING.finditer(text):
        value = m.group(6).strip()
        if ALLOWED_LENGTH.match(value) or "var(" in value:
            continue
        # A calc() that reaches the ramp is still on the ramp.
        if "--space-" in value:
            continue
        lengths = LENGTH.findall(value)
        if not lengths:
            continue
        # Below the ramp's smallest step it cannot have come from the ramp:
        # a hairline gap between grid cells, or an optical nudge between two
        # inline glyphs, is not a spacing decision the brand should own. `em`
        # tracks the type rather than the page, which is the other axis.
        if all(unit == "em" or float(n) * (16 if unit == "rem" else 1) <= RAMP_FLOOR_PX
               for n, unit in lengths):
            continue
        line = text[:m.start()].count("\n") + 1
        out.append((line, m.group(0).strip()))
    return out
