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

import html
import re

from _textutil import blank_comments

# @namespace is deliberately not here. It takes a URL that identifies an XML
# namespace and fetches nothing, so banning it would fail correct SVG.
AT_IMPORT = re.compile(r"@import\b", re.I)
# url() and the bare-string form of image-set(), which is valid CSS and
# reaches a host just as directly.
# Every quoted string inside an image-set(), not just the first - a
# third-party candidate is as reachable at 2x as at 1x - plus every url().
URL_FN = re.compile(r"""url\(\s*['"]?([^'")]+)""", re.I)
IMAGE_SET = re.compile(r"""image-set\(([^)]*)\)""", re.I)
QUOTED = re.compile(r"""['"]([^'"]+)['"]""")

# Properties that lay out the page and therefore belong to the brand's ramp.
SPACING = re.compile(
    # grid-gap and grid-row-gap are the legacy aliases; browsers still honour
    # them, so excluding them left the same declaration spelled a second way.
    r"(?<![-\w])((?:grid-)?(?:row-|column-)?gap|margin|padding)"
    r"(-(top|right|bottom|left|block|inline)(-(start|end))?)?\s*:\s*([^;}]+)",
    re.I)
# Absolute lengths that are not a spacing decision: hairlines, and the
# absolute floors that make a target a target rather than a proportion.
ALLOWED_LENGTH = re.compile(r"^(0|auto|inherit|initial|unset|revert)$", re.I)
# A leading minus is part of the length, not a disqualifier - a negative band
# opts out of the ramp exactly as a positive one does. And the unit set is
# every absolute or viewport unit, not the three that happened to be in use:
# 8vw and 72pt are as far off the ramp as 96px.
LENGTH = re.compile(
    r"(?<![\w.])(-?\d+(?:\.\d+)?)\s*"
    r"(px|rem|em|ch|ex|vw|vh|vmin|vmax|svw|svh|lvw|lvh|dvw|dvh|cm|mm|in|pt|pc|q)"
    r"(?![\w-])", re.I)

# --space-1 is 0.25rem. Nothing smaller can have come from the ramp.
RAMP_FLOOR_PX = 4.0

# The units a ramp of fixed steps could have produced.
RAMP_UNITS = {"px", "rem", "pt", "cm", "mm", "in", "pc", "q"}


def external_faults(text, kind):
    """(what, why) for every reference that leaves the host."""
    out = []
    if kind == "css":
        # Before the FIRST scan. Stripping between two of them left the
        # @import loop reading commented-out code.
        text = blank_comments(text)
        text = re.sub(r"@namespace[^;]*;",
                      lambda m: re.sub("[^" + chr(10) + "]", " ", m.group(0)),
                      text, flags=re.I)
        seen = set()
        for m in AT_IMPORT.finditer(text):
            line = text[:m.start()].count("\n") + 1
            out.append((f"line {line}: @import",
                        "@import does exactly what <link> is banned for, from "
                        "the file that is concatenated into the brand's "
                        "stylesheet"))
            # The url() this @import carries is the same reference.
            end = text.find(";", m.end())
            carried = URL_FN.search(text, m.end(),
                                    end if end != -1 else len(text))
            if carried:
                seen.add(carried.start(1))
        for m in IMAGE_SET.finditer(text):
            for target in QUOTED.findall(m.group(1)):
                target = target.strip()
                if not re.match(r"(https?:)?//", target, re.I):
                    continue
                line = text[:m.start()].count(chr(10)) + 1
                # url() inside an image-set() is found by both scans, and one
                # reference is one finding.
                if m.start() + m.group(0).find(target) in seen:
                    continue
                seen.add(m.start() + m.group(0).find(target))
                out.append((f"line {line}: image-set({target})",
                            "a pattern renders from the token contract and "
                            "pulls nothing in from elsewhere"))
        for m in URL_FN.finditer(text):
            target = m.group(1).strip()
            if target.startswith(("data:", "#")) or not re.match(
                    r"(https?:)?//", target, re.I):
                continue
            line = text[:m.start()].count("\n") + 1
            # One reference is one finding. A url() inside an image-set(), or
            # the one an @import carries, is found twice and reported once.
            if m.start(1) in seen:
                continue
            seen.add(m.start(1))
            out.append((f"line {line}: url({target})",
                        "a pattern renders from the token contract and pulls "
                        "nothing in from elsewhere"))
    else:
        # Decoded, and quoted or not. The action/formaction check this was
        # modelled on was moved onto decoded markup for exactly this reason
        # and this module did not follow, so an entity-encoded host and an
        # unquoted attribute both walked through.
        text = html.unescape(text)
        for attr in ("src", "srcset", "href", "poster", "data", "imagesrcset",
                     "ping", "cite", "background", "longdesc"):
            for m in re.finditer(
                    r"(?<![-\w])%s\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))"
                    % attr, text, re.I):
                value = next(g for g in m.groups() if g is not None)
                if not re.search(r"(?:^|[\s,])(?:https?:)?//", value, re.I):
                    continue
                line = text[:m.start()].count("\n") + 1
                out.append((f"line {line}: {attr}=\"{value[:60]}\"",
                            "a third-party host in a pattern is a request the "
                            "brand did not make and cannot see"))
    return out


def spacing_faults(css):
    """(line, declaration) for spacing set in a length instead of the ramp."""
    text = blank_comments(css)
    out = []
    # A pattern-local property is only off the ramp if its own definition is.
    # `--x-pad: 96px; padding: var(--x-pad)` is the natural way to write it and
    # was silent, because any var() at all was treated as reaching the ramp.
    # Resolved transitively: `--a: 96px; --b: var(--a); padding: var(--b)` is
    # the same declaration wearing one more hop, and stopping at one hop meant
    # the second hop was free.
    declared = {n: v.strip() for n, v in
                re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", text)}

    def resolve(name, seen=()):
        if name in seen or name not in declared:
            return ""
        value = declared[name]
        if "--space-" in value:
            return value
        for ref in re.findall(r"var\(\s*(--[\w-]+)", value):
            value += " " + resolve(ref, seen + (name,))
        return value

    def strip_names(value):
        """Token names removed, values kept. `--gutter-16px` is a name."""
        return re.sub(r"var\(\s*--[\w-]+", "var(", value)

    local_lengths = {}
    for name in declared:
        chain = resolve(name)
        # The guard reads this token's OWN value; only the length scan reads
        # the resolved chain.
        #
        # Reading the stripped value blinded the guard entirely, because
        # `var(--space-6` is exactly the text the strip rewrites. Reading the
        # resolved chain instead over-corrected the other way: a `--space-`
        # anywhere in a chain then excused every literal length in it, so
        # `--a: var(--b) 96px` with `--b` on the ramp went silent. The
        # declaration's own value is the thing the inline rule below tests,
        # and it is the thing to test here.
        if "--space-" not in declared[name] and LENGTH.search(strip_names(chain)):
            local_lengths[name] = strip_names(chain)

    for m in SPACING.finditer(text):
        value = m.group(6).strip()
        if ALLOWED_LENGTH.match(value):
            continue
        # A calc() that reaches the ramp is still on the ramp.
        if "--space-" in value:
            continue
        refs = re.findall(r"var\(\s*(--[\w-]+)", value)
        # Both the literal lengths in the declaration AND whatever its
        # references resolve to. Skipping the declaration whenever its refs
        # were unknown threw away a var() FALLBACK sitting in the same value:
        # `padding: var(--nothing, 96px)` was silent.
        # The token NAME is stripped before lengths are read: `--gutter-16px`
        # is a name, not a sixteen-pixel gutter, and the lookbehind permits a
        # preceding hyphen. The fallback text after the comma is kept, so
        # var(--nothing, 96px) is still read.
        lengths = LENGTH.findall(strip_names(value)) + [
            x for r in refs if r in local_lengths
            for x in LENGTH.findall(local_lengths[r])]
        if not lengths:
            continue
        # Only units the ramp could have produced. Three kinds are out of
        # scope by their nature rather than by exception:
        #   - em, ch, ex track the type, which is the type dial's axis.
        #   - vw, vh and % express a relationship to the viewport, which a
        #     ramp of fixed steps cannot express at all. A full-bleed breakout
        #     and a curtain pulled up one screen are layout geometry.
        #   - anything below the ramp's smallest step, 0.25rem, cannot have
        #     come from the ramp: a hairline between grid cells, or an optical
        #     nudge between two glyphs, is not the brand's rhythm.
        #
        # A percentage never enters `lengths` at all - `%` is not in the
        # LENGTH unit list - so it neither counts as ramp spacing nor hides
        # anything beside it. The blanket "any % skips the declaration" that
        # used to sit here let one percentage in a shorthand hide every other
        # length in the same value, so `padding: 96px 1%` was silent.
        if all(unit.lower() not in RAMP_UNITS
               or abs(float(n)) * (16 if unit.lower() == "rem" else 1) <= RAMP_FLOOR_PX
               for n, unit in lengths):
            continue
        line = text[:m.start()].count("\n") + 1
        out.append((line, m.group(0).strip()))
    return out
