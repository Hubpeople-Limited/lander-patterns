"""Ways to make text unreadable that the other checks wave through.

A contrast ratio cannot be computed in this repository, because the tokens
belong to the brand rather than to us. So the guarantee the contract gives is
only ever as good as the ink being used at full strength on a ground the
contract covers. These are the routes that quietly take that away.

WHAT THIS IS NOT. CSS has no bounded set of ways to make something invisible,
and this file does not pretend to enumerate them. It catches the accidents and
the obvious shortcuts. Someone determined to hide content from a reader while
passing CI can still do it - by moving it off-canvas, by scaling it to nothing,
by painting the ink in the ground colour - and no amount of pattern-matching
here will change that. Treat a clean run as "nothing obvious", never as proof,
and keep reading the previews.
"""
import re

HUB_CLASS = re.compile(r"\.hub-")

# @layer takes no condition, so "inside an at-rule" was a way straight out.
# Only a conditional at-rule is a decision about the environment - and only
# when the condition actually discriminates: `@media screen` and
# `(min-width: 0px)` are true everywhere and excuse nothing.
CONDITIONAL_AT = re.compile(r"@(media|supports|container)\b", re.I)
ALWAYS_TRUE_AT = re.compile(
    r"@media\s*(screen|all)\s*$"
    # Any floor at or below one CSS pixel is true on every device there is.
    # Recognising only a literal 0 let `(min-width: 1px)` excuse everything.
    r"|min-(width|height|inline-size|block-size)\s*:\s*(0(?![.\d])|[01](\.\d+)?px)"
    # @supports for anything universally implemented is the same trick played
    # on a different at-rule. Custom properties and var() have been everywhere
    # for years, so testing for them discriminates against nothing.
    r"|@supports\s*\(\s*[\w-]+\s*:\s*(block|none|flex|grid|var\([^)]*\))\s*\)",
    re.I)

HIDDEN = re.compile(
    r"(?<![-\w])("
    r"opacity\s*:\s*0(?:\.0+)?(?:%)?(?![.\d])"
    r"|visibility\s*:\s*(?:hidden|collapse)"
    r"|display\s*:\s*none"
    r"|content-visibility\s*:\s*hidden"
    r"|color\s*:\s*transparent"
    r"|-webkit-text-fill-color\s*:\s*transparent"
    r"|font-size\s*:\s*0(?:\.0+)?(?:px|rem|em|pt)?(?![.\d])"
    r"|transform\s*:\s*scale\(\s*0[\s,]*[0\s]*\)"
    r"|scale\s*:\s*0(?![.\d])"
    r"|(?:max-)?(?:height|block-size)\s*:\s*0(?![.\d])"
    r"|filter\s*:\s*opacity\(\s*0(?:\.0+)?(?:%)?\s*\)"
    r")", re.I)

# Ink painted in the page's own ground. Nothing else in the repository compares
# an ink to a ground, and this is squarely what this file is about.
INK_IS_GROUND = re.compile(
    r"(?<![-\w])color\s*:\s*var\(\s*(--color-(?:bg|surface|surface-soft))\s*\)",
    re.I)

# Moved out of the viewport rather than hidden.
OFF_CANVAS = re.compile(
    r"(?<![-\w])(left|right|top|bottom|inset-inline-start|translate)\s*:\s*"
    r"-\s*\d{3,}(px|vw|vh|rem|em)", re.I)

SHOWN = re.compile(
    r"(?<![-\w])("
    r"opacity\s*:\s*1"
    r"|visibility\s*:\s*visible"
    r"|display\s*:\s*(?!none)\w"
    r")", re.I)

# A state a reader can reach without script. `[data-open]` set by nobody is
# not a reveal, it is a decoration on a permanently hidden element.
REACHABLE_STATE = re.compile(
    r":(checked|target|focus-within|focus-visible|focus|open|hover|"
    r"first-of-type|last-of-type|nth-of-type|not|is|where)\b", re.I)


def split_parts(selector):
    """Split a selector list on its top-level commas only."""
    parts, buf, depth = [], "", 0
    for ch in selector:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def _bare(selector):
    """A selector with every functional pseudo-class argument removed.

    `:not(.hub-x)` mentions a class without depending on it, and so do
    `:is()`, `:where()` and `:has()`."""
    for _ in range(5):
        stripped = re.sub(r":(?:not|is|where|has|matches|any)\([^()]*\)", "",
                          selector)
        if stripped == selector:
            return stripped
        selector = stripped
    return selector


def _exempt(selector):
    """True only when EVERY part of the list depends on a class the behaviour
    library injects."""
    parts = split_parts(selector)
    return bool(parts) and all(HUB_CLASS.search(_bare(p)) for p in parts)


def _is_reveal(selector, html):
    """Can this selector actually bring hidden content back for a reader?

    A pattern's own `.x { display: grid }` is the element's default, not a way
    back. A state nobody can enter is no better: an attribute selector counts
    only if the markup carries that attribute, and a hover-only reveal is
    unreachable on a touch screen."""
    bare = _bare(selector)
    if REACHABLE_STATE.search(bare):
        # Hover alone leaves a touch reader with no way in.
        hover_only = ":hover" in bare.lower() and not re.search(
            r":(checked|target|focus|open)", bare, re.I)
        return not hover_only
    for attr in re.findall(r"\[([\w-]+)", bare):
        if html and re.search(rf"(?<![-\w]){re.escape(attr)}[\s=>]", html):
            return True
    return "--" in bare


def _rules(css):
    """(selector, body, line, excused) for every rule.

    `excused` is True when the rule sits inside an at-rule whose condition
    genuinely discriminates - a media query hiding a mobile bar on a desktop
    is a decision about a viewport, not content waiting for a script.

    @keyframes blocks are dropped whole, because `from { opacity: 0 }` is a
    starting frame rather than a state a page can be left in."""
    stripped = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    stripped = re.sub(r"@keyframes[^{]*\{(?:[^{}]*\{[^{}]*\}\s*)*\}", "",
                      stripped)
    depth, at_depth, buf, i = 0, [], "", 0
    while i < len(stripped):
        ch = stripped[i]
        if ch == "{":
            prelude = buf.strip()
            buf = ""
            depth += 1
            if prelude.startswith("@"):
                excuses = bool(CONDITIONAL_AT.match(prelude)) and \
                    not ALWAYS_TRUE_AT.search(prelude)
                at_depth.append((depth, excuses))
            else:
                body_start = i + 1
                j, inner = body_start, 1
                while j < len(stripped) and inner:
                    if stripped[j] == "{":
                        inner += 1
                    elif stripped[j] == "}":
                        inner -= 1
                    j += 1
                yield (prelude, stripped[body_start:j - 1],
                       stripped[:i].count("\n") + 1,
                       any(e for _d, e in at_depth))
                depth -= 1
                i = j
                continue
        elif ch == "}":
            if at_depth and at_depth[-1][0] == depth:
                at_depth.pop()
            depth -= 1
            buf = ""
        else:
            buf += ch
        i += 1


def _carries(html, cls):
    """Does any element in the markup carry this class? A reveal rule for a
    class nothing wears reveals nothing."""
    if not html:
        return True
    return any(cls in m.group(1).split()
               for m in re.finditer(r'class="([^"]*)"', html))


def check(css, report, html=""):
    """`report(detail)` is called once per finding."""
    for selector, body, line, _excused in _rules(css):
        faded = re.search(r"(?<![-\w])opacity\s*:\s*(0?\.\d+)", body, re.I)
        # The "and it also sets color" guard exempted the plainer version of
        # the same defect: a rule that only fades. Text at 8% is unreadable
        # whether or not an ink is named in the same block.
        if faded:
            report(f"line {line}: opacity {faded.group(1)} - dim with "
                   "--color-text-soft, which carries a guarantee, not with "
                   "opacity, which removes one")

        if re.search(r"(?<![-\w])color\s*:[^;]*color-mix\([^;]*transparent",
                     body, re.I):
            report(f"line {line}: text colour mixed toward transparent - "
                   "the result carries no guarantee, whatever went into it")

        ground = INK_IS_GROUND.search(body)
        if ground:
            report(f"line {line}: ink set to {ground.group(1)}, which is a "
                   "ground token - text painted in the colour behind it")

        off = OFF_CANVAS.search(body)
        if off and not _excused:
            report(f"line {line}: '{off.group(0).strip()}' moves content off "
                   "the canvas - if it is for a screen reader, clip it; if it "
                   "is hidden, say so")

    revealed = set()
    for selector, body, _line, _excused in _rules(css):
        if _exempt(selector) or not SHOWN.search(body):
            continue
        if not _is_reveal(selector, html):
            continue
        for cls in re.findall(r"\.([\w-]+)", _bare(selector)):
            if _carries(html, cls):
                revealed.add(cls)

    for selector, body, line, excused in _rules(css):
        if _exempt(selector) or excused:
            continue
        hidden = HIDDEN.search(body)
        if not hidden:
            continue
        # Per PART, not per list: one pseudo-element in a comma list used to
        # exempt every other part of it. A pseudo-element is the browser's own
        # drawing - hiding a disclosure triangle is not hiding the page.
        for part in split_parts(selector):
            if "::" in part:
                continue
            classes = re.findall(r"\.([\w-]+)", part)
            if any(r == c or r.startswith(c + "--")
                   for c in classes for r in revealed):
                continue
            report(f"line {line}: '{hidden.group(1).strip()}' with nothing in "
                   "this stylesheet to reveal it - the no-JS render is the "
                   "page, so content may not wait for a script")
            break
