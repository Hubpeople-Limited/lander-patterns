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
from pathlib import Path

from _textutil import blank_comments

HUB_CLASS = re.compile(r"\.hub-")

# A class attribute in any of its three legal spellings.
CLASS_ATTR = re.compile(r"""class\s*=\s*(?:["']([^"']*)["']|([^\s>]+))""")

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
    # `0`, `00`, `0.0`, `.0`, `0%`, `00%` - every spelling of nothing.
    # Narrowing OPACITY to exclude the fully-zero forms left `.0` and `00%`
    # matching neither regex, so two legal spellings of invisible were caught
    # by nothing at all. The alternation must consume at least one digit:
    # written as `0*(?:\.0+)?%?` every part is optional, so it matched the
    # empty string straight after the colon and fired on every opacity there is.
    r"opacity\s*:\s*(?:0+(?:\.0+)?|\.0+)\s*%?(?![.\d1-9])"
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
    # Newlines kept on both removals: this generator yields a line number for
    # every rule, and collapsing a multi-line comment or a @keyframes block
    # moved every line reported after it.
    stripped = blank_comments(css)
    stripped = re.sub(r"@keyframes[^{]*\{(?:[^{}]*\{[^{}]*\}\s*)*\}",
                      lambda m: re.sub("[^" + chr(10) + "]", " ", m.group(0)),
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
    for m in re.finditer(CLASS_ATTR, html):
        value = next(g for g in m.groups() if g is not None)
        if cls in value.split():
            return True
    return False


# Every way of writing a fade: the decimal, the percentage, the filter form,
# and a var() or calc() which cannot be resolved here and so are reported
# rather than assumed innocent. An unverifiable fade on text is exactly what
# this check exists to refuse.
OPACITY = re.compile(
    r"(?<![-\w])opacity\s*:\s*("
    r"0?\.0*[1-9]\d*"
    r"|0*(?:[1-9]|[1-8][0-9]|9[0-9])(?:\.\d+)?%"
    r"|var\([^;}]*\)"
    r"|calc\([^;}]*\)"
    r")"
    # filter: opacity() is the same fade through a different property, and
    # HIDDEN only ever matched the fully-zero form of it.
    # Not the fully-zero forms: HIDDEN reports those, and two findings for
    # one declaration is noise that teaches people to skim the output.
    r"|(?<![-\w])filter\s*:\s*opacity\(\s*(0?\.0*[1-9]\d*"
    r"|0*(?:[1-9]|[1-8][0-9])(?:\.\d+)?%)\s*\)",
    re.I)

# Above this, a fade is cosmetic rather than a legibility decision. Firing on
# `opacity: 0.95` - a 19:1 ink still measuring 19:1 - and telling the author
# to reach for --color-text-soft is advice about something they were not doing.
COSMETIC_ABOVE = 0.85

# Contexts where a fade is not a fade of text. A pseudo-element with content
# that is not words, a replaced element, and a disabled control - which the
# platform's own conventions fade, and which carries its own state semantics.
DECORATIVE_SUBJECT = re.compile(
    r"::(before|after|backdrop|marker|placeholder)$"
    r"|(?<![-\w])(img|svg|picture|video|canvas|iframe|use|path)(?![-\w])"
    r"|:disabled|\[disabled\]|\[aria-disabled",
    re.I)


def _drop_balanced(selector, names):
    """Remove `:name(...)` and everything inside it, brackets balanced.

    A regex cannot do this: `[^()]*` stops at the first nested paren, and
    `:not(:is(img))` is ordinary CSS.
    """
    out, i = "", 0
    while i < len(selector):
        m = re.compile(r":(?:%s)\(" % "|".join(names),
                       re.I).match(selector, i)
        if not m:
            out += selector[i]
            i += 1
            continue
        depth, j = 1, m.end()
        while j < len(selector) and depth:
            if selector[j] == "(":
                depth += 1
            elif selector[j] == ")":
                depth -= 1
            j += 1
        i = j
    return out


def _split_combinators(selector):
    """Split on combinators at the TOP LEVEL only.

    `:is()` and `:where()` are kept, because they are the subject - which
    means their argument lists are now in the string, commas and spaces and
    all. A plain regex split then cut inside them, so the subject of
    `.card :is(img, .t-label)` came out as a fragment and the verdict flipped
    depending on which member happened to be written last.
    """
    parts, buf, depth = [], "", 0
    for ch in selector:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if depth == 0 and ch in " \t\n>+~":
            if buf:
                parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        parts.append(buf)
    return parts or [selector]


def _subject(part):
    """The compound selector the rule actually applies to - the last one.

    `.card svg + .card-label` styles the label, not the svg, so searching the
    whole selector string let any element name anywhere in an ancestor chain
    excuse a rule about text.
    """
    # Only the arguments that do NOT determine the subject are removed.
    # `:not()` and `:has()` qualify the compound they hang off, so the subject
    # is that compound - but `:is()` and `:where()` ARE the subject, and
    # stripping them made `.card :is(img, svg)` look like a rule about .card.
    #
    # Balanced removal, because `[^()]*` cannot cross a nested paren and
    # `:not(:is(img))` is a real thing to write - a rule that explicitly
    # excludes images was being excused as an image.
    flat = _drop_balanced(part, ("not", "has"))
    # Attribute VALUES blanked, names kept. Blanking the whole bracket also
    # blanked `[disabled]` and `[aria-disabled]`, which are two of the three
    # alternatives in DECORATIVE_SUBJECT - so a change made to fix combinator
    # splitting silently switched off the check sitting beside it.
    # `\s*` after the bracket: `[ alt="x" ]` is legal CSS.
    flat = re.sub(r"\[\s*([\w-]+)[^\]]*\]", r"[\1]", flat)
    return _split_combinators(flat)[-1]


MATCHES_ANY = ("is", "where", "matches", "any")


def _find_group(selector, names):
    """(start, open, close) of the first `:name(...)`, brackets balanced.

    Balanced, because `[^()]*` stops at a nested paren - and
    `:is(.a:nth-of-type(2), img)` is ordinary CSS. Reading only the
    unnested form made the whole all-members rule fall through to the
    permissive check it was written to replace.
    """
    pattern = re.compile(r":(?:%s)\(" % "|".join(names), re.I)
    m = pattern.search(selector)
    if not m:
        return None
    depth, j = 1, m.end()
    while j < len(selector) and depth:
        if selector[j] == "(":
            depth += 1
        elif selector[j] == ")":
            depth -= 1
        j += 1
    if depth:
        # Unterminated. Returning j - 1 named an ordinary character as the
        # closing bracket, which dropped the last character of the member -
        # and `:is(imgx` truncated to `img`, calling a text subject
        # decorative. An unclosed group is not a group.
        return None
    return m.start(), m.end(), j - 1


def _expand(subject, depth=0):
    """Every concrete selector an :is()/:where() subject stands for.

    `:is(.a, .b)::before` becomes `.a::before` and `.b::before` - real
    selectors, each of which DECORATIVE_SUBJECT can be asked about directly.
    Every group is expanded, not just the first, so the verdict cannot depend
    on which group happens to be written last.
    """
    # The cap fails CLOSED. Returning the subject with an unexpanded
    # `:is(...)` still in it handed the raw group text to the decorative
    # search, where a bare `img` among the members matched the element-name
    # branch and excused the whole rule - which is the exact defect this
    # expansion exists to prevent, reappearing past the fifth group. An empty
    # string matches no branch, so a subject too deep to expand is reported.
    if depth >= 4:
        return [""]
    found = _find_group(subject, MATCHES_ANY)
    if not found:
        return [subject]
    start, inner, close = found
    members = [m.strip() for m in _split_top(subject[inner:close]) if m.strip()]
    # An empty list stands for nothing. Returning the subject unexpanded
    # keeps it answerable, where `all([])` would have called it decorative
    # by vacuum.
    if not members:
        members = [""]
    out = []
    for m in members:
        head = subject[:start]
        # `&` between two halves of a compound: it is CSS nesting's own
        # "this element" and, more to the point here, it is not a word
        # character. Joining `.a` and `img` directly gave `.aimg`, where the
        # element-name lookbehind cannot see an element name at all.
        joined = head + ("&" if head else "") + m + subject[close + 1:]
        out.extend(_expand(joined, depth + 1))
    return out


def _split_top(text):
    """Split on commas at the top bracket level only."""
    parts, buf, depth = [], "", 0
    for ch in text:
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
    return parts


def _fade_value(match):
    """The declared alpha as a float, or None when it cannot be resolved."""
    raw = (match.group(1) or match.group(2) or "").strip()
    if raw.endswith("%"):
        return float(raw[:-1]) / 100
    try:
        return float(raw)
    except ValueError:
        return None


def _is_decorative(selector, body):
    """True when the faded thing does not carry words.

    A ::before is only decorative when its content is empty or a symbol - a
    pseudo-element carrying a real string is text like any other, and this is
    how a counter or a label gets hidden by accident.
    """
    # An :is()/:where() list is decorative only if EVERY member is: one image
    # among them does not make the label beside it an image.
    #
    # The subject is EXPANDED into the concrete selectors it stands for,
    # rather than having its list members concatenated onto the rest of it.
    # Concatenation produced strings no selector could be - `::before.lead`
    # for `:is(.lead, .meta)::before` - which broke the $-anchored
    # pseudo-element branch of DECORATIVE_SUBJECT and reported every
    # decorative pseudo-element fade that happened to carry an :is().
    # Each expansion has its OWN subject re-taken. A member of an :is() list
    # may itself be a complex selector, and substituting it whole left its
    # ancestor in the string: `.x:is(img .b, svg .b)` expands to `.x&img .b`,
    # whose subject is `.b` - a label inside an image - and searching the
    # whole string saw the `img` and excused it.
    if not all(DECORATIVE_SUBJECT.search(_subject(s))
               for s in _expand(_subject(selector))):
        return False
    content = re.search(r"(?<![-\w])content\s*:\s*([^;}]+)", body, re.I)
    if content and re.search(r"[\"'][^\"']*\w{2,}", content.group(1)):
        return False
    return True


def check(css, report, html=""):
    """`report(detail)` is called once per finding."""
    for selector, body, line, _excused in _rules(css):
        # The defect is faded *text*. The original guard for that was "the
        # rule also sets color", which exempted a rule that only fades;
        # dropping it caught that, and started firing on every legitimate
        # decorative fade instead. Neither is the question. The question is
        # whether the thing being faded carries words.
        # SCOPED, never `continue`. Every check below runs on the same rule in
        # the same loop, so skipping ahead when a rule had no fade - or a
        # cosmetic one - silently disabled the ink-is-ground, off-canvas and
        # transparent-mix checks, which are what this file is actually for.
        faded = OPACITY.search(body)
        alpha = _fade_value(faded) if faded else None
        if faded and not (alpha is not None and alpha > COSMETIC_ABOVE):
            # Per PART, not per selector list. One decorative member of a list
            # excused every other member with it, which is the same defect the
            # HIDDEN check below was already fixed for.
            for part in split_parts(selector):
                if _is_decorative(part, body):
                    continue
                shown = faded.group(1) or faded.group(2)
                report(f"line {line}: opacity {shown.strip()} on "
                       f"{part.strip()} - dim with --color-text-soft, which "
                       "carries a guarantee, not with opacity, which removes "
                       "one")
                break

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


def main():
    """Run the legibility rules over every pattern.

    This module is imported by lint.py, which is where it does its work - but
    it was also documented as a command, and had no entry point at all. So
    `python ci/legibility.py` printed nothing and exited 0 whatever the state
    of the library, which is the most complete way a check can lie: it was
    quoted as evidence of a clean run several times over.
    """
    root = Path(__file__).resolve().parent.parent
    findings = []
    folders = sorted(p for p in (root / "patterns").iterdir() if p.is_dir())
    for folder in folders:
        css, html = folder / "pattern.css", folder / "pattern.html"
        if not css.is_file():
            continue
        check(css.read_text(encoding="utf-8"),
              lambda d, _n=folder.name: findings.append(f"{_n}: {d}"),
              html.read_text(encoding="utf-8") if html.is_file() else "")
    if findings:
        print("\n".join(findings))
        print(f"\n{len(findings)} finding(s).")
        return 1
    print(f"clean: {len(folders)} pattern(s) checked for legibility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
