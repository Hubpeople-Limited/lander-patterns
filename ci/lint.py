#!/usr/bin/env python3
"""Validate every pattern and (re)generate INDEX.md.

Usage:
  python ci/lint.py            validate + write INDEX.md
  python ci/lint.py --check    validate + fail if INDEX.md is stale
                               (local verification; CI regenerates instead)

Exit code 0 = clean. Any finding prints `file: rule: detail` and exits 1.
No dependencies beyond the standard library, so it runs anywhere.
"""
import hashlib
import html as html_mod
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import legibility
from _display_type import display_faults
from _heading_size import heading_size_faults
from _containment import external_faults, spacing_faults
import _dials as dials
import _heading_size as heading_size

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"
INDEX = ROOT / "INDEX.md"
# Everything a planner needs in order to choose patterns without opening one.
# Generated, never hand-edited, like INDEX.md.
MANIFEST = ROOT / "patterns.json"

REQUIRED_FIELDS = [
    "name", "version", "type", "page-types", "content-shape", "description",
    "keywords", "needs", "tokens-used", "motion", "status", "added",
    "one-per-page",
]
TYPES = {"component", "section", "page"}
MOTION = {"none", "subtle", "expressive"}
STATUS = {"active", "deprecated"}
ONE_PER_PAGE = {"yes", "no"}
README_MAX_LINES = 80
# pattern.css is appended verbatim into a brand's stylesheet and cannot be
# stripped, so its comments are permanently published: a tight ceiling, and
# only notes that stop someone breaking the rule beside them.
# pattern.html comments are build instructions - which slot takes what, what
# to duplicate - and are removed when the pattern is placed, so they earn more
# room. Neither may narrate how the file came to be.
COMMENT_MAX_PERCENT = {"css": 12, "html": 35}

# Class families the shared page chassis already owns; a pattern may not take
# one of these as its name, or its classes would collide on append.
RESERVED_NAMES = {
    "site", "btn", "card", "chip", "grid", "container", "section", "wrapper",
    "breadcrumb", "canvas", "profile", "footer", "header", "nav", "visually",
    "index", "band", "bar", "statement", "table", "editorial", "split",
    # The behaviour library injects .hub-* state classes. A pattern taking
    # that prefix would collide with them, and would also opt itself out of
    # every check that skips them.
    "hub",
}

# Vendored platform furniture-token registry (see TOKENS.md). The logo, login
# and join families also answer to a numbered middle segment.
FURNITURE = {
    "menu.navigation", "menu.navigation.default", "menu.footer",
    "footerLinks.antiSlaveryPolicyUrl", "footerLinks.cookiesUrl",
    "footerLinks.privacyPolicyUrl", "footerLinks.termsAndConditionsUrl",
    "logo.src", "logo.alt",
    "login.url", "login.text", "join.url", "join.text",
    "canonicalPage", "favicon",
    "pageTitle", "metaDescription", "metaKeywords",
}
NUMBERED_FAMILIES = ("logo", "login", "join")

REGISTRY_FILE = ROOT / "lib" / "REGISTRY.md"


def registered_behaviours():
    """Behaviour names from lib/REGISTRY.md's table (first column, backticked)."""
    if not REGISTRY_FILE.is_file():
        return set()
    names = set()
    for line in REGISTRY_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*`([\w-]+)`\s*\|", line)
        if m:
            names.add(m.group(1))
    return names

# Leak scan. The strings that must never reach a public file are not in this
# repo in any form - not in plaintext, and not as digests, which for a short
# guessable list is an index rather than a hash. Supply them at scan time,
# one per line, either way:
#   LANDER_LEAK_NEEDLES   environment variable, how CI passes a secret
#   ci/leak-needles.local untracked file, for running it locally
#
# With neither present the scan does not report clean; it says it could not
# run. One exception: GitHub will not give a secret to a pull request from a
# fork, so the workflow sets LANDER_LEAK_SKIP there and the scan runs again
# on the merge, before anything is released.
NEEDLES_FILE = ROOT / "ci" / "leak-needles.local"


def leak_needles():
    raw = os.environ.get("LANDER_LEAK_NEEDLES")
    if raw is None and NEEDLES_FILE.is_file():
        raw = NEEDLES_FILE.read_text(encoding="utf-8")
    if not raw:
        return None
    # `or None` matters: a secret containing only whitespace is truthy, so it
    # used to yield an empty list - which is not None, so nothing was
    # reported, and is falsy, so nothing was scanned. A stray newline in the
    # secret defeated the whole check silently. A whitespace-only list is no
    # list.
    return [n.strip().lower() for n in raw.splitlines() if n.strip()] or None


NAMED_COLOURS = set("""aliceblue antiquewhite aqua aquamarine azure beige bisque black
blanchedalmond blue blueviolet brown burlywood cadetblue chartreuse chocolate coral
cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen
darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon
darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink
deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia
gainsboro ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink
indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue
lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey lightpink
lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue
lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue
mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen
mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite
navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen
paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple
rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell
sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal
thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen""".split())

COLOUR_FUNCTIONS = r"\b(rgb|rgba|hsl|hsla|oklch|oklab|lab|lch|hwb|color|device-cmyk)\s*\("

# A pattern is appended into a page that already exists, so an unclosed
# container does not break the pattern - it swallows the rest of the document.
# The list therefore has to cover everything a pattern may legally contain,
# not the subset the patterns happened to use when it was written.
BALANCED_TAGS = ["section", "article", "div", "ul", "ol", "li", "main",
                 "header", "footer", "nav", "a", "p", "h1", "h2", "h3",
                 "h4", "h5", "h6", "dl", "dt", "dd", "button", "details",
                 "summary", "figure", "figcaption", "blockquote", "span",
                 "label", "table", "thead", "tbody", "tfoot", "tr", "td",
                 "th", "caption", "colgroup", "aside", "picture", "video",
                 "audio", "svg", "form", "fieldset", "legend", "select",
                 "option", "optgroup", "textarea", "time", "strong", "em",
                 "b", "i", "small", "pre", "code", "dialog", "address",
                 "hgroup", "search", "noscript"]

SLOT_CANONICAL = re.compile(r"<!-- slot: [\w-]+ -->")
SLOT_ANYWHERE = re.compile(r"<!--\s*slot\s*:", re.I)

findings = []


def find(path, rule, detail):
    findings.append(f"{path.relative_to(ROOT)}: {rule}: {detail}")


def parse_header(text, path):
    m = re.match(r"\s*<!--\n(.*?)\n-->", text, re.S)
    if not m:
        find(path, "header", "no metadata comment header at the top")
        return {}
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.split("#")[0].strip() if key.strip() in (
            "type", "motion", "status", "one-per-page") else value.strip()
    return meta


def furniture_ok(token):
    if token in FURNITURE:
        return True
    parts = token.split(".")
    if len(parts) == 3 and parts[0] in NUMBERED_FAMILIES and parts[1].isdigit():
        return ".".join([parts[0], parts[2]]) in FURNITURE
    return False


def colour_literal(value):
    """The name of the first hardcoded colour in `value`, or None. Shared by
    the stylesheet check and the style-attribute check so the two cannot
    disagree about what a literal is."""
    if re.search(r"#[0-9a-fA-F]{3,8}\b", value):
        return "hex colour"
    if re.search(r"%23[0-9a-fA-F]{3,8}\b", value):
        return "URL-encoded hex colour (%23...)"
    if re.search(COLOUR_FUNCTIONS, value, re.I):
        return "colour function"
    for word in re.findall(r"[a-zA-Z]+", value):
        if word.lower() in NAMED_COLOURS:
            return f"named colour '{word}'"
    for word in ("CanvasText", "Canvas", "AccentColor", "AccentColorText",
                 "LinkText", "VisitedText", "ButtonText", "ButtonFace",
                 "Field", "FieldText", "Highlight", "HighlightText",
                 "GrayText", "Mark", "MarkText", "SelectedItem",
                 "SelectedItemText", "ButtonBorder"):
        if re.search(rf"\b{word}\b", value):
            return f"CSS system colour '{word}'"
    return None


def check_html(path, meta, folder_name):
    text = path.read_text(encoding="utf-8")
    body = re.sub(r"\s*<!--\n.*?\n-->", "", text, count=1, flags=re.S)
    # Entity-decode before the script checks: browsers decode entities, so the
    # lint must too. Two variants: attribute checks need whitespace kept AS
    # whitespace (deleting a newline would glue attributes together and hide
    # a handler); the URL-scheme check needs it deleted (browsers strip
    # tab/newline inside schemes).
    unescaped = html_mod.unescape(body)
    decoded_ws = re.sub(r"[\t\n\r]", " ", unescaped)
    decoded_tight = re.sub(r"[\t\n\r]", "", unescaped)

    for field in REQUIRED_FIELDS:
        if not meta.get(field):
            find(path, "header", f"missing or empty field '{field}'")
    if meta.get("name") and meta["name"] != folder_name:
        find(path, "header", f"name '{meta['name']}' != folder '{folder_name}'")
    if folder_name.split("-")[0] in RESERVED_NAMES:
        find(path, "header",
             f"name starts with reserved chassis word '{folder_name.split('-')[0]}'")
    if meta.get("type") and meta["type"] not in TYPES:
        find(path, "header", f"type '{meta['type']}' not in {sorted(TYPES)}")
    if meta.get("motion") and meta["motion"] not in MOTION:
        find(path, "header", f"motion '{meta['motion']}' not in {sorted(MOTION)}")
    if meta.get("one-per-page") and meta["one-per-page"] not in ONE_PER_PAGE:
        find(path, "header",
             f"one-per-page '{meta['one-per-page']}' not in {sorted(ONE_PER_PAGE)}")
    if meta.get("status") and meta["status"] not in STATUS:
        find(path, "header", f"status '{meta['status']}' not in {sorted(STATUS)}")
    if meta.get("status") == "deprecated" and not meta.get("replaced-by"):
        find(path, "header", "deprecated pattern needs 'replaced-by'")
    if meta.get("version") and not meta["version"].isdigit():
        find(path, "header", "version must be a bare integer")

    if re.search(r"<script\b", body, re.I):
        find(path, "no-script", "script elements are not allowed in patterns")
    # A pattern pulls nothing in from elsewhere. <iframe>, <object> and
    # <embed> run third-party code, which is the outcome the no-script rule
    # exists to prevent; <link> pulls a stylesheet and defeats the token
    # contract wholesale; <base> silently repoints every relative URL,
    # including the platform's furniture tokens. An embed is a likely
    # contribution rather than a contrived one - a map, a video, a reviews
    # widget - so the refusal is explicit rather than implied by "no script".
    for tag in ("iframe", "object", "embed", "link", "base", "frame",
                "frameset", "portal", "applet"):
        if re.search(rf"<{tag}\b", body, re.I):
            find(path, "no-embedded-content",
                 f"<{tag}> is not allowed: a pattern renders from the token "
                 "contract and pulls nothing in from elsewhere")
    if re.search(r"<meta\b[^>]*http-equiv", body, re.I):
        find(path, "no-embedded-content",
             "<meta http-equiv> can redirect or re-scope the whole page")
    # Two ways to hide content that are not CSS at all, so no stylesheet check
    # can see them. <template> content never renders in any engine, and the
    # hidden attribute is the markup spelling of display: none.
    if re.search(r"<template\b", body, re.I):
        find(path, "legibility",
             "<template> content never renders - a pattern's markup is what "
             "the page shows")
    if re.search(r"<[a-z][^>]*\shidden(\s|=|>|/)", body, re.I):
        find(path, "legibility",
             "the hidden attribute leaves a reader with nothing; the "
             "behaviour library sets it at runtime, a pattern does not ship it")
    # The behaviour library's class prefix, which several checks treat as
    # "the platform put this here" and skip over.
    for m in re.finditer(r'class="([^"]*)"', body):
        if any(c.startswith("hub-") for c in m.group(1).split()):
            find(path, "legibility",
                 f'class="{m.group(1)}" carries the behaviour library prefix, '
                 "which other checks treat as the platform's and skip")
    # Decoded, because browsers decode entities and so must this - the handler
    # and javascript: checks below already do, and this one read raw markup,
    # so action="&#104;ttps://..." went straight through. formaction on a
    # button or input is the same door and was not checked at all.
    for m in re.finditer(r"<(form|button|input)\b([^>]*)>", decoded_ws, re.I):
        if re.search(r"(?<![-\w])(?:form)?action\s*=\s*[\"']?\s*(https?:)?//",
                     m.group(2), re.I):
            find(path, "no-embedded-content",
                 f"a {m.group(1).lower()} posting to an external host is not "
                 "allowed")
    if re.search(r"<style\b", body, re.I):
        find(path, "no-style-element", "style elements are not allowed")
    if re.search(r"(?<![-\w])on\w+\s*=", decoded_ws, re.I):
        find(path, "no-script", "inline event handlers (on*=) are not allowed")
    if re.search(r"javascript\s*:", decoded_tight, re.I):
        find(path, "no-script", "javascript: URLs are not allowed")
    # All three HTML attribute-value forms, on entity-decoded text - a
    # single-quoted or unquoted style would otherwise slip past this check
    # and every CSS check at once.
    for m in re.finditer(
            r"""style\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>][^\s>]*))""",
            decoded_ws, re.I):
        value = next(g for g in m.groups() if g is not None)
        decls = [d for d in value.split(";") if d.strip()]
        if any(not d.strip().startswith("--") for d in decls):
            find(path, "no-inline-style",
                 f'style attribute "{value}" carries a non-custom-property declaration')
        # A custom property is allowed here, but its VALUE was never checked -
        # so `style="--x-ink: #f00"` put a hardcoded colour into a pattern and
        # passed clean, defeating the one promise the library rests on. The
        # same literal rules apply as in pattern.css.
        for decl in decls:
            prop, _, val = decl.partition(":")
            if not prop.strip().startswith("--"):
                continue
            literal = colour_literal(val)
            if literal:
                find(path, "no-colour-literals",
                     f"{literal} in style attribute '{decl.strip()}' - the "
                     "property is allowed, the hardcoded value is not")
            if re.search(r"(^|\s)#[0-9a-fA-F]{3,8}\b", val) is None and \
               re.search(r"\b\d+(\.\d+)?(px|rem|em)\b", val) and \
               "radius" in prop:
                find(path, "no-hardcoded-dials",
                     f"hardcoded length in style attribute '{decl.strip()}'")

    # Every OTHER attribute value, because the colour check above only ever
    # looked inside style=. An inline SVG chevron with fill="#f00", or a
    # data-URI icon with %23f00 in it, is the most likely next thing anyone
    # adds to this library, and both shipped a fixed colour to every brand
    # with lint silent. Attributes that legitimately carry colour words in
    # prose - alt text, aria labels, slot names - are exempt.
    PROSE_ATTRS = {"alt", "title", "aria-label", "aria-labelledby",
                   "aria-describedby", "class", "id", "href", "src",
                   "srcset", "sizes", "data-hub-module",
                   # Visible prose, so a tier called "Silver" is a name and
                   # not a colour literal.
                   "data-hub-tab-label", "data-hub-tabs-label"}
    for m in re.finditer(
            r"""([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+))""",
            re.sub(r"<!--.*?-->", "", decoded_ws, flags=re.S)):
        attr = m.group(1).lower()
        val = next(g for g in m.groups()[1:] if g is not None)
        if attr == "style":
            continue
        # src and srcset are exempt for ordinary URLs, but a data: URI is not
        # a URL - it is inline content, and it can carry an encoded colour.
        if attr in PROSE_ATTRS and not val.strip().lower().startswith("data:"):
            continue
        if val.startswith("slot:") or "{{" in val:
            continue
        literal = colour_literal(val)
        if literal:
            find(path, "no-colour-literals",
                 f"{literal} in attribute {attr}=\"{val[:40]}\" - markup "
                 "carries no colour either")

    for m in re.finditer(r"\{\{\s*([^}]+?)\s*\}\}", body):
        if not furniture_ok(m.group(1)):
            find(path, "unknown-token",
                 f"{{{{{m.group(1)}}}}} is not on the furniture table")

    # Non-canonical slot comments lint-pass but survive the preview fill.
    for m in SLOT_ANYWHERE.finditer(body):
        line_start = body.rfind("\n", 0, m.start()) + 1
        snippet = body[m.start():m.start() + 40]
        if not SLOT_CANONICAL.match(body, m.start()):
            find(path, "slot-spelling",
                 f"slot comment must be exactly '<!-- slot: name -->' ({snippet!r})")

    counted = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    for tag in BALANCED_TAGS:
        opens = len(re.findall(rf"<{tag}(?=[\s>])", counted))
        closes = len(re.findall(rf"</{tag}\s*>", counted))
        if opens != closes:
            find(path, "unbalanced-tag", f"<{tag}> opens {opens}, closes {closes}")

    for img in re.finditer(r"<img\b[^>]*>", body, re.I):
        tag = img.group(0)
        for attr in ("alt", "width", "height"):
            if not re.search(rf"\b{attr}\s*=", tag, re.I):
                find(path, "img-attrs", f"an <img> is missing '{attr}'")

    # Behaviours: hooks in the markup and the header field must agree, and
    # both must name registered behaviours (lib/REGISTRY.md). Hooks are inert
    # without the platform-injected library, so this is consistency, not
    # safety - the safety rule is that no script ever rides in a pattern.
    declared = {b.strip() for b in meta.get("behaviours", "").split(",") if b.strip()}
    hooked = set()
    for m in re.finditer(
            r"""data-hub-module\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>][^\s>]*))""",
            decoded_ws, re.I):
        value = next(g for g in m.groups() if g is not None)
        hooked |= set(value.split())
    known = registered_behaviours()
    for name in sorted((declared | hooked) - known):
        find(path, "behaviours", f"'{name}' is not in lib/REGISTRY.md")
    for name in sorted(hooked - declared):
        find(path, "behaviours", f"markup hooks '{name}' but the header does not declare it")
    for name in sorted(declared - hooked):
        find(path, "behaviours", f"header declares '{name}' but no markup hooks it")

    slots = set(re.findall(r"<!-- slot: ([\w-]+) -->", body))
    slots |= set(re.findall(r'"slot:([\w-]+)"', body))
    return slots


def iter_selectors(css):
    """Yield every selector prelude, at any nesting depth, skipping at-rule
    preludes and everything inside @keyframes (whose preludes are frame
    names, not selectors)."""
    stripped = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    buff = ""
    stack = []
    for ch in stripped:
        if ch == "{":
            prelude = buff.strip()
            buff = ""
            if prelude.startswith("@keyframes"):
                stack.append("keyframes")
            elif prelude.startswith("@"):
                stack.append("at")
            else:
                stack.append("rule")
                if prelude and "keyframes" not in stack[:-1]:
                    yield prelude
        elif ch == "}":
            if stack:
                stack.pop()
            buff = ""
        elif ch == ";":
            buff = ""
        else:
            buff += ch


def split_selector_list(selector):
    """Split a selector list on its top-level commas only. A comma inside
    :is(), :where(), :not() or an attribute value separates arguments, not
    selectors - splitting on it invents fragments like `button` that no rule
    ever contained."""
    parts, buff, depth = [], "", 0
    for ch in selector:
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
    return [p for p in (x.strip() for x in parts) if p]


def iter_declarations(css):
    """Yield (property, value) for every declaration at any depth. A prelude
    ends with '{' and is discarded here; a declaration ends with ';' or '}'."""
    buff = ""
    for ch in css:
        if ch == "{":
            buff = ""
        elif ch in ";}":
            decl = buff.strip()
            buff = ""
            if ":" in decl:
                prop, _, value = decl.partition(":")
                if prop.strip():
                    yield prop.strip(), value.strip()
        else:
            buff += ch


def expand_var_fallbacks(value, local_prefix):
    """Replace `var(--<local_prefix>..., FALLBACK)` with FALLBACK, honouring
    nested parentheses. Used to see what a pattern-local dial actually
    resolves to on a brand that does not set it."""
    for _ in range(5):
        m = re.search(rf"var\(\s*{re.escape(local_prefix)}[\w-]*\s*,", value)
        if not m:
            return value
        depth, i = 1, m.end()
        while i < len(value) and depth:
            if value[i] == "(":
                depth += 1
            elif value[i] == ")":
                depth -= 1
            i += 1
        if depth:
            return value                       # unbalanced; leave it alone
        value = value[:m.start()] + value[m.end():i - 1].strip() + value[i:]
    return value


def check_css(path, folder_name, text=None):
    """ overrides the file's contents, so the behaviour library's
    injected stylesheet goes through exactly these checks rather than a
    simpler copy of them that can drift."""
    if text is None:
        text = path.read_text(encoding="utf-8")
    stripped = re.sub(r"/\*.*?\*/", "", text, flags=re.S)

    if re.search(r"#[0-9a-fA-F]{3,8}\b", stripped):
        find(path, "no-colour-literals", "hex colour found; use contract tokens")
    if re.search(COLOUR_FUNCTIONS, stripped, re.I):
        find(path, "no-colour-literals",
             "colour function found; use contract tokens (color-mix of tokens is fine)")

    # Every pattern-local property and its value, so a token-only check can
    # follow `--x: 12px; border-radius: var(--x)` to what it actually is.
    locals_map = {p: v for p, v in iter_declarations(stripped)
                  if p.startswith(f"--{folder_name}-")}

    # Named colours and token-only properties: inspect real declarations only
    # (the walker below cannot mistake selector text for a declaration).
    # Custom-property declarations are scanned for named colours too - a
    # locally defined --var is exactly the smuggling route - but words inside
    # var() token *names* are not colours and are stripped first.
    for prop, value in iter_declarations(stripped):
        scannable = re.sub(r"var\(\s*--[\w-]+", "var(", value)
        for word in re.findall(r"[a-zA-Z]+", scannable):
            if word.lower() in NAMED_COLOURS:
                find(path, "no-colour-literals",
                     f"named colour '{word}' in '{prop}: {value}'")
        if re.search(r"%23[0-9a-fA-F]{3,8}\b", value):
            find(path, "no-colour-literals",
                 f"URL-encoded hex colour in '{prop}: {value}' - a data URI is "
                 "not an exemption")
        sys_colour = colour_literal(re.sub(r"var\(\s*--[\w-]+", "var(", value))
        if sys_colour and sys_colour.startswith("CSS system colour"):
            find(path, "no-colour-literals", f"{sys_colour} in '{prop}: {value}'")
        # A pattern-local property is a legitimate dial, but it is also the
        # obvious smuggling route: --x-radius: 12px then border-radius:
        # var(--x-radius) put a hardcoded dial through a check that only
        # looked for the absence of var(). Hold local dials to the same rule
        # as the properties they feed.
        if prop.startswith("--"):
            continue
        if prop.endswith("-radius") or prop == "box-shadow":
            # Resolve pattern-local properties before judging. Checking only
            # for the absence of `var(` let `--x: 12px; border-radius:
            # var(--x)` through, and naming the local something that does not
            # contain "radius" defeated a name-based check too. What matters
            # is what the property ends up being, so follow the chain.
            resolved, seen = value, set()
            for _ in range(5):
                refs = re.findall(r"var\(\s*(--[\w-]+)", resolved)
                # Only substitute locals this file actually DECLARES. An
                # undeclared one is a dial a brand sets, and its fallback is
                # what applies here - substituting a placeholder for it both
                # mangled nested parens and reported a token-backed fallback
                # as hardcoded.
                local = [r for r in refs
                         if r.startswith(f"--{folder_name}-")
                         and r in locals_map and r not in seen]
                if not local:
                    break
                for r in local:
                    seen.add(r)
                    resolved = re.sub(rf"var\(\s*{re.escape(r)}\s*\)",
                                      locals_map[r], resolved)
            # An UNDECLARED local is a dial a brand may set, so what applies
            # here is its fallback. Replace each with that fallback and see
            # what is left: `var(--x-dial, var(--card-radius))` resolves to a
            # contract token and is fine; `var(--x-dial, 12px)` resolves to a
            # hardcoded value wearing a dial's clothes.
            resolved = expand_var_fallbacks(resolved, f"--{folder_name}-")
            # "Fully round" is a shape, not a brand decision - a circular
            # avatar is circular on every brand - so those forms are exempt.
            exempt = resolved.strip() in ("none", "0", "50%", "100%",
                                          "inherit", "initial", "unset",
                                          "revert") or \
                re.fullmatch(r"9{3,}px", resolved.strip())
            if "var(" not in resolved and not exempt:
                find(path, "token-only",
                     f"{prop} resolves to '{resolved.strip()}' with no contract "
                     "token - a local property is a dial, not an exemption")
        if prop == "filter" and "drop-shadow(" in value and "var(" not in value:
            find(path, "token-only",
                 f"{prop}: {value} - drop-shadow values must come from tokens")

    # Every selector, at any depth, must reference the pattern's own class
    # outside a :not(). A reference only inside :not() targets everything else.
    for selector in iter_selectors(text):
        for part in split_selector_list(selector):
            effective = re.sub(r":not\([^)]*\)", "", part)
            if f".{folder_name}" not in effective:
                find(path, "selector-prefix",
                     f"'{part.strip()}' does not reference .{folder_name}* "
                     "(references inside :not() do not count)")


def check_list_semantics(html_path, css_path, folder_name):
    """A ul/ol whose own stylesheet removes the markers loses its list
    semantics in Safari/VoiceOver, and with them the item count. role="list"
    restores it. Only fires where the pattern actually unsets list-style."""
    if not css_path.is_file():
        return
    css = re.sub(r"/\*.*?\*/", "", css_path.read_text(encoding="utf-8"), flags=re.S)
    if not re.search(r"list-style[\w-]*\s*:[^;}]*\bnone\b", css):
        return
    # Comments are stripped first: the builder notes talk ABOUT tags, and
    # "a CSS counter off the <ol>" is prose, not a list that needs a role.
    html = re.sub(r"<!--.*?-->", "", html_path.read_text(encoding="utf-8"),
                  flags=re.S)
    for m in re.finditer(r"<(ul|ol)(?:\s[^>]*)?>", html):
        if 'role="list"' not in m.group(0):
            find(html_path, "list-semantics",
                 f"<{m.group(1)}> needs role=\"list\": this pattern sets "
                 "list-style: none, which drops list semantics in Safari")


def contract_tokens():
    """Every token TOKENS.md defines, read from the first column of its
    tables. The contract is the document; this parses it rather than
    duplicating it, so the two cannot drift."""
    doc = ROOT / "TOKENS.md"
    if not doc.is_file():
        return set()
    text = doc.read_text(encoding="utf-8")
    tokens = set()
    for row in re.findall(r"^\|([^|]+)\|", text, re.M):
        tokens.update(re.findall(r"`(--[\w-]+)`", row))
    # The spacing scale has gaps, and inventing the missing steps here would
    # bless a token no brand defines - which resolves to nothing and takes
    # its whole declaration with it.
    tokens.update(re.findall(r"`(--space-\d+)`", text))
    tokens.update("--space-" + n for n in re.findall(r"`-(\d+)`", text))
    # Motion tokens are named in prose, not a table.
    tokens.update(re.findall(r"`(--transition-[\w-]+)`", text))
    return tokens


def check_contract_membership(html_path, css_path, folder_name, contract):
    """A `var(--whatever)` that is neither a contract token nor the pattern's
    own `--<name>-*` property resolves to nothing on a real brand, and the
    declaration around it is dropped whole. `tokens-used` only ever compared
    the header against the stylesheet, so two matching invented names passed
    clean."""
    if not css_path.is_file() or not contract:
        return
    local = f"--{folder_name}-"
    css = css_path.read_text(encoding="utf-8")
    unknown = sorted({t for t in re.findall(r"var\(\s*(--[\w-]+)", css)
                      if not t.startswith(local) and t not in contract})
    if unknown:
        find(css_path, "unknown-token",
             f"{', '.join(unknown)} - not in TOKENS.md and not this pattern's "
             f"own {local}* namespace, so it resolves to nothing on a brand")


def check_version_bumps(folders):
    """`version` is the library's only distribution guarantee: a brand pins
    `name@version` in its own stylesheet, so if pattern.css changes under an
    unchanged version, that pin now names two different stylesheets and the
    brand has no way to know. Compare each pattern's shipped files against
    the merge base and require the header to move with them.

    Skipped when there is no git, no upstream to diff against, or the pattern
    is new in this branch - a first version cannot have been bumped."""
    inside_git = subprocess.run(["git", "rev-parse", "--git-dir"],
                                capture_output=True, text=True, cwd=ROOT)
    if inside_git.returncode != 0:
        return                      # not a checkout at all; nothing to compare
    base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"],
                          capture_output=True, text=True, cwd=ROOT)
    if base.returncode != 0:
        # A shallow checkout has no origin/main, and this returned silently -
        # so the rule reported clean everywhere it was meant to run. Say so
        # instead: CI passes fetch-depth: 0 precisely to make this resolvable.
        find(ROOT / "ci" / "lint.py", "version",
             "cannot resolve origin/main, so the version-bump check did not "
             "run. Fetch it (CI uses fetch-depth: 0) rather than trusting "
             "this pass")
        return
    ref = base.stdout.strip()

    def consumer_visible(html_text, css_text):
        """What actually reaches a brand: the whole stylesheet, and the markup
        with comments stripped - the metadata header and the builder notes are
        removed when the pattern is placed, so a change confined to them
        cannot reach anyone and must not force a bump."""
        return re.sub(r"<!--.*?-->", "", html_text, flags=re.S).strip(), css_text

    for folder in folders:
        rel = f"patterns/{folder.name}"
        old = {}
        for name in ("pattern.html", "pattern.css"):
            got = subprocess.run(["git", "show", f"{ref}:{rel}/{name}"],
                                 capture_output=True, text=True, cwd=ROOT)
            if got.returncode != 0:
                break             # new pattern in this branch
            old[name] = got.stdout
        if len(old) != 2:
            continue
        now_html = (folder / "pattern.html").read_text(encoding="utf-8")
        now_css = (folder / "pattern.css").read_text(encoding="utf-8")
        was_markup, was_css = consumer_visible(old["pattern.html"], old["pattern.css"])
        now_markup, now_css_v = consumer_visible(now_html, now_css)
        moved = []
        if was_markup != now_markup:
            moved.append("markup")
        if was_css != now_css_v:
            moved.append("pattern.css")
        if not moved:
            continue
        # Flexible whitespace, because the header parser that reads this field
        # everywhere else partitions on the colon and accepts `version:5`.
        # This regex demanded exactly one space, so writing it without one
        # made `now` None and skipped the comparison entirely - while the
        # version still parsed fine into INDEX.md and patterns.json.
        was = re.search(r"^version\s*:\s*(.*)$", old["pattern.html"], re.M)
        now = re.search(r"^version\s*:\s*(.*)$", now_html, re.M)
        if was and now and was.group(1).strip() == now.group(1).strip():
            find(folder / "pattern.html", "version",
                 f"{' and '.join(moved)} changed since {ref[:8]} but version "
                 f"is still {now.group(1).strip()} - a brand that pinned "
                 f"{folder.name}@{now.group(1).strip()} has different code")


def check_control_bytes(path):
    """No control characters outside tab/newline/CR. A stray byte is invisible
    in every editor and in `git diff`, survives review, and ships. All 15
    patterns once carried a 0x01 on the same header line for exactly that
    reason: the header parser skipped the line for want of a colon, and the
    preview build deleted the whole comment before rendering, so nothing
    downstream ever saw it."""
    raw = path.read_bytes()
    for i, byte in enumerate(raw):
        if byte < 9 or byte in (11, 12) or 14 <= byte < 32:
            line = raw[:i].count(b"\n") + 1
            find(path, "control-byte",
                 f"line {line} contains {hex(byte)} - invisible in editors "
                 "and diffs, and it ships")
            return


# Comments in pattern.css are appended verbatim into a brand's stylesheet,
# and comments in pattern.html reach the page unless the builder strips them.
# Both are therefore published text. A comment earns its place only by
# stopping someone breaking the pattern; reasoning, history and measurement
# belong in README.md, which is read at build time and never shipped.
BANNED_COMMENT_TERMS = [
    # How the file came to be. Never of use to anyone building a page.
    "earlier version", "earlier pass", "earlier extraction", "an earlier",
    "previous version", "used to ", "this extraction", "the extraction",
    "originally", "at first", "initially", "we changed", "we decided",
    "we found", "turned out", "had missed", "was wrong", "is wrong",
    "claimed", "retracted", "corrected", "fixed a", "regression",
    # Review and generation process.
    "reviewer", "code review", "hostile review", "review round",
    "round 1", "round 2", "round 3", "round 4", "round 5", "round 6",
    "critic", "conversation", "prompt", "llm", "chatgpt", "claude",
    # First-person authorship.
    "i think", "i chose", "my own", "we think", "we chose",
]

# A shipped comment may state a measured limit, but not walk through the
# working. These read as workings.
BANNED_COMMENT_PATTERNS = [
    (r"\bmeasured\b", "a measurement belongs in README.md"),
    (r"\b\d+(\.\d+)?:1\b", "a contrast ratio belongs in README.md"),
]


def iter_comments(text, kind):
    """(text, line_number) for every comment. `kind` is 'css' or 'html'; the
    HTML metadata header is excluded, being machine-read and stripped."""
    pattern = r"/\*(.*?)\*/" if kind == "css" else r"<!--(.*?)-->"
    for i, m in enumerate(re.finditer(pattern, text, re.S)):
        if kind == "html" and i == 0 and m.start() < 5:
            continue                       # the metadata header
        yield m.group(1), text[:m.start()].count("\n") + 1


def check_comment_policy(path, kind):
    text = path.read_text(encoding="utf-8")
    total = len(text.splitlines()) or 1
    commented = 0
    for body, line in iter_comments(text, kind):
        commented += len(body.splitlines()) or 1
        low = body.lower()
        for term in BANNED_COMMENT_TERMS:
            if re.search(rf"(?<!\w){re.escape(term.strip())}(?!\w)", low):
                find(path, "comment-policy",
                     f"line {line}: comment says '{term.strip()}' - this file "
                     "is published, and how it came to be is not useful to "
                     "anyone building a page. Reasoning goes in README.md")
                break
        for rx, why in BANNED_COMMENT_PATTERNS:
            if re.search(rx, low):
                find(path, "comment-policy", f"line {line}: {why}")
                break
    ceiling = COMMENT_MAX_PERCENT[kind]
    if commented * 100 // total > ceiling:
        find(path, "comment-policy",
             f"{commented * 100 // total}% of this published file is comment "
             f"(ceiling {ceiling}%) - keep what a builder needs, move the "
             "reasoning to README.md")


def check_narration(path):
    """The vocabulary ban applies to prose files too. A README is public and
    is fetched by every agent that shortlists the pattern; how the file came
    to be is no more use there than in the stylesheet."""
    low = path.read_text(encoding="utf-8").lower()
    for term in BANNED_COMMENT_TERMS:
        if re.search(rf"(?<!\w){re.escape(term.strip())}(?!\w)", low):
            find(path, "comment-policy",
                 f"says '{term.strip()}' - describe the pattern, not how it "
                 "came to be")
            return


def check_edges_documented(readme_path, meta):
    """Every `avoid-with` entry must be named in the pattern's own README. The
    header is what an agent parses and the README is what a person reads; when
    they drift, one of the two is telling somebody the wrong thing. Seven
    edges were invisible to a reader before this rule existed."""
    if not readme_path.is_file():
        return
    text = readme_path.read_text(encoding="utf-8")
    for ref in [r.strip() for r in meta.get("avoid-with", "").split(",")]:
        if ref and ref != "none" and ref not in text:
            find(readme_path, "undocumented-edge",
                 f"header avoids '{ref}' and the README never says so")


def check_motion_claim(html_path, css_path, meta):
    """`motion: none` is a promise a brand can plan around, so it must match
    the stylesheet. Comments are stripped first - one pattern's opening note
    says the word "transitions" precisely to explain that it has none."""
    if meta.get("motion") != "none" or not css_path.is_file():
        return
    css = re.sub(r"/\*.*?\*/", "", css_path.read_text(encoding="utf-8"),
                 flags=re.S)
    moving = re.findall(r"\b(transition|animation|scroll-behavior)[\w-]*\s*:", css)
    if moving:
        find(html_path, "motion",
             f"motion: none, but pattern.css declares {sorted(set(moving))}")


def check_header_comments(html_path, meta_block):
    """The spec in CONTRIBUTING.md annotates fields with `# a | b | c` to say
    what is allowed. Those annotations are the spec's, not a pattern's, and
    copying the template carries them into every page built from it."""
    for line in meta_block.splitlines():
        if "#" in line and not line.strip().startswith("#"):
            find(html_path, "header",
                 f"spec annotation copied from the template: '{line.strip()}'")


def check_leaks(path, needles):
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    for needle in needles:
        if needle in text:
            find(path, "leak",
                 f"forbidden string at offset {text.index(needle)} "
                 "(the string itself is not printed)")


def check_token_sets_are_complete():
    """Every sample token set must define every token the patterns rely on.

    A var() with no fallback and no definition invalidates the whole
    declaration, so a token set missing one is a preview quietly rendering
    without that rule - and a preview that cannot show a fault is worse than
    no preview. This is also the check that would have caught the contract
    naming five tokens no real brand defines: the original three sets were
    written alongside the library and agreed with it by construction.

    ci/brand_fit.py asks the harder version of the same question, against real
    brand stylesheets rather than the samples here.
    """
    use = re.compile(r"var\(\s*(--[\w-]+)\s*(,)?")
    # Unanchored: several declarations may share a line, and an anchored match
    # would see only the first and understate what a set defines.
    define = re.compile(r"(--[\w-]+)\s*:")
    needed = set()
    for folder in sorted(p for p in PATTERNS.iterdir() if p.is_dir()):
        css = re.sub(r"/\*.*?\*/", "",
                     (folder / "pattern.css").read_text(encoding="utf-8"),
                     flags=re.S)
        own = set(define.findall(css))
        for token, fallback in use.findall(css):
            if token not in own and not fallback:
                needed.add(token)
    sets = sorted((ROOT / "preview").glob("tokens-*.css"))
    if not sets:
        find(ROOT / "preview", "token-sets", "no sample token sets found")
        return
    for path in sets:
        missing = sorted(needed - set(define.findall(path.read_text(encoding="utf-8"))))
        if missing:
            find(path, "token-sets",
                 f"does not define {len(missing)} token(s) the patterns use "
                 f"with no fallback: {', '.join(missing)}")


def check_dial_range_is_stated_once():
    """The documented range and the enforced range must be the same numbers.

    They are load-bearing in three places at once - brand_fit warns outside
    them, the --color-heading floors are held above 24px at the bottom of
    them, and TOKENS.md tells brands what is safe. Two of those drifting apart
    is how a contract comes to promise something CI does not check.
    """
    # Normalised: the document is wrapped prose, and a check that demanded an
    # unwrapped phrase would be a check fighting the format it reads.
    doc = " ".join((ROOT / "TOKENS.md").read_text(encoding="utf-8").split())
    for label, lo, hi in (("--type-scale", dials.TYPE_MIN, dials.TYPE_MAX),
                          ("--space-scale", dials.SPACE_MIN, dials.SPACE_MAX)):
        stated = f"Supported range `{lo}` to `{hi}`"
        if stated not in doc:
            find(ROOT / "TOKENS.md", "contract",
                 f"{label} is enforced over {lo}-{hi} but TOKENS.md does not "
                 f"say so - it must contain the exact words {stated!r}")
    if heading_size.TYPE_MIN != dials.TYPE_MIN:
        find(ROOT / "ci", "contract",
             f"the heading-size check holds floors above the bar at "
             f"{heading_size.TYPE_MIN} but the dial range starts at "
             f"{dials.TYPE_MIN} - the guarantee and the range must agree")


def check_containment(html, css, name):
    """A pattern pulls nothing in from elsewhere, and spaces on the brand ramp.

    The banned-tag list already stops <iframe>, <object>, <embed> and <link>,
    but nothing checked URLs - so the same reach was available through
    @import, @font-face, background-image, an img on a third-party host, a
    srcset entry, or <use href> into a remote sprite.

    And --space-scale is applied by the brand at the ramp, so a hardcoded
    length silently removes that band from the brand's spacing system. See
    ci/_containment.py.
    """
    for text, kind, path in ((html, "html", PATTERNS / name / "pattern.html"),
                             (css, "css", PATTERNS / name / "pattern.css")):
        for what, why in external_faults(text, kind):
            find(path, "no-embedded-content", f"{what} - {why}")
    for line, decl in spacing_faults(css):
        find(PATTERNS / name / "pattern.css", "token-only",
             f"line {line}: '{decl}' sets spacing in a length rather than the "
             f"--space-* ramp, so this band opts out of the brand's rhythm and "
             f"of --space-scale with it")


def check_heading_token_size(css, name):
    """--color-heading only where it is guaranteed, across the whole dial range.

    The token carries 3:1 and no more, so it is valid only on large text. Six
    patterns cleared that bar by landing exactly on 24px, which stopped being
    true the moment a brand could multiply it - and a seventh reached the
    token through a ground modifier, where the obvious version of this check
    could not see it at all. See ci/_heading_size.py.
    """
    for selector, floor, bar, at_min in heading_size_faults(css):
        find(PATTERNS / name / "pattern.css", "heading-token",
             f"{selector}: --color-heading at a {floor:.0f}px floor renders "
             f"{at_min:.1f}px at --type-scale 0.9, under the {bar:.2f}px this "
             f"token is guaranteed at. Raise the clamp floor so it clears the "
             f"bar across the documented dial range, or take --color-text")


def check_display_type_carries_the_dial(css, name):
    """Every display size must be multiplied by --type-scale.

    The dial is worth nothing if a pattern can quietly opt out of it: one
    hard-coded headline on a page is the one that does not move when a brand
    turns the register up, and it reads as a mistake rather than a choice.

    The rule this enforces is in TOKENS.md, and resolving it needs the whole
    file rather than one rule - see ci/_display_type.py, which also records
    what the first version of this check could not see.
    """
    for selector, value, why in display_faults(css):
        find(PATTERNS / name / "pattern.css", "type-scale",
             f"{selector}: display size {value} does not carry the dial - {why}")


def main():
    check_only = "--check" in sys.argv
    if not PATTERNS.is_dir():
        print("no patterns/ directory", file=sys.stderr)
        return 1

    # Whole-repo sweep: the leak scan and the control-byte scan both belong
    # here rather than per-pattern. The byte check used to run on four files
    # per pattern and nothing else, leaving the sample token sets, the
    # behaviour library and every root document uncovered.
    needles = leak_needles()
    if needles is None:
        # A pull request from a fork cannot be given the secret, so the scan
        # is skipped there deliberately and runs on the merge to main instead.
        # Anywhere else, a missing list is a failure: a check that reports
        # clean without running is worse than no check.
        if os.environ.get("LANDER_LEAK_SKIP", "").lower() == "true":
            print("leak scan skipped: fork pull request, runs again on merge",
                  file=sys.stderr)
        else:
            find(ROOT / "ci" / "lint.py", "leak-scan",
                 "no needle list supplied - set LANDER_LEAK_NEEDLES or create "
                 "ci/leak-needles.local. Refusing to report clean on a check "
                 "that did not run")
    generated = ROOT / "preview" / "site"
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        # Skip only the generated preview output, matched by path rather than
        # by a path segment named "site".
        if generated in path.parents:
            continue
        if path.suffix in (".md", ".html", ".css", ".json", ".yml", ".yaml",
                           ".py", ".js", ".svg", ".txt", ".sh", ".toml", ""):
            if needles:
                check_leaks(path, needles)
            check_control_bytes(path)

    check_token_sets_are_complete()

    rows = []
    manifest = {}
    names = set()
    cross_refs = []
    avoids, avoid_paths = {}, {}
    CONTRACT = contract_tokens()
    if not CONTRACT:
        find(ROOT / "TOKENS.md", "contract",
             "no tokens parsed from TOKENS.md - the membership check is blind")
    for folder in sorted(p for p in PATTERNS.iterdir() if p.is_dir()):
        html = folder / "pattern.html"
        css = folder / "pattern.css"
        readme = folder / "README.md"
        preview = folder / "preview-content.json"
        for required in (html, css, readme, preview):
            if not required.is_file():
                find(folder, "layout", f"missing {required.name}")
        # Agents fetch every README they shortlist, so length is a running
        # cost paid on every build. The ceiling stops the drift; the target
        # in CONTRIBUTING.md is about 50.
        if readme.is_file():
            lines = len(readme.read_text(encoding="utf-8").splitlines())
            if lines > README_MAX_LINES:
                find(readme, "readme-length",
                     f"{lines} lines, ceiling is {README_MAX_LINES} - put the "
                     "decision first and cut the restatement")
        if not html.is_file():
            continue

        meta = parse_header(html.read_text(encoding="utf-8"), html)
        slots = check_html(html, meta, folder.name)
        check_list_semantics(html, css, folder.name)
        check_motion_claim(html, css, meta)
        check_edges_documented(readme, meta)
        if css.is_file():
            legibility.check(
                css.read_text(encoding="utf-8"),
                lambda d, _p=css: find(_p, "legibility", d),
                html.read_text(encoding="utf-8"))
        check_comment_policy(html, "html")
        if css.is_file():
            check_comment_policy(css, "css")
        if readme.is_file():
            check_narration(readme)
        check_contract_membership(html, css, folder.name, CONTRACT)
        header_block = re.match(r"\s*<!--\n(.*?)\n-->",
                                html.read_text(encoding="utf-8"), re.S)
        if header_block:
            check_header_comments(html, header_block.group(1))
        if css.is_file():
            check_css(css, folder.name)
            check_display_type_carries_the_dial(
                css.read_text(encoding="utf-8"), folder.name)
            check_heading_token_size(
                css.read_text(encoding="utf-8"), folder.name)
            check_containment(html.read_text(encoding="utf-8"),
                              css.read_text(encoding="utf-8"), folder.name)
            # `tokens-used` names the CONTRACT tokens a pattern consumes. A
            # pattern's own custom properties (--<pattern-name>-*) are its
            # internal plumbing, not part of the contract, so they are
            # ignored on both sides: declaring one is as clean as not.
            local = f"--{folder.name}-"
            declared = set(t.strip() for t in meta.get("tokens-used", "").split(",")
                           if t.strip() and not t.strip().startswith(local))
            used = set(t for t in re.findall(r"var\(\s*(--[\w-]+)",
                                             css.read_text(encoding="utf-8"))
                       if not t.startswith(local))
            if declared != used:
                missing = sorted(used - declared)
                extra = sorted(declared - used)
                detail = []
                if missing:
                    detail.append(f"missing: {', '.join(missing)}")
                if extra:
                    detail.append(f"listed but unused: {', '.join(extra)}")
                find(html, "tokens-used", "; ".join(detail))

        if preview.is_file():
            try:
                sample = json.loads(preview.read_text(encoding="utf-8"))
            except ValueError as e:
                find(preview, "json", str(e))
                sample = {}
            for slot in sorted(slots):
                if slot not in sample:
                    find(preview, "preview-content", f"no sample value for slot '{slot}'")
            for key, value in sample.items():
                # A leading underscore marks builder configuration rather than
                # content - _repeat says how many of an item to render. None of
                # it reaches a page, so the sample rule below does not apply.
                if key.startswith("_"):
                    continue
                text = str(value)
                # A machine-readable value cannot also say "sample" and stay
                # valid, and a datetime attribute is exactly that case. The
                # rule exists so no preview value can be mistaken for a real
                # claim about a brand, and a bare date makes none.
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}(T[\d:.+-]+)?", text):
                    continue
                if "sample" not in text.lower() and "preview" not in text.lower():
                    find(preview, "preview-content",
                         f"value for '{key}' must self-declare as sample/preview")

        name = meta.get("name", folder.name)
        if name in names:
            find(html, "header", f"duplicate pattern name '{name}'")
        names.add(name)
        for field in ("pairs-with", "avoid-with", "replaced-by"):
            value = meta.get(field, "")
            for ref in [r.strip() for r in value.split(",") if r.strip()]:
                if ref == "none":
                    continue
                if ref == name:
                    find(html, "cross-ref", f"{field} names the pattern itself")
                    continue
                cross_refs.append((html, field, ref))
                if field == "avoid-with":
                    avoids.setdefault(name, set()).add(ref)
                    avoid_paths[name] = html
        # The index is where an agent shortlists, so a cardinality limit has
        # to be visible here - inside the pattern folder it arrives after the
        # decision it was meant to inform.
        limit = " · **one per page**" if meta.get("one-per-page") == "yes" else ""
        # The index is where an agent shortlists, so every field the choice runs
        # on has to be visible here. content-shape is the skill's own vocabulary
        # for picking a composition; needs is the gate that closes a pattern
        # when the brand has no material for it, and inside the folder it
        # arrives thousands of tokens after the decision it was meant to
        # inform; behaviours decides whether the brand needs the bundle at all.
        shape = meta.get("content-shape", "")
        beh = meta.get("behaviours", "")
        needs = meta.get("needs", "")
        manifest[name] = {
            "version": meta.get("version"),
            "type": meta.get("type"),
            "page-types": [s.strip() for s in meta.get("page-types", "").split(",") if s.strip()],
            "content-shape": shape,
            "requires": meta.get("requires", "none"),
            "whole-page": meta.get("whole-page") == "yes",
            "one-per-page": meta.get("one-per-page") == "yes",
            "needs": needs,
            "avoid-with": [s.strip() for s in meta.get("avoid-with", "").split(",")
                           if s.strip() and s.strip() != "none"],
            "pairs-with": [s.strip() for s in meta.get("pairs-with", "").split(",")
                           if s.strip() and s.strip() != "none"],
            "behaviours": [s.strip() for s in beh.split(",") if s.strip()],
            "motion": meta.get("motion"),
            "description": meta.get("description", ""),
        }
        rows.append(
            f"- **{name}** v{meta.get('version', '?')} · {meta.get('type', '?')} · "
            f"{meta.get('page-types', '?')}{limit} · {meta.get('description', '?')}"
        )

    # The behaviour library injects CSS into every page that gets it, so its
    # stylesheet reaches brands exactly as a pattern's does. It goes through
    # the same check rather than a simpler one beside it: a second
    # implementation is a second set of holes.
    hub = ROOT / "lib" / "hub.js"
    if hub.is_file():
        js = hub.read_text(encoding="utf-8")
        # Every template literal that looks like a stylesheet, not only the
        # ones under a `css:` key - a behaviour can push styles from anywhere.
        for block in re.findall(r"`([^`]*)`", js):
            # A stylesheet, not a message: an interpolated literal is a JS
            # string, and a real block has a declaration in it.
            # An interpolation used to skip the whole block, which put this
            # stylesheet one `${delay}` away from switching its own checks
            # off. Blank the interpolated spans and check what surrounds them.
            block = re.sub(r"\$\{[^{}]*\}", "0", block)
            if not re.search(r"\{[^{}]*[\w-]+\s*:", block):
                continue
            check_css(hub, "hub", block)
        # legibility.check is deliberately NOT run here. Its rule is that a
        # pattern may not hide content and wait for a script; this file IS
        # the script, and hiding a panel is the whole of what it does.

    check_dial_range_is_stated_once()
    check_version_bumps(sorted(p for p in PATTERNS.iterdir() if p.is_dir()))

    for path, field, ref in cross_refs:
        if ref not in names:
            find(path, "cross-ref", f"{field} names unknown pattern '{ref}'")

    # `avoid-with` says two patterns fight each other, which is not a thing
    # one of them can be true about on its own. A one-sided entry means an
    # agent reading the other pattern never learns about the clash.
    for name, targets in avoids.items():
        for ref in sorted(targets):
            if ref in names and name not in avoids.get(ref, set()):
                find(avoid_paths[name], "avoid-with",
                     f"'{name}' avoids '{ref}' but '{ref}' does not avoid "
                     f"'{name}' - avoid-with is mutual")

    index_text = (
        "# Pattern index\n\n"
        "One line per pattern - generated by `ci/lint.py`, never hand-edited.\n"
        "Shortlist here, then read only the chosen pattern's folder.\n\n"
        + "\n".join(rows) + "\n"
    )
    if check_only:
        current = INDEX.read_text(encoding="utf-8") if INDEX.is_file() else ""
        if current != index_text:
            find(INDEX, "stale-index", "INDEX.md does not match the patterns; run ci/lint.py")
    elif not findings:
        INDEX.write_text(index_text, encoding="utf-8", newline="\n")
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                            encoding="utf-8", newline="\n")

    if findings:
        print("\n".join(findings))
        print(f"\n{len(findings)} finding(s).")
        return 1
    print(f"clean: {len(rows)} pattern(s); INDEX.md {'checked' if check_only else 'written'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
