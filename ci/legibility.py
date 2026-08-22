"""Ways to make text unreadable that the other checks wave through.

A contrast ratio cannot be computed in this repository, because the tokens
belong to the brand rather than to us. So the guarantee the contract gives is
only ever as good as the ink being used at full strength on a ground the
contract covers. These are the routes that quietly take that away, and each
one has shipped somewhere before it was checked for.
"""
import re

# The behaviour library's injected classes. Testing the whole prelude for
# this leaked twice over: `:not(.hub-x)` mentions it without depending on it,
# and in a selector LIST one comma-part mentioning it exempted every other
# part. Both are checked against each part with :not() stripped, which is what
# the stylesheet checks in lint.py already do.
HUB_CLASS = re.compile(r"\.hub-")


def _exempt(selector):
    """True only when EVERY part of the selector list genuinely depends on a
    class the behaviour library injects."""
    parts = []
    depth, buf = 0, ""
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
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return False
    return all(HUB_CLASS.search(_bare(p)) for p in parts)


def _bare(selector):
    """A selector with every functional pseudo-class argument removed.

    `:not(.hub-x)` mentions a class without depending on it, and so do
    `:is()`, `:where()` and `:has()`. Stripping only `:not()` left the other
    three as the same escape."""
    for _ in range(5):
        stripped = re.sub(r":(?:not|is|where|has|matches|any)\([^()]*\)", "",
                          selector)
        if stripped == selector:
            return stripped
        selector = stripped
    return selector


def _is_state(selector):
    """Does this selector name a STATE rather than the plain element?

    A pattern's own `.x { display: grid }` is the default, not a reveal. Only
    something carrying a pseudo-class, an attribute or a modifier can bring
    hidden content back, so only those count."""
    bare = _bare(selector)
    return bool(re.search(r"[:\[]", bare) or "--" in bare)

HIDDEN = re.compile(
    r"(?<![-\w])("
    r"opacity\s*:\s*0(?:\.0+)?(?![.\d])"
    r"|visibility\s*:\s*(?:hidden|collapse)"
    r"|display\s*:\s*none"
    r"|content-visibility\s*:\s*hidden"
    r"|color\s*:\s*transparent"
    r"|-webkit-text-fill-color\s*:\s*transparent"
    r"|font-size\s*:\s*0(?:\.0+)?(?:px|rem|em)?(?![.\d])"
    r"|transform\s*:\s*scale\(\s*0\s*\)"
    r"|scale\s*:\s*0(?![.\d])"
    r"|max-height\s*:\s*0(?![.\d])"
    r")")

# @layer takes no condition, so "inside an at-rule" was a way straight out.
# Only a conditional at-rule is a decision about the environment.
CONDITIONAL_AT = re.compile(r"@(media|supports|container)\b")

# Deliberately absent from HIDDEN: clip-path and text-indent. Those are the
# visually-hidden idiom for text meant only for a screen reader, and this
# library uses them on purpose - a clipped radio input is still focusable and
# still announced.

SHOWN = re.compile(
    r"(?<![-\w])("
    r"opacity\s*:\s*1"
    r"|visibility\s*:\s*visible"
    r"|display\s*:\s*(?!none)\w"
    r")")


def _rules(css):
    """(selector, body, line, nested) for every rule.

    `nested` is True when the rule sits inside an at-rule. That matters: a
    media query is a legitimate place to hide something - a mobile bar has no
    business on a desktop - whereas a base rule hiding content is content
    waiting for a script.

    @keyframes blocks are dropped whole, because `from { opacity: 0 }` is a
    starting frame rather than a state a page can be left in, and reading one
    as a rule reports every honest animation as hidden content."""
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
                at_depth.append((depth, bool(CONDITIONAL_AT.match(prelude))))
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
                       any(cond for _d, cond in at_depth))
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
    """Does any element in the markup actually carry this class? A reveal rule
    for a class nothing wears reveals nothing."""
    if not html:
        return True
    for m in re.finditer(r'class="([^"]*)"', html):
        if cls in m.group(1).split():
            return True
    return False


def check(css, report, html=""):
    """`report(detail)` is called once per finding.

    `html` is the pattern's markup. Without it a reveal rule is taken on
    trust, and a class no element carries counts as one."""
    for selector, body, line, _nested in _rules(css):
        # A partial fade on text. The token promises 4.5:1 and opacity
        # silently divides it, so the guarantee stops holding at the exact
        # point somebody thought they were being subtle.
        faded = re.search(r"(?<![-\w])opacity\s*:\s*(0?\.\d+)", body)
        if faded and re.search(r"(?<![-\w])color\s*:", body):
            report(f"line {line}: opacity {faded.group(1)} on a rule that "
                   "also sets color - dim with --color-text-soft, which "
                   "carries a guarantee, not with opacity, which removes one")

        # The same move wearing the contract's clothes: color-mix() of
        # contract tokens is blessed, and `transparent` is not a colour
        # literal, so this reads as compliant and is not.
        if re.search(r"(?<![-\w])color\s*:[^;]*color-mix\([^;]*transparent",
                     body):
            report(f"line {line}: text colour mixed toward transparent - "
                   "the result carries no guarantee, whatever went into it")

    # Content hidden by default is legitimate when this same stylesheet can
    # reveal it again - a carousel card waiting on :checked needs no script.
    # It is not legitimate when only the behaviour library's injected classes
    # bring it back, because then the no-JS render is missing content.
    revealed = set()
    for selector, body, _line, _nested in _rules(css):
        # Only a STATE selector reveals. A pattern's own `.x { display: grid }`
        # is the element's default, not a way back from hidden - and counting
        # it made the whole check inert for any pattern that styles display,
        # which is most of them.
        if _exempt(selector) or not SHOWN.search(body):
            continue
        if not _is_state(selector):
            continue
        for cls in re.findall(r"\.([\w-]+)", _bare(selector)):
            if _carries(html, cls):
                revealed.add(cls)

    for selector, body, line, nested in _rules(css):
        # Nested in an at-rule: a media query hiding something is a decision
        # about a viewport, not content waiting for a script.
        if _exempt(selector) or nested:
            continue
        # A pseudo-element is not the page's content: hiding ::marker or
        # ::-webkit-details-marker removes a disclosure triangle the browser
        # drew, which is the ordinary way to style a <details>.
        if "::" in selector:
            continue
        hidden = HIDDEN.search(body)
        if not hidden:
            continue
        # A modifier reveals its base: `.card` hidden and `.card--1` shown is
        # one mechanism, not two, so match on prefix rather than equality.
        for cls in re.findall(r"\.([\w-]+)", selector):
            if any(r == cls or r.startswith(cls + "--") for r in revealed):
                break
        else:
            report(f"line {line}: '{hidden.group(1).strip()}' with nothing in "
                   "this stylesheet to reveal it - the no-JS render is the "
                   "page, so content may not wait for a script")
