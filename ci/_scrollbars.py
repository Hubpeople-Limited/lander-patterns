"""A row that scrolls sideways never shows the browser's scroll bar.

On a desktop that draws classic scroll bars - Windows, and a Mac with a mouse
plugged in - the bar under a carousel is always there, and a member rail or a
gallery reads as a page that has broken rather than a row to move along. So
every rule that lets a box scroll on the inline axis must also hide the bar,
both ways the engines spell it:

    scrollbar-width: none;                    the standard, on the same selector
    <selector>::-webkit-scrollbar { display: none; }   engines before it

The bar is not the only thing a hidden bar takes away. A mouse has no other
way along a row, so a pattern that hides it also owes the reader another one -
previous and next controls from the `carousel` behaviour, and a layout that
wraps where no script can build them. That half is a design review, not
something a stylesheet scan can see; this half is.

A vertical list (`overflow-y` alone) is not a sideways scroller and is not
held to this.

ALLOWED names the only boxes that keep their bar, and why. Each is a data
table, not a row of items: a table has no control to stand in for the bar, so
hiding it would leave a mouse unable to reach the columns past the edge. Both
are wider than their column only at a phone's width, where the bar is drawn
over the content and fades.
"""

import re

ALLOWED = {
    ("prose-column", ".prose-column figure"):
        "a wide table in an article, wider than the column only on a phone",
    ("comparison-table", ".comparison-table-scroll"):
        "a comparison table, wider than its container only on a phone",
}

SUFFIX = "::-webkit-scrollbar"


def _rules(css):
    """Yield (selector list, declarations) for every rule block at any depth,
    at-rule preludes skipped."""
    text = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    stack, buff, bodies = [], "", []
    for ch in text:
        if ch == "{":
            prelude = buff.strip()
            buff = ""
            kind = "at" if prelude.startswith("@") else "rule"
            stack.append((kind, prelude))
            bodies.append("")
        elif ch == "}":
            if stack:
                kind, prelude = stack.pop()
                body = bodies.pop() + buff
                if kind == "rule" and prelude:
                    decls = {}
                    for decl in body.split(";"):
                        prop, sep, value = decl.partition(":")
                        if sep and prop.strip():
                            decls[prop.strip().lower()] = value.strip().lower()
                    yield prelude, decls
            buff = ""
        elif ch == ";":
            if stack and stack[-1][0] == "rule":
                bodies[-1] += buff + ";"
            buff = ""
        else:
            buff += ch


def _split(prelude):
    parts, buff, depth = [], "", 0
    for ch in prelude:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(buff)
            buff = ""
        else:
            buff += ch
    parts.append(buff)
    return [" ".join(p.split()) for p in parts if p.strip()]


def _scrolls_inline(decls):
    for prop in ("overflow-x", "overflow-inline"):
        if re.fullmatch(r"(auto|scroll)(\s*!important)?", decls.get(prop, "")):
            return prop
    # The shorthand's first value is the inline axis.
    first = decls.get("overflow", "").split()
    if first and first[0] in ("auto", "scroll"):
        return "overflow"
    return None


def scrollbar_faults(css, name):
    """(selector, sentence) for every sideways scroller that can show its bar."""
    rules = list(_rules(css))
    hidden, webkit = set(), set()
    for prelude, decls in rules:
        for sel in _split(prelude):
            if sel.endswith(SUFFIX) and decls.get("display") == "none":
                webkit.add(sel[: -len(SUFFIX)])
            elif decls.get("scrollbar-width") == "none":
                hidden.add(sel)
    faults, seen = [], set()
    for prelude, decls in rules:
        prop = _scrolls_inline(decls)
        if not prop:
            continue
        for sel in _split(prelude):
            if sel in seen or (name, sel) in ALLOWED:
                continue
            seen.add(sel)
            missing = []
            if sel not in hidden:
                missing.append("scrollbar-width: none on the same selector")
            if sel not in webkit:
                missing.append(f"a {sel}{SUFFIX} rule with display: none")
            if missing:
                faults.append((sel, f"{sel} scrolls sideways ({prop}: {decls[prop]}) and "
                                    f"can show the browser's scroll bar - it needs "
                                    + " and ".join(missing)))
    return faults


def allowances_in_use(css, name):
    """The ALLOWED selectors this stylesheet still scrolls sideways, so an
    allowance that has outlived its box is reported rather than kept."""
    return {sel for prelude, decls in _rules(css) if _scrolls_inline(decls)
            for sel in _split(prelude) if (name, sel) in ALLOWED}
