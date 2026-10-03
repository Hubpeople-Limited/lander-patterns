#!/usr/bin/env python3
"""Run the section behaviours for real, and hold each to its registry row.

Every behaviour in `lib/hub.js` is a promise in `lib/REGISTRY.md`, and until
this gate nothing ran the section behaviours at all: the phone gate renders
with no script on purpose, and the header gate runs the bundle for the header
alone. A behaviour that mangles a figure, marks the wrong link or builds no
control passes every other check, because every other check reads the page as
authored.

So this gate puts each pattern that declares one of the section behaviours in
a page with the bundle, launched with file access allowed so the module
script actually runs, proves the bundle ran by reading its version off the
page, and holds each behaviour to what its row says:

    reveal     still on a pattern's default rung and easing in on its moving
               rung; the markup and styles of the last release before the
               switch ease in as they always did
    counter    a figure ends on the authored text, byte for byte, with its
               prefix, separators, decimals and suffix; it moved on the way
               there; under reduced motion it never moves; with no bundle the
               authored figure is the page
    scrollspy  the link whose heading the reader passed last carries
               aria-current and the state class, exactly one at a time, and
               none above the first heading
    carousel   two controls are built inside the block and none ship in the
               authored render; next moves the slide and previous moves it
               back, wrapping on a radio carousel and disabling at the ends
               of a scroller; the controls are thumb-sized at a phone width,
               and they hold their place while the carousel is operated -
               a control that moves as the rail does is one the reader has
               to chase, and it passes every other check on this list
    signup     a phone opens on one question; Next with nothing chosen stays
               and says why; a tapped answer moves on by itself; members
               show once "looking for" is answered and never after a failed
               search; the hand-off goes to the join link with the answers
               summed, spaces as %20, never "+", interests as a %3B list and
               no password, and it carries what every join link carries -
               the page's own parameters and its pn; under reduced motion it
               still moves on; a card given places asks where straight after
               "looking for", offers a big region's towns as the visitor types
               (its biggest from the first tap) and a small region's as a list,
               narrows the members to the town picked and sends its lat and
               long, and a card whose places will not load simply goes on;
               the town field is a named combobox over its own list, with an
               autocomplete word a browser's address autofill does not take;
               the line after an answer goes when the visitor goes back;
               a page in another language keeps its answers' capitals in
               the answers so far;
               dob and dob-wide give the wheel at one width and the boxes at
               the other, keeping a date across the switch, and dob-start
               opens the year wheel at an age with day and month blank

    python ci/check_behaviours.py                  every pattern declaring one
    python ci/check_behaviours.py stats-band
    python ci/check_behaviours.py --broken         the positive control, below
    python ci/check_behaviours.py --out /tmp/beh   keep the rendered pages
    python ci/check_behaviours.py --require-browser
    python ci/check_behaviours.py --compat         the bundle against the last one published
    python ci/check_behaviours.py --compat --broken   its positive control

THE POSITIVE CONTROL. `--broken` writes a COPY of the bundle with one named
line of each behaviour turned wrong - the counter's last write, the
scrollspy's aria-current, the carousel's move, the still switch - and
requires every one of the checks to fire. The file in lib/ is never touched.
A substitution that no longer matches is itself a failure, so the control
cannot go quietly stale when a behaviour is reworded.

WHICH PATTERNS. Discovered from the `behaviours:` header of every pattern:
anything declaring `reveal`, `counter`, `scrollspy` or `carousel`. A new
pattern taking one of them is measured the day it lands.

Exit codes: 0 clean, or skipped because no browser is available; 1 at least
one behaviour does not do what its row says; 2 the request itself is unusable.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"
PREVIEW = ROOT / "preview"
BUNDLE = ROOT / "lib" / "hub.js"

from build_preview import fill, repeat_block            # noqa: E402
from check_page import apply_variants                   # noqa: E402
from check_phone import browser_unavailable             # noqa: E402
import lint                                             # noqa: E402

BEHAVIOURS = ("counter", "scrollspy", "carousel", "signup", "reveal")
# The last release before motion became a switch. Pages built from it keep
# that markup and those styles and load the bundle from the floating URL,
# so the bundle is held to moving them exactly as it did.
LIVE_REF = "v213"
WIDTH, HEIGHT = 1280, 800
PHONE = 360
TAP_MIN = 44
# How far a control a behaviour builds may travel while its carousel is
# operated. Not zero: a scrollbar appearing or a snap settling can shift a row
# by a pixel or two, and a gate that fails on that teaches people to ignore it.
CONTROL_DRIFT_MAX = 4
# Past the counter's default duration, with room for a slow runner.
COUNTER_SETTLE_MS = 2600
# The figures a real brand writes: a grouped integer with a suffix, a
# decimal, a percentage, and a big grouped number. Each one has to come
# back exactly.
FIGURES = ("12,500+", "4.8", "98%", "1,000,000")
FILLER = "<p>Filler copy so the page scrolls, used only to render this check.</p>\n" * 12

# How long after a block comes into view a moving one has visibly moved.
MOTION_LOOK_MS = 300

MOTION_JS = """
() => ({
  revealed: document.querySelectorAll('.hub-reveal-pending, .hub-revealed').length,
  pending: document.querySelectorAll('.hub-reveal-pending').length,
  figures: Array.from(document.querySelectorAll('[data-hub-module~="counter"] dt'))
                .map(dt => dt.textContent),
  marquee: document.querySelectorAll('.hub-marquee-control, [data-hub-marquee-copy]').length,
})
"""

# The three behaviours that move a block for effect, each on the smallest
# block that shows it moving.
STILL_BLOCKS = {
    "reveal": '<ul data-hub-module="reveal" data-hub-reveal-children>'
              '<li>Sample one</li><li>Sample two</li></ul>',
    "counter": f'<dl data-hub-module="counter"><dt>{FIGURES[0]}</dt>'
               '<dd>Sample figure</dd></dl>',
    "marquee": '<div data-hub-module="marquee"><ul><li>Sample one</li>'
               '<li>Sample two</li><li>Sample three</li></ul></div>',
}
# (what the page's styles say, those styles, whether the block moves). The
# first is every page built before the switch.
STILL_STATES = (
    ("styles that never mention it", "", True),
    ("--hub-motion: none on the block", "[data-hub-module] { --hub-motion: none; }", False),
    ("--hub-motion: none on a section around it", ".still-around { --hub-motion: none; }", False),
    ("--hub-motion set to another word", "[data-hub-module] { --hub-motion: moving; }", True),
)

# One line per behaviour, turned wrong by the control. Each must still be
# present in the bundle, or the control has gone stale and says so.
CONTROL_SUBSTITUTIONS = {
    "counter": ("target.textContent = item.authored;",
                'target.textContent = "0";'),
    "scrollspy": ('current.a.setAttribute("aria-current", "true");',
                  'current.a.setAttribute("data-hub-broken", "true");'),
    "carousel": ("group[index].checked = true;",
                 "group[index].checked = group[index].checked;"),
    "carousel-scroller": ("scroller.scrollBy({ left: step * stepSize(), behavior });",
                          "void step;"),
    "signup": (".reduce((sum, r) => sum + Number(r.value), 0)",
               ".reduce((sum, r) => Number(r.value), 0)"),
    "signup-attribution": ("new URLSearchParams(location.search).forEach((v, k) => first(k, v));",
                           "void first;"),
    "signup-location": ('else if (where.at) { set("lat", where.at[0]); set("long", where.at[1]); }',
                        "else void where;"),
    "signup-postal": ('if (where.zip) set("zipCode", where.zip);', "if (where.zip) void where;"),
    "signup-town-autofill": ('town.setAttribute("autocomplete", "none");',
                             'town.setAttribute("autocomplete", "off");'),
    "signup-messages": ("const fresh = pool.filter((l) => !saidLines.has(l));",
                        "const fresh = pool;"),
    "signup-messages-back": ("if (dir < 0) cheer.hidden = true;", "if (dir < 0) void cheer;"),
    "signup-summary-case": ('.map(words).filter(Boolean).join(" & ")[english ? "toLowerCase" : "toString"]() : "";',
                            '.map(words).filter(Boolean).join(" & ").toLowerCase() : "";'),
    "signup-dob-wide": ('const dobWay = () => (optAt("dob") === "wheel" ? "wheel" : "boxes");',
                        'const dobWay = () => (opt("dob") === "wheel" ? "wheel" : "boxes");'),
    "still": ('const heldStill = (el) => getComputedStyle(el).getPropertyValue("--hub-motion").trim() === "none";',
              "const heldStill = (el) => false;"),
}

# The signup check hands off to this link and never follows it; the GUID in it
# is what the member strip searches with, and the search is answered here.
SIGNUP_JOIN = "https://example.invalid/s/register/00000000-0000-4000-8000-000000000000"
# The places the location step reads: the library's own, served from here.
SIGNUP_PLACES = "https://example.invalid/places/"
# The encouraging lines, served from here the same way.
SIGNUP_MESSAGES = "https://example.invalid/messages/"
# A pattern whose default rung does not scroll carries the carousel for another
# rung, and is measured on that one: the class to swap, and the element to
# repeat until the row is wider than a wide screen.
CAROUSEL_RUNGS = {
    "member-grid": ("member-grid--grid", "member-grid--rail", "mem-card", 12),
}
CAROUSEL_HOOK = re.compile(r'data-hub-module="[^"]*\bcarousel\b[^"]*"')
# A pattern whose moving rung glides by itself is measured on its still rung,
# the row the visitor drives with the controls; its glide is test_gates.py's.
CAROUSEL_MOTION = {"portrait-row": "default"}
# The town field's autocomplete word. Chrome treats `on`, `off` and `false` as
# no word at all and goes on to guess the field from its label - "Town or
# city" reads as an address, so the visitor's saved addresses cover the
# card's own list - while a word it does not recognise turns its address
# suggestions and filling off for that field (components/autofill:
# FieldTypeFromAutocompleteAttributeValue, ShouldSuppressSuggestionsAnd-
# FillingByDefault). It must also be one an accessibility checker accepts as
# a state rather than flagging it as a misspelt purpose: axe-core's
# autocomplete-valid takes these.
TOWN_AUTOCOMPLETE_IGNORED = {"", "on", "off", "false"}
TOWN_AUTOCOMPLETE_ACCEPTED = {"none", "disabled", "xoff", "true", "enabled", "undefined",
                              "null", "xon"}
TOWN_JS = """
el => {
  const list = document.getElementById(el.getAttribute('aria-controls') || '');
  return { role: el.getAttribute('role'), autocomplete: el.getAttribute('autocomplete'),
           ariaAutocomplete: el.getAttribute('aria-autocomplete'),
           expanded: el.getAttribute('aria-expanded'),
           listRole: list ? list.getAttribute('role') : null,
           name: el.getAttribute('name'), id: el.id,
           label: el.labels && el.labels.length ? el.labels[0].textContent.trim() : '' };
}
"""
SIGNUP_MEMBERS = [{"MemberName": f"Sample {i}", "MemberImage": f"sample-portrait.svg?m={i}",
                   "MemberAge": 28 + i, "Interests": ""} for i in range(12)]

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{tokens}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: var(--font-body); background: var(--color-bg);
       color: var(--color-text); line-height: 1.6; }}
.behaviour-check-section {{ min-height: 900px; padding: 24px 16px; }}
{css}
</style>
<script type="module" src="{bundle}"></script>
</head>
<body>
{before}
{markup}
{after}
</body>
</html>
"""


def bundle_version():
    m = re.search(r'version:\s*"([\d.]+)"', BUNDLE.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def pattern_meta(name):
    path = PATTERNS / name / "pattern.html"
    return lint.parse_header(path.read_text(encoding="utf-8"), path)


def declared(name):
    return {b.strip() for b in pattern_meta(name).get("behaviours", "").split(",") if b.strip()}


def has_switch(meta):
    return "moving" in (lint.parse_variants(meta.get("variants", "")) or {}).get("motion", [])


def discover():
    out = {}
    for folder in sorted(p for p in PATTERNS.iterdir() if p.is_dir()):
        have = declared(folder.name) & set(BEHAVIOURS)
        if have:
            out[folder.name] = have
    return out


def filled_markup(name, source=None):
    """The pattern filled with its sample. `source` is (pattern.html,
    pattern.css) from another release; by default the files in the tree."""
    folder = PATTERNS / name
    html, css = source or ((folder / "pattern.html").read_text(encoding="utf-8"),
                           (folder / "pattern.css").read_text(encoding="utf-8"))
    markup = re.sub(r"\s*<!--\n.*?\n-->", "", html, count=1, flags=re.S)
    sample_path = folder / "preview-content.json"
    sample = (json.loads(sample_path.read_text(encoding="utf-8"))
              if sample_path.exists() else {})
    filled = fill(markup, sample)
    repeat = sample.get("_repeat")
    if repeat:
        filled = repeat_block(filled, repeat["class"], int(repeat["count"]))
    return filled, css


def with_figures(filled):
    """Real figures in the dt slots, one of each shape, cycling."""
    i = [0]

    def swap(m):
        text = FIGURES[i[0] % len(FIGURES)]
        i[0] += 1
        return m.group(1) + text + m.group(3)
    return re.sub(r"(<dt\b[^>]*>)(.*?)(</dt>)", swap, filled, flags=re.S)


def page_for(name, behaviour, tokens, bundle_file, width, rung="moving", source=None):
    """The pattern in a page shaped so the behaviour has something to do."""
    filled, css = filled_markup(name, source)
    meta = pattern_meta(name)
    # Every check measures a pattern that offers the switch on its moving
    # rung unless it asks for another; a release's own markup is taken as
    # it shipped.
    if source is None and rung and has_switch(meta):
        filled = apply_variants(name, meta, filled, {"motion": rung})
    before = after = ""
    if behaviour == "counter":
        filled = with_figures(filled)
        before = '<section class="behaviour-check-section"><h1>Above</h1>' + FILLER + "</section>"
    elif behaviour == "scrollspy":
        # Four entries pointing at four headings spaced down the page.
        item = re.search(r"<li class=\"article-toc-item\">.*?</li>", filled, re.S).group(0)
        entries = "".join(
            re.sub(r'href="[^"]*"', f'href="#hub-s{k}"', item).replace(
                re.search(r"<a[^>]*>(.*?)</a>", item, re.S).group(1), f"Section {k}")
            for k in range(1, 5))
        filled = filled.replace(item, entries)
        after = "".join(
            f'<section class="behaviour-check-section"><h2 id="hub-s{k}">Section {k}</h2>'
            + FILLER + "</section>" for k in range(1, 5))
    elif behaviour == "carousel":
        if name in CAROUSEL_RUNGS:
            default, rung, item, count = CAROUSEL_RUNGS[name]
            if default not in filled:
                raise SystemExit(f"carousel: {name} no longer ships {default!r} - "
                                 f"re-pick the rung CAROUSEL_RUNGS measures it on")
            filled = repeat_block(filled.replace(default, rung, 1), item, count)
        after = '<section class="behaviour-check-section">' + FILLER + "</section>"
    elif behaviour == "signup":
        # The preview fill writes "#" for the join link; the check needs a
        # real-shaped one, because the member search reads its GUID from it.
        filled = re.sub(r'(<form class="(?:signup-steps-card|signup-card-form)"[^>]*action=")[^"]*"',
                        lambda m: m.group(1) + SIGNUP_JOIN + '"', filled, count=1)
        after = '<section class="behaviour-check-section">' + FILLER + "</section>"
    return SHELL.format(title=f"{name} {behaviour}", tokens=tokens, css=css,
                        bundle=bundle_file, before=before, markup=filled, after=after)


# ---------------------------------------------------------------- measures

VERSION_JS = "() => (window.HubBehaviours && window.HubBehaviours.version) || null"

COUNTER_JS = """
() => Array.from(document.querySelectorAll('[data-hub-module~="counter"] dt'))
        .map(dt => dt.textContent)
"""

SCROLLSPY_JS = """
() => Array.from(document.querySelectorAll('[data-hub-module~="scrollspy"] a[href^="#"]'))
        .map(a => ({ href: a.getAttribute('href'),
                     current: a.getAttribute('aria-current'),
                     marked: a.classList.contains('hub-scrollspy-current') }))
"""

CAROUSEL_JS = """
() => {
  const block = document.querySelector('[data-hub-module~="carousel"]');
  const prev = block && block.querySelector('.hub-carousel-prev');
  const next = block && block.querySelector('.hub-carousel-next');
  const radios = block ? Array.from(block.querySelectorAll('input[type="radio"]')) : [];
  const scroller = block && (/^(auto|scroll)$/.test(getComputedStyle(block).overflowX)
    ? block : Array.from(block.querySelectorAll('ul, ol'))
        .find(l => /^(auto|scroll)$/.test(getComputedStyle(l).overflowX)));
  const box = el => { if (!el) return null; const r = el.getBoundingClientRect();
                      return [Math.round(r.width), Math.round(r.height)]; };
  return {
    controls: !!(prev && next), prevBox: box(prev), nextBox: box(next),
    prevDisabled: prev ? prev.getAttribute('aria-disabled') : null,
    nextDisabled: next ? next.getAttribute('aria-disabled') : null,
    checked: radios.findIndex(r => r.checked), radios: radios.length,
    scrollLeft: scroller ? Math.round(scroller.scrollLeft) : null,
    scrollMax: scroller ? Math.round(scroller.scrollWidth - scroller.clientWidth) : null,
  };
}
"""


class Shell:
    def __init__(self, broken):
        self.broken = broken

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=True, args=["--allow-file-access-from-files"])
        self._dir = Path(tempfile.mkdtemp(prefix="lander-behaviours-"))
        for asset in PREVIEW.glob("*.svg"):
            shutil.copy(asset, self._dir / asset.name)
        source = BUNDLE.read_text(encoding="utf-8")
        if self.broken:
            for key, (old, new) in CONTROL_SUBSTITUTIONS.items():
                if old not in source:
                    raise SystemExit(f"control: the {key} substitution no longer matches "
                                     f"lib/hub.js - re-pick the line {old!r}")
                source = source.replace(old, new, 1)
        (self._dir / "hub.js").write_text(source, encoding="utf-8", newline="\n")
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()
        shutil.rmtree(self._dir, ignore_errors=True)
        return False

    def open(self, html, stem, width=WIDTH, reduced=False, before=None, query=""):
        path = self._dir / f"{stem}.html"
        path.write_text(html, encoding="utf-8", newline="\n")
        tab = self._browser.new_page(
            viewport={"width": width, "height": HEIGHT}, device_scale_factor=1,
            reduced_motion="reduce" if reduced else "no-preference")
        if before:
            before(tab)
        tab.goto(path.as_uri() + query)
        return tab


def check_counter(shell, name, tokens):
    faults = []
    where = f"{name} counter"
    html = page_for(name, "counter", tokens, "hub.js", WIDTH)
    tab = shell.open(html, f"{name}-counter")
    try:
        version = tab.evaluate(VERSION_JS)
        if version != bundle_version():
            return [f"{where}: the bundle did not run (version {version!r} on the page)"]
        # Bring the figures on screen and read them at once, before the
        # count has finished.
        tab.evaluate("() => document.querySelector('[data-hub-module~=\"counter\"]').scrollIntoView()")
        tab.wait_for_timeout(120)
        early = tab.evaluate(COUNTER_JS)
        tab.wait_for_timeout(COUNTER_SETTLE_MS)
        final = tab.evaluate(COUNTER_JS)
    finally:
        tab.close()
    expected = [FIGURES[i % len(FIGURES)] for i in range(len(final))]
    if not final:
        return [f"{where}: no figure found under the counter hook"]
    for i, (got, want) in enumerate(zip(final, expected)):
        if got != want:
            faults.append(f"{where}: figure {i + 1} ends as {got!r} where the page "
                          f"authored {want!r} - the last write is the authored text")
    if early == expected:
        faults.append(f"{where}: no figure had moved 120ms after arriving - the count "
                      f"never ran")
    # Reduced motion: never moves.
    tab = shell.open(html, f"{name}-counter-reduced", reduced=True)
    try:
        tab.evaluate("() => document.querySelector('[data-hub-module~=\"counter\"]').scrollIntoView()")
        tab.wait_for_timeout(150)
        still = tab.evaluate(COUNTER_JS)
    finally:
        tab.close()
    if still != expected:
        faults.append(f"{where}: under reduced motion the figures read {still!r} - "
                      f"the authored figure is the only one allowed")
    faults += motion_faults(shell, name, tokens, "counter")
    return faults


def movement(shell, html, stem, late_css=None):
    """What moved once the first behaviour block had been on screen a
    moment, or None when the bundle did not run. `late_css` arrives after
    the bundle has started, as a slow stylesheet would."""
    tab = shell.open(html, stem)
    try:
        if tab.evaluate(VERSION_JS) != bundle_version():
            return None
        if late_css:
            tab.add_style_tag(content=late_css)
        tab.evaluate("() => document.querySelector('[data-hub-module]').scrollIntoView()")
        tab.wait_for_timeout(MOTION_LOOK_MS)
        return tab.evaluate(MOTION_JS)
    finally:
        tab.close()


def moved(behaviour, got):
    if behaviour == "reveal":
        return got["revealed"] > 0
    if behaviour == "counter":
        return got["figures"] != [FIGURES[i % len(FIGURES)] for i in range(len(got["figures"]))]
    return got["marquee"] > 0


def motion_faults(shell, name, tokens, behaviour):
    """Still on the default rung, moving on its moving rung, and moving on
    the markup and styles LIVE_REF shipped."""
    runs = []
    if has_switch(pattern_meta(name)):
        runs += [("motion=default", page_for(name, behaviour, tokens, "hub.js", WIDTH,
                                             rung="default"), False),
                 ("motion=moving", page_for(name, behaviour, tokens, "hub.js", WIDTH,
                                            rung="moving"), True)]
    else:
        runs.append(("as shipped", page_for(name, behaviour, tokens, "hub.js", WIDTH), True))
    source = shipped(name)
    if source is not None:
        was = lint.parse_header(source[0], PATTERNS / name / "pattern.html")
        if behaviour in {b.strip() for b in was.get("behaviours", "").split(",")}:
            runs.append((f"as {LIVE_REF} shipped it",
                         page_for(name, behaviour, tokens, "hub.js", WIDTH,
                                  source=source[:2]),
                         True))
    faults = []
    for i, (label, html, want) in enumerate(runs):
        got = movement(shell, html, f"{name}-{behaviour}-motion-{i}")
        if got is None:
            return [f"{name} {behaviour}: the bundle did not run"]
        if moved(behaviour, got) != want:
            faults.append(f"{name} {behaviour}: {label} " + (
                "stayed still - it has to move" if want
                else "moved - still means nothing moves"))
    return faults


def check_reveal(shell, name, tokens):
    return motion_faults(shell, name, tokens, "reveal")


def check_still_means_still(shell, tokens):
    """A block that sets or inherits --hub-motion: none is left as authored;
    a page whose styles never set it moves exactly as it always has."""
    faults = []
    after = '<section class="behaviour-check-section">' + FILLER + "</section>"
    for behaviour, block in STILL_BLOCKS.items():
        for i, (label, css, want) in enumerate(STILL_STATES):
            html = SHELL.format(title=f"still {behaviour}", tokens=tokens, css=css,
                                bundle="hub.js", before="",
                                markup=f'<section class="still-around">{block}</section>',
                                after=after)
            got = movement(shell, html, f"still-{behaviour}-{i}")
            if got is None:
                return [f"still {behaviour}: the bundle did not run"]
            if moved(behaviour, got) != want:
                faults.append(f"still {behaviour}: with {label} it " + (
                    "stayed still - a page that never set the switch moves as it always did"
                    if want else "moved - a block built still stays still"))
    # Styles that arrive after the bundle has started: the block moves as it
    # would have, and nothing it hid is left hidden.
    html = SHELL.format(title="still late", tokens=tokens, css="", bundle="hub.js",
                        before="", after=after,
                        markup=f'<section class="still-around">{STILL_BLOCKS["reveal"]}</section>')
    got = movement(shell, html, "still-late",
                   late_css="[data-hub-module] { --hub-motion: none; }")
    if got is None or got["pending"]:
        faults.append("late reveal: styles that arrived after the bundle left "
                      f"{got['pending'] if got else 'the page'} hidden")
    return faults


def check_scrollspy(shell, name, tokens):
    where = f"{name} scrollspy"
    html = page_for(name, "scrollspy", tokens, "hub.js", WIDTH)
    tab = shell.open(html, f"{name}-scrollspy")
    try:
        version = tab.evaluate(VERSION_JS)
        if version != bundle_version():
            return [f"{where}: the bundle did not run (version {version!r} on the page)"]
        top = tab.evaluate(SCROLLSPY_JS)
        tab.evaluate("() => { const h = document.getElementById('hub-s3'); "
                     "window.scrollTo(0, h.offsetTop - 40); }")
        tab.wait_for_timeout(150)
        mid = tab.evaluate(SCROLLSPY_JS)
    finally:
        tab.close()
    faults = []
    if not top or len(top) < 4:
        return [f"{where}: fewer than four contents links were built ({len(top)})"]
    if any(l["current"] or l["marked"] for l in top):
        faults.append(f"{where}: a link is current at the top of the page, above "
                      f"the first heading")
    current = [l["href"] for l in mid if l["current"] == "true" and l["marked"]]
    if current != ["#hub-s3"]:
        faults.append(f"{where}: with the third heading passed, the current link(s) "
                      f"read {current} - one link, #hub-s3, should carry aria-current "
                      f"and the state class")
    return faults


def press(tab, which):
    """A DOM click, not a pointer click: the driver refuses to click a control
    carrying aria-disabled, and a disabled control ignoring a press is one of
    the things this gate has to be able to see."""
    tab.evaluate("w => document.querySelector('[data-hub-module~=\"carousel\"] .hub-carousel-' + w).click()", which)


def check_carousel(shell, name, tokens):
    where = f"{name} carousel"
    faults = []
    html = page_for(name, "carousel", tokens, "hub.js", WIDTH, rung=CAROUSEL_MOTION.get(name, "moving"))
    tab = shell.open(html, f"{name}-carousel")
    try:
        version = tab.evaluate(VERSION_JS)
        if version != bundle_version():
            return [f"{where}: the bundle did not run (version {version!r} on the page)"]
        tab.wait_for_timeout(100)
        first = tab.evaluate(CAROUSEL_JS)
        if not first["controls"]:
            return [f"{where}: no previous and next controls were built inside the block"]
        press(tab, "next")
        tab.wait_for_timeout(600)
        after_next = tab.evaluate(CAROUSEL_JS)
        press(tab, "prev")
        tab.wait_for_timeout(600)
        after_prev = tab.evaluate(CAROUSEL_JS)
        if first["radios"]:
            press(tab, "prev")
            tab.wait_for_timeout(100)
            wrapped = tab.evaluate(CAROUSEL_JS)
        else:
            wrapped = None
            # Walk to the end and expect the next control to disable.
            for _ in range(12):
                press(tab, "next")
                tab.wait_for_timeout(350)
            end = tab.evaluate(CAROUSEL_JS)
    finally:
        tab.close()
    if first["radios"]:
        if after_next["checked"] != 1:
            faults.append(f"{where}: next left slide {after_next['checked'] + 1} checked "
                          f"where slide 2 should be")
        if after_prev["checked"] != 0:
            faults.append(f"{where}: previous left slide {after_prev['checked'] + 1} "
                          f"checked where slide 1 should be")
        if wrapped["checked"] != first["radios"] - 1:
            faults.append(f"{where}: previous from the first slide left slide "
                          f"{wrapped['checked'] + 1} checked; it should wrap to the last")
    else:
        if not (after_next["scrollLeft"] or 0) > 0:
            faults.append(f"{where}: next did not move the scroller "
                          f"(scrollLeft {after_next['scrollLeft']})")
        if (after_prev["scrollLeft"] or 0) > 1:
            faults.append(f"{where}: previous did not bring the scroller back "
                          f"(scrollLeft {after_prev['scrollLeft']})")
        if first["prevDisabled"] != "true":
            faults.append(f"{where}: the previous control is not disabled at the start")
        if end["nextDisabled"] != "true":
            faults.append(f"{where}: the next control is not disabled at the end "
                          f"(scrollLeft {end['scrollLeft']} of {end['scrollMax']})")
    # No bundle: nothing built.
    plain = html.replace('<script type="module" src="hub.js"></script>', "")
    tab = shell.open(plain, f"{name}-carousel-plain")
    try:
        tab.wait_for_timeout(100)
        bare = tab.evaluate(CAROUSEL_JS)
    finally:
        tab.close()
    if bare["controls"]:
        faults.append(f"{where}: controls are present with no bundle on the page - "
                      f"the authored render carries none")
    # Phone: thumb-sized controls.
    tab = shell.open(html, f"{name}-carousel-phone", width=PHONE)
    try:
        tab.wait_for_timeout(100)
        phone = tab.evaluate(CAROUSEL_JS)
    finally:
        tab.close()
    for label, box in (("previous", phone["prevBox"]), ("next", phone["nextBox"])):
        if not box or min(box) < TAP_MIN:
            faults.append(f"{where}: the {label} control is {box} at {PHONE}px, under "
                          f"the {TAP_MIN}px thumb target")
    # Phone: the controls hold their place while the carousel is operated. A
    # control that moves as the rail does is one the reader has to chase, and a
    # thumb already travelling towards it lands on a photograph instead. This is
    # the half a working control can still fail: the two above prove it is built,
    # big enough and moves the slide, all of which stay true of a button that
    # will not stay still. Phone width because that is where a control is aimed
    # at rather than clicked, and where the scrollport is narrowest.
    tab = shell.open(html, f"{name}-carousel-stability", width=PHONE)
    try:
        tab.wait_for_timeout(100)
        travel = tab.evaluate(CAROUSEL_STABILITY_JS)
    finally:
        tab.close()
    if travel.get("controls"):
        for label in ("previous", "next"):
            moved = travel["moved"][label]
            if moved > CONTROL_DRIFT_MAX:
                faults.append(
                    f"{where}: the {label} control moves {moved}px across the "
                    f"carousel's range at {PHONE}px, over the {CONTROL_DRIFT_MAX}px "
                    f"a control may travel - it sits at {travel['seen'][label]}")
            if not travel["visible"][label]:
                faults.append(f"{where}: the {label} control leaves the viewport "
                              f"while the carousel is operated")
    # Every placement the registry offers, on this pattern's own markup. A
    # placement is an option a page can set, so each one is a way this pattern
    # can ship: "none" has to build nothing at all, and anything else has to
    # record what it resolved to and still hold its controls still.
    for asked in ("none", "edges"):
        marked = CAROUSEL_HOOK.sub(
            lambda m: f'{m.group(0)} data-hub-carousel-controls="{asked}"', html, count=1)
        tab = shell.open(marked, f"{name}-carousel-controls-{asked}", width=PHONE)
        try:
            tab.wait_for_timeout(100)
            placed = tab.evaluate(CAROUSEL_PLACEMENT_JS)
        finally:
            tab.close()
        used = placed.get("used")
        if asked == "none":
            if placed["controls"]:
                faults.append(f"{where}: controls are built with "
                              f'data-hub-carousel-controls="none"')
            if used != "none":
                faults.append(f'{where}: asked for "none" and recorded "{used}"')
            continue
        if used not in ("edges", "under"):
            faults.append(f'{where}: asked for "edges" and recorded "{used}" - '
                          f"the placement in force is not one the registry offers")
        if not placed["controls"]:
            faults.append(f'{where}: no controls built for "{asked}", which '
                          f"resolved to \"{used}\"")
        elif placed["nameKept"] is not True:
            faults.append(f"{where}: a control in the {used} placement lost its "
                          f"label as its accessible name")
    return faults


CAROUSEL_STABILITY_JS = """
async () => {
  const block = document.querySelector('[data-hub-module~="carousel"]');
  const prev = block && block.querySelector('.hub-carousel-prev');
  const next = block && block.querySelector('.hub-carousel-next');
  if (!prev || !next) return { controls: false };
  const scroller = /^(auto|scroll)$/.test(getComputedStyle(block).overflowX)
    ? block : Array.from(block.querySelectorAll('ul, ol'))
        .find(l => /^(auto|scroll)$/.test(getComputedStyle(l).overflowX));
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const seen = { previous: [], next: [] };
  const vis = { previous: true, next: true };
  const sample = () => {
    for (const [label, el] of [['previous', prev], ['next', next]]) {
      const r = el.getBoundingClientRect();
      seen[label].push(Math.round(r.left));
      if (r.right < 1 || r.left > window.innerWidth - 1) vis[label] = false;
    }
  };
  sample();
  if (scroller) {
    // A scroller moves continuously, so walk its whole range rather than
    // trusting the ends: a control can sit still at both and travel between.
    const max = scroller.scrollWidth - scroller.clientWidth;
    for (const frac of [0.25, 0.5, 0.75, 1]) {
      scroller.scrollLeft = Math.round(max * frac);
      await wait(160);
      sample();
    }
  } else {
    // A radio carousel moves in steps; one full lap covers every state.
    const radios = Array.from(block.querySelectorAll('input[type="radio"]'));
    for (let i = 0; i < Math.max(radios.length, 1); i++) {
      next.click();
      await wait(160);
      sample();
    }
  }
  const spread = xs => Math.max(...xs) - Math.min(...xs);
  return {
    controls: true,
    moved: { previous: spread(seen.previous), next: spread(seen.next) },
    visible: vis,
    seen,
  };
}
"""


CAROUSEL_PLACEMENT_JS = """
() => {
  const block = document.querySelector('[data-hub-module~="carousel"]');
  const prev = block && block.querySelector('.hub-carousel-prev');
  const next = block && block.querySelector('.hub-carousel-next');
  const asked = block ? block.getAttribute('data-hub-carousel-prev-label') : null;
  return {
    used: block ? block.getAttribute('data-hub-carousel-controls-used') : null,
    controls: !!(prev && next),
    // The words stay the control's accessible name in every placement, even
    // where the look replaces them with an arrow.
    nameKept: prev && next
      ? (prev.textContent.trim() === (asked || 'Previous') || prev.textContent.trim().length > 0)
        && next.textContent.trim().length > 0
      : null,
  };
}
"""


SIGNUP_PARTS_JS = """
() => Array.from(document.querySelectorAll('[data-hub-signup-part]'))
        .filter(p => p.offsetParent !== null).map(p => p.getAttribute('data-hub-signup-part'))
"""


def signup_stub(members, searches=None):
    """Answer the member search, serve the places, and keep the hand-off instead
    of following it. `searches`, a list, collects every member search made."""
    def before(tab):
        def answer(route):
            if searches is not None:
                searches.append(route.request.url)
            if members is None:
                route.fulfill(status=502, body="")
            else:
                route.fulfill(status=200, content_type="application/json",
                              headers={"Access-Control-Allow-Origin": "*"},
                              body=json.dumps(members))
        tab.route("**/api/hs/quicksearch**", answer)
        tab.route("https://example.invalid/**", lambda r: r.abort())

        def places(route):
            f = ROOT / "lib" / "places" / route.request.url.rsplit("/", 1)[-1]
            if f.is_file():
                route.fulfill(status=200, content_type="application/json",
                              headers={"Access-Control-Allow-Origin": "*"}, body=f.read_text(encoding="utf-8"))
            else:
                route.fulfill(status=404, body="")
        # Registered after the abort above, so it is asked first.
        tab.route(SIGNUP_PLACES + "**", places)
        tab.add_init_script("addEventListener('hub:signup:handoff', "
                            "e => { window.__signupHandoff = e.detail.url })")
        # The platform's record of the page, as its footer script sets it.
        tab.add_init_script("window.templateInfo = {template_name: 'Canvas Studio', "
                            "page_guid: 'abc123def456', template_lang: 'en', "
                            "template_brand_lang: 'en', is_prod: true}")
    return before


def tap(tab, selector):
    """A real press at the middle of the thing, as a finger makes one - once it
    has stopped moving. A step change scrolls the card up smoothly and the
    member strip can arrive above it, and a press measured mid-move lands on
    whatever slid under it."""
    target = tab.locator(selector).first
    box = target.bounding_box()
    for _ in range(40):
        tab.wait_for_timeout(50)
        again = target.bounding_box()
        if again == box:
            break
        box = again
    tab.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


def check_signup(shell, name, tokens):
    where = f"{name} signup"
    faults = []
    html = page_for(name, "signup", tokens, "hub.js", PHONE)
    face = 'input[name="{0}"][value="{1}"] + .' + name + '-opt-face'
    tab = shell.open(html, f"{name}-signup", width=PHONE, before=signup_stub(SIGNUP_MEMBERS),
                     query="?utm_source=s&utm_medium=m&cmp=abc&gclid=g&cmp=second")
    try:
        tab.wait_for_timeout(300)
        version = tab.evaluate(VERSION_JS)
        if version != bundle_version():
            return [f"{where}: the bundle did not run (version {version!r} on the page)"]
        parts = tab.evaluate(SIGNUP_PARTS_JS)
        if parts != ["iam"]:
            faults.append(f"{where}: a phone opens on {parts!r} - one question, 'iam', is the step")
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(150)
        if tab.evaluate(SIGNUP_PARTS_JS) != ["iam"] or not tab.locator(
                f'[data-hub-signup-part="iam"] .{name}-error').is_visible():
            faults.append(f"{where}: Next with nothing chosen must stay put and say why")
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        if tab.evaluate(SIGNUP_PARTS_JS) != ["seeking"]:
            faults.append(f"{where}: a tapped single answer did not move on by itself")
        before = tab.locator(f".{name}-members img").evaluate_all("els => els.map(e => e.src)")
        tap(tab, face.format("lf", 1))
        tap(tab, face.format("lf", 2))
        tab.wait_for_timeout(600)
        after = tab.locator(f".{name}-members img").evaluate_all("els => els.map(e => e.src)")
        if len(after) != 4:
            faults.append(f"{where}: four members should show once 'looking for' is answered")
        elif before and not set(after) - set(before):
            faults.append(f"{where}: answering 'looking for' showed the same four faces again, with "
                          f"unseen members in the results")
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        # The preview's places are a sample that will not load: the step goes.
        if tab.evaluate(SIGNUP_PARTS_JS) != ["dob"]:
            faults.append(f"{where}: places that will not load left the card on "
                          f"{tab.evaluate(SIGNUP_PARTS_JS)!r}, not the date of birth")
        for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
            tab.fill(f'input[name="{field}"]', value)
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        for chips in ("intent", "enjoy"):
            if tab.evaluate(SIGNUP_PARTS_JS) == [chips]:
                tap(tab, f'[data-hub-signup-part="{chips}"] .{name}-chip')
                tap(tab, f".{name}-next")
                tab.wait_for_timeout(500)
        if tab.evaluate(SIGNUP_PARTS_JS) != ["email"]:
            return faults + [f"{where}: the steps never reached the last one "
                             f"(stopped on {tab.evaluate(SIGNUP_PARTS_JS)!r})"]
        tab.locator('[data-hub-signup-part="email"] input').first.fill("Sam Lee")
        tab.fill('input[name="em"]', "sam@example.com")
        tab.check('[data-hub-signup-part="email"] input[type="checkbox"]')
        tap(tab, f".{name}-submit")
        tab.wait_for_timeout(400)
        url = tab.evaluate("() => window.__signupHandoff || null")
    finally:
        tab.close()
    if not url:
        return faults + [f"{where}: the last step handed nothing off"]
    query = url.split("?", 1)[-1]
    fields = dict(pair.split("=", 1) for pair in query.split("&") if "=" in pair)
    if not url.startswith(SIGNUP_JOIN + "?"):
        faults.append(f"{where}: handed off to {url.split('?')[0]!r}, not the join link")
    if fields.get("lf") != "3":
        faults.append(f"{where}: 'looking for' men and women sent as lf={fields.get('lf')!r} - "
                      f"the answers are summed, 3")
    if "+" in query:
        faults.append(f"{where}: the hand-off carries '+', which the join flow does not read as a space")
    if fields.get("firstname") != "Sam%20Lee":
        faults.append(f"{where}: a first name with a space sent as {fields.get('firstname')!r}")
    if "%3B" not in fields.get("interests", ""):
        faults.append(f"{where}: two interests sent as {fields.get('interests')!r} - "
                      f"a list separated by %3B")
    if "p" in fields:
        faults.append(f"{where}: a password was sent")
    # What every join link on the platform carries: the page's own parameters,
    # the first of each, and its pn attribution, ~ and / written plain.
    carried = {k: fields.get(k) for k in ("utm_source", "utm_medium", "cmp", "gclid")}
    if carried != {"utm_source": "s", "utm_medium": "m", "cmp": "abc", "gclid": "g"}:
        faults.append(f"{where}: the page's own parameters arrived as {carried!r} - each is passed "
                      f"on as it came, the first of each")
    if not fields.get("pn", "").startswith("ai~canvas-studio~abc123def456~/") or "%2F" in fields.get("pn", ""):
        faults.append(f"{where}: pn sent as {fields.get('pn')!r} - ai~<template>~<page>~<path>, "
                      f"as the platform writes it on every join link")
    # A brand with one possible answer to each: the questions are hidden
    # values, nobody is asked them, and each value is sent once.
    single = re.sub(rf'<fieldset class="{name}-step" data-hub-signup-part="(iam|seeking)">.*?</fieldset>',
                    lambda m: f'<input type="hidden" name="{"mt" if m.group(1) == "iam" else "lf"}" value="1">',
                    html, flags=re.S)
    tab = shell.open(single, f"{name}-signup-single", width=PHONE, before=signup_stub(SIGNUP_MEMBERS))
    try:
        tab.wait_for_timeout(300)
        opening = tab.evaluate(SIGNUP_PARTS_JS)
        for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
            tab.fill(f'input[name="{field}"]', value)
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        for chips in ("intent", "enjoy"):
            if tab.evaluate(SIGNUP_PARTS_JS) == [chips]:
                tap(tab, f'[data-hub-signup-part="{chips}"] .{name}-chip')
                tap(tab, f".{name}-next")
                tab.wait_for_timeout(500)
        tab.locator('[data-hub-signup-part="email"] input').first.fill("Sam")
        tab.fill('input[name="em"]', "sam@example.com")
        tab.check('[data-hub-signup-part="email"] input[type="checkbox"]')
        tap(tab, f".{name}-submit")
        tab.wait_for_timeout(400)
        single_url = tab.evaluate("() => window.__signupHandoff || ''")
    finally:
        tab.close()
    if opening != ["dob"]:
        faults.append(f"{where}: with both questions fixed the card opens on {opening!r}, not the date of birth")
    sent = single_url.split("?", 1)[-1].split("&")
    if sent.count("mt=1") != 1 or sent.count("lf=1") != 1:
        faults.append(f"{where}: fixed answers must be sent once each - got "
                      f"{[x for x in sent if x.startswith(('mt=', 'lf='))]!r}")
    # Where the visitor lives: a county page asks only the town, offers its
    # biggest towns from the first tap and the rest as they are typed, narrows
    # the members to the one picked, and sends its coordinates. The keyboard
    # picks it, which a finger cannot miss.
    def with_places(scope):
        page = re.sub(r'\sdata-hub-signup-places="[^"]*"', "", html, count=1)
        return page.replace('data-hub-module="signup"',
                            f'data-hub-module="signup" data-hub-signup-places="{scope}" '
                            f'data-hub-signup-places-from="{SIGNUP_PLACES}"', 1)
    placed = with_places("UK/England: Greater London")
    searches = []
    tab = shell.open(placed, f"{name}-signup-places", width=PHONE,
                     before=signup_stub(SIGNUP_MEMBERS, searches))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(700)
        asked_where = tab.evaluate(SIGNUP_PARTS_JS)
        town = f'[data-hub-signup-part="location"] input[role="combobox"]'
        offered, first_tap, town_attrs = [], [], {}
        if asked_where == ["location"]:
            town_attrs = tab.locator(town).evaluate(TOWN_JS)
            tab.locator(town).focus()
            tab.wait_for_timeout(300)
            first_tap = tab.locator(f".{name}-places [role=option]").all_inner_texts()
            tab.locator(town).press_sequentially("lond", delay=40)
            tab.wait_for_timeout(300)
            offered = tab.locator(f".{name}-places [role=option]").all_inner_texts()
            tab.locator(town).press("ArrowDown")
            tab.locator(town).press("Enter")
            tab.wait_for_timeout(600)
            tap(tab, f".{name}-next")
            tab.wait_for_timeout(500)
        for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
            tab.fill(f'input[name="{field}"]', value)
        tab.wait_for_timeout(700)
        dob_searched = any("ageMin=" in u for u in searches)
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        for chips in ("intent", "enjoy"):
            if tab.evaluate(SIGNUP_PARTS_JS) == [chips]:
                tap(tab, f".{name}-skip" if chips == "enjoy" else f'[data-hub-signup-part="{chips}"] .{name}-chip')
                if chips != "enjoy":
                    tap(tab, f".{name}-next")
                tab.wait_for_timeout(500)
        tab.locator('[data-hub-signup-part="email"] input').first.fill("Sam")
        tab.fill('input[name="em"]', "sam@example.com")
        tab.check('[data-hub-signup-part="email"] input[type="checkbox"]')
        tap(tab, f".{name}-submit")
        tab.wait_for_timeout(400)
        placed_url = tab.evaluate("() => window.__signupHandoff || ''")
    finally:
        tab.close()
    uk = json.loads((ROOT / "lib" / "places" / "uk.json").read_text(encoding="utf-8"))["regions"]
    london = uk["England: Greater London"]["London"]
    sent = dict(x.split("=", 1) for x in placed_url.split("?", 1)[-1].split("&") if "=" in x)
    if asked_where == ["location"]:
        ac = (town_attrs.get("autocomplete") or "").strip().lower()
        if ac in TOWN_AUTOCOMPLETE_IGNORED or ac not in TOWN_AUTOCOMPLETE_ACCEPTED:
            faults.append(f"{where}: the town field says autocomplete={town_attrs.get('autocomplete')!r} - "
                          f"Chrome reads that as no word and offers saved addresses over the "
                          f"card's list; one of {sorted(TOWN_AUTOCOMPLETE_ACCEPTED)}")
        if town_attrs.get("name") or town_attrs.get("id"):
            faults.append(f"{where}: the town field carries name={town_attrs.get('name')!r} "
                          f"id={town_attrs.get('id')!r}, which browsers match to an address")
        if (town_attrs.get("role"), town_attrs.get("ariaAutocomplete"), town_attrs.get("listRole")) \
                != ("combobox", "list", "listbox") or town_attrs.get("expanded") not in ("true", "false") \
                or not town_attrs.get("label"):
            faults.append(f"{where}: the town field is no longer a labelled combobox over a "
                          f"listbox: {town_attrs!r}")
    if asked_where != ["location"]:
        faults.append(f"{where}: with places the step after 'looking for' was {asked_where!r}, not where they live")
    elif not first_tap or first_tap[0] != "London":
        faults.append(f"{where}: the first tap on the town field offered {first_tap!r} - the region's "
                      f"biggest towns, London first")
    elif not offered or offered[0] != "London":
        faults.append(f"{where}: typing 'lond' offered {offered!r} - the region's towns, London first")
    elif (sent.get("lat"), sent.get("long")) != (str(london[0]), str(london[1])):
        faults.append(f"{where}: London sent as lat={sent.get('lat')!r} long={sent.get('long')!r}, "
                      f"not its coordinates {london!r}")
    if not dob_searched:
        faults.append(f"{where}: a full date of birth brought no members of that age before the next step")
    if not any("city=London" in u and "region=England%3A+Greater+London" in u and "country=UK" in u
               for u in searches):
        faults.append(f"{where}: no member search narrowed to London, England: Greater London, UK")
    # A small county offers its few towns as a list to pick from, not a field.
    tab = shell.open(with_places("UK/England: Avon"), f"{name}-signup-places-few", width=PHONE,
                     before=signup_stub(SIGNUP_MEMBERS))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(700)
        pick = tab.locator(f'[data-hub-signup-part="location"] select')
        few = pick.count() == 1 and pick.is_visible() and \
            not tab.locator('[data-hub-signup-part="location"] input[role="combobox"]').is_visible()
        towns = pick.locator("option").all_inner_texts() if pick.count() else []
    finally:
        tab.close()
    if not few or "Bristol" not in towns:
        faults.append(f"{where}: a county of {len(uk['England: Avon'])} towns should offer them as a list "
                      f"to pick from (got {towns!r})")
    # Two copies of the bundle on one page - a page's own tag and the
    # platform's - build the card once.
    twice = html.replace('<script type="module" src="hub.js"></script>',
                         '<script type="module" src="hub.js"></script>\n'
                         '<script type="module" src="hub.js?again"></script>', 1)
    tab = shell.open(twice, f"{name}-signup-twice", width=PHONE, before=signup_stub(SIGNUP_MEMBERS))
    try:
        tab.wait_for_timeout(600)
        tops = tab.locator(f".{name}-top").count()
        if tops != 1:
            faults.append(f"{where}: with the bundle on the page twice the card was built {tops} times")
        elif tab.locator(f".{name}-submit").is_visible():
            faults.append(f"{where}: with the bundle on the page twice the first step shows the join button")
    finally:
        tab.close()
    # A US card asks the ZIP code first: a known code hands the join flow the
    # code itself and narrows the members to its town; an unknown one says so
    # and does not move on. Asked for the lists first, the code is a tap away.
    zipped = with_places("USA")
    zip_searches = []
    tab = shell.open(zipped, f"{name}-signup-zip", width=PHONE, before=signup_stub(SIGNUP_MEMBERS, zip_searches))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(900)
        code = tab.locator('[data-hub-signup-part="location"] input[autocomplete="postal-code"]')
        zip_first = code.count() == 1 and code.is_visible()
        unknown_said = stayed = False
        if zip_first:
            code.fill("00000")
            tab.wait_for_timeout(600)
            unknown_said = tab.locator(f".{name}-postal .{name}-place-note[data-hub-signup-warn]").is_visible()
            tap(tab, f".{name}-next")
            tab.wait_for_timeout(400)
            stayed = tab.evaluate(SIGNUP_PARTS_JS) == ["location"]
            code.fill("10001")
            tab.wait_for_timeout(900)
            tap(tab, f".{name}-next")
            tab.wait_for_timeout(500)
        for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
            tab.fill(f'input[name="{field}"]', value)
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        for chips in ("intent", "enjoy"):
            if tab.evaluate(SIGNUP_PARTS_JS) == [chips]:
                tap(tab, f".{name}-skip" if chips == "enjoy" else f'[data-hub-signup-part="{chips}"] .{name}-chip')
                if chips != "enjoy":
                    tap(tab, f".{name}-next")
                tab.wait_for_timeout(500)
        tab.locator('[data-hub-signup-part="email"] input').first.fill("Sam")
        tab.fill('input[name="em"]', "sam@example.com")
        tab.check('[data-hub-signup-part="email"] input[type="checkbox"]')
        tap(tab, f".{name}-submit")
        tab.wait_for_timeout(400)
        zip_url = tab.evaluate("() => window.__signupHandoff || ''")
    finally:
        tab.close()
    zip_sent = dict(x.split("=", 1) for x in zip_url.split("?", 1)[-1].split("&") if "=" in x)
    if not zip_first:
        faults.append(f"{where}: a US card should ask the ZIP code first")
    else:
        if not unknown_said or not stayed:
            faults.append(f"{where}: an unknown ZIP code should say so and stay on the step "
                          f"(said {unknown_said}, stayed {stayed})")
        if zip_sent.get("zipCode") != "10001" or "lat" in zip_sent:
            faults.append(f"{where}: ZIP 10001 handed off as zipCode={zip_sent.get('zipCode')!r}"
                          f"{' with lat/long' if 'lat' in zip_sent else ''} - the code itself, and no coordinates")
        if not any("region=New+York" in u and "city=New+York" in u for u in zip_searches):
            faults.append(f"{where}: ZIP 10001 did not narrow the members to New York, New York")
    tab = shell.open(zipped.replace('data-hub-signup-places="USA"', 'data-hub-signup-places="USA" data-hub-signup-postal="lists"', 1),
                     f"{name}-signup-zip-lists", width=PHONE, before=signup_stub(SIGNUP_MEMBERS))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(900)
        lists_first = tab.locator('[data-hub-signup-part="location"] select').first.is_visible()
        switch = tab.locator(f".{name}-switch", has_text="ZIP")
        offered = switch.count() > 0 and switch.first.is_visible()
    finally:
        tab.close()
    if not lists_first or not offered:
        faults.append(f"{where}: postal=lists should show the state list with the ZIP code a tap away "
                      f"(list {lists_first}, link {offered})")
    # A failed search leaves nothing behind.
    tab = shell.open(html, f"{name}-signup-failed", width=PHONE, before=signup_stub(None))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tab.wait_for_timeout(600)
        if tab.locator(f".{name}-members").is_visible():
            faults.append(f"{where}: a failed member search left the strip showing")
    finally:
        tab.close()
    # A page in another language keeps its answers' capitals in the line of
    # answers so far: German nouns are written with a capital.
    german = html.replace('data-hub-module="signup"', 'data-hub-module="signup" lang="de"', 1)
    german = german.replace("<span>Sample: men</span>", "<span>Männer</span>", 1)
    tab = shell.open(german, f"{name}-signup-summary-de", width=PHONE, before=signup_stub(SIGNUP_MEMBERS))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tab.wait_for_timeout(400)
        recap = tab.locator(f".{name}-summary").inner_text().strip()
    finally:
        tab.close()
    if "Männer" not in recap:
        faults.append(f"{where}: a German page's answers so far read {recap!r} - the answer "
                      f"'Männer' keeps its capital outside English")
    # Reduced motion still moves on, without waiting on a tick nobody sees drawn.
    tab = shell.open(html, f"{name}-signup-reduced", width=PHONE, reduced=True,
                     before=signup_stub([]))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(250)
        if tab.evaluate(SIGNUP_PARTS_JS) != ["seeking"]:
            faults.append(f"{where}: under reduced motion a tapped answer did not move on")
    finally:
        tab.close()
    # The date of birth by width: wheel on a phone and boxes from 60rem, a
    # date typed wide turning the wheels when the screen narrows; and a year
    # wheel asked to open at 30 opens there with day and month still blank.
    dob_js = (f"() => ({{ wheels: !!(document.querySelector('.{name}-wheels') || {{}}).offsetParent, "
              f"boxes: !!document.querySelector('.{name}-dob').offsetParent, "
              "values: ['dd', 'dm', 'dy'].map(n => document.forms[0].elements[n].value) })")

    def to_dob(attrs, width):
        tab = shell.open(html.replace('data-hub-module="signup"', f'data-hub-module="signup" {attrs}', 1),
                         f"{name}-signup-dob-{width}", width=width, before=signup_stub(SIGNUP_MEMBERS))
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(700)
        return tab
    by_width = 'data-hub-signup-dob="wheel" data-hub-signup-dob-wide="boxes"'
    for width, want in ((PHONE, (True, False)), (WIDTH, (False, True))):
        tab = to_dob(by_width, width)
        try:
            got = tab.evaluate(dob_js)
            if (got["wheels"], got["boxes"]) != want:
                faults.append(f"{where}: dob=wheel dob-wide=boxes at {width}px showed wheels {got['wheels']}, "
                              f"boxes {got['boxes']} - wheels on a phone, boxes from 60rem")
            if width == WIDTH and got["boxes"]:
                for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
                    tab.fill(f'input[name="{field}"]', value)
                tab.set_viewport_size({"width": PHONE, "height": HEIGHT})
                tab.wait_for_timeout(700)
                turned = tab.evaluate(f"() => Array.from(document.querySelectorAll('.{name}-wheel "
                                      "[aria-selected=true]')).map(li => li.dataset.hubSignupValue)")
                if turned != ["14", "8", "1992"] or tab.evaluate(dob_js)["values"] != ["14", "8", "1992"]:
                    faults.append(f"{where}: a date typed wide read {turned!r} on the wheels once the screen "
                                  f"narrowed - the wheels turn to what was typed, and keep it")
        finally:
            tab.close()
    tab = to_dob('data-hub-signup-dob="wheel" data-hub-signup-dob-start="30"', PHONE)
    try:
        opened = tab.evaluate(dob_js)["values"]
    finally:
        tab.close()
    year = str(__import__("datetime").date.today().year - 30)
    if opened != ["", "", year]:
        faults.append(f"{where}: dob-start=30 opened the wheels on {opened!r} - the year {year}, "
                      f"day and month blank")
    # The lines after an answer are the card's; the older block has none.
    return faults + (check_signup_messages(shell, name, tokens) if name == "signup-card" else [])


def messages_stub(members, platform_file):
    """signup_stub, and the message files: the library's own step lines, and
    `platform_file` served as affinity.json, standing in for a platform's."""
    base = signup_stub(members)

    def before(tab):
        base(tab)

        def lines(route):
            file = route.request.url.rsplit("/", 1)[-1]
            if file == "steps.json":
                body = (ROOT / "lib" / "messages" / "steps.json").read_text(encoding="utf-8")
            elif file == "affinity.json" and platform_file is not None:
                body = json.dumps(platform_file)
            else:
                route.fulfill(status=404, body="")
                return
            route.fulfill(status=200, content_type="application/json",
                          headers={"Access-Control-Allow-Origin": "*"}, body=body)
        tab.route(SIGNUP_MESSAGES + "**", lines)
    return before


def check_signup_messages(shell, name, tokens):
    """The encouraging line: one after each answer, from the library's lines,
    the page's own and its platform's, never the same twice in a visit. Off is
    off, and a platform file that says it is another platform's is never read,
    because one platform's lines are written for adults."""
    where = f"{name} signup messages"
    faults = []
    steps = json.loads((ROOT / "lib" / "messages" / "steps.json").read_text(encoding="utf-8"))["steps"]
    html = re.sub(r'\sdata-hub-signup-(platform|say-[a-z]+|messages[a-z-]*)="[^"]*"', "",
                  page_for(name, "signup", tokens, "hub.js", PHONE))
    face = 'input[name="{0}"][value="{1}"] + .' + name + '-opt-face'
    chip = '[data-hub-signup-part="intent"] .' + name + '-chip:nth-child({0}) label'
    platform = {"platform": "affinity", "interests": {
        "Sample one": ["Affinity line for sample one."], "Sample two": ["Affinity line for sample two."]}}

    def filled(lines, key, value):
        out = set()
        for line in lines:
            line = line.replace("{" + key + "}", value)
            out.add(line.replace("{" + key.capitalize() + "}", value[:1].upper() + value[1:]))
        return out

    def page(attrs):
        return html.replace('data-hub-module="signup"', f'data-hub-module="signup" '
                            f'data-hub-signup-messages-from="{SIGNUP_MESSAGES}" {attrs}', 1)

    def said(tab):
        tab.wait_for_timeout(300)
        box = tab.locator(f".{name}-cheer")
        return box.inner_text().strip() if box.count() and box.is_visible() else None

    def to_intent(tab):
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
            tab.fill(f'input[name="{field}"]', value)
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        return tab.evaluate(SIGNUP_PARTS_JS) == ["intent"]

    # The library's lines, the page's own for one label, and the platform's.
    tab = shell.open(page('data-hub-signup-platform="affinity" '
                          'data-hub-signup-say-labels="Sample two: Page line for sample two."'),
                     f"{name}-signup-messages", width=PHONE, before=messages_stub(SIGNUP_MEMBERS, platform))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        first = said(tab)
        tab.wait_for_timeout(600)
        tap(tab, face.format("lf", 1))
        seeking = said(tab)
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
            tab.fill(f'input[name="{field}"]', value)
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        ticked = []
        for n in (1, 2, 3):
            tap(tab, chip.format(n))
            ticked.append(said(tab))
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        if tab.evaluate(SIGNUP_PARTS_JS) == ["enjoy"]:
            tap(tab, f".{name}-skip")
            tab.wait_for_timeout(500)
        last = said(tab)
    finally:
        tab.close()
    if first not in steps["iam"]:
        faults.append(f"{where}: after 'I am' the card said {first!r}, not one of the library's lines")
    if seeking not in filled(steps["seeking"], "who", "sample: men"):
        faults.append(f"{where}: after 'looking for' the card said {seeking!r}, not a line playing "
                      f"the answer back")
    if ticked[0] != "Affinity line for sample one.":
        faults.append(f"{where}: an interest the platform has a line for said {ticked[0]!r}")
    if ticked[1] not in ("Page line for sample two.", "Affinity line for sample two."):
        faults.append(f"{where}: an interest with the page's own line and the platform's said {ticked[1]!r}")
    if ticked[2] not in filled(steps["interest"], "interest", "Sample three"):
        faults.append(f"{where}: an interest with no line of its own said {ticked[2]!r}, not a general one")
    if last not in steps["last"]:
        faults.append(f"{where}: the last step said {last!r}, not one of the library's lines")

    # A file that says it is the other platform's is not read.
    wrong = dict(platform, platform="excite")
    tab = shell.open(page('data-hub-signup-platform="affinity"'), f"{name}-signup-messages-wrong",
                     width=PHONE, before=messages_stub(SIGNUP_MEMBERS, wrong))
    try:
        tab.wait_for_timeout(300)
        reached = to_intent(tab)
        tap(tab, chip.format(1))
        line = said(tab)
    finally:
        tab.close()
    if not reached or line not in filled(steps["interest"], "interest", "Sample one"):
        faults.append(f"{where}: an interest file saying it is another platform's was read ({line!r})")

    # The page's own lines only, and never the same one twice.
    mine = ["One of the page's lines.", "Another of the page's lines.", "A third of the page's lines."]
    tab = shell.open(page('data-hub-signup-say-mode="replace" data-hub-signup-say-iam="Hello from the page." '
                          f'data-hub-signup-say-interest="{";".join(mine)}"'),
                     f"{name}-signup-messages-own", width=PHONE, before=messages_stub(SIGNUP_MEMBERS, None))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        hello = said(tab)
        tab.wait_for_timeout(600)
        tap(tab, face.format("lf", 1))
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
            tab.fill(f'input[name="{field}"]', value)
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(500)
        again = []
        for _ in range(3):
            tap(tab, chip.format(1))
            again.append(said(tab))
            tap(tab, chip.format(1))
    finally:
        tab.close()
    if hello != "Hello from the page.":
        faults.append(f"{where}: say-mode=replace said {hello!r} after 'I am', not the page's own line")
    if sorted(again) != sorted(mine):
        faults.append(f"{where}: three ticks of one interest said {again!r} - each of the page's three "
                      f"lines once, none repeated")

    # A page in another language speaks only its own lines.
    tab = shell.open(page('lang="de" data-hub-signup-say-iam="Guter Anfang."'), f"{name}-signup-messages-de",
                     width=PHONE, before=messages_stub(SIGNUP_MEMBERS, platform))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        german = said(tab)
        tab.wait_for_timeout(600)
        tap(tab, face.format("lf", 1))
        unsaid = said(tab)
    finally:
        tab.close()
    if german != "Guter Anfang." or unsaid != german:
        faults.append(f"{where}: a German page said {german!r} then {unsaid!r} - only its own line, "
                      f"and nothing where it has none")

    # A town typed in full is settled without the list, and said all the same.
    placed = re.sub(r'\sdata-hub-signup-places(-from)?="[^"]*"', "", page(
        'data-hub-signup-say-mode="replace" data-hub-signup-say-location="{Place} it is."'))
    placed = placed.replace('data-hub-module="signup"', 'data-hub-module="signup" data-hub-signup-places='
                            f'"UK/England: Greater London" data-hub-signup-places-from="{SIGNUP_PLACES}"', 1)
    tab = shell.open(placed, f"{name}-signup-messages-place", width=PHONE,
                     before=messages_stub(SIGNUP_MEMBERS, platform))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tap(tab, f".{name}-next")
        tab.wait_for_timeout(700)
        town = tab.locator('[data-hub-signup-part="location"] input[role="combobox"]')
        typed = None
        if town.count():
            town.focus()
            town.press_sequentially("Islington", delay=30)
            typed = said(tab)
    finally:
        tab.close()
    if typed != "Islington it is.":
        faults.append(f"{where}: a town typed in full said {typed!r}, not the page's line for it")

    # Back takes the line away: it answers the step just left, not the one
    # returned to. On a phone and on a wide screen, where two questions share
    # a step.
    for width, label in ((PHONE, "a phone"), (WIDTH, "a wide screen")):
        tab = shell.open(page(""), f"{name}-signup-messages-back-{width}", width=width,
                         before=messages_stub(SIGNUP_MEMBERS, platform))
        try:
            tab.wait_for_timeout(300)
            tap(tab, face.format("mt", 2))
            tab.wait_for_timeout(900)
            tap(tab, face.format("lf", 1))
            before_back = said(tab)
            if width == WIDTH:
                tap(tab, f".{name}-next")
                tab.wait_for_timeout(500)
            tap(tab, f".{name}-back")
            tab.wait_for_timeout(500)
            after_back = said(tab)
            returned = tab.evaluate(SIGNUP_PARTS_JS)
        finally:
            tab.close()
        if before_back is None:
            faults.append(f"{where}: on {label} 'looking for' said nothing, so Back could not be checked")
        elif after_back is not None:
            faults.append(f"{where}: on {label} Back to {returned!r} still showed {after_back!r} - "
                          f"the line answers the step left, not the one returned to")

    # Off is off, and the card still works.
    tab = shell.open(page('data-hub-signup-messages="off"'), f"{name}-signup-messages-off",
                     width=PHONE, before=messages_stub(SIGNUP_MEMBERS, platform))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        quiet = said(tab)
        tab.wait_for_timeout(600)
        moved = tab.evaluate(SIGNUP_PARTS_JS) == ["seeking"]
    finally:
        tab.close()
    if quiet is not None or not moved:
        faults.append(f"{where}: messages=off said {quiet!r}{'' if moved else ' and did not move on'}")
    return faults


# ------------------------------------------------------------ compatibility

"""THE PREVIOUS BUNDLE. lib/hub.js is served to every live page from the
floating URL, so a page built long ago meets whatever is newest. Every new
setting is opt-in, and --compat holds the bundle to that: a carousel or
marquee block that sets none of the settings added since the last published
bundle has to come out of this bundle exactly as it came out of that one -
the same controls, in the same place, with the same words, moving the rail
the same way. The blocks are each carousel pattern as released (the tag in
LATEST, read from git) and as it stands, both with every --hub-carousel-*,
--hub-marquee-* and matching data-hub-* setting taken out. The other way
round, today's markup, settings and all, has to fall back on the previous
bundle to the controls that bundle knows, with nothing thrown.

--compat --broken swaps one line of the bundle so a block with no settings
draws the new look anyway, and requires the comparison to fire."""

COMPAT_CONTROL = ('if (round) controls.classList.add("hub-carousel-controls--round");',
                  'controls.classList.add("hub-carousel-controls--round");')
SETTING_CSS = re.compile(r"--hub-(?:carousel|marquee)-[\w-]+\s*:[^;{}]*;?")
SETTING_ATTR = re.compile(r'\s+data-hub-(?:carousel-(?:controls|look|phone)|marquee-(?:look|fit))="[^"]*"')
# (label, pattern, rung class to swap in, or None; module list to swap in, or None)
COMPAT_BLOCKS = [
    ("gallery-scroll", "gallery-scroll", None, None),
    ("testimonial-carousel", "testimonial-carousel", None, None),
    ("member-grid rail", "member-grid", ("member-grid--grid", "member-grid--rail"), None),
    ("member-grid marquee", "member-grid", ("member-grid--grid", "member-grid--marquee"), "marquee"),
]

COMPAT_JS = """
() => Array.from(document.querySelectorAll('[data-hub-module]')).map(block => {
  const built = Array.from(block.querySelectorAll('.hub-carousel-controls, .hub-marquee-control'));
  const box = el => { const r = el.getBoundingClientRect();
    return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; };
  return {
    module: block.getAttribute('data-hub-module'),
    used: block.getAttribute('data-hub-carousel-controls-used'),
    built: built.map(el => ({ html: el.outerHTML,
      at: Array.prototype.indexOf.call(el.parentNode.children, el),
      parent: el.parentNode === block ? 'block' : el.parentNode.className,
      box: box(el), shown: el.offsetParent !== null })),
  };
})
"""


def previous_bundle():
    """The newest published bundle older than the one in lib/, as (version, path)."""
    root = ROOT / "publish" / "hub-behaviours"
    now = tuple(int(n) for n in bundle_version().split("."))
    found = []
    for d in root.iterdir() if root.is_dir() else []:
        if re.fullmatch(r"\d+\.\d+\.\d+", d.name) and (d / "hub.js").is_file():
            v = tuple(int(n) for n in d.name.split("."))
            if v < now:
                found.append((v, d))
    if not found:
        return None, None
    v, d = max(found)
    return ".".join(map(str, v)), d / "hub.js"


def released(name):
    """(markup, css) of a pattern at the release LATEST names, or None."""
    import subprocess
    tag = (ROOT / "LATEST").read_text(encoding="utf-8").strip()
    got = []
    for f in ("pattern.html", "pattern.css", "preview-content.json"):
        r = subprocess.run(["git", "show", f"{tag}:patterns/{name}/{f}"], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            return None
        got.append(r.stdout)
    return tag, got


def compat_page(html_text, css, sample, rung, module, tokens, bundle, strip):
    markup = re.sub(r"\s*<!--\n.*?\n-->", "", html_text, count=1, flags=re.S)
    markup = fill(markup, sample)
    repeat = sample.get("_repeat")
    if repeat:
        markup = repeat_block(markup, repeat["class"], int(repeat["count"]))
    if rung:
        markup = markup.replace(rung[0], rung[1], 1)
        if 'class="mem-card"' in markup:
            markup = repeat_block(markup, "mem-card", 12)
    if module:
        markup = re.sub(r'data-hub-module="[^"]*"',
                        lambda m: m.group(0).replace("reveal", module), markup, count=1)
    if strip:
        css = SETTING_CSS.sub("", css)
        markup = SETTING_ATTR.sub("", markup)
    return SHELL.format(title="compat", tokens=tokens, css=css, bundle=bundle,
                        before="", markup=markup,
                        after='<section class="behaviour-check-section">' + FILLER + "</section>")


def compat_snapshot(shell, html, stem, width, motion):
    errors = []

    def before(tab):
        tab.on("pageerror", lambda e: errors.append(str(e)))
    tab = shell.open(html, stem, width=width, reduced=not motion, before=before)
    try:
        tab.wait_for_timeout(250)
        snap = tab.evaluate(COMPAT_JS)
        moved = None
        if not motion and tab.locator(".hub-carousel-next").count():
            tab.evaluate("() => document.querySelector('.hub-carousel-next').click()")
            tab.wait_for_timeout(250)
            moved = tab.evaluate("""() => {
              const r = Array.from(document.querySelectorAll('input[type=radio]')).findIndex(i => i.checked);
              const s = Array.from(document.querySelectorAll('ul, ol')).find(l => /^(auto|scroll)$/.test(getComputedStyle(l).overflowX))
                || document.querySelector('[data-hub-module]');
              return [r, Math.round(s.scrollLeft)]; }""")
    finally:
        tab.close()
    if motion:
        # A moving rail is at a different place at every read, and the ends
        # it has reached with it: which control is disabled is the rail's
        # position, not the bundle's, so it is left out of the comparison.
        for block in snap:
            for b in block["built"]:
                b["html"] = re.sub(r' aria-disabled="(true|false)"', "", b["html"])
    return {"blocks": snap, "moved": moved, "errors": errors}


def placements_known(source):
    """The control placements a bundle builds, read from its own source:
    "under" is every bundle's fallback, and the rest are the ones it tests
    for by name."""
    named = {p for p in ("edges", "top")
             if re.search(rf'placement\s*[!=]==\s*"{p}"|\[[^\]]*"{p}"[^\]]*\]\.includes\(placement\)',
                          source)}
    return {"under"} | named


def check_compat(shell, tokens, broken):
    version, old = previous_bundle()
    if not old:
        return ["compat: no earlier bundle is published under publish/hub-behaviours - "
                "nothing to hold this one to"], 0
    shutil.copy(old, shell._dir / "hub-previous.js")
    known = placements_known(old.read_text(encoding="utf-8"))
    moving = "hub.js"
    if broken:
        source = (shell._dir / "hub.js").read_text(encoding="utf-8")
        for control in (COMPAT_CONTROL, MOTION_COMPAT_CONTROL):
            if control[0] not in source:
                raise SystemExit(f"control: the compat substitution {control[0]!r} no "
                                 f"longer matches lib/hub.js")
        moving = "hub-still.js"
        (shell._dir / moving).write_text(source.replace(*MOTION_COMPAT_CONTROL, 1),
                                         encoding="utf-8", newline="\n")
        (shell._dir / "hub.js").write_text(source.replace(*COMPAT_CONTROL, 1),
                                           encoding="utf-8", newline="\n")
    faults, count = [], 0
    for label, name, rung, module in COMPAT_BLOCKS:
        folder = PATTERNS / name
        forms = [("as it stands", (folder / "pattern.html").read_text(encoding="utf-8"),
                  (folder / "pattern.css").read_text(encoding="utf-8"),
                  json.loads((folder / "preview-content.json").read_text(encoding="utf-8")))]
        rel = released(name)
        if rel:
            tag, (h, c, j) = rel
            forms.insert(0, (f"as released in {tag}", h, c, json.loads(j)))
        else:
            faults.append(f"compat: {name} could not be read at the release LATEST names")
        for form, h, c, sample in forms:
            for width in (WIDTH, PHONE):
                for motion in ((False, True) if module else (False,)):
                    new = compat_page(h, c, sample, rung, module, tokens, "hub.js", True)
                    prev = compat_page(h, c, sample, rung, module, tokens, "hub-previous.js", True)
                    a = compat_snapshot(shell, new, "compat-new", width, motion)
                    b = compat_snapshot(shell, prev, "compat-prev", width, motion)
                    count += 1
                    where = f"compat: {label} {form}, no settings, {width}px"
                    if a["errors"]:
                        faults.append(f"{where}: the bundle threw {a['errors'][0]}")
                    if a["blocks"] != b["blocks"]:
                        faults.append(f"{where}: the controls differ from {version}'s - "
                                      f"{json.dumps(a['blocks'])[:300]} against "
                                      f"{json.dumps(b['blocks'])[:300]}")
                    if a["moved"] != b["moved"]:
                        faults.append(f"{where}: next moves the block to {a['moved']} where "
                                      f"{version} moved it to {b['moved']}")
        # Today's markup, settings and all, on the previous bundle.
        h = (folder / "pattern.html").read_text(encoding="utf-8")
        c = (folder / "pattern.css").read_text(encoding="utf-8")
        sample = json.loads((folder / "preview-content.json").read_text(encoding="utf-8"))
        for width in (WIDTH, PHONE):
            prev = compat_page(h, c, sample, rung, module, tokens, "hub-previous.js", False)
            got = compat_snapshot(shell, prev, "compat-fallback", width, bool(module))
            count += 1
            where = f"compat: {label} as it stands on {version}, {width}px"
            if got["errors"]:
                faults.append(f"{where}: the previous bundle threw {got['errors'][0]}")
            carousel = [b for b in got["blocks"] if "carousel" in (b["module"] or "").split()]
            for b in carousel:
                if b["used"] not in known:
                    faults.append(f"{where}: fell back to {b['used']!r}, not a placement "
                                  f"{version} knows")
                built = [x for x in b["built"] if 'class="hub-carousel-controls' in x["html"]]
                if not built:
                    faults.append(f"{where}: no controls were built")
    more, renders = check_motion_compat(shell, tokens, version, moving)
    return faults + more, count + renders


# ------------------------------------------------ compatibility: motion

"""THE PAGES BUILT BEFORE THE SWITCH. Every page built from LIVE_REF or
earlier eases in, counts up or glides with no --hub-motion anywhere in its
styles, and keeps loading the newest bundle. So each block LIVE_REF shipped
that hooks reveal, counter or marquee, as it shipped it, has to move on this
bundle exactly as it moves on the last one published: the same items eased
in, the same figures counting and ending on the same text, the same glide,
and nothing at all under reduced motion.

--compat --broken also hands these pages a bundle that holds every block
still, and requires the comparison to fire."""

MOTION_HOOKS = {"reveal", "counter", "marquee"}
# A rung that moves by swapping its behaviour in rather than shipping it:
# (label, pattern, the class to swap, the module word to swap in).
MOTION_COMPAT_RUNGS = [
    ("member-grid marquee", "member-grid", ("member-grid--grid", "member-grid--marquee"), "marquee"),
]
MOTION_COMPAT_CONTROL = (CONTROL_SUBSTITUTIONS["still"][0], "const heldStill = (el) => true;")


def git_out(*args):
    got = subprocess.run(["git", *args], capture_output=True, cwd=ROOT)
    return got.stdout.decode("utf-8") if got.returncode == 0 else None


def shipped(name, ref=None):
    """pattern.html, pattern.css and the preview sample as `ref` (LIVE_REF
    by default) shipped them, or None for a pattern it did not have.
    Without the tag in the checkout the run stops: the pages built from it
    cannot be checked without it."""
    ref = ref or LIVE_REF
    if git_out("rev-parse", "--verify", "-q", f"{ref}^{{commit}}") is None:
        raise SystemExit(f"behaviours: {ref} is not in this checkout - run "
                         f"git fetch --tags so the pages built from it can be checked")
    out = []
    for part in ("pattern.html", "pattern.css", "preview-content.json"):
        got = git_out("show", f"{ref}:patterns/{name}/{part}")
        if got is None:
            return None
        out.append(got)
    return tuple(out)


def moving_at_live_ref():
    """(label, pattern, rung, module) for every block LIVE_REF shipped that
    eases in, counts up or glides."""
    listing = git_out("ls-tree", "--name-only", f"{LIVE_REF}:patterns") or ""
    blocks = []
    for name in sorted(n for n in listing.split() if n):
        files = shipped(name)
        if files is None:
            continue
        meta = lint.parse_header(files[0], PATTERNS / name / "pattern.html")
        hooks = {b.strip() for b in meta.get("behaviours", "").split(",")}
        if hooks & MOTION_HOOKS:
            blocks.append((name, name, None, None))
    have = {b[1] for b in blocks}
    blocks += [r for r in MOTION_COMPAT_RUNGS if r[1] in have]
    return blocks


def motion_snapshot(shell, html, stem, width, reduced, want_version):
    errors = []

    def before(tab):
        tab.on("pageerror", lambda e: errors.append(str(e)))
    tab = shell.open(html, stem, width=width, reduced=reduced, before=before)
    try:
        version = tab.evaluate(VERSION_JS)
        if version != want_version:
            return None, [f"the bundle did not run (version {version!r} on the page)"]
        tab.evaluate("() => document.querySelector('[data-hub-module]').scrollIntoView()")
        tab.wait_for_timeout(MOTION_LOOK_MS)
        look = tab.evaluate(MOTION_JS)
        settled = None
        if look["figures"]:
            tab.wait_for_timeout(COUNTER_SETTLE_MS)
            settled = tab.evaluate(MOTION_JS)["figures"]
    finally:
        tab.close()
    # A figure part-way through its count is wherever the clock put it, so
    # what is compared is that it was counting and where it ended.
    return {"revealed": look["revealed"], "pending": look["pending"],
            "marquee": look["marquee"],
            "counting": moved("counter", look) if look["figures"] else None,
            "ended": settled}, errors


def check_motion_compat(shell, tokens, version, bundle):
    """Each block LIVE_REF shipped that moves, on `bundle` and on the last
    published one: the two have to move it the same way."""
    faults, count = [], 0
    for label, name, rung, module in moving_at_live_ref():
        h, c, j = shipped(name)
        sample = json.loads(j)
        for width, reduced in ((WIDTH, False), (PHONE, False), (WIDTH, True)):
            new = with_figures(compat_page(h, c, sample, rung, module, tokens, bundle, False))
            prev = with_figures(compat_page(h, c, sample, rung, module, tokens,
                                            "hub-previous.js", False))
            a, a_err = motion_snapshot(shell, new, "motion-new", width, reduced, bundle_version())
            b, b_err = motion_snapshot(shell, prev, "motion-prev", width, reduced, version)
            count += 1
            where = (f"compat motion: {label} as {LIVE_REF} shipped it, {width}px"
                     + (", reduced motion" if reduced else ""))
            if a_err or b_err:
                faults.append(f"{where}: {(a_err or b_err)[0]}")
                continue
            if a != b:
                faults.append(f"{where}: moved as {a} where {version} moved it as {b}")
            elif not reduced and not any((a["revealed"], a["counting"], a["marquee"])):
                faults.append(f"{where}: nothing moved on either bundle - the check "
                              f"is measuring nothing")
    return faults, count


CHECKS = {"counter": check_counter, "scrollspy": check_scrollspy, "carousel": check_carousel,
          "signup": check_signup, "reveal": check_reveal}


def main():
    ap = argparse.ArgumentParser(description="Run the section behaviours for real "
                                             "and hold each to its registry row.")
    ap.add_argument("names", nargs="*", help="patterns to check (default: every "
                                             "pattern declaring one of the behaviours)")
    ap.add_argument("--tokens", default="brand")
    ap.add_argument("--broken", action="store_true",
                    help="the positive control: a copy of the bundle with one line "
                         "of each behaviour turned wrong; every check must fire")
    ap.add_argument("--compat", action="store_true",
                    help="hold the bundle to the last one published: a block with no "
                         "new setting builds the same controls, and today's markup "
                         "falls back on the old bundle")
    ap.add_argument("--out", help="write the rendered pages here")
    ap.add_argument("--require-browser", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    found = discover()
    names = args.names or sorted(found)
    for name in names:
        if name not in found:
            print(f"{name!r} declares none of {', '.join(BEHAVIOURS)}")
            return 2
    why = browser_unavailable()
    if why:
        if args.require_browser:
            print(f"FAIL behaviours: no browser, and --require-browser was asked for - {why}")
            return 1
        print(f"SKIPPED behaviours: {why}. A skip is not a pass.")
        return 0
    tokens = (PREVIEW / f"tokens-{args.tokens}.css").read_text(encoding="utf-8")
    if args.compat:
        with Shell(False) as shell:
            faults, count = check_compat(shell, tokens, args.broken)
        for line in faults:
            print(f"  FAIL  {line}")
        version = previous_bundle()[0]
        if args.broken:
            look = [f for f in faults if not f.startswith("compat motion:")]
            still = [f for f in faults if f.startswith("compat motion:")]
            if look and still:
                print(f"  control: {len(look)} fault(s) caught with the new look forced on "
                      f"a block that asked for none, and {len(still)} with every block "
                      f"{LIVE_REF} shipped held still. The gate fires.")
                return 0
            print("  CONTROL FAILED: " + ("the new look was forced on" if not look
                                         else f"every block {LIVE_REF} shipped was held still")
                  + " and nothing fired.")
            return 1
        if faults:
            return 1
        print(f"  clean: {count} render(s) - with no new setting the bundle builds what "
              f"{version} built, today's markup falls back on {version}, and every "
              f"block {LIVE_REF} shipped moves as {version} moved it")
        return 0
    print(f"behaviours: {len(names)} pattern(s) on the {args.tokens} tokens, bundle "
          f"{bundle_version()}" + ("  [control: one line of each turned wrong]" if args.broken else ""))
    print()
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for name in names:
            for behaviour in sorted(found[name]):
                (out / f"{name}--{behaviour}.html").write_text(
                    page_for(name, behaviour, tokens, "hub.js", WIDTH),
                    encoding="utf-8", newline="\n")

    fired = {b: 0 for b in BEHAVIOURS}
    faults = []
    still = []
    with Shell(args.broken) as shell:
        for name in names:
            for behaviour in sorted(found[name]):
                got = CHECKS[behaviour](shell, name, tokens)
                fired[behaviour] += len(got)
                faults.extend(got)
                print(f"  {name} {behaviour}: {'FAIL ' + str(len(got)) if got else 'ok'}")
        if not args.names:
            still = check_still_means_still(shell, tokens)
            faults.extend(still)
            print(f"  still means still: {'FAIL ' + str(len(still)) if still else 'ok'}")
    print()
    for line in faults:
        print(f"  FAIL  {line}")

    exercised = {b for n in names for b in found[n]}
    if args.broken:
        silent = [b for b in BEHAVIOURS if b in exercised and not fired[b]]
        if silent:
            print(f"  CONTROL FAILED: {', '.join(silent)} passed with a line turned "
                  f"wrong. This gate cannot see the thing it exists for.")
            return 1
        held = [b for b in STILL_BLOCKS
                if not args.names and not any(f.startswith(f"still {b}:") for f in still)]
        if held:
            print(f"  CONTROL FAILED: with the still switch turned off, "
                  f"{', '.join(held)} still held still. This gate cannot see "
                  f"the thing it exists for.")
            return 1
        print(f"  control: {len(faults)} fault(s) caught across "
              f"{', '.join(sorted(exercised))}. The gate fires.")
        return 0
    if not faults:
        print(f"  clean: {', '.join(sorted(exercised))} do what the registry says, "
              f"on {len(names)} pattern(s)")
    if args.out:
        print(f"\n  pages written to {args.out}")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
